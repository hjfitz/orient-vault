#!/usr/bin/env python3
"""FUSE-1078 step 2: copy routing (SHH/REH) and Shopify line ids (SHL) still held only in SNAP
attachments into the Firestore routing-metadata docs, for every open shipment/receipt and every
outbound-queue item of one business.

  survey: python3 fuse1078_backfill.py survey --business PURDYFIGG --creds creds.json --out plan_PURDYFIGG.json
  apply:  python3 fuse1078_backfill.py apply --plan plan_PURDYFIGG.json [--limit N]

survey is read-only (SNAP GETs, paced; Firestore batchGet). apply writes exactly the plan file's
entries, each with an update mask and an exists/absent precondition, so nothing else on a doc moves.
Every write stamps backfilledBy/backfilledAt so the set can be found again.
"""

import argparse
import base64
import datetime
import json
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter

PROJECT = "bifrost-prod-global1"
DATABASE = "fuse-wms-routing"
COLLECTION = "routing-metadata"
MARKER = "fuse-1078-backfill"
SNAP_PAGE = 500
SNAP_PAUSE_S = 1.0
FS_BATCH = 100


class Snap:
    def __init__(self, host: str, username: str, password: str):
        self.host = host.rstrip("/")
        self.auth = base64.b64encode(f"{username}:{password}".encode()).decode()
        self.calls = 0

    def get(self, path: str, **query):
        url = self.host + path + ("?" + urllib.parse.urlencode(query) if query else "")
        req = urllib.request.Request(
            url, headers={"Authorization": "Basic " + self.auth, "Accept": "application/json"}
        )
        self.calls += 1
        time.sleep(SNAP_PAUSE_S)
        for attempt in range(3):
            try:
                with urllib.request.urlopen(req, timeout=120) as resp:
                    body = json.load(resp)
                return body.get("Results", body) if isinstance(body, dict) else body
            except urllib.error.HTTPError as err:
                if err.code == 404:
                    return []
                if err.code < 500 or attempt == 2:
                    raise
            except (urllib.error.URLError, TimeoutError):
                if attempt == 2:
                    raise
            time.sleep(5 * (attempt + 1))
        return []

    def paged(self, path: str, flt: str, order: str):
        skip = 0
        while True:
            page = self.get(path, **{"$filter": flt, "$top": str(SNAP_PAGE), "$skip": str(skip), "$orderby": order})
            if not isinstance(page, list):
                raise RuntimeError(f"{path}: unexpected {str(page)[:200]}")
            yield from page
            if len(page) < SNAP_PAGE:
                return
            skip += SNAP_PAGE

    def attachments(self, table: str, key: str) -> list:
        rows = self.get(f"/v2/attachments/{table}/{urllib.parse.quote(key)}")
        if not isinstance(rows, list):
            return []
        return [r for r in rows if r.get("Key") == key and r.get("Table") == table and r.get("Type") == "TXT"]


def gcloud_token() -> str:
    return subprocess.run(["gcloud", "auth", "print-access-token"], capture_output=True, text=True, check=True).stdout.strip()


def fs_request(method: str, url: str, body=None):
    req = urllib.request.Request(url, data=json.dumps(body).encode() if body is not None else None, method=method)
    req.add_header("Authorization", f"Bearer {gcloud_token()}")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return resp.status, json.load(resp)
    except urllib.error.HTTPError as err:
        return err.code, json.loads(err.read() or b"{}")


def doc_name(business: str, entity_id: str) -> str:
    return f"projects/{PROJECT}/databases/{DATABASE}/documents/{COLLECTION}/{business}__{entity_id}"


def fs_batch_get(business: str, ids: list) -> dict:
    out = {}
    url = f"https://firestore.googleapis.com/v1/projects/{PROJECT}/databases/{DATABASE}/documents:batchGet"
    for i in range(0, len(ids), FS_BATCH):
        chunk = ids[i : i + FS_BATCH]
        status, body = fs_request("POST", url, {"documents": [doc_name(business, x) for x in chunk]})
        if status != 200:
            raise RuntimeError(f"batchGet {status}: {str(body)[:300]}")
        for item in body:
            if "found" in item:
                out[item["found"]["name"].rsplit("__", 1)[1]] = item["found"].get("fields", {})
    return out


