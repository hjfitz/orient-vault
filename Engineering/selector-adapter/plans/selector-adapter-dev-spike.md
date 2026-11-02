---
ticket: none
title: Selector adapter dev spike
service: selector-adapter
status: complete
created: '2026-10-27'
updated: '2026-10-27'
repo: /home/hjf/code/fuse/selector-adapter
worktree: /home/hjf/code/fuse/selector-adapter
branch: hjf/selector-adapter-spike
base: origin/main
base_sha: 89c7886
pr: '4'
tags:
- waypoint
- plan
impl_model: opus
impl_effort: medium
---
# Selector adapter dev spike

<!-- Guidance in this file is written as HTML comments: Obsidian hides them, agents read them,
     and `wp signoff` ignores them. Only <angle spans> are treated as unfilled placeholders, so
     they mark the places a human or agent must actually type something. Leave the comments in
     place — deleting them costs the next reader the guidance and gains nothing at the gate.

     SUPERSEDING A STATEMENT. This file is edited by several sessions over days. When something
     here stops being true, do NOT strike it through, delete it, or bury a correction inside it.
     Put one blockquote immediately ABOVE the stale text and leave the text alone:

         > SUPERSEDED 2026-09-04 — the monitor now lives in `gfs-bifrost/observability`.
         > Everything below is kept as the record of how it was first built here.

     One marker, always above, never inside. `wp decide` writes the dated entry in
     `## Decisions & deviations` that explains why. -->
- 2026-10-27 — Routing: the deduper stamps `selector: "true"` for businesses with Selector config, and the adapter's subscription filters on it. That wiring lands after the service is built, in separate plans. The fuse-mocker attribute option is dropped. Golden image: no, sidecar. Sandbox credentials as plain env: yes. (Harry)

## Intent
<!-- What we are changing and why. Link the ticket. -->
> SUPERSEDED 2026-10-27 — PM/EM have already decided the split: delivery gets its own portal (Merak). The spike proves the Selector side ahead of the [[Delivery Backends/Overview|Delivery Backends]] programme, not to inform that call.
A new Go service, `selector-adapter`, lives in a new `gfs-bifrost` repo. It takes a canonical `sales_order` off `create_record` and books a carrier shipment in GFS Selector. It does that with one SOAP `ProcessShipment` call per order, for customers who have already packed their goods. This is a **dev-only spike**. It proves the Selector side so PM/EM can decide how delivery and fulfilment split in the product. It publishes nothing, returns no labels, shows nothing in fuse-ui and never deploys to prod. The service is built and deployed first. Live traffic is wired in afterwards: the deduper tags `create_record` messages for businesses that hold Selector config, and the adapter's subscription filters on that tag. That wiring is its own cross-linked plans. Done means a fuse-mocker order for a Selector-configured business, sent through the deduper, books exactly once in the Selector sandbox, and the findings are written up for PM/EM.

Context: [[selector-rest-proxy/overview]] (the service this replaces and the contract reference); explainers `Explainers/2026-10-27-selector-processshipment-soap-flow.md` and `Explainers/2026-10-27-selector-adapter-spike-shape.md`. No ticket: out-of-team work, branch `hjf/<desc>`.

## Acceptance criteria
<!-- Observable, checkable outcomes — not tasks. Numbered by order: increments cite them as
     (AC 2,4), and sign-off prints which criteria no increment claims. -->
- [x] 1. `selectorprobe` gets a `ConsignmentNo` back from the Selector sandbox for a hand-built `ProcessShipment`. The findings doc answers duplicate-reference behaviour, the bad-credentials response shape and p50/p95 latency.
- [x] 3. A redelivery (subscription seek) or republish of the same order logs `already claimed` and books no second shipment.
- [x] 5. A Selector `ERROR`/`FAILURE` is acked once and logged as rejected. An unreachable endpoint, a 5xx or a timeout answers 503, and after restore the order books once.
- [x] 6. The adapter publishes to no topic and logs no request/response body or credential. Nothing in the repo can deploy to prod.
- [x] 7. A findings write-up is published for PM/EM. The dev resources are torn down or kept by a recorded decision. The fleet records (MCP data, ledger, Waypoint onboarding) are done.

