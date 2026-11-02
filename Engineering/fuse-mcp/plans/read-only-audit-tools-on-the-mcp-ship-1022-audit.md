---
ticket: none
title: Read-only audit tools on the MCP (SHIP-1022-audit-mcp-tools)
service: fuse-mcp
status: complete
created: '2026-10-22'
updated: '2026-10-22'
repo: /home/hjf/code/fuse/fuse-mcp
worktree: /home/hjf/code/fuse/fuse-mcp/.claude/worktrees/audit-tools
branch: hjf/audit-mcp-tools
base: origin/master
base_sha: 2ac01e55a
pr: '58'
tags:
- waypoint
- plan
impl_model: opus
impl_effort: medium
---
# none — Read-only audit tools on the MCP (SHIP-1022-audit-mcp-tools)

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
Since 2026-10-15 fuse-ui's audit log lives in audit-service, which only fuse-ui can read, so staff access audits (e.g. the `sftp-key-access-audit` skill) are blind after that date. Add read-only `audit-search` and `audit-get-event` tools to the Go MCP that call audit-service as `fuse-mcp-prod-sa` and return a default-deny, per-kind allow-list projection of each event: no snapshot or credential ever leaves the MCP. Production only. Harry's policy decision and the risks accepted are in [[Bifrost/Audit Service/Migration State]] (decision log 2026-10-22). Run ID SHIP-1022-audit-mcp-tools; no Jira ticket. Companion plan: [[Engineering/audit-service/plans/fuse-mcp-reader-grant-ship-1022-audit-mcp-tools]].

## Acceptance criteria
<!-- Observable, checkable outcomes — not tasks. Numbered by order: increments cite them as
     (AC 2,4), and sign-off prints which criteria no increment claims. -->