def map_fields(value: dict) -> dict:
    return value.get("mapValue", {}).get("fields", {}) if value else {}


def doc_state(fields: dict | None) -> dict:
    if fields is None:
        return {"exists": False, "routing": {}, "has_lines": False}
    routing = {k: v.get("stringValue") for k, v in map_fields(fields.get("routing")).items() if v.get("stringValue")}
    has_lines = bool(map_fields(fields.get("lines"))) or bool(map_fields(fields.get("lineExtensions")))
    return {"exists": True, "routing": routing, "has_lines": has_lines, "entityId": "entityId" in fields}


def parse_body(text: str):
    try:
        body = json.loads(text or "")
    except ValueError:
        return None
    return body if isinstance(body, dict) else None


def routing_from(rows: list) -> dict:
    for row in rows:
        body = parse_body(row.get("AttachmentText"))
        routing = body.get("routing") if body else None
        if isinstance(routing, dict):
            picked = {k: routing[k] for k in ("connectorId", "source") if isinstance(routing.get(k), str) and routing[k]}
            if picked:
                return picked
    return {}


def shopify_lines_from(rows: list) -> dict:
    out = {}
    for row in rows:
        body = parse_body(row.get("AttachmentText"))
        shopify = body.get("shopify") if body else None
        if isinstance(shopify, dict) and isinstance(shopify.get("fulfillmentId"), str) and shopify["fulfillmentId"]:
            out[row["KeyLine"]] = {"fulfillmentId": shopify["fulfillmentId"]}
    return out


QUEUE_KEY = re.compile(r'(Shipment|Receipt)="([^"]+)"')


def survey(args) -> int:
    creds = json.load(open(args.creds))[args.business]
    snap = Snap(creds["host"], creds["username"], creds["password"])
    biz = args.business

    if args.shipments:
        shipments = {x: {"ShipmentId": x} for x in args.shipments.split(",")}
        receipts, queue = {}, []
    else:
        shipments = {s["ShipmentId"]: s for s in snap.paged("/v2/shipments", "Stage lt '90'", "ShipmentId")}
        receipts = {r["ReceiptId"]: r for r in snap.paged("/v2/receipts", "Stage lt '90'", "ReceiptId")}
        queue = snap.get("/v2/snapoutbound", **{"$top": "1000"})
    queued = Counter()
    for item in queue if isinstance(queue, list) else []:
        if item.get("Transaction") == "STOCK_MOVE":
            continue
        for kind, key in QUEUE_KEY.findall(item.get("Key") or ""):
            queued[kind] += 1
            if kind == "Shipment":
                shipments.setdefault(key, {"ShipmentId": key, "_queuedOnly": True})
            else:
                receipts.setdefault(key, {"ReceiptId": key, "_queuedOnly": True})

    docs = fs_batch_get(biz, sorted(set(shipments) | set(receipts)))
    stats = Counter(shipments=len(shipments), receipts=len(receipts), queued_shipments=queued["Shipment"], queued_receipts=queued["Receipt"])
    writes = []

    for kind, items, table in (("shipment", shipments, "SHH"), ("receipt", receipts, "REH")):
        for entity_id, entity in items.items():
            state = doc_state(docs.get(entity_id))
            stats[f"{kind}_doc_{'present' if state['exists'] else 'absent'}"] += 1
            routing = state["routing"]
            write = {}
            if not routing:
                found = routing_from(snap.attachments(table, entity_id))
                if found:
                    write["routing"] = found
                    routing = found
                    stats[f"{kind}_routing_from_attachment"] += 1
                else:
                    stats[f"{kind}_no_routing_anywhere"] += 1
            else:
                stats[f"{kind}_routing_in_store"] += 1

            if kind == "shipment" and routing.get("source") == "shopify":
                if state["has_lines"]:
                    stats["shopify_lines_in_store"] += 1
                else:
                    lines = shopify_lines_from(snap.attachments("SHL", entity_id))
                    if lines:
                        write["lineExtensions"] = lines
                        stats["shopify_lines_from_attachment"] += 1
                    else:
                        stats["shopify_no_lines_anywhere"] += 1

            if write:
                if kind == "shipment":
                    entity_type = "work_order" if entity.get("OrderType") == "S10" else "sales_order"
                else:
                    entity_type = (
                        "return_goods_authorization"
                        if entity.get("OrderClass") in ("CUSRTN", "WHSRTN")
                        else "purchase_order"
                    )
                writes.append(
                    {
                        "entityId": entity_id,
                        "kind": kind,
                        "exists": state["exists"],
                        "entityType": entity_type,
                        "queuedOnly": bool(entity.get("_queuedOnly")),
                        **write,
                    }
                )

    stats["writes_planned"] = len(writes)
    stats["writes_creating_doc"] = sum(1 for w in writes if not w["exists"])
    stats["snap_calls"] = snap.calls
    plan = {"business": biz, "project": PROJECT, "surveyedAt": datetime.datetime.now(datetime.timezone.utc).isoformat(), "stats": dict(stats), "writes": writes}
    json.dump(plan, open(args.out, "w"), indent=1)
    print(json.dumps({"business": biz, **dict(sorted(stats.items()))}))
    return 0


