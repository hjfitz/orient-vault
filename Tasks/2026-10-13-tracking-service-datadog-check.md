---
tags: [adhoc-task]
date: 2026-10-13
tldr: "Cut over to tracking-service and removed fuse-tracker entirely, then shipped every open programme unit (B5–B11, C6–C8) via parallel agents; only paused B12/B13 remain"
session_id: 5bbbf341-856f-4573-b91b-8896039ab833
status: done
---
# Check whether tracking-service logs to Datadog and why monitors spike

## Outcome
Code and IaC ship logs and fuse.tracking.* metrics via the serverless-init sidecar, but there are zero logs or metrics for service:tracking-service or fuse-tracker in 30 days; prod Cloud Run is still fuse-tracker-api-prod (cutover not done). The [FUSE][Tracking Service] monitors exist only on observability branch hjf/tracking-service-dashboard. Owed: ask which alert prompted the question (likely legacy ECM Unexpected Error Logs / consignment-manager restarts).

## Follow-up (same session)
The tripping monitor is the platform Pub/Sub ack-headroom one (>180s), fired by legacy `fuse-tracker.prod.*` subs, not a tracking-service monitor. Peaks were not redeploy failures: 7 Oct 09:00-12:22 UTC was deliberate INGEST_HOLD=true (503s answered in ~2ms; revisions 00011/00016), released by revision 00018; 8 Oct ~07:00-07:17 UTC was Firestore store errors (contention + "mint used too late") on a long-running revision. Retry policy (10s-600s) matches dedupe/collector/snap-adapter. Owed: exclude or mute `tracking-service.*` subs on the platform monitors before the cutover hold; 9 Oct 15:00-16:00 UTC 429s on 00019 not investigated.

## Follow-up (2026-10-14): dev cutover run
- Explained `ingest_hold` (cutover-only; no other repo has it) and why the cutover hadn't happened (gate G1, nothing applied).
- Ran the dev cutover end to end: stack applied held (166 added), legacy DB exported and imported, counts compared, backfill dry run found nothing to change, hold released (#2), backlog drained to 0, dead-lettering on (#4), old and new APIs agree (stats 140/140, 38 sampled records). Separate fix for the red container scan (#3). Prod untouched.
- Owed: dev soak (about a day) then repoint fuse-ui dev; prod cutover needs the platform-monitor downtime for `tracking-service.prod.*`, an agreed plan, and a human for the prod Firestore ops.

## Follow-up (2026-10-14, evening): prod cutover run
Harry lifted the human-run-prod-backfill rule for this cutover and said to work autonomously, so I ran prod end to end.
- Observability#68: downtime on the four platform Pub/Sub monitors for `subscription_id:tracking-service.prod.*` (prefix wildcard verified live first). It also applied Matt Shaw's merged stock-sync monitors (#62), which were parked at the gate. Removed after the drain in #69.
- Prod stack applied held (166 add), export of `fuse-tracker` then import into `tracking-service` (131,001 docs, both SUCCESSFUL), backfill dry-run found nothing to rewrite.
- Hold released 21:50Z (tracking-service#5), drained to ~0 in ten minutes, no 5xx. Dead-lettering on (#6). All 40 subs at 0.
- Parity: 7 days of stats identical, 258 shipment docs identical. 7 PURDYFIGG shipments differ only in which Shopify duplicate resend is the representative `received` event (out-of-order replay of the held backlog).
- Datadog: logs are `service:tracking-service` with `env:serverless` (the runbook's `env:$ENV` filter is wrong; use `project_id`/`configuration_name`). `fuse.tracking.*` metrics carry `environment:prod`.
- Owed: prod soak (a few days) then fuse-ui `fuse_tracker_api_url` repoint (dev and prod); legacy destroy (dev after soak, prod needs a plan); fuse-mcp re-deploy; observability B7 monitors made hold-aware before merge; fix `env:$ENV` in docs/cutover.md; Migration State and programme ticks.

## Follow-up (2026-10-15): repoint and legacy destroy
- Soak clean in both envs: no 5xx, all 80 subscriptions (incl. dead-letter) at 0, platform Pub/Sub monitors OK.
- fuse-ui repointed (gfs-bifrost/fuse-ui#327, dev+prod applied, prod plan 0/1/0).
- 7a: legacy database, indexes, fields taken out of state with `removed` blocks (gfs-bifrost/tracking-service#7); runbook Datadog filter fixed.
- 7b: legacy stack destroyed, 27 resources per env; `fuse-tracker` database kept (prod delete-protected).
- 8: fuse-mcp Deploy re-run; `tracking-list-businesses` answers from tracking-service in both envs.
- **Owed from 2026-10-22 (7c):** delete the `fuse-tracker` databases (prod: disable protection first), `migration_bucket_enabled=false` once the bucket is empty, delete `iac/projects/fuse-tracker`, `iac/env/fuse-tracker`, `legacy-stack.yaml`, the tf-plan matrix entry and `terraform_scan_legacy` (+ branch protection).
- 2026-10-15, on Harry's call (not waiting the week): deleted the `fuse-tracker` Firestore databases in dev and prod (prod protection disabled first). Exports kept in the migration buckets (30-day expiry). Left of 7c: legacy IaC, `legacy-stack.yaml`, tf-plan matrix entry, `terraform_scan_legacy` + branch protection; `migration_bucket_enabled=false` once the bucket empties.
- 2026-10-15: legacy files removed (gfs-bifrost/tracking-service#8): IaC, `legacy-stack.yaml`, plan matrix entry, `terraform_scan_legacy`, deploy.yaml's stack picker; `DEV_STACK`/`PROD_STACK` variables deleted. No branch protection to update. Left: `migration_bucket_enabled=false` once the exports expire (~2026-11-13).
- 2026-10-15: emptied both migration buckets (1,026 dev / 983 prod objects, the old-database exports) on Harry's call and switched the bucket off (gfs-bifrost/tracking-service#9, plan 0/1/2 per env). Cutover complete; nothing owed.

## Follow-up (2026-10-15, afternoon): programme finished
- B7 observability#70/#71 (dashboard ut4-puv-cv7, monitors; hold-aware composite fixed after No Data), B8 fuse-mcp data + Waypoint onboarding + Confluence pages 331776001/331251735, B9 tracking-service#11, B11 #12, B5 #14 (branch protection), C6 #10, C7 fuse-ui#331/#332 + tracking-service#13, C8 fuse-ui#329, B10 fuse-ui#330.
- Verified live that goods-out made is `goods_out_confirmation` (not `sales_order`); fuse-mcp note corrected (2ac01e5).
- 9 Oct 429s: instance cap under slow stats transactions; no change.
- Cancelled Matt's stale parked observability run 38596058659 (its changes were already applied).
- Left: B12/B13 paused; the tracking-service main checkout still holds the original uncommitted C6 work (now shipped via #10) — Harry's to discard.

