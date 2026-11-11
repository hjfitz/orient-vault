---
tags:
- system
- ecm
verified: '2026-11-11'
title: ecm — firebird change feed
thesis: "Two change feeds may leave central Firebird for GCP, and only one is evidenced live. The Firebird Transfer Service moved 3.0M rows in 15 days, but the triggers that fill its queue are in no source we can read. The other feed, an UPLOAD_2_GCP event on every shipment insert, has a confirmed trigger and an unread publisher."
confidence: moderate
---
# ecm: firebird change feed

```orient-bluf
{ "v": 1, "bluf": "Two change feeds may leave central Firebird for GCP, and only one is evidenced live. The Firebird Transfer Service moved 3.0M rows in 15 days, but the triggers that fill its queue are in no source we can read. The other feed, an UPLOAD_2_GCP event on every shipment insert, has a confirmed trigger and an unread publisher.", "confidence": "moderate", "action": "Get the trigger text from a Firebird admin or from the Transfer Service repo before a replacement relies on any trigger. Harry decides who is asked." }
```

Source: read-only research of 2026-11-11 [13][14]. Code was read in Selector's `V4-Server-Database` at `82dde6b` (an October 2023 snapshot, so production may differ) and `V4-Server-UploadServer` at `5773b8e` [1][5]. Descriptions of the Transfer Service come from Confluence 206274620 and the Tech Services knowledge vault [8][9]. The research contacted no database or host. Confidence is `moderate` because no production trigger text has been read. Harry asked for orient first. A Confluence page may follow, and none exists.

Terms: a trigger is SQL that Firebird runs when a row changes. DDL is the SQL that defines an object, here a trigger. `POST_EVENT` signals clients that listen to Firebird. DBA is database administrator. `fb.*` are the Pub/Sub topics of the form `fb.<table>.v1`.

- **CONFIRMED** Three MPK pages (11 Nov 2026) cover the Selector site, the central database and what crosses between them. They are Selector at a Site (357171228), Central Firebird (357531678) and Between a Site and the Centre (357367820). Copies: [[Handovers/2026-11-09-merak-replacement-pages.page10-selector-local]], [[Handovers/2026-11-09-merak-replacement-pages.page11-selector-central]] and [[Handovers/2026-11-09-merak-replacement-pages.page12-selector-interaction]].
- **CONFIRMED** The site's upload client reads the upload address from the site table `CUST_UPL_SERVERS` (`V4/Client/Client.Alpha/sqlStatements.pas:305`), not from `Client4.exe`.
- **UNKNOWN** Whether the executable ships a default address. It was not checked.

## Short answers
- **CONFIRMED** Selector's source holds 16 triggers on `SHIPMENTS` and 10 on `SHIP_PIECES`. No later script drops one, and none writes a queue row for the `fb.*` feed [1][2].
- **CONFIRMED** `SHIPMENTS_AI2` posts the event `UPLOAD_2_GCP` after every shipment insert [1].
- **UNKNOWN** The text of every `TRANSFER_QUEUE` trigger. The word appears nowhere in the Selector source [1]. The Tech Services vault named the queue and its triggers from a metadata read of the Test replica [9].
- **CONFIRMED** The Firebird Transfer Service is live in production and busy: 3,022,807 rows in the window [10].
- **UNKNOWN** Whether the second feed runs. Datadog holds no data under its names, which does not prove the service has stopped [10].
- **CONFIRMED** An upload inserts a new consignment with a plain `INSERT`, so every after-insert trigger fires [3][5].

## What you can read and what you cannot