## Affected boundaries
<!-- Components, paths and contracts this touches. Wikilink existing explainers; do not restate
     their contents. If this names a topic, endpoint, canonical type, collection, inter-service
     dependency or shared package, sign-off will prompt for the Fuse MCP data file too. -->
- **New repo `gfs-bifrost/selector-adapter`**: a poly-app layout copied from wms-gateway (`apps/adapter/{cmd,internal/{core,adapters,http,bootstrap,observability,models,shared}},tools/canonschema}`, `iac/projects/selector-adapter`). Ports declared in `core/booking`: `ConnectionProvider`, `ClaimStore`, `ShipmentBooker`.
- **Selector SOAP**: `ClientShipService.asmx`, SOAP 1.1 document/literal, `SOAPAction: "ProcessShipment"`, credentials in the body, namespace `http://justshoutgfs.com/Client/Ship/v5/`. Contract source: the sandbox WSDL. See [[selector-rest-proxy/architecture]] for what the proxy got wrong (bodies in logs, `ERROR` with no detail read as success).
- **Pub/Sub**: a new push subscription on `bifrost.dev.create_record.v1`, filtered `attributes.recordType = "sales_order" AND attributes.selector = "true"` (topic owned by bifrost-pubsub, read through `terraform_remote_state` as `snap-adapter/iac/projects/snap-adapter/remote.tf` does). It shares the topic with snap-adapter, collector and tracking-service. Changing the filter means recreating the subscription.
- **github-config** `iac/projects/bifrost-github-config/main.tf`: a new `module "selector_adapter"`, applied behind `terraform-prod`.
> SUPERSEDED 2026-10-27 — the wiring is the **Delivery Backends** programme ([[Bifrost/Delivery Backends/Migration State|Migration State]]), not separate plans. Selector config is a `SELECTOR` type in `BACKEND_CONFIG` ([[config-service/decisions/2026-10-27-delivery-and-fulfilment-backends-share-one-backend-config-mo|decision record]]), added beside the SNAP schema and never widening it; the old surfaces go SNAP-only first (A2, gate G1). Gate D = units **A3 + B1**. B2 swaps in the config-service `ConnectionProvider` and the (order, backendId) claim key. B3 is the snap-adapter subscription swap. The Selector UI is a Merak portal (C1/C2), not fuse-ui.
- **Wiring, in separate cross-linked plans (not touched here):**
  > SUPERSEDED 2026-10-27 — Selector config is a `SELECTOR` type in `BACKEND_CONFIG`; see [[config-service/decisions/2026-10-27-delivery-and-fulfilment-backends-share-one-backend-config-mo]].
  - config-service: a Selector-only resource per business (endpoint, credentials, `ShipperId`, carrier defaults, print spec). Not `BACKEND_CONFIG`, and nothing in fuse-ui.
  - dedupe-service: when forwarding to `create_record`, look up the business's config and add `selector: "true"` when Selector config exists. Today it publishes only `recordType`. A failed lookup must nack, never forward untagged.
  - snap-adapter: recreate its `create_record` subscriptions filtered on a Snap tag stamped the same way, so Selector-only orders stop reaching it. This has a hard ordering requirement: the deduper must stamp the Snap tag in prod before the swap, or Snap traffic stops.
  - selector-adapter: swap the static `ConnectionProvider` for the config-service-backed one.
- **fuse-mocker**: no change. Its `create_record_request` target already sends through the deduper.
- **GCP `bifrost-dev-global1`**: Cloud Run `selector-adapter-dev`, a named Firestore database for claims, IAM. The project-level `roles/iam.serviceAccountTokenCreator` binding is **authoritative** and owned by `snap-adapter/iac/projects/snap-queue-polling-service/iam.tf`, so this repo must not declare one.
- **fuse-mcp-server data**: `services.json` and `pubsub-topology.json` (a new service and a new `create_record` subscriber).
- **Not touched**: config-service, fuse-ui, `@gfs-bifrost/types`, dedupe-service, snap-adapter, replay-service.

## Assumptions & uncertainty
<!-- One line each, with how it was established. A genuine product or domain question goes here
     as UNRESOLVED: and is raised with the user, never invented. -->
