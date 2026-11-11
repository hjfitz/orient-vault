---
tags: [waypoint, ledger]
---
# tracking-service — work ledger

Agent-facing. Newest first. What meaningful work happened here, and the
context a future agent needs. Not a diary, not release notes, not a diff.

## 2026-11-11 — Add the Firestore to MongoDB parity check

Add the Firestore to MongoDB parity check

cmd/parity compares every record (hidden fields, events, notes) and the served stats, insights, businesses and full counter history between Firestore and MongoDB; a duplicates difference or any record difference fails it, so the flip waits on a faithful copy. Stacked on #36.

PR: gfs-bifrost/tracking-service#37

## 2026-11-11 — Freeze notes under the hold and add the Firestore to MongoDB import

Freeze notes under the hold and add the Firestore to MongoDB import

INGEST_HOLD now also 503s note POST/PATCH, so nothing changes Firestore while the cut copies it. cmd/import-mongo copies the frozen duplicates history, then every shipment and return with all events and notes in one read-only transaction each; it refuses a live MongoDB, skips bad identities, resumes from a checkpoint that never passes a failure, and exits non-zero unless every record was written. Emulator rate 575-607 records/s at 16 workers.

PR: gfs-bifrost/tracking-service#36

## 2026-11-11 — Wire the Mongo connection into the API service

Wire the Mongo connection into the API service

Adds var.store (firestore|mongodb, explicit in both envs, firestore) and passes STORE, MONGODB_URI and MONGODB_DATABASE to the API Cloud Run service so a tfvars flip can move it to Mongo. No behaviour change.

PR: gfs-bifrost/tracking-service#35

## 2026-11-09 — Write and serve returns from the MongoDB store

Write and serve returns from the MongoDB store

Mongo store W3, stack 2/2: ApplyReturn in one transaction with a session-scoped ShipmentReader and a linked-shipment patch that must match one shipment, return reads/queries/counts, uniq_business_rga. The AC 3 differential (memory vs Mongo, in order and shuffled) is DeepEqual on every served stat, insight, per-day view and business count. Measured: a return beside its shipment's uncommitted first insert links on its next event.

PR: gfs-bifrost/tracking-service#32

## 2026-11-09 — Serve shipment queries and stats from the MongoDB store

Serve shipment queries and stats from the MongoDB store

Mongo store W3, stack 1/2: shipment List/search/attention/counts with Firestore's pushdown and _id keyset paging, a covered Businesses $group, and Stats/Insights served from marks through serve plus a keptFor stub matching #29's AllBusinesses convention. mongo_indexes.go declares every index; mongo_explain_test.go fails on a COLLSCAN, a blocking sort or an index that serves nothing. Mongo runs the live-counter conformance cases; the compose harness raises nofile to 64000.

PR: gfs-bifrost/tracking-service#31

## 2026-11-09 — Open the MongoDB store from every binary

Open the MongoDB store from every binary

storeopen opens STORE=mongodb (connect, ping primary, ensure indexes); cmd/api counts transaction retries as fuse.tracking.store.retries; recompute-stats and backfill-upgrade -all have Mongo twins; mongo-test runs ./cmd/...; README and apps/api CLAUDE.md describe the Mongo path.

PR: gfs-bifrost/tracking-service#30

## 2026-11-09 — Add notes, kept counters and the import primitive to the MongoDB store

Add notes, kept counters and the import primitive to the MongoDB store

Mongo store notes (one transaction each, importedAt dropped on every note write), kept counters as arrays with ReadCounters/ReplaceCounters on memory's semantics plus ImportKept and the keptFor read seam, and ImportShipment/ImportReturn guarded by importedAt so a re-import never overwrites a record written live; Live() for D8. Also raises mongod's nofile limit in the test harness.

PR: gfs-bifrost/tracking-service#29

## 2026-11-09 — Write shipments to the MongoDB store

Write shipments to the MongoDB store

