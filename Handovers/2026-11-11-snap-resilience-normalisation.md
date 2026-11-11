---
tags: [handover]
status: open
workstream: SNAP Resilience Normalisation — S1 shipped; X1 steps 2–4, X2, S2 and S3 are next
programme: SNAP Resilience Normalisation
repo: gfs-bifrost/snap-adapter (also pkg-node, observability, ilg-platform/images)
from: hjf.shell.platform.ilg.software (rc-hjf)
to: laptop
session_id: 3958064e-f29c-4a24-8868-8f726d62feae
resumed_by: ""
updated: __NOW__
---
# Handover: SNAP Resilience Normalisation, workstation → laptop

State of the programme itself lives in `Bifrost/SNAP Resilience Normalisation/Migration State.md` (read it with `python3 ~/.claude/waypoint/wp.py programme status "SNAP Resilience Normalisation"`). This record covers what that doc can't: what is live right now, what is in flight, and how this session worked.

## Where things stand

Checked live at __NOW__. Every behaviour change in the programme ships behind an env switch that defaults to today's behaviour, and **only one switch is on in prod: `SNAP_TRANSPORT_GUARD=adapter`** (since 2026-11-10 12:05Z). The poller has none of its switches set. The S1 prod apply (below) was approved at about 10:40Z today and is the only thing still moving.

| Where | Image | Revision | Switches set |
| --- | --- | --- | --- |
| snap-adapter prod | `dd86e1a` (S1, applying; was `afdb226`) | `snap-adapter-prod-00101-7dp` → new revision rolling out | `SNAP_TRANSPORT_GUARD=adapter`. Not set: `SNAP_CB_TRIP_ON_429`, `SNAP_ASSERT_WRITE_RESPONSES` |
| snap-adapter dev | `dd86e1a` | `snap-adapter-dev-00577-428` | `SNAP_TRANSPORT_GUARD=adapter`. `SNAP_ASSERT_WRITE_RESPONSES` removed again after the S1 check |
| snap-polling-service prod | `8b2e5af` | `snap-polling-service-prod-00109-hzq` | none |
| snap-polling-service dev | `8b2e5af` | `snap-polling-service-dev-00521-t7r` | none |

Programme ledger: 25 units, 15 done, 2 in progress (X1, S1), 5 todo, 3 deferred. The poller services are named `snap-polling-service-{dev,prod}` in Cloud Run (the repo is `snap-queue-polling-service`).

| Unit | Delivered | PRs | State |
| --- | --- | --- | --- |
| A1–A3 | `@gfs-bifrost/resilience` 0.2.0, adapter on it, `snap.breaker.*` metrics | #321–#325 | merged, prod |
| Q1–Q5, Q2b, Q3a | poller timeout, breaker parity, `snap.breaker.*`, host-key normalisation, single probe, concurrency cap | #324, #326–#330 | merged, prod, switches off |
| (zod) | zod ^4.6.6 in both apps; 3 base-image CVE suppressions in `.trivyignore` expiring 2026-11-16 | #332 | merged, prod |
| X1 step 1 | `SNAP_TRANSPORT_GUARD=adapter` | #331 | live in prod since 2026-11-10 12:05Z |
| S1 | every SNAP create checks its 2xx response (`assertSnapEntityWritten`); sales order and master data behind `SNAP_ASSERT_WRITE_RESPONSES` (off) | #333 (`dd86e1a`) | merged 2026-11-10 13:14Z, prod apply in progress |

## In flight

| Work | PR / branch | State | To close it |
| --- | --- | --- | --- |
| S1 prod rollout | #333, Deploy run 42822697396 (`gh run list --workflow "Deploy snap-adapter"`) | The prod gate was approved at about 10:40Z today; the plan was the routine one (image tag plus the sensitive-env `-/+` reorder, 0 add / 1 change / 0 destroy). Apply was running when this was written. | Confirm the run finished and `snap-adapter-prod` is serving `prod-dd86e1a…` (`gcloud run services describe snap-adapter-prod --project bifrost-prod-global1 --region europe-west2`). Read-only prod smoke (Datadog: errors, p95, `snap.breaker.*`, create failures by `failureMode`). Then `wp programme tick "SNAP Resilience Normalisation" --unit S1 --status done --pr "#333"` and add a Decision log row. The ledger entry and the Confluence row (page 352616450) are already written. |
| Attachment-completion fix | [[Handovers/2026-11-09-snap-adapter-attachment-completion]] | **Not mine.** That record is `open` with `resumed_by` empty (nobody has picked it up) and lives under this programme. No plan or PR exists. | Leave it to whoever resumes that record; two sessions must not drive one workstream. Branch any work off `origin/master` at or after `dd86e1a`. |