- The canonical sales order has no packages, so the spike sends one package per order — agreed with Harry 2026-10-27.
- `ProcessShipment` (single) over `ProcessShipments` (batch): one order per message, no partial success — agreed 2026-10-27. The proxy only ever ran the batch call, so the single call is unproven until Inc 1.
- Required WSDL value fields the mapping must set explicitly: `Recipient.SequenceId`, `SaveAB`; `ShipperId`, `DespatchDate`, `ConsolidateShipment`, `TotalWeight`, `Packs`, `ShipmentID`, `Liquids`, `CarbonNeutral`; `CarrierService.Dropoff`; package `ItemID`, `Weight`, `ExpLicense`; `PrintSpecification.TextCN23`, `LabelSpecType`, `LabelOrientType`, `LabelStock` — read from the WSDL, confirmed by the grounding review. The proxy's print-spec defaults come from its own `defaults.ts`, **not** from Selector.
- `RequestedShipmentDetails` is an `xs:sequence`, so struct field order must copy the WSDL. Whether ASMX silently drops an out-of-order element is unverified (Inc 1 probe 9).
- `ShipReply.ResponseStatus` is top-level and always present. Status detail and `ConsignmentNo` exist only under `Shipment`, which can be absent on `FAILURE` — read from the WSDL.
- Canonical dates parse as local time, so a BST date serialises as the previous day's `23:00Z`. Taking the UTC date part sends yesterday, and Selector rejects a past despatch date. That is the proxy's most common tenant 400 — fuse-mocker vault notes + selector-rest-proxy known-context.
- snap-adapter's `deriveCountryCode` defaults unknown countries to GB. The adapter must reject an unknown country, not copy that default — read at `snap-adapter@origin/master`.
- fuse-mocker's sales-order generator makes a non-UK `Zip()`, no `dates.shipment`, no `quantities.weight`, and a Snap `CustomerText` as `shipping.method`. E2E payloads need hand-editing — read at `fuse-mocker@origin/main`.
- dedupe-service publishes `create_record` with only `recordType`, so the `selector` tag has to be added there — read in dedupe-service's e2e spec. Replay redrives go to `create_record_request`, so they pass through the deduper and get tagged too.
- The tag is named `selector`, not `fulfilmentSelector`: Selector is delivery, and the delivery-vs-fulfilment naming is deferred (Harry, 2026-10-27).
- The dev WIF pool `661226359806` is `bifrost-dev-global1`, and its condition allows `repository_owner == "gfs-bifrost"` — verified live by the grounding review.
- Fleet DLQs don't forward. `bifrost.dev.create_record.v1.dlt` has an empty IAM policy and no service-agent grants exist in any repo — verified live.
- UNRESOLVED (Gate C): after a post-send timeout, which is worse for a customer: a missing shipment (never auto-rebook) or a duplicate (release and retry)?
- UNRESOLVED (Gate C): what counts as domestic — GB only? Northern Ireland (BT), Channel Islands, Isle of Man?
- UNRESOLVED (Gate C): sandbox carrier, service, contract, `ShipperId`, `Dropoff` and print spec. The proxy smoke used HERMES / 2DAY / 123456.
- UNRESOLVED (Gate C): a past `dates.shipment`: use today or reject? Default weight, and the unit of `quantities.weight`? Which `shipAddresses`/`shipContacts` entry is the recipient, and does `name` map to `Company` or `PersonName`? Are `shipping.carrier`/`method` Selector codes?
- UNRESOLVED (Gate C): does an amended or redriven order that is already booked rebook, or stay booked? It doesn't matter for the spike, but the claim TTL encodes an answer.
- Until the snap-adapter subscription swap lands, a tagged order still reaches snap-adapter, collector and tracking-service, because their filters ignore the tag. For a Snap-backed test business (HJF) that's harmless in dev. A Selector-only business would fail in snap-adapter until the swap — established 2026-10-27.

