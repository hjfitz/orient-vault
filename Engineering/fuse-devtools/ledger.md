---
tags: [waypoint, ledger]
title: fuse-devtools — work ledger
---
# fuse-devtools — work ledger

Agent-facing. Newest first. What meaningful work happened here, and the
context a future agent needs. Not a diary, not release notes, not a diff.

## 2026-10-31 — Cut pr-sitrep over from TypeScript to Go

Cut pr-sitrep over from TypeScript to Go

Unit X1 of the pr-sitrep Go programme. Replaces apps/pr-sitrep with the Go port and makes the CI Go-only for the app (secops now nightly). Merged on Sat 2026-10-31 after both gates cleared: byte parity on two days (41 then 32 live PRs, all three GET formats identical) and Friday's 09:00 TS post landing once. The prod plan was the image plus DD_VERSION and the known scaling no-op. After approval, pr-sitrep-prod-00006-b8v (prod-ba9780f) took 100% of traffic with source:go. The rollback target is pr-sitrep-prod-00005-4fd. The first Go scheduled run is Mon 2026-11-02 09:00.

PR: gfs-bifrost/fuse-devtools#17

## 2026-10-29 — Serve the pr-sitrep Go port over HTTP and verify it on dev

Serve the pr-sitrep Go port over HTTP and verify it on dev

Unit V2 of the pr-sitrep Go programme. Adds the HTTP layer (same routes, error contract, correlation ids, Express-style routing), the bootstrap wiring and the one-shot CLI, which completes the Go app. GET output was byte-identical to TS on 41 live PRs in json, markdown and the Slack plan (G1 day 1). On dev a scheduled run through the Go revision returned 200, with the full log sequence in Datadog under source go. Dev was then given back to TS.

PR: gfs-bifrost/fuse-devtools#16

## 2026-10-29 — Port the pr-sitrep sweep, merge, publish and run services to Go

Port the pr-sitrep sweep, merge, publish and run services to Go

Unit V1 of the pr-sitrep Go programme. Ports the four use-cases: the sequential read-only sweep (author and window resolution, bot filtering, stacking), the gated merge with failures as outcomes, the publish (one mention lookup per author, ordered mrkdwn posts, failures recorded), and the scheduled run with its completion log. All 48 TS spec cases are ported.

PR: gfs-bifrost/fuse-devtools#15

## 2026-10-29 — Port the pr-sitrep Jira and Slack clients to Go

Port the pr-sitrep Jira and Slack clients to Go

Unit A2 of the pr-sitrep Go programme. Ports the Jira sprint-window client, which reads the sprint field as loosely as TS and falls back to the window rule (an HTTP failure is still an error), and the Slack client (ok must be exactly true, users_not_found means no id, unfurling off, body unescaped). All 34 TS spec cases are ported.

PR: gfs-bifrost/fuse-devtools#14

## 2026-10-29 — Port the pr-sitrep GitHub client and app tokens to Go

Port the pr-sitrep GitHub client and app tokens to Go

Unit A1 of the pr-sitrep Go programme. Ports the GitHub REST client: search, PR read, reviews, check runs, default branch, and squash merge then branch delete. The mergeable_state re-read rules are kept exactly: up to three re-reads while unknown, one long-idle re-read measured from the first read, and a null state never retried. Also ports the GitHub App installation tokens (stdlib RS256 JWT, a cached token per owner). All 51 TS spec cases are ported.

PR: gfs-bifrost/fuse-devtools#13

## 2026-10-29 — Port the pr-sitrep renderers to Go

Port the pr-sitrep renderers to Go

Unit C2 of the pr-sitrep Go programme. Ports the markdown report, the Slack message plan and the mrkdwn conversion. Authors are collated with x/text/collate en-US, which matches localeCompare in the node24-runtime image (checked inside that image). All 56 spec cases are ported, and TS-generated goldens pin byte-identical output for four synthetic payloads plus mrkdwn edge cases.

PR: gfs-bifrost/fuse-devtools#12

## 2026-10-29 — Port the pr-sitrep models and classifier to Go

Port the pr-sitrep models and classifier to Go

Unit C1 of the pr-sitrep Go programme. Ports the binary merge bar and the five-state report bar with their evidence, self-hold, ticket, bot, working-day, check and review rules. The text matching is written by hand to keep JavaScript's regex semantics, which RE2 doesn't share. All 68 spec cases are ported under their TS names, and a TS-generated golden (2,160 classify combinations plus edge text) pins the parity.

PR: gfs-bifrost/fuse-devtools#11