Shipment Apply on a bounded own-loop transaction with a seen collection (8-day TTL), marks docs skipped when unchanged, and Get/GetMany/Events/ShipmentIDs/ReturnIDs. Six shipment conformance cases now run on Mongo, plus 20 Mongo-only tests pinning seen ids, aborts, concurrency, the loop bounds and the marks shape. Stacked on #26.

PR: gfs-bifrost/tracking-service#27

## 2026-11-09 — Scaffold the MongoDB store

Scaffold the MongoDB store

BSON tags beside the Firestore tags, a microsecond time codec, the Mongo type with errNotYet stubs so it satisfies storeopen.Backend, and a mongo conformance backend with a pending map; make mongo-test now runs the store suite. Groundwork for the Firestore to Mongo move, nothing selectable yet.

PR: gfs-bifrost/tracking-service#26

## 2026-11-09 — Sum marks in Mongo as the memory store does

Sum marks in Mongo as the memory store does

Mongo marks aggregation (tallyMarksOn/tallyAllMarks: $match, $unwind with entry index, $group with $min first entry, rows added in record-id then entry order) as pure functions over a marks collection, plus the memory store's served-stats helpers moved to shared code with no behaviour change. A seeded differential test proves it DeepEquals memory's tally; make mongo-test now covers internal/store. The store type and wiring follow in the later Mongo store PRs.

PR: gfs-bifrost/tracking-service#25

## 2026-11-09 — Clear CVE-2026-78661 from the api image

Clear CVE-2026-78661 from the api image

Bumped x/net to 0.62.0 in apps/api; the v0.61.0 copy is in datadog-init in the go-runtime base image, so allowlisted in .trivyignore with a 7-day expiry.

PR: gfs-bifrost/tracking-service#24

## 2026-11-06 — Record each record's marks on every write

Record each record's marks on every write

D2 (stacked): #22 adds store.Marks (core.Counters shape) to Write/ReturnWrite at all 7 write sites from Contribution of the written record (sorted, so equal records give equal marks); CapReasons and Tally move into store and recompute-stats uses them. Firestore ignores marks. #23 makes the memory store serve stats/insights by summing marks (ErrNoMarks on a non-noop write without them). Golden test pins the only G5 divergence (stage day); redelivery_test pins why Mongo writes must be atomic with the event insert.

PR: gfs-bifrost/tracking-service#22
PR: gfs-bifrost/tracking-service#23

## 2026-11-06 — Open the store through internal/storeopen

Open the store through internal/storeopen

D4: storeopen.Open builds the store from STORE/MONGODB_URI/MONGODB_DATABASE for all 5 binaries; Backend = store.Store + Maintenance (ShipmentIDs, ReturnIDs, ReadCounters, ReplaceCounters), which D5's Mongo store must implement. STORE=mongodb errors 'not implemented yet'. Mongo 8.0 replica-set harness (docker-compose.integration.yaml, make test-mongo) with a transaction smoke test; non-required api-mongo CI job. Gotcha: compose files in apps/api need an explicit name: — project 'api' collided with another local repo's containers.

PR: gfs-bifrost/tracking-service#21

## 2026-11-06 — Provision Atlas clusters for tracking-service

Provision Atlas clusters for tracking-service

D6: mongodbatlas M10 per env (termination protection in prod, backup + PIT, 8.0), readWrite user, connection string local for D7; Atlas keys via tf_var_extra_* in deploy, tf-plan and manual-deploy. No network resources: no Fuse Atlas stack declares any (project-level access); D7 must confirm Cloud Run egress is allowed. Draft; merge creates real clusters, plan to Harry first.

PR: gfs-bifrost/tracking-service#19

## 2026-11-06 — Run the store tests against every backend

Run the store tests against every backend

D3: portable store tests (firestore_*_test.go → store_*_test.go) run through an eachBackend factory against memory and the Firestore emulator; 13 live-counter stats cases gated by backend.liveCounters for D2's marks semantics. Memory passes every portable case. Emulator RUN count 161 → 307.

PR: gfs-bifrost/tracking-service#20

