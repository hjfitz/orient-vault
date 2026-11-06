---
ticket: none
title: Stop republished copies contending on the shared stats docs
service: tracking-service
status: active
created: '2026-10-19'
updated: '2026-10-19'
repo: /home/hjf/code/fuse/tracking-service
worktree: /home/hjf/code/fuse/tracking-service/.claude/worktrees/skip-identical-republishes
branch: hjf/skip-identical-republishes
base: origin/main
base_sha: 6f6259620
pr: '16'
tags:
- waypoint
- plan
impl_model: sonnet
impl_effort: medium
---
# none — Stop republished copies contending on the shared stats docs

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

## Intent
<!-- What we are changing and why. Link the ticket. -->
Out-of-ticket.

**The problem.** Identical republishes are 78.5% of prod ingest (15–18 Oct), and 98% of PURDYFIGG's sales orders. shopify-connector resends every open order about every 5 minutes, by design, because Shopify tags arrive late. Every copy still increments the duplicates stat on `stats/<biz>_<day>` and `stats/_all__<day>` (`foldTimeline`, `core/dedupe.go:269`). Commits serialise on those shared docs: on 2026-10-18, Firestore commits ran at 1.1–2.3 s (25–75 ms overnight), push latency was about 4 s, and the backlog spiked to 434. Traffic is expected to grow about 6×.

**The change.** A copy stops writing any counter doc, and only its own shipment or return doc is written. The daily `duplicates` stat stops being counted; per-record copy counts keep counting.