| Thing | Status | Evidence |
| --- | --- | --- |
| The 2014 base schema plus `update_1` to `update_417` (the last numbered script) for `SHIPMENTS`, `SHIP_PIECES` and related tables. These are the server (central) database scripts: `Updates/` in `V4-Server-Database`, whose base file is `server_db.sql` and whose `REG_SHIPMENTS` the upload server calls. The same repo's `ClientScripts/` folder holds the separate site (client) database scripts, with their own four `SHIPMENTS` triggers (`SHIPMENTS_AD0`, `AU0`, `BI0`, `BU0`) that this note does not cover. The 16 `SHIPMENTS` triggers were catalogued from the scripts the first reading covered. A text search on 2026-11-11 found no `TRIGGER` statement in scripts 412 to 417, so the catalogue still holds for the repo, though no one read those six line by line | CONFIRMED readable (server side). That the live central database runs this schema without drift is STATED only: the source is an October 2023 snapshot | [1][2] |
| `SHIPMENTS_AI2` posts `UPLOAD_2_GCP`. `RELOAD_PUBLISH_SHIPMENTS_AI` posts `RELOAD_2_GCP` | CONFIRMED | [1] |
| Triggers are switched on and off in production by scripts (`ALTER TRIGGER ... INACTIVE`) | CONFIRMED | [7] |
| Uploads go through `REG_SHIPMENTS` and `REG_SHIP_ITEMS` | CONFIRMED | [3][5] |
| The Transfer Service polls `TRANSFER_QUEUE` and publishes `fb.<table>.v1` | STATED (Confluence, vault). Live in Datadog | [8][9][10] |
| The push to Pub/Sub starts from the main Firebird, not from Client4, CSS or a site database | STATED (a Selector team member, 4 Nov 2026, paraphrased) | [12] |
| `GFSPublisher` listens for `UPLOAD_2_GCP` and walks `SHIP_PUBLISHED` through 0, 1, 2 | STATED (vault). Its source is unread | [9] |
| Trigger DDL on any Confluence page found by search | CONFIRMED absent | [14] |
| Text of the `TRANSFER_QUEUE` triggers | UNKNOWN | [1][9] |
| About 9 extra production triggers on `SHIPMENTS`, and any extra on `SHIP_PIECES` | UNKNOWN | [1][9] |
| Whether `SHIPMENTS_AI2` and the queue triggers are active in production | UNKNOWN | [1] |
| Delete capture, ordering, batching and resume in the Transfer Service | UNKNOWN | [8] |
| The live Transfer Service config: tables, topics, project, poll interval, batch size | UNKNOWN | [8] |

## The two feeds

```orient-flow
{ "v": 1, "preset": "data-flow", "title": "Two candidate feeds from central Firebird",
  "nodes": [
    { "id": "up", "label": "Upload server", "sub": "REG_SHIPMENTS, REG_SHIP_ITEMS", "kind": "external" },
    { "id": "fb", "label": "Central Firebird", "sub": "SHIPMENTS, SHIP_PIECES", "kind": "store", "tone": "accent" },
    { "id": "tq", "label": "TRANSFER_QUEUE triggers", "sub": "text unread", "kind": "step", "unconfirmed": true },
    { "id": "fts", "label": "Firebird Transfer Service", "sub": "live in Datadog", "kind": "service" },
    { "id": "fbt", "label": "fb.<table>.v1", "sub": "shipments, ship_pieces", "kind": "topic" },
    { "id": "mod", "label": "gfs-modernizer", "sub": "joins shipment and parcels", "kind": "service" },
    { "id": "ai2", "label": "SHIPMENTS_AI2", "sub": "POST_EVENT UPLOAD_2_GCP", "kind": "step" },
    { "id": "pub", "label": "GFSPublisher", "sub": "source unread", "kind": "service", "unconfirmed": true },
    { "id": "unk", "label": "Topic unknown", "sub": "SHIP_PUBLISHED 0, 1, 2", "kind": "topic", "unconfirmed": true }
  ],
  "edges": [
    { "from": "up", "to": "fb", "label": "plain INSERT per new consignment" },
    { "from": "fb", "to": "tq", "label": "row writes", "unconfirmed": true },
    { "from": "tq", "to": "fts", "label": "queue rows" },
    { "from": "fts", "to": "fbt", "label": "one message per row", "style": "dashed" },
    { "from": "fbt", "to": "mod", "label": "shipment and parcel messages", "style": "dashed" },
    { "from": "fb", "to": "ai2", "label": "after insert" },
    { "from": "ai2", "to": "pub", "label": "UPLOAD_2_GCP event", "style": "dashed", "unconfirmed": true },
    { "from": "pub", "to": "unk", "label": "publishes SHIPMENTS", "style": "dashed", "unconfirmed": true }
  ] }
```

