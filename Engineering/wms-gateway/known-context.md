---
tags: [waypoint, wms-gateway]
---
# wms-gateway — known context

Interview truth (Harry, 2026-10-01) plus facts that source and tooling can't re-derive. Dated claims are
snapshots of mutable state and age out.

## Intent

- **Multiple WMSes are a real goal, not speculation.** The service is a *WMS* gateway. Nothing is designed
  for it yet: `snap.Provider.Get` returns a concrete `*snap.Adapter`, `core/*` imports the SNAP adapter and
  `models/canonical` carries `Snap*` types. A second WMS means introducing a seam, and that is a design
  decision rather than a refactor to do on the side. A WMS-specific rule needs an owner for where it lives
  (adapter vs core) before it is written.
- **Ownership:** the Fuse team owns it. Other teams may query it, so routes and response shapes are a contract
  with consumers beyond fapi, and `openapi.yaml` is how that is expressed.
- **Why separate:** multi-WMS, a possible team boundary, and keeping live backend credentials and the SNAP
  concurrency protection off the public edge. Customer auth, tenancy, rate limiting and v1-legacy shaping stay
  in fapi.

## Surprises

- It is a **Go service** in a TypeScript fleet. Fleet tooling (the four pnpm gate commands, pkg-node
  release flow, `@gfs-bifrost/*` imports) mostly doesn't apply, and the only link to `pkg-node` is the
  codegen step in `tools/canonschema`.
- The service is **new and little is known about its real behaviour under load**. Treat code comments and
  design notes as intent, not tested truth.

- **Two of this folder's docs lag the code** (snapshot 2026-10-27, found while selector-adapter copied the
  runtime): `architecture.md` says `INGRESS_TRAFFIC_INTERNAL_ONLY` but `cloud-run.tf` on main is
  `INGRESS_TRAFFIC_ALL`, and the repo's `CLAUDE.md` still says deploy isn't wired.
- **`iac/projects/root.hcl` sends every env except `dev` to the prod tfstate bucket**, `local` included.
  Anything copying this file for a dev-only service must pin the dev bucket instead.

## Repo-specific conventions

- **Not LLM-first:** the repo's own `CLAUDE.md` says it is written and reviewed by humans first. The org
  rules in the workspace-root `CLAUDE.md` still apply.
- `README.md` must stay current with route, layer, gate or env-var changes (repo `CLAUDE.md`).
- A canonical type is added by listing its root schema in `WANTED` (`tools/canonschema/src/index.ts`) and
  running `make gen`. It must exist in the `@gfs-bifrost/types` version the tool pins, and the Snap wire
  schemas it converts today (`SnapShipment`, `SnapReceipt`, `SnapProduct`, `SnapBackendConfigResponseDTO`)
  come from `types` as well.

## Snapshots

- (snapshot 2026-10-01) **Prod:** deployed, **no traffic** (Harry). Nothing calls it from prod yet.
- (snapshot 2026-10-01) **Nobody can invoke it on Cloud Run yet:** `caller_service_account` is a commented-out placeholder in both
  `iac/env/dev.tfvars` and `prod.tfvars`, so there is no `run.invoker` binding. fapi can't call it until that
  is set.
- (snapshot 2026-10-09) **Stock routes are served from SNAP on `origin/main`:** the paged list and `/sku/{sku}`, from the
  per-business snapshot described in [[architecture]]. Backend resolution on the read path (the config-service
  path fix and the credentials canary) is in. Nobody calls the routes yet, so nothing has been seen under real
  traffic.
- (snapshot 2026-10-01) **`README.md` and `CLAUDE.md` have drifted from the tree:** both still say deployment isn't wired and `iac/`
  is a placeholder, while `deploy.yaml`, `manual-deploy.yaml` and `iac/projects/wms-gateway/*` exist. Trust
  the tree and `operations.md`.
- (snapshot 2026-10-01) **Not in the Fuse MCP:** `lookup-service wms-gateway` returns not found, so `fuse-mcp-server/data/services.json`
  (and likely `api-endpoints.json`, `service-dependencies.json`, `deployment.json`) have no entry yet.
- (snapshot 2026-10-01) `mise.toml` pins Go 1.25.1 but `go.mod` needs 1.27.1, so a plain `mise install` can't build the module.

## SNAP behaviour the code relies on

Observed on GADG's dev SNAP unless noted; GADG has no UNLINK, non-W or other-state rows, so those cases are
proved on the fuse-mocker simulator only.

- **Stock-total rows have no unique id and split by `Facility`** inside one site (TTRS3 has `2SP` and `2SP_REWORK`;
  of 103 W/00 rows only 93 are distinct without it). Dedupe on SKU+Site+Facility+OwnerId+Status+State, with a
  null `Facility` as empty (TTRS has some), never the simulator's SKU×Site×Owner×Status.
- **An empty filtered list is `200`, `Successes: 0/0`, `Results: []`**, also for a `$skip` past the end, not a "no
  matching entity" error. A pager can stop on an empty page.
- **`$orderby=LineId` is a 400** on `/v2/stocktotals`: the wire field is `LineID` and is null on every row. The
  stock-total wire also carries `Unit`, which `SnapStockTotalSchema` lacks.