## 2026-11-06 — Exempt unqueried fields from Firestore indexing

Exempt unqueried fields from Firestore indexing

D1 stopgap: 9 single-field index exemptions (lastSeenAt, totalDuplicates, stageTimes, confirmations; returns adds confirmation, linkedShipmentJson) after 536 RESOURCE_EXHAUSTED commits in the 2026-11-06 reap bursts. Tests the index-hotspot hypothesis; bar is zero resource_exhausted in burst minutes over 48h.

PR: gfs-bifrost/tracking-service#18

## 2026-11-05 — Run tracking-service on the golden runtime image

Run tracking-service on the golden runtime image

Moved the API image from distroless/static to ILG go-runtime:0.1-affogato (Datadog serverless-init as entrypoint, CMD only) and dropped the serverless-init sidecar, shared volume and container-dependencies annotation; DD_* moved onto the app container with the sidecar's values. The API now logs to stdout only (the /shared-volume file sink is removed). manual-deploy announces failures only. Verified on dev revision tracking-service-api-dev-00018-qxg: one container, no volumes, logs tagged dd.datadog_init_version:1.11.2, metrics and Pub/Sub pushes flowing. Draft; dev left on the branch.

PR: gfs-bifrost/tracking-service#17

## 2026-10-19 — Stop republished copies writing the shared stats docs

Stop republished copies writing the shared stats docs

foldTimeline no longer returns a duplicates StatIncrement, so a copy (same content hash in its group) writes only its own record doc, never stats/<biz>_<day> or stats/_all__<day>. Those shared per-day docs serialised every message's transaction (18 Oct: commits 1–2 s during PURDYFIGG's 5-minute resend batches). Per-record copy counts are unchanged; stats duplicates is historic only from 2026-10-19 and recompute-stats keeps it (keptCounters). An identical copy still moves lastSeenAt and the latest-success time that failed reads, which is why skipping copies outright was deferred. Paths: internal/core/dedupe.go, returns_reduce.go. Plan stop-republished-copies-contending-on-the-shared, inc 2.

PR: gfs-bifrost/tracking-service#16

## 2026-10-19 — Add a dev-only manual deploy workflow

Add a dev-only manual deploy workflow

manual-deploy.yaml runs Deploy's two dev jobs only (with Slack notify), so a branch can reach dev without parking a prod apply of its sha behind terraform-prod. It can't be dispatched until merged (workflow_dispatch resolves from the default branch); the live check runs on the next increment's branch. Increment 1 of plan stop-republished-copies-contending-on-the-shared.

PR: gfs-bifrost/tracking-service#15

## 2026-10-15 — Record the repo standards now in place

Record the repo standards now in place

B5: applied branch protection on main (8 required PR checks, no review — fleet norm), granted bifrost-admins admin for CODEOWNERS; Renovate and PR template are org-level. Docs and CODEOWNERS comment updated.

PR: gfs-bifrost/tracking-service#14

## 2026-10-15 — Name the failing field in a rejected record's summary

Name the failing field in a rejected record's summary

C7 item 4 (API side): the failure note keeps the first error's field and the shipment/return summaries render '<field> <problem>', so 'Required.' says what was required.

PR: gfs-bifrost/tracking-service#13

## 2026-10-15 — Point the README at the archived spec and close done doc items

Point the README at the archived spec and close done doc items

B11: fixed the README's dead spec link and recorded the done doc items (specs archived, released deprecated, apps/ exception tracked) in productionisation.md.

PR: gfs-bifrost/tracking-service#12

## 2026-10-15 — Retire the ledger v1-4 upgrade paths and the delivered stats remap

Retire the ledger v1-4 upgrade paths and the delivered stats remap

B9: removed shipment seeding below ledger v2, the v<4 delivered remap and the read-time delivered->despatch_confirmed stats remap. Precondition verified live: all shipments v5+ in dev and prod, no stats doc with a nonzero delivered count.

PR: gfs-bifrost/tracking-service#11