### Feed A: the Firebird Transfer Service
- **CONFIRMED** The service is live. Datadog shows its metrics and logs on one production host, with the latest log line at 2026-11-11T11:04Z [10].
- **ASSESSED** It polls a queue, reads each row's table data, publishes, then deletes the queue row. The metric names say so, and select and delete counts match (100,435 and 100,079) [10].
- **ASSESSED** Confluence 206274620 states the output (**STATED**, and its author read the repo config). The envelope is `{published_timestamp, event_type, event_timestamp, data, meta}`. `event_type` is INSERT, UPDATE or DELETE [8].
- **ASSESSED** The same page states that `SHIPMENTS` carries `SHIPMENT_EXTRA` as a joined object, and that one message goes out per table row [8].
- **UNKNOWN** Which triggers fill `TRANSFER_QUEUE`. The vault names `CUSTOMERS_AI1` and says the triggers write `(ROW_IDS, TABLE_NAME, EVENT_TYPE)` [9].

### Feed B: the `UPLOAD_2_GCP` event
- **CONFIRMED** `SHIPMENTS_AI2` posts `UPLOAD_2_GCP` after every shipment insert. `update_285` also adds `SHIP_PUBLISHED`, `PUBLISH_OBJ` and `PUBLISH_DATE`, and sets every existing row to 2 [1].
- **UNKNOWN** Who reads the event. The vault names `GFSPublisher`, a .NET Framework service in the ADO repo `V6`. Nobody has read that source this year [9].
- **UNKNOWN** Whether Feed B runs beside Feed A, replaced by it, or never ran in this form. The 0, 1, 2 state machine lives in the publisher, because nothing in the source writes those values [1].

## How an upload reaches the feed
- **ASSESSED** A Selector team member says (**STATED**) that uploads consolidate site data into the main Firebird, and that the push starts there [12].
- **CONFIRMED** The upload server calls `REG_SHIPMENTS` per shipment and `REG_SHIP_ITEMS` per parcel. It issues no direct `UPDATE shipments` [5].
- **CONFIRMED** `REG_SHIPMENTS` does a plain `INSERT` when the consignment is absent. Every after-insert trigger fires, `SHIPMENTS_AI2` included [3].
- **CONFIRMED** A repeat upload does not update `SHIPMENTS` in the branch read. The procedure copies the old row to `RECYCLE_SHIPS` only when key fields differ [3].
- **UNKNOWN** The recycle, swap and carrier branches were not read line by line. `delete from shipments` appears only in the swap-consignment branch of `REG_SHIP_ITEMS` [4].
- **UNKNOWN** Whether a delete, replace or rename reaches `fb.shipments.v1` as a DELETE. That depends on trigger text we cannot read.
- **ASSESSED** An earlier session reported (**STATED**, not re-read) about 1.8 updates per new shipment, from `sql/4_fts_doppelganger_updates_3.sql` in the Transfer Service repo. This session could not re-read that file.
- **ASSESSED** Upload alone makes one insert per shipment and one per parcel, so those updates come from later status writes. Scan procedures, the Scan Injector and `CHECK_SHIP_STATUS` write status. Some filter then lets them through, and that filter is the unread part [3].
- **ASSESSED** Feed A moved 1,715,298 `SHIPMENTS` rows against 674,672 new shipment IDs, which is 2.5 rows per new shipment [10][15]. That is near one insert plus 1.8 updates, but the two counts come from different stages.

## Triggers in the Selector source
Full catalogue with files: research copy [[Handovers/2026-11-09-merak-replacement-pages.firebird-triggers-findings]], section 4. The rows below are the ones that matter to a change feed.

| Trigger | When | What it does | Evidence |
| --- | --- | --- | --- |
| `SHIPMENTS_AI2` | after insert | `POST_EVENT 'UPLOAD_2_GCP'` | [1] |
| `SHIPMENTS_AI3`, `SHIPMENTS_AU7` | after insert, after update | Insert a row into `SHIPMENTS_SCANNING`, the web-scanner work queue, at status 100, 200 to 999 or 200 | [2] |
| `SHIPMENTS_AU0` | after update | On some status changes, copies the status to `SHIP_PIECES` | [2] |
| `SHIPMENTS_AU2` | after update | On notifiable status changes, calls `ADD_NOTIFY_ITEM` | [2] |
| `SHIP_PIECES_AU0`, `SHIP_PIECES_AU3` | after update | Queue notifications, and call `set_shipment_state_by_pieces` | [2] |
| `RM_REPLICA_AI` and the `CUSTOMERS`, `CUST_SITES` and contract triggers | after insert, update, delete | Write `RM_REPLICA` queue rows for the Royal Mail sync service. Each insert posts `RM_REPLICA` | [6] |
| `RELOAD_PUBLISH_SHIPMENTS_AI` | after insert | `POST_EVENT 'RELOAD_2_GCP'` for a re-publish request | [1] |

