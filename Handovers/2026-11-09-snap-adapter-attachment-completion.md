---
tags: [handover]
status: open
workstream: snap-adapter — complete post-create attachments on retried orders, then per-order slot/breaker handling and visibility (9 Nov 2026 ilg005 incident follow-up)
programme: SNAP Resilience Normalisation
repo: gfs-bifrost/snap-adapter
from: laptop (harry, tmux session `monitors`)
to: hjf.shell.platform.ilg.software
session_id: 7f84afae-380e-4959-8dc8-c8b0cbe9f19d
resumed_by: ""
updated: 2026-11-09T23:04Z
---
# Handover: snap-adapter attachment completion (ilg005 incident follow-up)

The source session is a `datadog-watch` session and **stays on the laptop** (it keeps replying to alert threads). It does not carry over. This record is the fix workstream only: plan it with `waypoint-plan`, action it, open a **draft** PR, DM Harry as it goes.

## Where things stand

On 9 Nov 2026 Snap host ilg005 (DB5, Brackmills 2) was slow to accept writes at 16:05–16:36Z and hung for up to 120 s at 20:00–20:18Z. snap-adapter nacked transient failures (`slot_timeout`, `circuit_open`, `snap_api_error`) and Pub/Sub redelivered. Every affected order reached Snap, nothing was exhausted, nothing is held in replay-service. **35 shipments (PURDYFIGG 32, STUBBLE 3) were created without their `PRODDETAIL` attachment** ("Cleaning Products" for PURDYFIGG, "Backpacks & Bags" for STUBBLE, the customs product description, a static per-business mapping default). No shipment created after 20:18Z is missing it.

Mechanism (read from master `8b2e5af`; the deployed prod revision `snap-adapter-prod-00100-qk9` carries the same version tag):
- `createInSnap` (`apps/snap-adapter/src/core/sales-order/sales-order.service.ts`, about :460-480) GETs the shipment and throws `already_in_wms` for any stage other than 00.
- `event.controller.ts` acks that via `acknowledgeAlreadyInWms` (about :323-330, :388-412) and **skips `handleAttachments`** (:264-266). `handleAttachments` is a separate `PUT /v2/attachments` (sales-order.service.ts:~332), with its own slot and breaker gate.
- During a stall the shipment is created, the attachment call times out or is starved, the delivery is nacked, Snap allocates the shipment to Stage 10, and the redelivery then acks without the attachment. (Inferred from timing and absence of a "created" log; the `slot_timeout` log carries no path. Also: 13 of 18 timed-out `PUT /v2/attachments` were committed by Snap anyway.)
- This gap is already recorded in Waypoint `Engineering/snap-adapter/known-context.md:82` (2026-09-29 PURDYFIGG timeouts) and was never closed. Related: a keyed re-PUT of a shipment replaces its child rows (FUSE-1147, `plans/FUSE-1147-stop-re-putting-live-shipments.md`). **Never fix this by re-PUTting the shipment.**