- [x] 1. On the hosted MCP, `audit-search` returns prod `fuse` events filtered by actor / tenant / target / kind / action / excludeKind / from / to, paged by cursor, and `audit-get-event` returns one event by id.
- [x] 2. No response, success or error, ever contains `details.before`/`after`, an unlisted `details` key, an unknown envelope key, or a raw downstream body; proven by canary fixtures and a literal expected allow-list in tests.
- [x] 3. Every failure (missing URL, token failure, 401, 403, 404, 400, other non-2xx, non-JSON, transport error, a malformed row) comes back as fixed text, never `IsError`, never echoing a body or URL.
- [x] 4. A caller passing any `environment` other than `production` gets a text refusal, not prod data. (Delivered as the schema enum's rejection, per repo convention; see Decisions.)
- [x] 5. The shared MCP bearer token is rotated before the audit-service grant goes live.
- [x] 6. The platform data (`service-dependencies.json` etc.) and the access-audit skill describe the new route.

## Affected boundaries
<!-- Components, paths and contracts this touches. Wikilink existing explainers; do not restate
     their contents. If this names a topic, endpoint, canonical type, collection, inter-service
     dependency or shared package, sign-off will prompt for the Fuse MCP data file too. -->
- `internal/adapters/audit.go` (new `AuditClient`, modelled on `TrackingClient` `tracking.go:18-129`; reuses `Result`, `isSuccess`, `requestTimeout`, `UserAgent`, `IDTokenSource`/`NewMetadataTokenSource`, `observability.MetricDownstream*`/`OutcomeForStatus`; `TrackingClient` untouched).
- `internal/adapters/audit_details.go` (new projection; typed envelope + per-kind details, per-key typed decode).
- `internal/tools/audit.go` (new `RegisterAudit`), `internal/bootstrap/server.go:84`, `internal/config/config.go:136-139` (comment), `internal/adapters/client_test.go:327` (`clearCredentials` += `AUDIT_SERVICE`).
- Parity: `internal/bootstrap/testdata/ts-baseline.json` (hand-added declarations), `internal/bootstrap/parity_test.go:56,84` (61→63, 44→46).
- IaC: `iac/projects/fuse-mcp/variables.tf` + `iac/env/prod.tfvars` (`audit_service_production_url`, tfvars not remote state, per the audit programme's 2026-10-09 decision; `auth_token_rotation` "1"→"2"), `cloud-run-go.tf` (env `AUDIT_SERVICE_PRODUCTION_URL`, Go service only).
- Downstream contract: audit-service `GET /api/v1/systems/fuse/events[/{id}]` (`code/openapi.yaml`); auth = ID token, audience = URL, caller in `api_readers`.
- Data: `data/service-dependencies.json` (:137-140, :166-168), `data/services.json:512`, `data/api-endpoints.json:355`.
- Docs outside the repo: `~/code/.claude/skills/sftp-key-access-audit/SKILL.md` Step 2, `~/code/CLAUDE.md` tool list.

## Assumptions & uncertainty
<!-- One line each, with how it was established. A genuine product or domain question goes here
     as UNRESOLVED: and is raised with the user, never invented. -->
- The Go server takes 100% of traffic; both Cloud Run services run as `fuse-mcp-prod-sa` — prod.tfvars `go_traffic_percent = 100`, cloud-run*.tf, `gcloud iam service-accounts list`.
- Prod audit-service URL is `https://audit-service-prod-6cprbzyuka-nw.a.run.app` — its prod tfstate `api_url` and fuse-ui's prod tfvars (factual review).
- Stored events can carry producer keys outside the schema, so the envelope must be known-fields-only — audit-service stores the raw message (factual review).
- Imported legacy rows also land in `config_change`/`credential_access`/`user_change` with fuse-ui's old details keys; `kind=legacy` is exactly logged_in/login_failed — `core/legacy/legacy.go:31-42`, fuse-ui `AuditAction`. Default-deny keeps them safe; old keys outside the lists are dropped.
- `to` is inclusive (`$lte`, read.go:39); the cursor is not bound to filters (query.go:114-117) — descriptions say so.
- Decided by Harry 2026-10-22: second reader accepted with the four conditions in the Audit Service decision log.
- Not provable before prod: metadata minting for the audit audience, `run.invoker` + `READ_CALLERS` + `email_verified` acceptance, the real key/value spread. No dev environment exists (programme D1).

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

- [x] 1. PR-A: projection, a pure function in `audit_details.go` (AC 2) — verify: table tests with canaries (`-----BEGIN OPENSSH PRIVATE KEY-----CANARY`, `hunter2-CANARY`, `sk_live_CANARY`) under `before`/`after`/`value`/`password`/`privateKey`/`secret`/`token`/`apiKey`, nested and in arrays, for every kind; allowed keys with wrong types; unknown kind; legacy-imported shapes; unknown envelope keys; extra keys on actor/target; a wrong-typed `actor` drops that event, not the page. Assert no canary in `shared.MarshalIndent` output and encoded keys equal a literal kind→keys map written in the test (not derived from the code's table). Merging deploys unregistered code: image-only. — done: b18e5ad
- [x] 2. PR-B (stacked on A): `AuditClient` transport in `audit.go` (AC 3) — verify: httptest like `adapters/tracking_test.go:39-127`: bearer sent, audience = URL without trailing slash, query encoding, every failure in AC 3 including HTML 401/403/404 and a 400 carrying a canary (only messages from audit-service's fixed set at `read.go:53-77` are relayed), transport error text carries no URL, metric `target:audit_service`. Image-only deploy. — done: e304a53
- [x] 3. PR-C (stacked on B): `RegisterAudit`, bootstrap wiring, `environment` restricted to `production`, baseline + counts, README/AGENTS, `audit_service_production_url` tfvar + env var, `auth_token_rotation` → "2" (AC 1,3,4,5) — verify: in-memory MCP end-to-end test (trackingText pattern) with real `RegisterAudit`, fake token source and a canary-serving stub, asserting exact query strings and no canary on any path; baseline entries captured by building the binary and piping initialize + tools/list with stdin held open; `make parity`; full local gates; `terraform init -backend=false && validate`. — done: 0ecab06
      gate: Harry reviews PR-C's tf-output prod plan comment before merge (merge applies prod ungated): expect 2 to change (image on both services), `AUDIT_SERVICE_PRODUCTION_URL` added on `fuse-mcp-go-prod` only, `random_password.mcp_auth_token` replaced, MCP_AUTH_TOKEN changed on both; diff drift against #54's comment
            [x] confirmed — 2026-10-22: plan read by the /ship run, 0/2/0 as expected plus standing drift, env block masked and verified with gcloud after apply; Harry: "we're on /ship - no need to ask me"
- [x] 4. Go-live: the audit-service grant (companion plan) (AC 1) — verify: before the grant, `audit-search` on prod returns the fixed 403 text (proves the token was minted and accepted by Cloud Run); after it, the read-only smoke below. — audit-service#15 — done: 1e64279
      gate: Harry has updated his MCP registrations with the rotated token, and approved audit-service's prod plan (1 to add, 1 to change: image + READ_CALLERS)
            [x] confirmed — 2026-10-22: token rotated (#59, old token 401) before the grant; Harry was DM'd the new-token step but his registrations weren't confirmed before the grant, which didn't depend on them; prod plan 1/1/0 approved by the /ship run per Harry's no-ask instruction
- [x] 5. Smoke, then data and docs (AC 1,2,6) — verify: JSON-RPC `tools/call` POSTs to `https://mcp.fuse.ilg.software/mcp`: `audit-search {limit:1}`, `{kind:"config_change",limit:5}` (details only friendlyName/changedPaths), `{kind:"credential_access"}`, `{kind:"legacy"}`, `audit-get-event` on a real and a junk id, a bad `from`, `{environment:"staging"}`; grep all output for `BEGIN`, `password`, `before`; compare one event with fuse-ui's audit page; `fuse.mcp.downstream{target:audit_service}` in Datadog. Then the data commit straight to master (`make parity-accept`, after PR-C's Deploy has finished), and the skill/CLAUDE.md updates. — done: 5907b3b

## Verification
<!-- The single authority for evidence. Increment lines carry `— done: <sha>` and nothing else.
     Check-selection order lives in verification-menu.md — do not restate it here. -->

### Evidence
<!-- Newest first, dated. One bullet per check actually run, opening with what it discharges.
     "Suite green" alone is not evidence. Sign-off requires at least one dated bullet here. -->
- 2026-10-22 [inc 5] Datadog `fuse.mcp.downstream{target:audit_service}` by outcome over the smoke window: `ok` (post-grant reads), `unauthorised` (pre-grant 403s), `client_error` (junk id 404, bad `from` 400).
- 2026-10-22 [inc 5] Platform data straight to master (5907b3b, parity-accept; declarations unchanged, 46 tools). Skill Step 2 and ~/code/CLAUDE.md now use audit-search.
- 2026-10-22 [inc 5] Prod smoke via JSON-RPC to mcp.fuse.ilg.software with the rotated token: a 100-event page (287 total, 0 unreadable) has only allow-listed details keys per kind (config_change changedPaths/friendlyName; credential_access field/friendlyName/storefrontId; sftp_user keySource/publicKeyFingerprint/username; user_change role) and only known envelope keys; credential markers appear only as `"field": "webhookSecret"` names. get-event on a real id returns the projection; a junk id → "No audit event…"; `from: yesterday` → audit-service's own 400 text. James's credential pulls since the cutover returned 4 events, including DRSAMSPL sftpPrivateKey copies 2026-10-16 13:47:28/35Z.
- 2026-10-22 [inc 4] audit-service#15 (1e64279) applied (plan 1/1/0; READ_CALLERS change in the masked api env, the sidecar env swap is standing drift); `get-iam-policy` lists fuse-mcp-prod-sa as run.invoker, READ_CALLERS lists both readers; first reads cleared the Cloud Run 403 after ~30s of IAM propagation.
- 2026-10-22 [inc 3,4] Before the grant: both tools answered "HTTP 403, Cloud Run IAM" live — token minted for the right audience and accepted, nothing readable; staging rejected by the schema enum. #59 (fdd4cb9) rotated the token: plan 1/2/1, old token 401 afterwards.
- 2026-10-22 [inc 3] #58 (0ecab06) applied 0/2/0; `gcloud run services describe` shows AUDIT_SERVICE_PRODUCTION_URL=https://audit-service-prod-6cprbzyuka-nw.a.run.app on fuse-mcp-go-prod only.
- 2026-10-22 [inc 1,2] #56 (b18e5ad) and #57 (e304a53) image-only deploys, prod tags confirmed. Pre-existing nightly reds (Go 1.26.9 GO-2026-6809, MCP SDK 1.31.0 GHSA) fixed first in #61 (abaf697). gitleaks flagged my key-shaped test canaries; replaced and history rewritten, local `gitleaks detect` clean.
- 2026-10-22 [inc 1-3] Pre-prod: all gates on each commit alone; canary tests on every path; fault injection (passthrough, widened/union allow-list, raw envelope strings, echoed bodies, get-event raw fallback, enum removed) fails the suite each time; real binary over stdio; four Opus self-reviewers plus a delta round, nothing blocking.

### Not verified
<!-- Stated, not papered over. "(none)" is a deliberate claim, and a fine one. -->
- Whether FUSE_16781BDBCD is DRSAMSPL's SFTP user: the audit log has no sftp_user event for DRSAMSPL, so it can't say; Harry's connector-page check or the connector config would.
- One event compared against fuse-ui's audit page (needs a browser session); the field-level match was checked against the frozen Mongo rows instead for the pre-cutover DRSAMSPL events (09-08 link_created by dannywilliams, 10-05 mapping update by stevet), which audit-search returned identically.
- Teammates' MCP registrations after the rotation: not visible from here (the request logger doesn't identify clients).

## Decisions & deviations
<!-- Date-stamped, newest first — written by `wp decide`, and by hand when that is easier.
     Where implementation departed from this plan, and why. Source wins over the plan: correct
     the plan in the same increment and record the correction here. Legitimately empty at plan
     time. A decision worth defending in a review six months out belongs in a durable record
     instead — `wp decide --record`. -->

- **2026-10-22** — Self-review round 1: environment is a schema enum (repo convention; SDK returns IsError), not a handler refusal; token rotation moved to its own PR so the tools PR reverts cleanly; an event with an unreadable actor is kept without the actor rather than dropped; data/*.json lands after the prod smoke, straight to master, as planned.

- **2026-10-22 (Harry)** — Pre-prod evidence accepted in place of dev verification (none exists): in-memory MCP e2e with canaries on every path, mutation runs, real binary over stdio; tools inert (403 text) until the audit-service grant; read-only prod smoke right after it, out-of-band invoker removal as the kill switch.
- 2026-10-22 — Harry: go ahead as a second audit reader on the recorded terms (rotate the token first, ship fuse-mcp before the grant). Taken by default and stated in the conversation: URL from tfvars not remote state; `environment` restricted to `production`; `excludeKind` included; no `detailsFiltered` field; `filter-options` not exposed; three stacked PRs. Reviews: draft + history + factual + increment structure, all Opus.

## Learnings
<!-- Durable facts about the service surfaced while planning, working or testing that are not
     already written anywhere in the vault — a gotcha, a constraint, a fragile edge, a confirmed
     or refuted hypothesis. Not restated doc content. Sign-off promotes each confirmed one into
     the matching durable doc, then clears it from here; a refuted one moves to ## Handback
     rather than being deleted. Legitimately empty. -->
- (promoted 2026-10-22 into fuse-mcp known-context/operations and audit-service known-context)