def string_value(v: str) -> dict:
    return {"stringValue": v}


def mapv(fields: dict) -> dict:
    return {"mapValue": {"fields": fields}}


def apply(args) -> int:
    plan = json.load(open(args.plan))
    biz = plan["business"]
    if plan.get("project", PROJECT) != PROJECT:
        sys.exit(f"plan was surveyed against {plan['project']}, not {PROJECT}")
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    done = failed = 0
    for entry in plan["writes"][: args.limit or None]:
        fields, mask = {}, []
        if "routing" in entry:
            fields["routing"] = mapv({k: string_value(v) for k, v in entry["routing"].items()})
            mask.append("routing")
        if "lineExtensions" in entry:
            fields["lineExtensions"] = mapv(
                {line: mapv({"shopify": mapv({"fulfillmentId": string_value(v["fulfillmentId"])})}) for line, v in entry["lineExtensions"].items()}
            )
            mask += [f"lineExtensions.`{line}`" for line in entry["lineExtensions"]]
        if not entry["exists"]:
            fields.update(businessId=string_value(biz), entityId=string_value(entry["entityId"]), entityType=string_value(entry["entityType"]))
            mask += ["businessId", "entityId", "entityType"]
        fields.update(backfilledBy=string_value(MARKER), backfilledAt={"timestampValue": now})
        mask += ["backfilledBy", "backfilledAt"]

        query = [("updateMask.fieldPaths", m) for m in mask]
        query.append(("currentDocument.exists", "true" if entry["exists"] else "false"))
        url = f"https://firestore.googleapis.com/v1/{doc_name(biz, entry['entityId'])}?{urllib.parse.urlencode(query)}"
        status, body = fs_request("PATCH", url, {"fields": fields})
        if status == 200:
            done += 1
        else:
            failed += 1
            print(f"FAILED {entry['entityId']}: {status} {str(body)[:200]}")
    print(json.dumps({"business": biz, "written": done, "failed": failed}))
    return 1 if failed else 0


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("survey")
    s.add_argument("--business", required=True)
    s.add_argument("--creds", required=True)
    s.add_argument("--out", required=True)
    s.add_argument("--shipments", help="explicit ShipmentIds instead of listing SNAP (targeted re-run)")
    a = sub.add_parser("apply")
    a.add_argument("--plan", required=True)
    a.add_argument("--limit", type=int)
    for p in (s, a):
        p.add_argument("--project", default="bifrost-prod-global1")
    args = parser.parse_args()
    global PROJECT
    PROJECT = args.project
    return survey(args) if args.cmd == "survey" else apply(args)


if __name__ == "__main__":
    sys.exit(main())