Backfill done tonight (read-only checks, then one `PUT /v2/attachments` row per shipment, each read back):
- 30 shipments fixed: PURDYFIGG 27 (#6700369, #6701849, #6702933, #6703566, #6703606, #6703620, #6703684, #6703686, #6703726, #6703789, #6703822, #6705593, #6705896, #6705900, #6705902, #6705905, #6705906, #6705907, #6705911, #6705913, #6705919, #6705921, #6705922, #6705927, #6705943, #6705976, #6705982) and STUBBLE 3 (SC17420681, SC17420682, SC17420683).
- 5 left untouched, already Stage 90 and despatched with Evri labels: #6703573, #6703602, #6703666, #6703713, #6703820 (all domestic GB).
- Posted to #bifrost-general (ts 1794262802.922819) and #snap-wms (ts 1794263199.942269) and noted in the alert thread in #bifrost-notifications (ts 1794262810.475209).
- Row format, verified identical to an adapter-written row (shipment PURD7978AF54F1E, LineId PURD1F20A8): `{Table:"SHH", Key:<ShipmentId>, KeyLine:"0", LineId, Type:"PRODDETAIL", AttachmentText}`. `LineId` = `createDeterministicId(businessId, undefined, "<TYPE>:<keyLine>", shipmentId, 10)` (`apps/snap-adapter/src/shared/identity-helper/create-deterministic-id.ts`): first 4 chars of the uppercased businessId, plus the first 14 hex of sha256 over `<BIZ>::<TYPE>:<KEYLINE>:<SHIPMENTID>` uppercased, cut to 10.

Programme context (read before planning): this lives in **SNAP Resilience Normalisation** (`Bifrost/SNAP Resilience Normalisation/Migration State.md`). `@gfs-bifrost/resilience` provides the semaphore, token bucket and per-host breaker. **PR #331 (open, ready, Harry's account, updated 2026-11-09T10:50Z) flips `SNAP_TRANSPORT_GUARD=adapter` in prod (unit X1 step 1)**; prod is on the legacy interceptor path today (`SNAP_TRANSPORT_GUARD` unset live). The guard (`guardSnapTransport`, #322) runs per HTTP request: `canAttempt` → token → slot → `breaker.execute` → release in `finally`, with a single half-open probe. Do not duplicate or fight that work; the fix below must work in both modes.

Live limits at 9 Nov (Cloud Run revision 00100 plus code defaults; prod env for the semaphore not read): max 3 instances, 30 concurrency each; 5 slots per instance per host; `SNAP_SLOT_ACQUIRE_TIMEOUT_MS` 30000; request timeout 120000 ms; `SNAP_MAX_TRANSIENT_DELIVERY_ATTEMPTS` 30 (adapter self-reports to `create_data_failure`); subscription ack deadline 300 s, `maxDeliveryAttempts` 35, backoff 10–600 s. Legacy breaker: 5 consecutive 5xx or no-response failures, probes after 30 s; slot timeouts are not counted.

## In flight

| Work | PR / branch | State | To close it |
| --- | --- | --- | --- |
| The fix itself | none yet | Not started. Plan not written. | Run `waypoint-plan` for snap-adapter (folder `Engineering/snap-adapter/`), then `waypoint-work`. Branch `hjf/<short-description>` off fresh `origin/master`; **no ticket key** in branch, PR title or commit. Open a **draft** PR. After it exists: `wp ledger snap-adapter --title "<imperative>" --body "<what and why>\n\nPR: gfs-bifrost/snap-adapter#<n>" --programme "SNAP Resilience Normalisation"` (no `--ticket`). |
| PR #331 (X1 step 1) | `hjf/snap-transport-guard-on` | Open, not part of this work. A Terraform apply behind the prod gate. | Not yours. Do not merge or approve it. Rebase onto or around it if the fix touches the same files. |

## Waiting on Harry

- The 5 despatched shipments have no attachment. Recommendation: leave them (customs description only, domestic GB, labels already generated). Harry or ILG to confirm.
- Whether to raise tonight's episode to P2. It was called P3 all evening and no incident was declared; Harry has not replied to the DM.
- ILG call 10 Nov 11:00 (UK): ask for IIS time-taken logs from 7 Nov 04:26Z (about 4.07 s stall on all five hosts) and DB5 blocking/lock waits for 9 Nov 20:00–20:20Z. Harry's to run.
- Snap latency monitor 179927768 is muted until about 2026-11-10T10:21Z. Recommendation: let it lapse.

## Next up

Design, in this order (recommended; the plan should challenge it):
1. **Resumable completion (the actual fix).** On the `already_in_wms` path, before acking, GET `/v2/attachments/SHH/{id}` (or per-row), and run `handleAttachments` for what is missing. LineIds are deterministic, so it is idempotent. A transient failure nacks. A Snap rejection on a despatched/closed shipment is logged, metered and acked. Open question not verified: whether `PUT /v2/attachments` replaces or adds to existing rows; always write the full computed set so either is safe. Also unverified: whether Snap accepts the write at Stage 30/90 (the backfill wrote Stage 30 fine, Stage 90 never tried).
2. **Per-order resource handling.** Idea from Harry: one slot and one breaker check per order so a half-written order never starves at its attachment call. Challenge it against `guardSnapTransport` (per request) and the single-probe design: a per-order slot held across several calls needs an order-level time budget well under the 300 s ack deadline (calls can take 120 s each). Alternatives to weigh: priority or reserved slot for post-create calls, or acquiring one slot for the create+attachments pair only.
3. **Visibility.** A metric for "acked without attachments"; the request path/method on `slot_timeout` logs (`classify-snap-failure.ts:325-333` carries none); consider a longer slot wait for post-create calls.
4. Out of scope for this PR: the Shopify connector's 3-hour sliding poll window (re-sends about 1.7k mostly duplicate PURDYFIGG records every 5 minutes; dedupe drops 98–99%, none reach Snap; recommendation was to narrow to `updated_at >= 15–30m`, a PURDYFIGG config change to check via the preview endpoint first), and all X1/X2 Terraform flips.

## How work is done here

- Repo rules: `~/code/fuse/snap-adapter/CLAUDE.md` / `AGENTS.md` if present, and the Waypoint folder `Engineering/snap-adapter/` (read `known-context.md`, `architecture.md`, `operations.md`, recent `ledger.md` first; run `wp stale` and treat anchored docs that have not been re-verified as suspect).
- Skills: `waypoint-plan`, then `waypoint-work`, `action-ticket`/`create-pr` conventions for the mechanics (dev deploy and e2e verification with evidence, `review-panel` on your own diff before handing it over). Harry's standing rule: any review goes through `review-panel`.
- **Limits:** open the PR as a **draft**. Do not merge. Do not approve or apply Terraform. Do not deploy to prod. No writes to Snap prod. No replays, retries, config writes or monitor edits. Dev deploys and dev verification are fine. Never print or store credentials; `get-business-config` returns Snap credentials and an SFTP key in plaintext, so avoid it.
- **DM Harry** (Slack user U0990E3P8BC) at each milestone via Bifrost Support Bot, using the `slack-bot` skill: run from `~/code/fuse/bifrost-support-bot` with `~/.slack/bin/slack api chat.postMessage` (never an `mcp__slack` write tool, which would post as Harry). Milestones: plan written, implementation started, tests green, dev verified, draft PR open (link), anything blocked. One or two lines each.
- Anything ambiguous goes under **Waiting on Harry** here and in a DM.

## On the target

Not checked. `ssh harry@hjf.shell.platform.ilg.software` from the laptop failed with `Host key verification failed`, so the tool, login and repo checks, the `~/.claude` sync and the vault pull are all owed. Needs: `claude`, `gh` (logged in), `git`, `pnpm`, `node`, `gcloud`, `jq`, `python3`; clones of `gfs-bifrost/snap-adapter` (at `~/code/fuse/snap-adapter`) and `bifrost-support-bot` (for the Slack CLI path), the Slack CLI logged in for the app `A0C2EJ3FMFD` / team `T0561688FEJ`, and `"defaultMode": "auto"` so it does not stall at a prompt.

## Gotchas

- The laptop's `~/code/fuse/snap-adapter` was 15 commits behind `origin/master` on its local `master`. Use a fresh worktree from `origin/master` (8b2e5af at the time of writing).
- Datadog `snap.request.latency` has no path/method tag, and `slot_timeout` logs carry no path. Do not claim which call timed out without evidence.
- The adapter log tag `version` is the git sha; check `analyze_datadog_logs` by `version` to see what prod runs.
- `snap-write`/direct Snap GETs need the business's own credentials from `get-snap-connection`; STUBBLE and PHLUR rows are invisible with another business's credentials.
- Datadog's Slack posts lag the event by about 80 s; Recovered posts are not alerts.

## Closed since handover

| When (UTC) | Work | Result |
| --- | --- | --- |