- **`BizId` and `OwnerId` select different rows.** The gateway scopes by `BizId`; stock sync scopes by `OwnerId`. A
  row can carry another owner under the business (TTRS3 has a `GADGET2` row under `BizId` GADG), and the position
  sums it with the SKU's other rows.
- **A stock list built from stock totals alone omits products with no stock row** (37 of GADG's 112). The catalogue
  read (`/v2/products` with `$filter=BizId eq '<id>'`) is what makes a zero-quantity SKU appear.
- **`$skip` with `$orderby=SKUId,Site,Facility,OwnerId` is stable on real SNAP:** pages of 10 and of 500 returned the
  same 106 rows in the same order. The real `$top` cap is unknown, because dev has too few rows to reach it.
- **Real products use 0 for "unset"** in `BoxQty`, `Life` and every dimension, and some carry a malformed `Values`
  string (`INNERUNIT="`), so `Values` cannot be turned into the canonical inner-pack value without a tolerant
  parser. The mapping passes zeros through and leaves their meaning to the consumer.
- **Latency moves a lot:** a list request took 0.15 to 0.3 s on 2026-10-02 and about 1.3 s on 2026-10-05, so 106 rows
  took about 3 s through the pager. Size the snapshot build timeout against the slower figure.
- **The fuse-mocker simulator's fault injection fails only writes**, so it cannot fail a read. Exercise read
  failures against a local fake upstream.
- **SNAP ignores `$filter` on the keyed `/v2/shipments/{id}` route** (2026-11-05, GADG dev and the simulator). A read
  with `Owner eq 'ZZNOTTHEOWNER'` still returned GADG's shipment. On the **list** route `Owner eq` is a 400, and
  `BizId eq` is honoured. `GetShipment` (`adapters/snap/request.go`, behind the sales-order route) relies on that
  `Owner` filter, so it is **not scoped to the business**. pkg-go `snap` v0.1.0's `Shipment` checks the result's
  `BizId` instead.

## SNAP kits

- **A kit is a product with `Group2 = MASTERSKU`; its bill of materials is `/v2/kits`**, whose rows (`ProductKitId`, `Unit`,
  `ComponentSKUID`, `Qty`, `ComponentSKUUnit`, `DateEffective`, `DateClosed`, `MaintInd`) have no business field. The shared
  dev host holds another business's kit (`EJTEST`), so a business's kits are read by naming them. `ProductKitId eq 'X'`, an `or`
  of several and `$orderby=ProductKitId,ComponentSKUID,DateEffective` all work on real SNAP and on the simulator.
- **SNAP's own `PotentialKitQty`** is the minimum over components of `floor(Σ max(Qty − QtyDueOut, 0) over State W / Status 00 rows ÷ BOM Qty)`;
  allocated and assigned quantities are not subtracted. The gateway's derivation reproduced it on GADG's seven kits with a BOM.
- **`/v2/stocktotalskit` is not used.** Its list route returned 500 for any parameters on GADG (a SNAP-side `DivideByZeroException` in
  `CalculatePotentialKitQtyByOwner`, one bad kit takes the whole list down), and the per-SKU route 404s for a `MASTERSKU` product with no BOM
  rows (GADG: IDRINKANDIKNOWTHINGSTOTE26, SKUFUSEKIT, TTRS4), which the gateway lists at 0. Observed 2026-10-01 and 2026-10-05.
  `SnapStockTotalKit` was never live-verified.
- **A nested kit's availability counts the sub-kit's own assembled stock first** and builds the rest from its components (HJF NEST: 5
  assembled plus 7 built = 12 sub-kits for 6 kits). The Go derivation and the simulator's independent algorithm agreed on every
  fixture, which proves the two implementations match, not that SNAP would. SNAP itself returns 500 for a kit whose only line has Qty 0
  and a kit component (`EJTEST`).
- **Component-level State and Group1 exclusion is unproved on real SNAP:** GADG has no row with a State other than W and no UNLINK product,
  so it needs a stock write on a real tenant. The simulator covers it (UNLINK component 0, non-W component 0).
- **The simulator returns quantities as strings**, and its kit BOM rows cannot be deleted through the control plane (only products can).
- **SNAP's front end answers 403 to Python's default user agent** while curl's passes (2026-10-01).

## Unknowns

- **Banked fix (Harry, 2026-11-05): `GetShipment` should check `BizId` on the result**, returning not-found for
  another business's shipment, because SNAP ignores the `Owner` filter (see SNAP behaviour). It's a few lines, or it
  comes for free when the gateway adopts pkg-go `snap`. How exposed it is depends on something unverified: whether
  any shared SNAP host uses one SNAP account for several businesses. If it does, one business can read another's
  shipment by id through the sales-order route.

- Multi-site: backend config is one per business with no site field. The stock snapshot sums across sites and takes an optional `site` filter, so it does not need to know; whether a multi-site customer ends up as several `businessId`s is still open.
- Whether SNAP's own kit figure excludes components that are non-W or UNLINK (see SNAP kits); the gateway applies those filters itself.
- Who besides fapi will query it, and how they would authenticate. Today there is a single shared `x-api-key`
  and an optional invoker service account.
- What the WMS-agnostic seam should look like, and when it is due.
- Why the SNAP cap is 20 service-wide (the rationale or the real SNAP limit behind it).
- Whether any Datadog dashboard or monitor exists for the service, and who is paged.
- Real fragility under load: none observed yet because there is no traffic.
