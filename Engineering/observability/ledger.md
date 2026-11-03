---
tags: [waypoint, ledger]
---
# observability — work ledger

Agent-facing. Newest first. What meaningful work happened here, and the
context a future agent needs. Not a diary, not release notes, not a diff.

## 2026-11-03 — Add an SFTP Host tab to the SFTP Connector dashboard

Add an SFTP Host tab to the SFTP Connector dashboard

Tabbed [FUSE][SFTP Connector] Overview (rnw-pit-a9v): the Connector tab's widgets were repointed at the shared metric catalogue (22/38 queries had been reading nothing since the move off fuse.messages.* / fuse.config.retrieval.failure / fuse.record_parse.failure). Adds an SFTP Host tab covering health, logins, uploads to ingest, users.json/provisioning/config, logs and the legacy VM. Gotchas: a logs query's $environment expands to environment:<v>, so @environment needs $environment.value; host container.* metrics carry env, not environment, so GCE instance_name:sftp-host-<env>-* is used instead; validate a tabbed body by POSTing a temp dashboard, because plan doesn't catch 400s.

PR: gfs-bifrost/observability#82

## 2026-11-02 — Publish the prod SFTP host monitors ahead of S2

Publish the prod SFTP host monitors ahead of S2

Flips the prod copies in monitors.sftp-host.tf from draft to published so they evaluate and notify when the prod host takes customer traffic at S2. Dev bad config-service key injection (sftp-connector Plan C inc 3 gate) proved the lookup/config-API monitors fire first. Draft pending Harry's plan-then-proceed.

PR: gfs-bifrost/observability#81

## 2026-10-29 — Read the dev SFTP canary's logged outcome in its monitors

Read the dev SFTP canary's logged outcome in its monitors

Canary failing/not-running monitors move from gcp.run.job.completed_execution_count (GCP stopped reporting it 10-28 00:45Z) to gcp.logging.user.sftp_canary_runs by outcome, with a 15 min evaluation delay; backend-unhealthy message updated for sftp-connector#380. Dev soak criterion b. Open, awaiting plan agreement.

PR: gfs-bifrost/observability#80

## 2026-10-28 — Alert when the weekday pr-sitrep run doesn't succeed

Alert when the weekday pr-sitrep run doesn't succeed

Ship: SHIP-1028-pr-sitrep-ready. One monitor, custom-scheduled 10:00 Europe/London Mon-Fri: no 2xx on pr-sitrep-prod in 2h (scheduler is the only caller) = failed or missing run. Custom schedules require on_missing_data, and show_and_notify_no_data refuses default_zero, so missing data carries the missing-run case. Notifies #bifrost-notifications only (priority 4). Held until pr-sitrep-prod is live.

PR: gfs-bifrost/observability#79

## 2026-10-27 — Route Snap-only monitors to #snap-wms and alert on a SNAP host circuit opening

Route Snap-only monitors to #snap-wms and alert on a SNAP host circuit opening

Adds a snap_wms_alert_handles variable (@slack-snap-wms), appends it to the SNAP API latency monitor (message made Snap-only), and adds a monitor on snap.circuit_opened by snap_host. Plan 1 add / 1 change; applied in prod 2026-10-27.

Ship: SHIP-1027-snap-wms-alerts
PR: gfs-bifrost/observability#78

## 2026-10-20 — Route dead-handle monitors to alert_handles and stop repeat-record alert noise

Route dead-handle monitors to alert_handles and stop repeat-record alert noise

Repointed 7 monitors (10 lines) from the nonexistent @slack-bifrost-alerts to local.alert_handles. Rewrote Snap Adapter entity creation to alert on distinct failing records over 15m (warn >5, alert >10), so one re-polled bad record can't hold it open. Excluded non-transient snap_adapter rejections from the platform error-rate monitor. Changed the SFTP overwrite-exposure monitor to alert on 'Confirmation write failed irrecoverably'. Plan: 1 add, 8 change, 1 destroy (274521171 replaced because of the type change). Not applied.

PR: gfs-bifrost/observability#75

## 2026-10-19 — Alert when a high-volume client's new orders stop

Alert when a high-volume client's new orders stop

One multi-alert monitor, [FUSE][Platform] New orders stopped for {{businessid.name}} (id 334504858), grouped by businessid so new clients need no change. Fires when a client has had zero fresh sales orders (fuse.dedupe.event.fresh, recordtype:sales_order) for ~2h+ while each matching hour last week had >= 5. Query uses the classic evaluation path: no .as_count() (it forces sum and aggregates before arithmetic), bare .rollup(sum, 3600) x10 because the metric is a 10s-interval rate, min(last_3h), week_before() carries a fully silent client's group (proven in the monitor engine with a throwaway). Rejected after backtests: agile/weekly anomaly (8-23 false alarms per client per 4 weeks) and ratio-drop rules (P&F's batch timing). Real coverage: P&F, Stubble, Dockbay; misses partial drops, thin clients (Saira), a client's first week. Log @businessId is upper case; metric tags are lower case. Rode along: #73's 3 dev stock-sync destroys (Harry agreed); parked runs 39275466329 and 37486023450 (both ancestors) cancelled to remove the rollback hazard. Workshop action S18 / FUSE-1126 (partial).