**What proves it.**
- In prod, a PURDYFIGG burst no longer drives commit latency up.
- A 6× load test then decides whether the remaining shared-doc writes (from records that aren't copies) need a hot-spot fix.

## Acceptance criteria
<!-- Observable, checkable outcomes — not tasks. Numbered by order: increments cite them as
     (AC 2,4), and sign-off prints which criteria no increment claims. -->
- [x] 1. A branch can be deployed to dev alone. No prod apply is created or parked.
- [x] 2. An identical republish of a shipment or a return whose fold changes no real counter (the normal case) leaves `stats/*`, `insights/*`, `returnStats/*` and `returnInsights/*` untouched, for both the business and the `_all_` scope (their `updateTime` doesn't change). Its own record doc is still written, and served per-record copy counts still grow.
- [x] 3. Everything else behaves as today. The core suites pass, including both shuffle tests; the only changed expectations are the duplicates-stat ones. A copy whose fold changes a real counter still writes that counter.
- [x] 4. The API and README say the stats `duplicates` counter is no longer counted from the release date. The README no longer claims a copy "cannot change" state.
- [x] 5. In prod, during a PURDYFIGG burst after release, average Firestore commit latency for the `tracking-service` database stays under 150 ms. The sales_order subscription's oldest unacked message stays under 30 s.
- [x] 6. A 6× load test on dev is recorded. Harry has signed off a decision on the remaining hot spot against a threshold agreed before the test.
- [ ] 7. Only if that decision says so: at 6×, commits on the `_all_` docs are back to the 25–75 ms band, served stats are identical, and `recompute-stats` agrees.

## Affected boundaries
<!-- Components, paths and contracts this touches. Wikilink existing explainers; do not restate
     their contents. If this names a topic, endpoint, canonical type, collection, inter-service
     dependency or shared package, sign-off will prompt for the Fuse MCP data file too. -->
- `apps/api/internal/core/dedupe.go`: `foldTimeline`. Shared by shipments and returns, so the change covers both.
- Stats contract: `duplicates` in `StatCounts`/`ReturnStatCounts` and the business-day rows (`apps/api/openapi.yaml`). The field stays; its meaning is reworded. fuse-ui vendors this file, so its weekday drift check (`tracker-contract.yaml`) goes red until it re-vendors: [[retire-the-order-tracker-s-duplicates-week-tile]].
- `apps/api/README.md`, republished-messages section (`:235-251`), plus `:113`, `:495`, `:589-590`, `:615-616`, and the "nightly reap" wording at `:241-244` and in `apps/api/CLAUDE.md:112-113`.
- `.github/workflows/` (new `manual-deploy.yaml`, inc 1); `iac` is untouched.
- Increment 4 only, if it happens: `store/firestore.go` (`writeCounters`, `groupStats`, `readStats`, `readInsights`, `readReasonCodes`), `store/scopes.go`, `store/counters.go`, `cmd/recompute-stats`, `firestore.indexes.json`.

## Assumptions & uncertainty
<!-- One line each, with how it was established. A genuine product or domain question goes here
     as UNRESOLVED: and is raised with the user, never invented. -->
- **A copy's only shared-doc write is the duplicates stat.** Established from source by the planning agent and the factual reviewer. Other counter changes are zero for identical content; a later copy can only fill an empty channel (`earliestBeats`).
- **A later identical copy does change the record** (`lastSeenAt`, `failed` via `LastCreateOKAt`, attempts, delivery state, latest-wins keys; `reduce.go:92,100,533`, `rules.go:155`, `deliveries.go:21`). That is why it keeps writing its own doc here. Skipping it outright is a contract change (see Options).
- **What remains after inc 2.** Records that aren't copies are ~21.5% of ingest: about 16k a day now, about 100k a day at 6×. They still write `_all_`. Their peak shape at 6× is unmeasured, and inc 3 measures it.
  - The draft's figure of "~1,500 non-copies per burst" was wrong: it applied the daily ratio to a burst that is 98% copies.
- **Measure with GCP metrics, not DogStatsD.** `fuse.tracking.events.*` counted about 1/3 of what Pub/Sub delivered (unverified).
- **Dev load uses business HJF**, whose `BACKEND_CONFIG` points at the fuse-mocker Snap simulator. Established from the fuse-mcp docs.
- **`mock-load-run` re-rolls references on every send for `create_record_request`**, so every message is new content. Copies are only possible on `create_record` with `randomiseReferences` off, which is the `deduplicated` group. Established by the factual reviewer from fuse-mocker `load/loop.go:222-236`.
- **This supersedes the 10-07 "no load test" decision** (Migration State decision log), on Harry's 2026-10-19 direction.

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

- [x] 1. **Dev-only manual deploy** (AC 1). This is its own PR off `main`. `manual-deploy.yaml` applies dev only, with `notify_on_success`, `notify_on_failure` and `slack_webhook`. Today a branch `workflow_dispatch` of `deploy.yaml` parks a prod apply of the branch sha. — dispatched on a branch: dev-only jobs, dev runs the branch sha — done: 6f4d206
  - verify: dispatch it on a branch. A dev revision tagged with the branch sha comes up, and the run creates no `terraform-prod` job.
- [x] 2. **Copies write no counter docs** (AC 2,3,4). Drop the duplicates `StatIncrement` from `foldTimeline`. Reword the stats `duplicates` text in openapi and the README sections listed above. Stored history is kept: `keptCounters` in `cmd/recompute-stats/main.go:166` is unchanged. — dev: identical copy left both stats docs' updateTime unchanged; shipment counted it — done: 64b81ae
  - verify, unit: update `TestDuplicateStats` (0 for both scopes) and `TestRedeliveryOfACountedRepublish/"does not count in stats twice"`.
  - verify, emulator: invert `TestFirestoreRepublishes/"the duplicates stat is kept"` (`store/firestore_test.go:467`). Assert that `UpdateTime` is unchanged on `stats/HJF_<day>` and `_all__<day>` while the shipment's `duplicates.received.count` grows. Add the same check for returns.
  - verify, dev (via inc 1): `mock-send` the same `create_record_request` twice for HJF. The Firestore REST `updateTime` of both stats docs is unchanged, and the served shipment's `duplicates.received.count` goes up by 1.
  - Also run `make fmt-check vet lint test-race test-emulator`.
  > SUPERSEDED 2026-10-19: the test ran without `mock-load-run`, because it can't produce the real shape (many distinct orders re-sent unchanged). Instead an uncommitted `cmd/loadtest` driver called the real `core.Ingestor` at 240-way concurrency against a throwaway dev Firestore database (`ts-loadtest-1019`, same field overrides, deleted afterwards), with a pre-fix (6f4d206) control. See Evidence.
- [x] 3. **6× load test on dev** (AC 5,6). No tracking-service PR. — harness, not mock-load-run; 6x copies drain 44 s; genuine path ceiling ~40/s — done: 389adbc
  - Agree the pass threshold with Harry before running. Proposed: average commit latency under 150 ms, push latency under 1 s, oldest unacked under 60 s.
  - Run two shapes against HJF:
    - new content: `mock-load-run` on `create_record_request`;
    - copies: `create_record` with `randomiseReferences` off.
  - Run each at 1× and at 6× of the 2026-10-18 burst (about 1,200 and about 7,200 messages).
  - Record the GCP-side numbers: Firestore commit latency and write count, Pub/Sub push latency, oldest unacked age.
  - If `mock-load-run`'s maximum or its interference with shared dev blocks the 6× run, extend it in fuse-mocker (direct to main).
  - verify: the numbers are in Evidence, alongside the prod post-release number from inc 2.
      gate: inc 2 approved to prod and one PURDYFIGG burst observed (AC 5)
            [x] confirmed
      gate: Harry signs off the hot-spot decision against the threshold
            [x] confirmed
> SUPERSEDED 2026-11-06 — tracking-service moves to MongoDB with stats aggregated over per-record marks (programme Tracking Service, group D), which removes every shared counter write. Not built.
- [ ] 4. **Conditional: fix the `_all_` hot spot** for stats and insights, both record types (AC 7). The design (sharded counter docs summed at read, or `_all_` computed on read from per-business docs) is chosen from inc 3's numbers.
  - Reason codes stay unsharded, because `reasonSlot`'s 50-per-day cap reads the doc.
  - If the counter layout changes, a human runs `recompute-stats` in prod (dry-run first, ingest held).
  - Re-size this increment against the 500–700 line PR target once the design is chosen.
  - verify: the emulator shows served stats identical before and after on fixtures; `recompute-stats` passes on docs written by the old build; a dev 6× rerun shows `_all_` commits back in the 25–75 ms band.
      gate: inc 3 decision says "fix needed"
            [x] confirmed

## Verification
<!-- The single authority for evidence. Increment lines carry `— done: <sha>` and nothing else.
     Check-selection order lives in verification-menu.md — do not restate it here. -->

### Evidence
<!-- Newest first, dated. One bullet per check actually run, opening with what it discharges.
     "Suite green" alone is not evidence. Sign-off requires at least one dated bullet here. -->
- 2026-10-19 [inc 3] **Load test**, throwaway dev Firestore `ts-loadtest-1019`. The driver called `core.Ingestor.Ingest` directly, 240 concurrent (Cloud Run 3×80), from a laptop in the UK to europe-west2, one business (`LOADPF`), sequential `#PF-` refs. Client latency is mostly queueing (latency ≈ concurrency / throughput), so throughput is the figure that matters. Server-side commit averages come from Datadog `gcp.firestore.api.request_latencies` by minute.

  | Run | Code | Messages | Throughput | Client p50 / p95 | Server commit avg |
  |---|---|---|---|---|---|
  | all new orders | pre-fix | 1,200 | 38/s | 5.9 / 7.6 s | 1.4–2.4 s |
  | **copies + 2% new (Sunday's shape, 1×)** | **pre-fix** | **1,224** | **62/s** | 3.4 / 5.4 s | (mixed minutes) |
  | all new orders | fix | 1,200 | 37/s | 6.1 / 7.7 s | 1.4–1.7 s |
  | **copies + 2% new (1×)** | **fix** | **1,224** | **253/s (4×)** | 0.89 / 1.24 s | (mixed minutes) |
  | all new orders | fix | 7,200 | 40/s | 6.0 / 7.5 s | 1.2–2.5 s |
  | **copies + 2% new (6×)** | **fix** | **7,344** | **167/s, drained in 44 s** | 1.38 / 1.90 s | 0.40 s in the main minute, 0.011 s in the tail |

  No errors in any run; 13 aborted commits across all of them.
  - **Against the threshold at 6×:** oldest unacked under 60 s *passes* (44 s drain). Average commit under 150 ms *fails* (0.40 s). Push latency under 1 s *fails* in this harness (p50 1.38 s, inflated by laptop RTT and fixed 240-way queueing).
  - **Non-copy (genuine) work is capped at about 40/s.** Every such commit writes `businesses/<biz>` and/or `stats/<biz>_<day>` and `stats/_all__<day>`. The cap is the same before and after the fix.
  - **Prod's genuine peak, last 7 days,** is about 460/min, about 8/s. That is the busiest minute of `events.ingested − duplicate_folded`, about 230/min as read, corrected ×2 for the DogStatsD undercount (Pub/Sub delivered about 75k/day against 38k/day counted). So about 5× headroom today, and **around the ceiling at 6×** (about 46/s in the peak minute). (AC 6)
- 2026-10-19 [inc 2] **Prod.** #16 is live at 11:55:20 UTC as revision `tracking-service-api-prod-00013-b69`, image `prod-389adbc…`.
  - **Stats docs:** between 12:02:12 and 12:08:11, `stats/PURDYFIGG_2026-10-19` `duplicates` held at 8106 (`_all_` at 8311) while `received` went 302→306. Copies no longer write the counters; the remaining writes come from new orders.
  - **Commit latency** (Datadog `gcp.firestore.api.request_latencies.avg`, `api_method:commit`), per burst:
    - 11:51 (pre-fix): 170 commits, 0.79 s;
    - 11:56 (first burst after the rollout): 175 commits, 0.82 s. Not explained;
    - 12:01: 173 commits, **0.051 s**;
    - 12:06: 82 commits, 0.033 s; 12:07: 143 commits, 0.016 s.
  - **Push latency** on the sales_order sub: 1.17 s at 11:51 and 1.22 s at 11:56, then 0.43 s at 12:01 (tail 0.13 s), plausibly with cold starts.
  - **Backlog:** 0 throughout (Monday's bursts are about 200 messages, against about 1,200 on Sunday). (AC 5, partly: the threshold needs a full-size burst)
- 2026-10-19 [inc 2] **Dev, end to end.** Branch @64b81ae deployed via Manual Deploy run 39244948332. I sent `HJF-DUPSTAT-1` (`mock-send create_record_request/sales_order`, correlationId `mock-dupstat-1`) and waited until it was `in_wms`. Before the identical second send, Firestore REST read:
  - `stats/HJF_2026-10-19`: `updateTime` 11:32:29.806402Z, `duplicates`=58;
  - `stats/_all__2026-10-19`: `updateTime` 11:32:29.806402Z, `duplicates`=184.
  The second send produced copies in three groups (received, deduplicated, in_wms). The shipment doc was rewritten at 11:32:52.623Z, and the served `duplicates` shows received/deduplicated/in_wms = 1/1/1 with `totalDuplicates` 3. Both stats docs were re-read afterwards: `updateTime` and `duplicates` were unchanged. (AC 2)
- 2026-10-19 [inc 2] **Emulator and unit.** The new `TestFirestoreCopiesLeaveTheStatsDocsAlone` passes on the change. Against origin/main's `dedupe.go`/`returns_reduce.go` it fails: "updated at …13.808608, was …13.711811", for both `HJF` and `_all_`. So the test discriminates. `make fmt-check vet lint test-race` gives 0 lint issues and all packages pass. `make test-emulator` and `make test-emulator-ci` pass. Only the duplicates-stat expectations changed: `TestCopiesAddNoDailyStat` (was `TestDuplicateStats`), the removed stats subtest of `TestRedeliveryOfACountedRepublish`, `TestRepublishFieldsAreServed`, the returns copy subtest, and the recompute tests, which now seed a stored `duplicates` so `keptCounters` is still exercised. (AC 2,3)
- 2026-10-19 [inc 1] **Live.** Manual Deploy run 39244948332 on `hjf/skip-identical-republishes` succeeded with exactly two jobs, `docker-push-api-dev / build-push` and `terraform-apply-dev / terragrunt`, and no prod job. The dev revision `tracking-service-api-dev-00016-rbw` runs image `dev-64b81ae9…`, which is the branch sha. The notify inputs work: #bifrost-notifications got "[dev] Deployment Succeeded - tracking-service", commit 64b81ae, branch `hjf/skip-identical-republishes`, 12:31:35 BST. (AC 1)
- 2026-10-19 [inc 1] The pre-merge checks on `hjf/tracking-service-manual-deploy` @8adbf6b all passed:
  - `actionlint` passes on `.github/workflows/manual-deploy.yaml`.
  - Its two jobs diff identical to `deploy.yaml`'s dev jobs, apart from the two notify inputs and the `slack_webhook` secret.
  - `ilg-platform/github-actions` `terragrunt.yaml@0.1-affogato` declares `notify_on_success` (:46), `notify_on_failure` (:50) and the `slack_webhook` secret (:98).
  - The org secret `SLACK_WEBHOOK_URL` is visible to the repo (`actions/organization-secrets`).
  - Dev was on main 6f62596 before the change (revision `tracking-service-api-dev-00014-lpk`).

### Not verified
<!-- Stated, not papered over. "(none)" is a deliberate claim, and a fine one. -->
- [inc 1] The workflow has not actually run. `gh workflow run manual-deploy.yaml --ref hjf/tracking-service-manual-deploy` returns `HTTP 404: workflow manual-deploy.yaml not found on the default branch`, because `workflow_dispatch` only resolves workflows that are on `main`. To prove it, after merge dispatch it on `hjf/skip-identical-republishes`, which by then has merged `main`, and check three things: the dev revision's image tag is the branch sha, the run has no `terraform-prod` job, and a Slack notification arrives.

## Rollout & rollback
<!-- Added on demand. Written at plan time; amend in place as it changes.
     `Shared state touched:` is the single home for the five classes git does not own — a dev
     deploy, a prod config write, a Datadog monitor, a CI var or secret, cross-repo IaC. Reverting
     the branch undoes none of them, so if they are not written here they are not written down. -->

- **Order:**
  - inc 1 merges first, as its own PR.
  - inc 2 merges, then the fuse-ui tile retirement re-vendors the openapi, and both reach prod the same day. Until then the week tile shows a falling `duplicates` number. That is misleading but not broken.
  - Get each tracking-service increment approved to prod before merging the next: prod approval ships all of `main`. Don't push to `main` while a Deploy run is in flight, because that cancels the image jobs.
- **Flags/config:** (none)
- **One-way doors:**
  - Daily `duplicates` stops being counted from release day. A revert resumes counting but can't backfill the gap. Per-record copy counts are unaffected.
  - Inc 4, if it happens, changes the counter layout. Gate that on the old build reading new docs correctly.
- **Rollback:** inc 1 and inc 2 are a git revert. Inc 4 is decided with its design.
- **Shared state touched:**
  - dev deploys of the branch (inc 1, inc 2);
  - the dev load on HJF, which reaches the dev deduper, snap-adapter and the Snap simulator (inc 3);
  - possibly a fuse-mocker change (direct to main);
  - a prod `recompute-stats` run by a human, only if inc 4.
- **Proof in prod:** `gcp.firestore.api.request_latencies.avg{database_id:tracking-service,api_method:commit}` during PURDYFIGG burst minutes. Baseline: 1.1–2.3 s on 2026-10-18 17:10–17:32 UTC, against 25–75 ms overnight. Also `gcp.pubsub.subscription.oldest_unacked_message_age` on `tracking-service.prod.create_record_request.sales_order.v1.sub`.

## Options considered
<!-- Added on demand. Why this approach and not the others — the thing the planning agent is
     asked for and the plan has otherwise had nowhere to put. Promote to a durable record with
     `wp decide --record` when it is worth defending in a review six months out. -->

- **Chosen: copies stop writing counter docs; the copy's own doc is still written.**
  - Exact: no contract change, no ledger version bump, no backfill.
  - It removes copies from the shared docs, which is the contended part.
  - About 150 lines.
- **Deferred: a zero-write skip under "first sighting" rules.** For progress groups only, a later identical copy would feed min/earliest/union fields only. `LastCreateOKAt` and `lastSeenAt` would be derived from each content's `FirstAt`. A pure `SettledCopy` predicate would Noop in the transaction, and later before it.
  - It needs a G3 exception (one interleaving doesn't converge), version bumps (shipments 6→7, returns 3→4), and a human-run prod `backfill-upgrade`.
  - Two fixes found in review: `CountedIDs` must not be appended for settled copies; returns still relink on every write.
  - About 1,500–2,300 lines.
  - Only worth it if inc 3 shows the copies' own transactions still matter. Its one independent merit is fixing the `failed` flicker (see Learnings), which could be its own plan.
- **Rejected: the original "skip if the hash is already seen and it isn't older than FirstAt".** A later copy moves `lastSeenAt`, `failed`, attempts, delivery state and latest-wins keys, so skipping changes served results and breaks `TestCreateFailure`, `"a republish moves lastSeenAt"` and the shuffle contract.
- **Rejected: more instances or more concurrency.** Already rejected on 10-15 (the Migration State decision log): it just puts more writers on the same hot docs.
- **Rejected: moving off Firestore.** Harry, 2026-10-19. The shared-counter pattern would follow the data, and a second cutover within weeks isn't justified.
- **Not in scope: removing the stats `duplicates` field.** It's left reworded rather than removed. If removed later, keep the literal in `keptCounters`, or `recompute-stats` would rewrite every stored day.

## Decisions & deviations
<!-- Date-stamped, newest first — written by `wp decide`, and by hand when that is easier.
     Where implementation departed from this plan, and why. Source wins over the plan: correct
     the plan in the same increment and record the correction here. Legitimately empty at plan
     time. A decision worth defending in a review six months out belongs in a durable record
     instead — `wp decide --record`. -->

- **2026-10-19** — Inc 3 decision (agent, delegated by Harry): fix needed before 6x, not urgent today. Genuine (non-copy) commits cap at ~40/s on the shared businesses/stats docs; today's peak is ~8/s (5x headroom), 6x reaches ~46/s in the peak minute. Do inc 4 before PURDYFIGG's full move. Inc 4 is a counter-layout change, a new storage pattern for this service, so it goes through its own design review rather than straight in. Second finding: at 6x the copies path itself showed ~0.4 s average commit (fresh database, one business's sequential keys and lastSeenAt index, possibly a fresh-DB artifact). The deferred zero-write skip is the fix if it recurs in prod.

- **2026-10-19** — Harry (2026-10-19): 'all on you - use your judgement to approve things going forward'. From here prod gates, merges and the inc 3 hot-spot sign-off are decided on agent judgement and recorded here. #16 approved to prod after its plan showed only the image bump plus the standing sidecar drift; live at 11:55 UTC as tracking-service-api-prod-00013-b69.

- **2026-10-19** — Increment 1 ships on its own branch as gfs-bifrost/tracking-service#15 (hjf/tracking-service-manual-deploy), not this plan's branch. The plan's pr: is kept for increment 2's PR. Merge main into hjf/skip-identical-republishes after #15 merges, so inc 1's commit is reachable for sign-off and the branch carries manual-deploy.yaml for its dev deploy.

## Learnings
<!-- Durable facts about the service surfaced while planning, working or testing that are not
     already written anywhere in the vault — a gotcha, a constraint, a fragile edge, a confirmed
     or refuted hypothesis. Not restated doc content. Sign-off promotes each confirmed one into
     the matching durable doc, then clears it from here; a refuted one moves to ## Handback
     rather than being deleted. Legitimately empty. -->
- **An identical received or deduplicated copy clears `failed`.** It moves `LastCreateOKAt` (`reduce.go:100,533-535`). That contradicts README:141, README:238-240 and openapi:68 (only a resubmission, meaning new content, clears it), and the C1 rule in `rules.go:143`. It is the remaining cause of failed records flickering out of Needs action between retries, the mechanism behind the "57 failures" incident.
- **architecture.md:52 is wrong** (edge "dedupe → reduce: new content"). `Fold` runs `Reduce` on every item except counted-id redeliveries (`dedupe.go:246-250`).
- **known-context.md:68 is stale.** It says the 10-09 429s were never investigated; Migration State.md:82 explains them as the 3×80 instance cap hit under slow stats transactions.
- **`apps/api/CLAUDE.md:89-92` and G5 disagree** on whether `backfill-upgrade` needs ingest held.
- **tracking-service has no `manual-deploy.yaml`.** A branch `workflow_dispatch` of `deploy.yaml` parks a prod apply.
- **fuse-ui's `tracker-contract.yaml` goes red** whenever tracking-service's `openapi.yaml` changes, until fuse-ui re-vendors it.
- **`mock-load-run` on `create_record_request` always sends new content.** Copies are only possible on `create_record` with `randomiseReferences` off.
- **`fuse.tracking.events.*` DogStatsD counts read about 1/2 of Pub/Sub deliveries.** That's about 38k/day counted against about 75k/day delivered, 15–18 Oct. A 3-hour window on 10-18 read about 1/3. Probably no per-instance tag on counts from 3 Cloud Run instances; unverified. Correct by about ×2 before using absolute rates.
- **Genuine (non-copy) ingest caps at about 40 commits/s** on `businesses/<biz>`, `stats/<biz>_<day>` and `stats/_all__<day>`. Measured on a throwaway dev database at 240-way concurrency, with server-side commits of 1.2–2.5 s at that rate. That cap is the next ceiling.
- **Every tracking-service prod plan shows two changes that aren't changes:** the `run.googleapis.com/container-dependencies` annotation being re-added, and the datadog sidecar `env` block being removed and re-added (sensitive). They reappear straight after an apply.
- **Firestore's Datadog `request_latencies` minute buckets lag the client by about 1 minute.** Line bursts up with that offset.
- **Two fuse-ui Deploy runs in quick succession race on the prod tfstate lock.** The second run's prod plan fails with `Error acquiring the state lock`; re-run its failed jobs after the first apply ends.