- **CONFIRMED** The source has no `SHIP_PIECES` trigger that posts a publish event. Parcel messages on `fb.ship_pieces.v1` must come from the Transfer Service queue or from something unseen [2].
- **ASSESSED** The gaps in the trigger numbering, such as `SHIPMENTS_AU3` and `AU6`, are the likeliest home of the 9 extra production triggers. That rests on naming, not evidence.

## Datadog evidence
Window: 2026-10-23 to 2026-11-07 UTC (15 days), production. Source: [[Handovers/2026-11-09-merak-replacement-pages.firebird-feeds-datadog]] [10][11].

| Measure (service `gfs.firebird_transfer_service`) | 15 days | 24 hours |
| --- | ---: | ---: |
| Rows transferred, all tables | 3,022,807 | 281,914 |
| of which `shipments` | 1,715,298 | 155,655 |
| of which `ship_pieces` | 692,234 | 66,814 |
| of which `ship_shipper` | 460,049 | 45,459 |
| Events received from Firebird | 590,876 | 49,641 |
| Queue length, average and maximum | 33.1 and 20,630 | 66.9 and 13,978 |
| Median transfer latency (unit not declared; read as ms) | about 7.5 s | about 8.1 s |

- **CONFIRMED** Feed A is live. Its rows include `shipments` and `ship_pieces`, which are 79.6% of the total [10].
- **UNKNOWN** The mix of insert, update and delete. No metric carries an event type or a topic tag [10].
- **ASSESSED** Feed A produces the `fb.*` topics. Five small tables match the modernizer's input counts exactly: carriers 36, customers 36, contracts 420, contract services 458 and products 43 [10].
- **UNKNOWN** Why the modernizer received 1,906,654 shipment messages, 11.2% more than Feed A's 1,715,298. Parcels show 14.2% more. INFERRED, not shown: existing notes say Slipway also publishes to `fb.shipments.v1`, which may explain part of it [10].
- **UNKNOWN** The `fb.shipments.v1` volume itself. No Pub/Sub topic metric exists for `fb.*` [10].
- **UNKNOWN** Whether Feed B runs. No `gfs.legacy-publisher.*` metric exists and no indexed log carries `GFSPublisher` or `UPLOAD_2_GCP`. The service may report nowhere [10].
- **CONFIRMED** Five Datadog monitors cover Feed A, all in state OK (one muted). None covers a legacy publisher [10].

## Gaps
1. **UNKNOWN** The text of every `TRANSFER_QUEUE` trigger. It is in no readable repo. The likeliest home is the `sql/` folder of the Firebird Transfer Service repo (ADO project GFS Legacy Migration, commit `8569227`). The ADO tools could not reach it.
2. **UNKNOWN** The 9 or so extra production triggers on `SHIPMENTS`, and any extra on `SHIP_PIECES`.
3. **UNKNOWN** The live Transfer Service config: tables, topic names, project, poll interval, batch size.
4. **UNKNOWN** The `GFSPublisher` code in ADO repo `V6`, and whether it runs.
5. **UNKNOWN** Whether `SHIPMENTS_AI2` and the queue triggers are active in production.
6. **UNKNOWN** Delete capture, ordering, batching and resume in the Transfer Service.
7. **UNKNOWN** The topic naming gap: config says `fb.<x>.v1.prod` in project `gfs-ecm`, and Terraform says `fb.<x>.v1` in `gfs-ecm-prod-uk1`.
8. **CONFIRMED** Repo SQL is not proof of what runs. Only a read of `RDB$TRIGGERS` settles that.

## DBA ask list
**Harry decides whom to ask. This research sent nothing to anyone.** The queries below are read-only. Copied from the findings file, section 7.