## 2026-10-29 — Start the pr-sitrep Go port with a skeleton, config and CI

Start the pr-sitrep Go port with a skeleton, config and CI

Unit S1 of the pr-sitrep Go programme. apps/pr-sitrep-go holds the Go module beside the TS app, so prod keeps deploying TS until cutover. The config validation is ported with zod's semantics and the same cross-field refusals. /health returns the same bytes as TS. Adds Go code-quality and secops jobs and a Go manual deploy to dev; the dev deploy workflows share a concurrency group and announce failures only.

PR: gfs-bifrost/fuse-devtools#10

## 2026-10-29 — Retry the scheduled pr-sitrep run with backoff

Retry the scheduled pr-sitrep run with backoff

The 2026-10-29 09:00 prod run was dropped: Cloud Scheduler hit a scale-to-zero cold start, Cloud Run answered 429 "no available instance", and with retry_count = 0 nothing was posted. The scheduler job now retries 3 times (10s/20s/40s, max 60s), applied to prod and verified with a manual run that posted to #bifrost-forge. This knowingly overrides guardrail G5 (at-most-once): a 502 after a partly posted run is now retried and re-posts the report; same-day idempotency is a follow-up.

PR: gfs-bifrost/fuse-devtools#9

## 2026-10-28 — Move pr-sitrep to zod 4 and fail runs whose Slack post fails

Move pr-sitrep to zod 4 and fail runs whose Slack post fails

Owed items from the pr-sitrep rollout, resolved. #7: zod ^3.25 -> ^4.6.7 clears GHSA-mrhx-c7xc-m3w5 at source; both allowlists (audit-ci entry, .trivyignore + secops trivyignores input) removed. zod 4 doesn't parse .default() through a transform, so boolean flags default to false not "false"; z.url()/z.email() replace deprecated forms. #8: POST /api/v1/sitrep/run answers 502 when any Slack post failed (body unchanged, retry_count 0 so no double post), closing the 10:00 monitor's blind spot. Prod now rev 00004 (prod-5e8fcb9). Vault refreshed: overview/architecture re-anchored at 5e8fcb9 with iac/ paths added; known-context deploy-gap section and waypoint.yaml deploy/observability/note corrected.

PR: gfs-bifrost/fuse-devtools#7
PR: gfs-bifrost/fuse-devtools#8

## 2026-10-28 — Turn on pr-sitrep's Slack post and retire the digest's

Turn on pr-sitrep's Slack post and retire the digest's

Ship: SHIP-1028-pr-sitrep-ready. Prod live and posting: pr-sitrep-prod rev 00002 (prod-d602d8e), Cloud Scheduler 09:00 Europe/London Mon-Fri, private (scheduler SA is the only invoker), ilg-platform-ci app (owned by gfs-dev; now checks:read + pull_requests:write). Slack via the Bifrost Deployments app's bot token (bot user 'deployments', chat:write/.public, users:read.email), prod only (local.slack_enabled). First post 2026-10-28 10:47: header + 17 PRs, real mentions. Secrets created by hand, never in state: pr-sitrep-github-app-key (dev+prod, from platform-priv.pem), pr-sitrep-slack-bot-token (prod). morning-digest Step 4b retired the same day (skill file, no repo). Known: a failed Slack post still returns 200, so the 10:00 monitor (observability#79) only catches failed/missing runs; zod allowlist expires 2026-11-04.

PR: gfs-bifrost/fuse-devtools#6

## 2026-10-28 — Get pr-sitrep ready to run on a schedule

Get pr-sitrep ready to run on a schedule

Ship: SHIP-1028-pr-sitrep-ready. Ported the pr-sitrep skill's later fixes into the service: newest check run per app+name (suite keying kept cancelled superseded runs, seen live on fuse-ui), drafts never reach Slack. Added GitHub App auth (ilg-platform-ci; key parsed + RSA-checked at start-up; app mode refuses MERGE_ENABLED). Live sweep matches the skill exactly (58 PRs, 0 diffs). Cleared new express/zod advisories (lockfile bump; zod allowlisted to 2026-11-04 — zod 4 upgrade owed). Deploy stack #3 (private Cloud Run + OIDC scheduler 09:00 UK weekdays, node24 golden image, secrets created by hand) is held on: app permissions (PRs+Checks read) and pr-sitrep-github-app-key in both projects.

PR: gfs-bifrost/fuse-devtools#1
PR: gfs-bifrost/fuse-devtools#2
PR: gfs-bifrost/fuse-devtools#3
PR: gfs-bifrost/fuse-devtools#5