Ship: SHIP-1019-client-volume-drop
PR: gfs-bifrost/observability#74

## 2026-10-15 — Group tracking-service's hold input by subscription so its composite evaluates

Group tracking-service's hold input by subscription so its composite evaluates

The backlog-age composite (332917922) had 0 groups and sat in No Data because its hold input was ungrouped while the age input is grouped by subscription_id. Grouped the hold input to match; proven with throwaway monitors (composite alerted on 20 groups), now 20 groups OK. Plan 0/1/0, applied.

PR: gfs-bifrost/observability#71

## 2026-10-15 — Add the tracking-service dashboard, monitors and catalog entry

Add the tracking-service dashboard, monitors and catalog entry

Operational Overview dashboard (Speed/Flow/Health), 12 monitors (5 notify), percentile tag configs and the catalog entity for tracking-service, now its metrics are live. The backlog-age monitor is a composite that ignores a backlog built in hold mode. Plan 16/3/0, applied.

PR: gfs-bifrost/observability#70

## 2026-10-14 — Mute then unmute Pub/Sub monitors for tracking-service's held prod stack

Mute then unmute Pub/Sub monitors for tracking-service's held prod stack

Scoped downtime for subscription_id:tracking-service.prod.* on the four platform Pub/Sub monitors during the prod cutover hold (observability#68), removed after the drain (observability#69). The #68 apply also carried Matt Shaw's already-merged stock-sync monitors (#62), whose run was parked at the gate.

PR: gfs-bifrost/observability#68, gfs-bifrost/observability#69

## 2026-10-13 — Alert when fapi or shopify-connector drops a Pub/Sub push as invalid

Alert when fapi or shopify-connector drops a Pub/Sub push as invalid

Closes Poller Clear-Down E3's owed guard: prod monitors for an acked invalid push in fapi (errors.pubsub_decode) and shopify-connector (log alert), since a dropped confirmation push is now a lost confirmation.

PR: gfs-bifrost/observability#67

## 2026-10-13 — Point the clear-failure runbook at the poller, not the removed allow-list

Point the clear-failure runbook at the poller, not the removed allow-list

Monitor 327518496 named the removed clear_after_publish_business_ids allow-list; now says there's no per-business switch. Dashboard widget title de-staled.

PR: gfs-bifrost/observability#66

## 2026-10-12 — Alert when fuse-ui fails to publish an audit event

Alert when fuse-ui fails to publish an audit event

Prod monitor on fuse.audit.publish_failed by {reason} (>0 in 15m, P2) plus a dev copy that notifies nobody, in monitors.fuse-ui.tf. Required before fuse-ui prod moves to AUDIT_SINK=both (Audit Service UF). Tags: environment + service_name:fuse-ui-app-<env>.

PR: gfs-bifrost/observability#65

## 2026-10-12 — Apply audit-service monitors and catalog, shipping parked stock-sync monitors

Apply audit-service monitors and catalog, shipping parked stock-sync monitors

Merged and applied gfs-bifrost/observability#64: four audit-service monitors (rejected/lost prod + dev copy, dead-lettered, 5xx rate) and catalog entities audit-service, audit_fuse queue, audit-service-mongodb. The same apply shipped #61's stock-sync monitors, whose prod approval had been parked since 10-06. Before applying, codified the UI edits on snap_poller_businesses_skipped (threshold 18, on_missing_data show_no_data, both set 10-08) so the apply did not revert them; plan was 9 add, 1 change (#61's message), 0 destroy. Dev monitor proven OK→Alert by publishing a wrong-system message to audit.dev.fuse.v1.

PR: gfs-bifrost/observability#64

## 2026-10-12 — Add audit-service monitors and catalog entities (held)

Add audit-service monitors and catalog entities (held)

Audit Service UE.6: prod monitors for dead-lettered audit messages, the 5xx rate and rejected (lost) messages, a dev copy of the last that notifies nobody, and catalog entities. Not merged: the plan also carries #61's parked stock-sync monitors and reverts a UI-raised threshold on snap_poller_businesses_skipped (18 back to 17), so it's waiting on a human.

PR: gfs-bifrost/observability#64

## 2026-10-12 — FUSE-1118

Warn-only monitor for skipped confirmation lines

Prod monitor on fuse.confirmations.lines_skipped by businessid: warns on the first skip in an hour; the unreachable critical threshold and handles inside the is_warning block mean it never alerts and its recovery notifies nobody. Merge after shopify-connector#329; share the plan before apply.

PR: gfs-bifrost/observability#63

## 2026-10-02 — Add a monitor for failing outbound-queue clears

Add a monitor for failing outbound-queue clears

Poller Clear-Down C2/D1 prerequisite. Prod monitor on snap.outbound.clear_failed (warn 3, alert 10 per business in 30m) plus a dev copy that notifies nobody. Plan: 2 to add. Firing proof in dev after apply.

PR: gfs-bifrost/observability#60

## 2026-10-02 — Codify the PURDYFIGG exclusion on the production error-rate monitor

Codify the PURDYFIGG exclusion on the production error-rate monitor

Console-added exclusion on the error-rate monitor would have been reverted by the next apply. Put into code; plan was a no-op. Applied.

PR: gfs-bifrost/observability#58

## 2026-10-02 — Raise Pub/Sub ack-headroom monitor to warn 90s / critical 180s

Raise Pub/Sub ack-headroom monitor to warn 90s / critical 180s

Ack-headroom monitor warned on normal push redelivery: its 30s warn equalled the 30s min backoff on the sftp/shopify subs. Raised to warn 90s / critical 180s and corrected the message. Applied and verified live.

PR: gfs-bifrost/observability#59

## 2026-09-30 — FUSE-1238

Point replay's dropped-failure monitors at the live metric

Two replay monitors ("Failures dropped forever" and "Replay dropping failures (data loss)") queried replay_service.event.create_failure_dropped, which replay no longer emits, so they could never fire. They now query fuse.failure.dropped scoped to service:replay_service in prod, which recorded 32 real drops in 30 days with no alert. Plan: 2 in-place monitor updates. Poller Clear-Down unit B4.

PR: gfs-bifrost/observability#55

## 2026-09-30 — Gate Fuse API availability alert on a minimum failure count

Gate Fuse API availability alert on a minimum failure count

Fuse API availability monitor is now a composite: failure ratio >5% AND at least 3 failed requests in 15m, so a single failed request on ~1-3 req/min traffic no longer pages. The 1% warning tier is dropped. Composite id 326574293 carries the original name and handles; 302685705 is now a silent ratio input and 326574290 the silent count input. Latency p95 monitor left as is.

PR: gfs-bifrost/observability#54

## 2026-09-29 — Add poller 401 and skipped-business monitors, fix poison-record wording

Add poller 401 and skipped-business monitors, fix poison-record wording

The snap poller had no monitor for SnapFulfil 401s or for the set of businesses it skips (14 to 21 to 18 on 24 Sep, no alert), and the poison-record monitor matched a plural log line that has not been written in 30 days. Adds two monitors and fixes that one.

PR: gfs-bifrost/observability#53

## 2026-09-29 — Don't notify on recovery for the SFTP canonical validation monitor

Don't notify on recovery for the SFTP canonical validation monitor

Wrapped the monitor message in {{^is_recovery}}, so its recovery posts nothing.

PR: gfs-bifrost/observability#52

## 2026-09-24 — Add businessId to sftp-connector canonical validation failures alert

Add businessId to sftp-connector canonical validation failures alert

Surfaced during a datadog-triage pass on the STUBBLE dates.dueOut canonical-validation
alert: the monitor's message showed record type/schema/error but not which business
triggered it, so every triage needed a manual log lookup just to name the customer.
Added Business: {{log.attributes.businessId}} to the message, sourced from the
triggering log line. Message-only change; plan confirmed exactly one resource, one
line added.

PR: gfs-bifrost/observability#49

## 2026-09-23 — Tune dedupe silent-publish-drop monitor and exclude SAIRA from platform error-rate monitor

Tune dedupe silent-publish-drop monitor and exclude SAIRA from platform error-rate monitor

Out-of-ticket, two Terraform-only monitor changes. (1) observability#47: [FUSE][Dedupe Service] Silent publish drop (id 302511456) flapped twice in 4 days from log-to-metric ingestion lag, not real drops; added evaluation_delay = 300 (the fix) and raised thresholds 30→50 / 10→20. (2) observability#48: SAIRA's shopify-connector orderUpdate tag writes failed on a missing write_orders scope (FUSE-1252), tripping the platform error-rate monitor; added NOT(service:shopify-connector AND @businessId:SAIRA), mirroring the existing snap-polling-service exclusion. Temporary: remove once scopes are widened (shopify-connector#278) and SAIRA reauthorises. The targeted shopify fulfilment-order-tag monitor still covers genuine widespread failures.

PR: gfs-bifrost/observability#47
PR: gfs-bifrost/observability#48
