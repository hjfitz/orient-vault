---
title: "SNAP Polling Log Volume — Migration State"
programme: "snap-polling-log-volume"
status: planning
owner: ""
services: ["snap-queue-polling-service"]
created: "2026-09-22"
updated: "2026-09-22"
tags: [bifrost, migration-state]
---
# SNAP Polling Log Volume — Migration State

<!-- The single source of truth for PROGRESS. The Overview carries the narrative and the verdict;
     this doc is the live ledger a session reads to know what is done and what is next.
     `wp programme status/next/tick` read and write the `## Unit status` tables below, so keep the
     table shape intact. Guidance lives in HTML comments (Obsidian hides them); <angle spans> mark
     what a human or agent must fill in. -->

## What this is
Cutting `snap-queue-polling-service`'s (repo `gfs-bifrost/snap-adapter`, `apps/snap-queue-polling-service`)
prod log volume from a baseline of **395,752 logs/day** (`service:snap-polling-service`, measured
2026-09-22) toward a small fraction of that, without losing the operational visibility those logs
exist to provide. Nine units, drawn from a `waypoint-ideate` pass on 2026-09-22 prompted by a Datadog
investigation into the volume. Every unit already has a draft plan stub in
`plans/` (created by that ideate pass) — promote with `wp plan new snap-queue-polling-service
--programme snap-polling-log-volume --unit <id>` when picked up, folding the stub's Intent in rather
than starting blank.

## Unit status
Legend: ⬜ not started · 🟨 in progress · ✅ merged · ⛔ blocked · ⏸ deferred · ❌ dropped · 🔄 rescoped

### A — Kill the two dominant volume sources
| Unit | St | Summary | Deps | Risk | Tier | PR | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **A1** | ⬜ | Replace StU-not-found warn with a metric | | med | sonnet/medium | | **87% of daily volume (345,517/day).** `consignmentsToCanonical()` (`goods-out.confirmation-handler.ts:494-501`) warns once per consignment-line row, no dedup, for ~4,207 consignments across 19 businesses that never resolve and re-poll every 2 min forever (same consignment+StU fires up to 11x in one poll). User's explicit call: remove the log line entirely, replace with `snap.confirmation.stu_unmatched{businessId}`. Risk: the warn was deliberately added (FUSE-1009/#196) to replace silent-zeroing with visibility — the metric must carry enough cardinality (businessId at minimum) to triage without it, see R1. Plan: `plans/replace-the-per-item-stu-not-found-warn-with-a-m.md`. |
| **A2** | ⬜ | Stop double-logging raw Axios error | | low | sonnet/low | | Every failed SNAP request logs the full raw Axios error object twice — `metrics.interceptor.ts`'s `responseFailureMetricInterceptor` and `fetch-outbound-queue.ts`'s catch block both log `error` in full for the same failure. 12,431 error logs/day total; one sampled payload alone exceeded a 20k-token read. Log once, at the site closest to the failure. Plan: `plans/stop-double-logging-the-raw-axios-error-on-snap-.md`. |
| **A3** | ⬜ | Per-business backoff for chronic SNAP failures | | med | sonnet/high | | No breaker trips on a single business's 4xx (per-host breaker only trips on 5xx/network) — a permanently-broken business (dev tenant `HJF`/`FUSEDEV`, or a real customer with stale creds) retries at full 2-min poll frequency forever, feeding A2's error pair indefinitely. Add per-business suppression/backoff; must stay visible via metric, never silent (R2). Touches the same failure path as A2 — sequence after it to avoid a conflicting diff, not a hard dependency. Plan: `plans/per-business-backoff-for-chronically-failing-sna.md`. |