## 2026-10-15 — Track confirmation delivery per connector

Track confirmation delivery per connector

C6: per-connector confirmation outcomes in the ledger, served as confirmations.<kind>.connectors; deliveryFailed while any connector's latest send failed. Ledger v6/returns v3, older docs seeded under 'unknown' on read. Ported from the 2026-10-07 uncommitted work onto main.

PR: gfs-bifrost/tracking-service#10

## 2026-10-15 — Switch off the migration bucket

Switch off the migration bucket

Emptied both migration buckets (old-database exports) and set migration_bucket_enabled=false by default, removing the bucket and its Firestore agent grant per env. Last cutover leftover.

PR: gfs-bifrost/tracking-service#9

## 2026-10-15 — Remove the legacy fuse-tracker stack's files

Remove the legacy fuse-tracker stack's files

Cutover 7c: deleted the legacy Terraform, legacy-stack.yaml, its plan matrix entry and scan job, and deploy.yaml's stack picker (now tracking-service only); docs describe one stack. Old databases deleted the same day; exports kept in the migration buckets.

PR: gfs-bifrost/tracking-service#8

## 2026-10-15 — Take the legacy Firestore database out of the fuse-tracker state

Take the legacy Firestore database out of the fuse-tracker state

Cutover step 7a: removed{destroy=false} for the legacy database, indexes and 20 field overrides, so the step 7b destroy keeps the old database for a week. Also fixed the runbook's Datadog filter (log env tag is serverless).

PR: gfs-bifrost/tracking-service#7

## 2026-10-14 — Enable dead-lettering in prod

Enable dead-lettering in prod

Step 4b of the prod cutover: hold released 21:50Z, backlog drained, parity checked; turns dead-lettering on. Observability hold downtime removed in gfs-bifrost/observability#69.

PR: gfs-bifrost/tracking-service#6

## 2026-10-14 — Release the prod ingest hold after the export and import

Release the prod ingest hold after the export and import

Prod tracking-service stack applied held, legacy fuse-tracker exported and imported (131,001 docs), backfill dry-run clean; releases INGEST_HOLD in prod (cutover step 4a). Observability hold downtime: gfs-bifrost/observability#68.

PR: gfs-bifrost/tracking-service#5

## 2026-10-14 — Enable dead-lettering in dev (cutover step 4b)

Enable dead-lettering in dev (cutover step 4b)

Dev dead_letter_enabled set to true after the hold release and a fully drained backlog; 20 push subscriptions gained their dead-letter policy. Prod untouched.

PR: gfs-bifrost/tracking-service#4

## 2026-10-14 — Build with Go 1.26.9 and x/net 0.60.0 to clear the container scan

Build with Go 1.26.9 and x/net 0.60.0 to clear the container scan

container_scan_api had been red on main nightly (4 HIGH findings: stdlib 1.25.14 x3, x/net 0.58.0). Bumped the toolchain in go.mod, dockerfile, CI and mise, plus x/net to 0.60.0. Independent of the cutover; found while merging the dev hold release.

PR: gfs-bifrost/tracking-service#3

## 2026-10-14 — Release the dev ingest hold (cutover step 4a, dev)

Release the dev ingest hold (cutover step 4a, dev)

Dev cutover to the tracking-service stack: stack applied held, legacy database exported and imported, counts compared, backfill-upgrade dry run found nothing to change, then ingest_hold set to false for dev only. Prod untouched.

PR: gfs-bifrost/tracking-service#2

## 2026-10-09 — Retire the standalone web UI and stdio MCP server

Retire the standalone web UI and stdio MCP server

Removes apps/web, the stdio MCP (apps/api/cmd/mcp) and all web infra (Cloud Run, LB, cert, DNS, AUTH_PASSWORD) from both stacks, and grants fuse-mcp's service account invoker on the private API. fuse-mcp serves the tracking-* tools instead. Draft; merge is gated on agreeing the Terraform plan (merging destroys the live legacy web infra).

PR: gfs-bifrost/tracking-service#1