## Increments
<!-- Each independently implementable AND verifiable. Cite the criteria it discharges as
     (AC n,n). Tick with `wp tick`, which stamps `— done: <sha>` from HEAD; never hand-write it.
     Prefer 3-7 — more usually means the ticket is too big, so say that rather than splitting
     hairs.

     A PRECONDITION THAT IS NOT CODE goes on its own indented `gate:` line, with a confirmation
     box under it. Sign-off blocks on a ticked increment sitting above an unconfirmed gate, and
     `wp brief` shows unmet gates in its NEXT block — so "do not action this yet" stops being
     bold prose a fresh session can miss:

         - [ ] 6. Widen the subscription filter (AC 6) — verify: filter matches in dev
               gate: FUSE-1052 AND FUSE-1053 confirmed in prod
                     [ ] confirmed
-->
- [x] 0. Gate A — create the repo (AC 6) — github-config#21 merged + applied; repo internal/main; envs reviewers bifrost-admins; org secrets visible — done: d464d31
      gate: github-config PR merged and its `terraform-prod` apply approved (plan shared with Harry first, per plan-then-proceed). Verify: `gh repo view gfs-bifrost/selector-adapter`; both environments exist **with non-empty reviewers** (the secrets-hub race, github-config ledger 2026-10-13 #20); org secrets include `DATADOG_API_KEY`, `GH_TOKEN`, `SLACK_WEBHOOK_URL`
            [x] confirmed
- [x] 1. Skeleton, SOAP client, probe and sandbox findings (AC 1, 6) — verify: in a local repo (`git init ~/code/fuse/selector-adapter`, pushed once Gate A clears; mise pins Go to match `go.mod`): — go test -race, fmt-check, lint clean; sandbox probe booked T003FA0000006421; findings 1-9 in docs/selector-sandbox-findings.md — done: d464d31
  - `make fmt-check`, `go build`, `go vet`, `go test -race ./...`. `make lint` uses the `GOBIN` golangci-lint workaround from wms-gateway operations.
  - Golden request XML, plus decode fixtures for `SUCCESS`, `ERROR`, `FAILURE` with no `Shipment`, `soap:Fault`, httptest timeout and 503.
  - Booked requires `SUCCESS`/`NOTE`/`WARNING` **and** a non-empty `ConsignmentNo`. The adapter logs only classification fields, never bodies.
  - `go run ./cmd/selectorprobe` against the sandbox prints a `ConsignmentNo`.
  - `docs/selector-sandbox-findings.md` answers probes 1–9: duplicate `ShipmentReference`, `ShipmentID=0`, Fault vs `FAILURE` on bad credentials, `ShipperId=0`, past date, `ValidateShipment` as a dry run, `DailyShipQuery` by reference, `DeleteShipments` cleanup, latency p50/p95 over about 10 calls, element order.
- [x] 2. Gate C — owner decisions (AC 3, 5) — decisions recorded under Decisions & deviations — done: d464d31
      gate: Harry answers the UNRESOLVED items above against the findings doc; answers written into this plan via `wp decide`
            [x] confirmed
- [x] 3. Mapping, booking use case, Firestore claim store (AC 1, 3, 5) — verify: — mapping+use case+Firestore claim; emulator tests incl 8-way race; sandbox booked T003FA0000006572 via --canonical, found by DailyShipQuery — done: 79d8fb3
  - `canonical.gen.go` is generated once locally from trimmed canonschema (`WANTED = ["CanonicalSalesOrderSchema"]`, `embed-openapi` and the `@gfs-bifrost/snap/types` import dropped). There is no CI gen-check.
  - Golden canonical JSON → request XML covers: domestic; unknown or international country rejected; no weight; past/absent date; **a BST-dated fixture formatting in Europe/London**; carrier override.
  - Use-case table tests against an in-memory `ClaimStore` fake: fresh → booked; booked → ack with no call; in-flight claim held by another delivery → **503**; rejected → claim released, ack; pre-send transport error → release, nack; post-send timeout → Gate C policy.
  - The Firestore adapter is tested on the emulator. Claims use `Create()` keyed `{businessId}:{shipmentId}` and store the `messageId`.
  - `selectorprobe --canonical testdata/canonical/sales_order.gb.json` books in the sandbox.
- [x] 4. Push service, run locally (AC 2, 3, 5, 6) — verify: — local push service vs emulator+sandbox: booked/already-claimed/rejected/not-bookable 204; unreachable/badcreds/claim-store-down 503 — done: a2f620a
  - `POST /events/v1/record/create/sales_order` with audit-service's `RequireCaller` ID-token check (bypassed locally).
  - Firestore emulator, endpoint pointed at the sandbox.
  - `curl` the push fixture: 204 booked. Again: 204 `already claimed` and no outbound call. ERROR fixture: 204 rejected. Unreachable URL: 503. Claim store unavailable: 503 (fails closed, never memory-only).
  - Metrics under `selector_adapter.*`.
- [x] 6. Dev deploy and live e2e (AC 2, 3, 4, 5, 6). The service and its subscription can deploy before Gate D; the filter matches nothing until the deduper tags. The live e2e checks wait for Gate D. Verify: — deploy half done; live e2e moved to Delivery Backends B2 (Harry, 2026-10-27) — done: e5f710a
  - **Infra:** Cloud Run with `INGRESS_TRAFFIC_ALL`, invoker = push SA only, `max_instance_count = 1`, Datadog sidecar + `ResolveSink`. Named Firestore database. Subscription filter `attributes.recordType = "sales_order" AND attributes.selector = "true"`, OIDC, ack deadline sized from Inc 1 latency, retry 10–600 s, `retain_acked_messages` 1 day, **no dead-letter policy**.
  - **Dev-only guards:** `env` validation allows only `dev`; `root.hcl`/`remotes.tf` map every env to the dev bucket and `bifrost-dev-global1`; there is no prod tfvars; there are no prod jobs. The dev deploy and manual-deploy carry the `notify_on_*` + `slack_webhook` inputs.
  - **Deploy checks:** the tf-plan comment touches only `selector-adapter*` resources (shared with Harry before the first dev apply); Deploy is green; `gcloud pubsub subscriptions describe … --format='value(filter)'` shows both clauses.
  - **Live e2e** (after Gate D; the Selector-configured test business; hand-edited payload with a GB postcode, future `dates.shipment`, weight, real SKUs; sent with `curl` to fuse-mocker `POST /api/v1/messages` with target `create_record_request`, header `x-api-key: $MOCKER_API_KEY` from fuse-mocker tfstate):
    - booked log, checked in Datadog with `project_id:bifrost-dev-global1` (not `env:`);
    - `seek` → `already claimed`, and `DailyShipQuery` shows one shipment;
    - a mock for a business without Selector config → no selector-adapter request;
    - an invalid postcode → rejected, `deliveryAttempt` 1;
    - a manual-deploy with an unreachable URL → 503s with `deliveryAttempt` rising, then a manual-deploy of `main` restores it, confirmed by the `version` sha; the order books once.
  - **Side effects:** snap-adapter shows a create, not `CreateFailed`, for the mock `correlationId`; `replay-list-failures` for HJF shows nothing new.
- [x] 7. Write-up and wrap-up (AC 7) — verify: — findings explainer 2026-10-27-selector-adapter-spike-findings; fuse-mcp 3bedd50; ledger; onboarded; dev kept (B2 builds on it) — done: e5f710a
  - The findings explainer is published for PM/EM.
  - `fuse-mcp-server/data/services.json` and `pubsub-topology.json` are updated, with `make parity-accept` in the same direct-to-master push.
  - `wp ledger` entries for the github-config, selector-adapter and fuse-mocker work.
  - `waypoint-onboard selector-adapter`.
  - Teardown (`terragrunt destroy` dev, delete the subscription), or a recorded keep decision.

## Verification
<!-- The single authority for evidence. Increment lines carry `— done: <sha>` and nothing else.
     Check-selection order lives in verification-menu.md — do not restate it here. -->

### Evidence
<!-- Newest first, dated. One bullet per check actually run, opening with what it discharges.
     "Suite green" alone is not evidence. Sign-off requires at least one dated bullet here. -->
- 2026-10-27 [inc 6, deploy half] selector-adapter #1–#4 merged to `main` as `e5f710a`. Deploy run 40539924975 succeeded.
  - `selector-adapter-dev-00001-cxx` is Ready at `https://selector-adapter-dev-j677gxplja-nw.a.run.app`.
  - Anonymous `/health` and push both return 403, so only the push identity invokes.
  - The subscription filter is `attributes.recordType = "sales_order" AND attributes.selector = "true"`, ack 60 s.
  - The Firestore database `selector-adapter-dev` exists (native, europe-west2).
  - Datadog `service:*selector-adapter*` shows `App build started` / `Server listening` (`environment:dev`, `source:go`).
  - PR #4 checks were all green: plan, code quality, Semgrep, container, Go deps, gitleaks, Terraform scan.
  - Live e2e not run yet: it waits on Gate D.
- 2026-10-27 [inc 4] At a2f620a: the service ran locally (`ENVIRONMENT=local`, Firestore emulator, Selector sandbox), driven with `curl` push fixtures in `testdata/push/`.
  - Booked `T003FA0000006584`: 204 in 605 ms.
  - Same push again: 204 `already_booked` in 3 ms, with no Selector call.
  - Postcode `NOTAPOSTCODE`: Selector `ERROR 0003 Invalid postcode.` → 204 `rejected`.
  - Country `FR`: 204 `not_bookable`, Selector not called.
  - Endpoint `127.0.0.1:9`: 503 `not_sent`.
  - Password `wrong`: 503 `config_fault`.
  - Firestore unreachable: 503 `claim_store_error` in 5.0 s (before the per-op timeout it hung 25 s until the client gave up).
  - Log grep for the password or address found 0 hits.
  - The sandbox booking was deleted afterwards.
  - Controller and `RequireCaller` unit tests pass; lint 0 issues.
- 2026-10-27 [inc 3] At 79d8fb3: `go test -race ./...` with `FIRESTORE_EMULATOR_HOST` (Docker `google-cloud-cli:emulators`). The claim store passes 8 emulator tests, including 8 concurrent claims → exactly one `ClaimWon`. Use-case table tests cover booked, already-booked (no Selector call), in-flight (503), rejected (released, ack), config fault (released, nack), not-sent, ambiguous, reconcile-found, reconcile-not-found and reconcile-error. Mapping tests cover a BST UTC-midnight → next UK date, a past date → today, non-domestic rejection, and the default weight. Live: `selectorprobe --canonical internal/core/booking/testdata/sales_order.gb.json` booked `T003FA0000006572` (SUCCESS, no company warning) and `FindBooking` returned the same consignment; deleted afterwards. Lint 0 issues.
- 2026-10-27 [inc 1] Sandbox `ProcessShipment` via `selectorprobe` booked `T003FA0000006421` (WARNING 0002, company missing). All nine probes run; answers in `docs/selector-sandbox-findings.md`. Highlights: a repeated `ShipmentReference` booked 3 consignments; bad credentials → HTTP 200 FAILURE 0010; a past or missing `DespatchDate` → ERROR 0003; `DailyShipQuery` lists by date with upper-cased `ShipRef`; `DeleteShipments` cleaned up every probe booking (confirmed `DELETED`); latency p50 430 ms / p95 474 ms over 10 calls. `go test -race ./...`, `make fmt-check`, `make lint` (golangci-lint rebuilt with Go 1.27) clean at f1b1a24. Golden request XML is the shape the sandbox accepted.
- 2026-10-27 [gate A] github-config#21 CI plan: 5 to add (selector_adapter repo `auto_init=true` internal, branch protection, terraform-dev/prod environments, bifrost_admins access), 1 to change: unrelated standing drift on `shopfiy-app` `vulnerability_alerts false -> true`. 0 to destroy.

### Not verified
<!-- Stated, not papered over. "(none)" is a deliberate claim, and a fine one. -->
- That org Actions secrets reach a new repo. They are visible to the two newest repos, so expected; Gate A checks it.

## Rollout & rollback
<!-- Added on demand. Written at plan time; amend in place as it changes.
     `Shared state touched:` is the single home for the five classes git does not own — a dev
     deploy, a prod config write, a Datadog monitor, a CI var or secret, cross-repo IaC. Reverting
     the branch undoes none of them, so if they are not written here they are not written down. -->
- **Order:** Gate A → Inc 1 (can start locally before Gate A) → Gate C → Inc 3 → Inc 4 → Inc 6 deploy. Gate D (the wiring plans) → Inc 6 live e2e. Without Gate D the filter matches nothing, and an empty subscription would pass the negative check falsely.
- **Flags/config:** the static `ConnectionProvider` reads env (Harry agreed 2026-10-27): sandbox URL, `TEST`/`TEST` (already public in `selector-rest-proxy/.env.development`), carrier defaults. No Secret Manager for the spike. Real credentials arrive with the config-service plan.
- **One-way doors:** none in prod. The github-config repo creation is reversible only by archiving or deleting the repo.
- **Rollback:**
  - Inc 6: `terragrunt destroy` dev, or a manual-deploy of `main`.
  - Inc 5: revert the commit on fuse-mocker `main`, which redeploys on push. Don't push while a Deploy run is in flight; it cancels image jobs.
  - github-config: a revert PR.
- **Shared state touched:**
  - github-config apply (`terraform-prod`, GitHub org only).
  - GCP `bifrost-dev-global1`: a Cloud Run service, a Firestore database, a subscription on the shared `create_record` topic, IAM.
  - fuse-mcp-server data on master.
  - Sandbox bookings in Selector, cleaned up with `DeleteShipments` if probe 7 shows it works.
  - Dev side effects: mock orders also reach snap-adapter (Snap simulator), collector and tracking-service.
- **Proof in prod:** n/a. Dev-only by design; the dev proof is AC 2.

## Options considered
<!-- Added on demand. Why this approach and not the others — the thing the planning agent is
     asked for and the plan has otherwise had nowhere to put. Promote to a durable record with
     `wp decide --record` when it is worth defending in a review six months out. -->
- **Chosen — Firestore `Create()` claim store** — atomic create-if-absent, durable, no VPC. It follows the fleet pattern of one named DB per service (tracking-service, dedupe-service, fuse-wms-routing in dev) and is prod-shaped.
- **Rejected — Redis `SET NX` on BASIC Memorystore** — it needs a VPC and subnet, and wms-gateway's `ConnectRedis` fails open to memory-only. BASIC also restarts empty: INC-40 lost Redis for about 5 h. Any of those means a redelivery books twice.
- **Rejected — an in-process claim map** — scale-to-zero between retries wipes it, so the duplicate test would prove nothing.
- **Chosen — no dead-letter policy for the spike** — the fleet DLQs don't forward (empty IAM), and a DLT without a hold subscription discards messages. Prod uses tracking-service's DLT + `.dlt.sub` hold pattern, a deliberate exception to the retry-budget preference because there is nowhere to publish exhaustion.
- **Chosen — hand-written `encoding/xml`, single `ProcessShipment`, no runtime WSDL fetch** — rejected gowsdl output (3,119-line WSDL), the batch call, and a shared Go module (none exists).
- **Chosen — generate canonical types once locally** — CI gen-check deferred to a prod plan; it also leans on the `GH_TOKEN` PAT debt.
- **Chosen — Datadog sidecar + `ResolveSink`** — copies proven wms-gateway behaviour. Not the go-runtime golden-image canary: another agent is testing that independently (Harry, 2026-10-27).
- **Chosen — deduper tags, subscriptions filter** — one routing decision in one place, following the fleet rule to filter at the subscription. Rejected: each adapter checking config and skipping in code. Rejected for the live path: fuse-mocker stamping the tag itself, because that tests a route real traffic never takes. It stays a fallback only if the wiring plans slip.

## Decisions & deviations
<!-- Date-stamped, newest first — written by `wp decide`, and by hand when that is easier.
     Where implementation departed from this plan, and why. Source wins over the plan: correct
     the plan in the same increment and record the correction here. Legitimately empty at plan
     time. A decision worth defending in a review six months out belongs in a durable record
     instead — `wp decide --record`. -->

- **2026-10-27** — Reconciled at sign-off: the increment stamps (d464d31, 79d8fb3, a2f620a, 0575ed8) are the pre-squash branch commits. On main the stack landed as ef563cb (#1 SOAP client), f165228 (#2 booking + claim), 7e54f05 (#3 push service) and e5f710a (#4 IaC + CI, including the PR-trigger change). The diff matches the plan, with two additions: a 5 s per-call claim-store timeout (found in the inc 4 local run) and the Terraform secops scan. No system explainer was written: architecture.md covers the mechanism, and the event explainers cover the SOAP flow and findings.

- **2026-10-27** — Live dev test removed from the spike and moved into the Delivery Backends programme (Harry): AC 2 (real-route booking in dev), AC 4 (untagged orders never reach the adapter) and Gate D (A3 + B1 in dev) are deleted here and now sit in programme unit B2's verification. The spike closes on local + sandbox evidence plus the dev deploy.

- **2026-10-27** — Spike closes without a live dev e2e (Harry). The deployed path is first exercised through the real route by Delivery Backends B2 once A3 + B1 land in dev. AC 2 and AC 4 (real-route booking and routing) move to B2. AC 3 and AC 5 rest on the local run against the emulator and sandbox (inc 4). Dev resources are kept: B2 builds on selector-adapter-dev, and the subscription filter matches nothing until B1 stamps selector.

- **2026-10-27** — Gate D repointed at Delivery Backends programme units A3 + B1 (B1's notes: 'Together with A3, this clears the spike's Gate D'). The separate config-service/dedupe-service plans are dropped. Selector config follows the programme's decision record: a SELECTOR type in BACKEND_CONFIG, not a separate resource. The claim key stays {businessId}:{shipmentId} until B2, which re-keys by (order, backendId) once A3 mints backendIds. The sandbox findings + Gate C decisions are the input to A1's field set.

- **2026-10-27** — Shipped as a 4-PR native stack (selector-adapter #1–#4, one per increment, each 740–1,530 review lines), squash-merged atomically with gh stack merge (main e5f710a) after Harry agreed the dev plan (7 add / 0 change / 0 destroy). tf-plan and code-quality run on every PR (branch filter dropped) so stacked PRs get checks. Increment 6 is split: the deploy half is done; its live e2e checks stay open until Gate D (config-service Selector resource + dedupe-service selector tag).

- **2026-10-27 (Harry)** — The delivery-vs-fulfilment call is already made (PM/EM): the split goes through a separate delivery portal, Merak. The spike no longer exists to inform that decision.

- **2026-10-27 (Harry)** — Selector config moves into BACKEND_CONFIG as a SELECTOR backend type, not a Selector-only resource; the deduper tag becomes one boolean attribute per backend type (selector keeps its name); the Merak portal lives in its own ilg-merak repo, not here. See [[config-service/decisions/2026-10-27-delivery-and-fulfilment-backends-share-one-backend-config-mo]].

- **2026-10-27** — Gate C (Harry, 2026-10-27, against docs/selector-sandbox-findings.md): (1) post-send timeout → keep claim 'ambiguous'; on redelivery reconcile via DailyShipQuery on the despatch date matching upper-cased ShipRef — found → mark booked, absent → book; (2) FAILURE 0010 bad credentials → nack 503 (config fault, not an order fault) with log + metric; (3) domestic = CountryCode GB only (incl. NI); JE/GG/IM/unknown → rejected; (4) past or missing dates.shipment → today in Europe/London; (5) quantities.weight is kg, missing → connection default (1 kg in sandbox); (6) recipient = shipAddresses[0] + shipContacts[0], contact name → PersonName, customer.name → Company; (7) carrier/service/contract from connection defaults only (HERMES/2DAY/123456 in sandbox), shipping.carrier/method ignored in the spike; (8) an already-booked order that is amended or redriven stays booked (ack, no rebook).

## Learnings
<!-- Durable facts about the service surfaced while planning, working or testing that are not
     already written anywhere in the vault — a gotcha, a constraint, a fragile edge, a confirmed
     or refuted hypothesis. Not restated doc content. Sign-off promotes each confirmed one into
     the matching durable doc, then clears it from here; a refuted one moves to ## Handback
     rather than being deleted. Legitimately empty. -->

<!-- promoted 2026-10-27: Selector and Firestore facts → `selector-adapter/known-context.md`; wms-gateway doc drift and the `root.hcl` prod-bucket default → `wms-gateway/known-context.md`; tracking-service on create_record is already in the MCP topology -->