### B — Remaining log discipline
| Unit | St | Summary | Deps | Risk | Tier | PR | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **B1** | ⬜ | Aggregate claim-skip / already-claimed info logs | | low | sonnet/low | | "Confirmation claim skipped duplicates" (733/day) + "Skipping already-claimed queue items" (512/day) log the INC-30 idempotency mechanism working as designed, once per occurrence. Collapse to one per-poll summary count each — same pattern as PR #142's earlier "quiet per-cycle outbound-queue fetch log". Plan: `plans/aggregate-claim-skip-and-already-claimed-info-lo.md`. |
| **B2** | ⬜ | Migrate remaining raw logger calls onto FUSE-995 seam | A1, A2 | low | sonnet/medium | | FUSE-995 (PR #236) migrated the sibling "Receipt line consignment not matched" warning onto `FuseEventLogger.event()` but left the SNAP-failure logging and other raw sites untouched. Do this after A1/A2 land so "remaining" is accurate rather than migrating code about to be deleted. Plan: `plans/migrate-remaining-raw-logger-calls-onto-the-fuse.md`. |
| **B3** | ⬜ | Extend DROPPED_CONFIRMATION tag convention | | low | sonnet/low | | Only two standardized grep-able tags exist today (`DROPPED_CONFIRMATION`, `DROP_GOODS_IN_CONFIRMATION_LINE`); degraded-but-non-fatal per-item warnings (the StU case being the clearest example) carry no tag from that vocabulary. Also closes the stale `// TODO: move to CONFIRMATION_METRIC` at `confirmation-failure.ts:10`. Natural to sequence after A1 (the reference case) but not a hard dependency. Plan: `plans/extend-the-dropped-confirmation-tag-convention-t.md`. |
| **B4** | ⬜ | Investigate debug logs leaking into prod | | med | sonnet/medium | | 8,850 debug-level logs/day despite `iac/env/prod.tfvars` setting `LOG_LEVEL=info` (confirmed via PR #231's description) — a real anomaly, root cause not yet known (raw `console.*`? logger built before config loads?). Plan: `plans/investigate-debug-level-logs-leaking-into-prod.md`. |

### C — Make it observable going forward
| Unit | St | Summary | Deps | Risk | Tier | PR | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **C1** | ⬜ | Add a Datadog log-volume monitor | | low | sonnet/low | | No monitor exists today for this service's overall log volume — the 4,207-consignment backlog behind A1 grew to 87% of daily volume over an unknown number of weeks before a human happened to ask. Monitor daily/hourly count (or rate-of-change) for `service:snap-polling-service`. Plan: `plans/add-a-datadog-log-volume-monitor-for-snap-pollin.md`. |
| **C2** | ⬜ | Add log-volume/StU-unmatched tab to SNAP dashboard | A1, C1 | low | sonnet/low | | User-suggested during keep/discard. Surface A1's `stu_unmatched` metric and C1's monitor as a new tab on the existing "FUSE — SNAP WMS Operations" dashboard (`yer-2rs-zwp`) rather than leaving them monitor/metric-only. Plan: `plans/add-a-log-volume-stu-unmatched-tab-to-the-snap-w.md`. |

## Gates
(none) — every dependency here is a same-programme unit, tracked via the Deps column above; nothing external gates this work.

## Risks
- **R1 ★** Replacing the per-item StU-not-found log with a metric-only signal loses the ability to grep-trace one specific stuck consignment by id — today's warn carries `consignmentId`/`stockTrackingUnit`/`businessId` per occurrence. Mitigation: A1's metric must carry `businessId` at minimum, and consider a heavily-sampled/rate-limited log line (e.g. one example per business per day) rather than zero detail. Status: to be resolved in A1's plan, not yet decided.
- **R2 ★** A3's per-business backoff could mask a genuinely ongoing customer-impacting SNAP integration failure if suppression isn't paired with an always-on metric/alert. Mitigation: the metric behind the suppressed error must keep incrementing even while the log is dampened, and C1's log-volume monitor is not a substitute for a per-business failure-rate monitor if one doesn't already exist. Status: to be resolved in A3's plan.

## Decision log
- **2026-09-22** — Programme created from a `waypoint-ideate` pass. Scope deliberately excludes root-causing *why* SNAP never returns a StU for the ~4,207 stuck consignments (discarded idea, reason: "already covered elsewhere") — this programme is about the logging/observability discipline around that condition, not the underlying SNAP data gap. Also excludes plain aggregation of the StU warning (discarded in favour of A1's metric-only replacement, per the user's explicit direction during keep/discard).

## Scar tissue
- The StU-not-found warn was deliberately added (FUSE-1009, PR #196) to replace silent-zeroing of unmatched-StU physicals with visibility. A1 removes the log line but is not a reversion to silent-zeroing — the metric must be the equivalent-or-better signal, not a net loss of visibility. Don't let A1 ship as a pure deletion.