## Waiting on Harry

None outstanding. Each flip below is a Terraform change and needs its prod plan shared and agreed before the merge and the `terraform-prod` approval (global CLAUDE.md, plan-then-proceed). Nothing has been shown to Harry yet, so nothing is awaiting an answer.

## Next up

Harry's direction on 2026-11-10: "follow your recommendation starting with S1 and moving all the way in to S3 as we progress things with our switches". The order:

1. **X1 step 2, due today under the one-a-day pace** (step 1 was 2026-11-10): Terraform for the poller, `SNAP_REQUEST_TIMEOUT_MS=120000` and `SNAP_BREAKER_SINGLE_PROBE=true` together (the poller refuses to boot with the probe switch but no timeout). Mirror #331's shape in `iac/projects/snap-queue-polling-service`. Share the prod plan first.
2. **Flip `SNAP_ASSERT_WRITE_RESPONSES`.** It is *not plumbed through Terraform yet*: the flip PR adds the variable (like `snap_transport_guard` in `iac/projects/snap-adapter/variables.tf`, with validation), the `cloud-run.tf` env entry and the value. Recommend dev first for a day, then prod.
3. **X1 step 3:** adapter `SNAP_CB_TRIP_ON_429=true`, plus the message edit on monitor 337501612 (observability repo).
4. **X1 step 4:** poller `SNAP_NORMALISE_HOST_KEY=true`, plus repointing the latency monitor groups and the `$snap_host` dashboard variable. This clears G3.
5. **X2:** delete the adapter's interceptor transport path once `SNAP_TRANSPORT_GUARD=adapter` has soaked a few days. The soak started 2026-11-10 12:05Z.
6. **S2** after X2, then **S3** with the `SNAP_RESPONSE_PARSE_MODE=strict|tolerant` breakglass (Harry's requirement: an env var that falls back to today's tolerant parsing). Designs are in the Migration State and the decision record `Engineering/snap-adapter/decisions/2026-11-05-snap-resilience-is-shared-through-gfs-bifrost-resilience-not.md`.
7. **Q3b** (measure per-host concurrency, then cap, IaC) and **O1–O3** (metric cutover with the observability monitors).
8. **Golden image, deadline 2026-11-16:** the `.trivyignore` entries expire then. In `ilg-platform/images` the Dependabot bump (#22) merged 2026-11-09 and the `node24-runtime` nightly was green on 2026-11-10 12:27Z and 2026-11-11 05:23Z, so the base image may already be fixed. To close: rebuild the snap-adapter and poller images, confirm `image_scan` passes with the three entries removed, then drop them.
9. **Small owed items:** a retained subscription on the create_record `.dlt` topics; retune or retire monitor 304004530; the expired no-review section in `~/code/CLAUDE.md`; the product-alternates response check in master data; transient-classification parity with `SNAP_ENDPOINTS`.

## How work is done here

- **Per unit:** worktree off a fresh `origin/master`; implement behind a default-off switch; mutation-test the specs; one independent review agent (sonnet) on the diff, with every claim re-verified; deploy the branch to dev and drive the real flow; non-draft PR; `wp ledger snap-adapter --programme "SNAP Resilience Normalisation" --title … --body "…\n\nPR: gfs-bifrost/snap-adapter#N"`; Confluence changelog row on the November page (id 352616450, newest first); CI; merge; read the prod plan; approve; prod smoke. This is the `/ship` skill's flow and Harry has said to carry on in it.
- **Prod gate:** merging runs the dev apply and the prod plan, then parks at `terraform-prod`. Approve only the run whose `headSha` is your merge, with `POST repos/gfs-bifrost/snap-adapter/actions/runs/<id>/pending_deployments` (environment id 6958844742, a comment naming the ship id). Cancel only runs whose head is an ancestor of the approved sha. Re-check the live prod image before and after, since approving an older parked run rolls prod back.
- **Routine prod plan:** image tag plus the sensitive `env` `-/+` reorder. Anything else (a destroy, IAM, topics, a new resource, env vars you didn't add) is a stop: share it.
- **Terraform flips** are the one place to stop for Harry's agreement on the plan, per change, not as a blanket approval.
- **Programme discipline:** `wp programme tick` statuses are `todo|doing|done|blocked|deferred|dropped|rescoped`. Add a dated Decision log row for anything decided. Don't rewrite the Overview or Scar tissue; supersede with a `> SUPERSEDED` blockquote.
- **Review requests** from Harry go through `review-panel`, not the `/ship` review agents.
- **Out-of-hours DMs** to Harry (U0990E3P8BC) as Bifrost Support Bot, only outside 09:00–17:00 London (`slack-bot` skill, from `~/code/fuse/bifrost-support-bot`; the DM channel comes from `conversations.open users=U0990E3P8BC`).
- **Memories that apply:** `feedback_sprint_cadence`, `feedback_pr_clear_autonomy_blocked` (a background agent told to "merge without confirmation" is refused; split repair from merge), `project_merak_context` is unrelated.

## On the target (laptop)

Not checked from rc-hjf: the laptop isn't reachable from here (same as the carrier-playground handover). Before starting, on the laptop:
- `git -C ~/code/fuse/snap-adapter fetch` and make a worktree from `origin/master`; the rc-hjf primary checkout was stale at `7f4e10d`, and the laptop's may be too.
- Have `gh`, `gcloud` (projects `bifrost-dev-global1`, `bifrost-prod-global1`) and `wp` working. Terraform plans only come from CI: rc-hjf has no local credentials, and the laptop's are unchecked.
- The vault (this record, the Migration State, the ledger) arrives by `orient-vault-sync`; never copy it.
- The S1 branch is gone from the remote (deleted on merge). Three merged worktrees are left on rc-hjf and don't matter to the laptop: `snap-assert-write-responses`, `snap-transport-guard-on`, `zod-4-6`.

## Gotchas

- The deploy workflow is named `Deploy snap-adapter`. `--workflow Deploy` finds nothing, and a poll loop on it 404s forever. The dev-branch deploy is `snap-adapter-manual-deploy.yaml` with `--ref <branch>`.
- GitHub's API limit (5,000/hr) is per user, so it's shared by every session on both machines. Check `gh api rate_limit`, and prefer a scheduled wake-up over a retry loop.
- Job logs: `gh run view --log` refuses while a run is in progress. Use `gh api --allow-escape-sequences repos/gfs-bifrost/snap-adapter/actions/jobs/<id>/logs | sed 's/\x1b\[[0-9;]*m//g'`.
- Transient CI failures that passed on re-run: Terragrunt "Missing required GCS remote state configuration location" and a `tf-output` state-lock 412.
- Dev testing of a switch: `gcloud run services update snap-adapter-dev --project bifrost-dev-global1 --region europe-west2 --update-env-vars X=Y`, then `--remove-env-vars` to restore. A merge's dev apply also resets env to the Terraform state.
- Simulator faults: `POST https://crackle.devtools.fuse.freightops.dev/api/v1/businesses/HJF/faults` with `{"entity":"shipments|products|receipts","mode":"status_error","count":1}` (one write each; work orders and sales orders both use `shipments`). `status_error` returns HTTP 200 with `{Status:"Error"}`. The key is the `CONTROL_API_KEY` env on `fuse-mocker-snap-api-dev`: read it into a chmod-600 scratch file, never print it, delete it. Faults only hit writes and the outbound clear.
- `mock-send` must target `create_record_request` (`create_record` is IAM-denied). Read the adapter's result in logs by `jsonPayload.correlationId`, which is `mock-<your id>`.
- A live breaker-open recipe on dev: `SNAP_CB_CONSECUTIVE_FAILURES=2` plus a 429/503 fault. The poller's breaker never opens for dev's `tests.com` host.
- `snap-write` style config refusals: `SNAP_BREAKER_SINGLE_PROBE` and `SNAP_MAX_CONCURRENT_REQUESTS` refuse to boot without `SNAP_REQUEST_TIMEOUT_MS`.
- The comment-density hook blocks a commit or push that adds a multi-line comment block. Use one-line comments, and don't move an existing multi-line comment (it counts as added).
- Lint reflows code, which breaks scripted string replaces; re-read, then use Edit.
- A cockatiel Closed-branch failure calls `open()` even if the circuit is already half-open; both apps guard it with the "late failure" sentinel. Don't remove that.
- `@gfs-bifrost/snap`'s `assertSnapWriteOk` throws `SnapWriteRejectedError`, which `classifySnapFailure` treats as `unexpected`. Re-raise as `EntityCreationException` via `assertSnapEntityWritten`.
- `tsc -p tsconfig.json` in `apps/snap-adapter` shows 11 spec-fixture type errors that master also has (`customerRef` missing, SnapShipment args). `build:check` is clean; these are not ours.
- Datadog: metrics are in the `snap.` namespace, the tag is `environment:` (not `env:`), and breaker state is 0 closed / 0.5 half_open / 1 open or isolated, per `snap_host`.

## Closed since handover

| When (UTC) | Work | Result |
| --- | --- | --- |