```sql
-- 1. Every user trigger, with type and active flag
SELECT RDB$TRIGGER_NAME, RDB$RELATION_NAME, RDB$TRIGGER_TYPE, RDB$TRIGGER_SEQUENCE, RDB$TRIGGER_INACTIVE
FROM RDB$TRIGGERS
WHERE COALESCE(RDB$SYSTEM_FLAG,0) = 0
ORDER BY RDB$RELATION_NAME, RDB$TRIGGER_NAME;

-- 2. Trigger source for the two tables
SET BLOB ALL; SET LIST ON;
SELECT RDB$TRIGGER_NAME, RDB$TRIGGER_TYPE, RDB$TRIGGER_SEQUENCE, RDB$TRIGGER_INACTIVE, RDB$TRIGGER_SOURCE
FROM RDB$TRIGGERS
WHERE COALESCE(RDB$SYSTEM_FLAG,0) = 0
  AND RDB$RELATION_NAME IN ('SHIPMENTS','SHIP_PIECES','SHIPMENT_EXTRA','SHIP_PIECES_HIST')
ORDER BY RDB$RELATION_NAME, RDB$TRIGGER_TYPE, RDB$TRIGGER_SEQUENCE;

-- 3. Every trigger that touches the queue or posts an event (pattern search, no row data)
SELECT RDB$TRIGGER_NAME, RDB$RELATION_NAME, RDB$TRIGGER_INACTIVE
FROM RDB$TRIGGERS
WHERE COALESCE(RDB$SYSTEM_FLAG,0) = 0
  AND (UPPER(RDB$TRIGGER_SOURCE) CONTAINING 'TRANSFER_QUEUE'
    OR UPPER(RDB$TRIGGER_SOURCE) CONTAINING 'POST_EVENT');

-- 4. Queue shape (no rows)
SELECT RDB$FIELD_NAME, RDB$FIELD_SOURCE FROM RDB$RELATION_FIELDS
WHERE RDB$RELATION_NAME IN ('TRANSFER_QUEUE','TRANSFER_QUEUE_DEAD_LETTER')
ORDER BY RDB$RELATION_NAME, RDB$FIELD_POSITION;

-- 5. Which tables feed the queue (counts only)
SELECT TABLE_NAME, EVENT_TYPE, COUNT(*) FROM TRANSFER_QUEUE GROUP BY 1, 2;
```

Run 1 to 4 on Test (a day-behind restore, already used for read-only metadata). Query 5 reads only counts and is best run on production by the DBA in a quiet period. If ADO becomes reachable, reading `sql/` in the Transfer Service repo is cheaper and settles most of the same ground, but still needs query 1 to prove it is what runs.

Questions for the DBA and the service owners:
1. Which service reads `TRANSFER_QUEUE`: the Firebird Transfer Service, `GFSPublisher`, or both? Does the queue row get deleted after publish, or flagged?
2. Which tables are in the live Transfer Service config, and what topic and project names does it publish to (the repo config says `fb.<x>.v1.prod` in `gfs-ecm`, Terraform says `fb.<x>.v1` in `gfs-ecm-prod-uk1`)?
3. Does the `SHIPMENTS` feed publish every update or a filtered set, and where is the filter (trigger `WHEN` logic, or service code)? Do `SHIP_PIECES` updates and `SHIP_PIECES_HIST` inserts publish?
4. Are deletes captured for `SHIPMENTS`, `SHIP_PIECES`, `CUSTOMERS`, `CUST_SITES`, `CUST_CONTRACTS`?
5. What are the live `EVENT_TYPE` codes?
6. How does the service batch, order and resume after an outage, and what drives the `RETRY_COUNT` and dead-letter handling?
7. Is `GFSPublisher` (`UPLOAD_2_GCP`) running, and does it publish a different topic from the Transfer Service?
8. Who owns the Transfer Service deploy and config? (The 6 and 7 Oct stand-ups named Rob Fletcher as a possible owner; unconfirmed.)

## What a replacement must keep
These are facts the evidence shows, not a recommendation. The guardrails are G15 to G18 in [[Systems/ecm/architecture]].
- **ASSESSED** The central `SHIPMENTS` and `SHIP_PIECES` writes are ECM's first event. A successor writes them the way the registration procedures do [3][5].
- **ASSESSED** The 1.8 updates per new shipment come from status writes after upload. A successor that changes status behaviour changes what the topic carries.
- **ASSESSED** Scripts switch triggers on and off, so the source snapshot is a lead, not a record [7].

## Research copies
- **CONFIRMED** [[Handovers/2026-11-09-merak-replacement-pages.firebird-triggers-findings]] holds: artifacts, the trigger catalogue, the two feeds, consolidation, gaps, queries.
- **CONFIRMED** [[Handovers/2026-11-09-merak-replacement-pages.firebird-feeds-datadog]] holds: metric discovery, Feed A totals, Feed B no-data, cross-check, monitors, re-run snippet.

## Evidence
```orient-evidence
{ "v": 1, "items": [
  { "id": 1, "kind": "code", "ref": "V4-Server-Database/Updates/update_285.sql@82dde6b:L32", "note": "SHIPMENTS_AI2 POST_EVENT UPLOAD_2_GCP. Line 40 RELOAD_2_GCP. Line 78 sets existing rows to SHIP_PUBLISHED 2. No TRANSFER_QUEUE anywhere in the repo" },
  { "id": 2, "kind": "code", "ref": "V4-Server-Database/Updates/server_db.sql@82dde6b:L13483-13913", "note": "2014 base SHIPMENTS and SHIP_PIECES triggers. Later definitions in update_91, 133, 164, 181, 190, 200, 245, 298, 304, 316, 330, 334 and 411. Catalogue in the research copy" },
  { "id": 3, "kind": "code", "ref": "V4-Server-Database/Updates/update_284.sql@82dde6b:L195-401", "note": "REG_SHIPMENTS: plain INSERT when absent, RECYCLE_SHIPS when key fields differ" },
  { "id": 4, "kind": "code", "ref": "V4-Server-Database/Updates/update_284.sql@82dde6b:L1681-1684", "note": "delete from shipments, swap-consignment branch of REG_SHIP_ITEMS" },
  { "id": 5, "kind": "code", "ref": "V4-Server-UploadServer/uplConst.pas@5773b8e:L66-268", "note": "upload calls stored procedures, no direct UPDATE shipments" },
  { "id": 6, "kind": "code", "ref": "V4-Server-Database/Updates/update_335.sql@82dde6b:L31", "note": "RM_REPLICA_AI posts RM_REPLICA. Later scripts 350, 368 and 398 add the other queue triggers" },
  { "id": 7, "kind": "code", "ref": "V4-Server-Database/Updates/update_210.sql@82dde6b:L94-95", "note": "ALTER TRIGGER ... INACTIVE. Also update_386 and update_388" },
  { "id": 8, "kind": "doc", "ref": "Confluence 206274620 Modernizer Shipment Data Ingestion: Firebird Transfer Service Bypass and Message Format Overview (Carrier Integrations, 2026-06-04, v1)" },
  { "id": 9, "kind": "doc", "ref": "Tech Services knowledge vault, ilg-tech-services/knowledge-system@3493146: guides/firebird-to-ecm-sync-and-write-back.md, systems/legacy-manager-write-path.md, systems/legacy-capability-register.md (metadata read of the Test replica, 2026-07-10)" },
  { "id": 10, "kind": "log", "ref": "sum:gfs.firebird_transfer_service.rows_transfered{*} by {table_name}.as_count(), 2026-10-23 00:00 to 2026-11-07 00:00 UTC (Datadog). Other queries in the research copy" },
  { "id": 11, "kind": "doc", "ref": "Handovers/2026-11-09-merak-replacement-pages.firebird-feeds-datadog.md (research copy, 2026-11-11)" },
  { "id": 12, "kind": "doc", "ref": "Slack direct message from a Selector team member, 2026-11-04 (paraphrased, text not reproduced)" },
  { "id": 13, "kind": "doc", "ref": "Handovers/2026-11-09-merak-replacement-pages.firebird-triggers-findings.md (research copy, 2026-11-11)" },
  { "id": 14, "kind": "doc", "ref": "Confluence search across spaces for TRANSFER_QUEUE, POST_EVENT, CREATE TRIGGER and GFSPublisher found no trigger DDL. Closest: 67633184 Firebird - Incremental Extraction Analysis (Data Solutions, 2025-12-08), extraction by query" },
  { "id": 15, "kind": "doc", "ref": "Systems/ecm/known-context.md, canonical figures: 674,672 new shipment IDs, gfs.shipment_identity_service.ids_created, same window" }
] }
```
