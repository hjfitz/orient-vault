---
ticket: none
title: Cross-org Go + Terraform module auth via the CI GitHub App
service: github-actions
status: draft
created: '2026-11-03'
updated: '2026-11-03'
repo: ilg-platform/github-actions
worktree: /home/harry/code/ilg-platform/github-actions
branch: hjf/github-module-auth
base: origin/main
base_sha: 7d03e30
pr: null
tags:
- waypoint
- plan
impl_model: opus
impl_effort: medium
---
# none — Cross-org Go + Terraform module auth via the CI GitHub App

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
Give every Go/Terraform-fetching reusable in this repo one shared mechanism — a composite action,
`.github/actions/github-module-auth` — that mints a **contents:read-narrowed** token from the
platform CI GitHub App (app 4035291, today `ilg-platform-ci`) **per source org** and wires per-org
git `insteadOf` + `GOPRIVATE`, so a repo in org A can fetch private Go modules and Terraform module
sources from orgs B, C… with no personal PAT. npm stays PAT/`github.token` (G5). Code only, all
additive on `0.2-bonbon`; app rename, org installs, org secrets and the Confluence page live in
[[enterprise-ci-github-app-rollout-rename-install-]]. No ticket — out-of-ticket platform work.

## Acceptance criteria
<!-- Observable, checkable outcomes — not tasks. Numbered by order: increments cite them as
     (AC 2,4), and sign-off prints which criteria no increment claims. -->
- [ ] 1. A caller passing the app id + key and `private_module_owners: ilg-platform,gfs-bifrost` fetches a private repo from **each** org in one job (Go, Docker build, and terragrunt paths).
- [ ] 2. Every token the repo mints is narrowed to `contents: read` (no inherited `packages:write`/`pull_requests:write`), is masked, and is revoked at job end.
- [ ] 3. No token lands in an image layer/history/config, the workspace, an uploaded artifact, `$GITHUB_ENV`, or a `.terraform/modules/*` remote URL.
- [ ] 4. `secops-dep-go` no longer reports ✅ when govulncheck could not load the module graph (missing private module, parse failure) — it renders ⚠️ in the job summary and a `::warning`.
- [ ] 5. Every existing `0.2-bonbon` caller (no new inputs) behaves identically after each force-move — opt-in only, G1.
- [ ] 6. `secops-terraform`'s custom policy bundle checkout succeeds (summary shows "wired") when the app is supplied.
- [ ] 7. README + CLAUDE.md describe the single app auth path, its contract, the 5-owner cap and the Dockerfile pattern, in the same PR as each behaviour change.

## Affected boundaries
<!-- Components, paths and contracts this touches. Wikilink existing explainers; do not restate
     their contents. If this names a topic, endpoint, canonical type, collection, inter-service
     dependency or shared package, sign-off will prompt for the Fuse MCP data file too. -->
- NEW `.github/actions/github-module-auth/action.yaml` (composite) — new internal lockstep ref (G2) from `docker-build-push`, `terragrunt` (first internal refs in either) and `secops-dep-go`/`secops-terraform`/`secops-container`.
- `.github/workflows/secops-dep-go.yaml` (:67-71 `set +e` run, :95-97 summary) + `.github/actions/govulncheck-gate/check-allowlist.mjs` (:191-201 read/empty/parse → `[]`).
- `.github/workflows/docker-build-push.yaml` (mint :87-95, BuildKit secrets :121-122) — the fleet's prod deploy path.
- `.github/workflows/secops-container.yaml` (mint :83-90, :115-116).
- `.github/workflows/terragrunt.yaml` (gate :120, owner :74-78, mint :214-221, pre-exec :230-234) — runs inside the `gruntwork-io/terragrunt-action@v2` **Docker** container (`HOME=/github/home`; only home/workspace/workflow/file_commands mounted).
- `.github/workflows/secops-terraform.yaml` (policy checkout :67-106, Trivy :115-126).
- Input/secret contract (API surface): `gh_app_id` (new input, falls back to `vars.PLATFORM_CI_APP_ID`), `gh_app_private_key` (secret), `private_module_owners` (new input); aliases kept: `gh_app_owner` (terragrunt), `repo_read_app_id`/`repo_read_app_private_key`/`repo_read_owner`/`repo_read_repositories` + BuildKit secret `repo_read_token` (CXD-719, #40).
- [[architecture]] "Auth model" (stale: says app is terragrunt-only), repo `CLAUDE.md` "Three distinct auth paths" (stale: says both docker builds use `--build-arg`).

## Assumptions & uncertainty
<!-- One line each, with how it was established. A genuine product or domain question goes here
     as UNRESOLVED: and is raised with the user, never invented. -->
- Installation token = one org; `owner` set + `repositories` empty → whole installation — create-github-app-token `action.yml@v2` read by reviewer.
- `create-github-app-token@v2` supports `permission-contents` and revokes in a `post:` step — action.yml read. Post steps of nested `uses:` inside a composite run at job end — reviewer memory, medium confidence; **inc 1 verifies it**.
- git honours `include.path` supplied via `GIT_CONFIG_COUNT/KEY/VALUE` env (absolute path) — unverified; **inc 1 verifies it**.
- terragrunt-action container does not see `$RUNNER_TEMP` root or host `~/.gitconfig` — action.yml + `src/main.sh` read; so terragrunt gets gitconfig **content** via step env, not a path.
- Opt-in, not default-on: resolving the key from `secrets.PLATFORM_CI_APP_PRIVATE_KEY` via `secrets: inherit` would silently start minting for gfs-ecm/ilg-merak inherit callers — a changed default under G1. Auto-on deferred to the 0.3 follow-up. Decided here (sensible default), flag if you disagree.
- Key and app id resolve **as a pair** from one source (`repo_read_app_id`+`repo_read_app_private_key`, else `gh_app_id||vars.PLATFORM_CI_APP_ID`+`gh_app_private_key`) — prevents pairing a caller's own app id with the platform key (README:64-69 example).
- `0.2-bonbon` == `main` == 7d03e30 today; `0.1-affogato` == `0-1-affogato` == 2e47b65 — git read 2026-11-03.
- Known `secops-dep-go` consumers: gfs-bifrost sftp-connector, tracking-service, fuse-mocker (apps/api, apps/snap-api), wms-gateway, fuse-devtools, selector-adapter, audit-service — gh code search; other orgs not yet searched (each increment re-searches every enterprise org per G1).
- UNRESOLVED: Darren Rielly's CXD-719 (#40, merged today) `repo_read_*` interface — is it called anywhere yet, and is he happy for it to become an alias of the canonical names? Ask before inc 3.
- UNRESOLVED: does any `0.1-affogato` caller need multi-org modules? If yes, a separate backport plan (composite must land on `0-1-affogato` before its terragrunt can ref it, G2). Not in this plan; 18 repos call `docker-build-push@0.1-affogato`, so "enterprise standard" here is 0.2-only.

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
Release rule for every increment: merge → canary at `@main` → `git log 0.2-bonbon..main` shows only this change → force-move `0.2-bonbon` → post-roll run on the real tag → announce in `#platform-engineering` (rolling tags don't fire `on-tag`). The composite's interface is **frozen after inc 1**: a later composite change ships composite-first as its own step, because consumers ref it literally `@0.2-bonbon` (G2), so a branch-ref canary of inc 2-6 runs the composite from the tag. No job-level `permissions:` added anywhere (a reusable asking for an ungranted permission = startup_failure).

- [ ] 1. Add `github-module-auth` composite: inputs `app_id`, `private_key`, `owners` (≤5, error above), `repositories` (single-owner only, error otherwise), `fallback_token`, `required` (default false → `::warning`, `enabled=false`); 5 `create-github-app-token@v2` slot steps with `permission-contents: read`; writes `$RUNNER_TEMP/github-module-auth.gitconfig` (0600) with per-org `insteadOf` for https/`git@`/`ssh://` forms (PAT fallback = one global rule); outputs `gitconfig_path`, `gitconfig`, `goprivate`, `tokens` (JSON), `token`, `enabled`. README + CLAUDE.md section. (AC 1,2,3,7) — verify: canary calls `@hjf/github-module-auth` with owners `ilg-platform,gfs-bifrost` and `git ls-remote`s a private repo in each via step-env `include.path`; token masked, file 0600 outside workspace, both post-step revocations in log; failure modes: gfs-sink owner (not installed) → warning + `enabled=false`; same with `required: true` → fail; 6 owners → error; `repositories` + 2 owners → error; `fallback_token` only → global rule.
      gate: canary repo `ilg-platform/github-actions-canary` exists (private, repo-level `PLATFORM_CI_APP_ID` var + key secret, fixtures: private Go module + TF module in gfs-bifrost and ilg-platform, a Dockerfile doing `go mod download` via the gitconfig secret) AND new action raised in `#platform-engineering` per CLAUDE.md "Stop and ask"
            [ ] confirmed
- [ ] 2. `secops-dep-go`: add `gh_app_id` input, `private_module_owners` input, optional `gh_app_private_key` secret; when supplied, step-env include + `GOPRIVATE` on the govulncheck step. Independently of the app: capture govulncheck exit/stderr and make the gate distinguish "empty/unreadable/unparseable report" from "no findings" → ⚠️ summary + `::warning` (text change, not a gate flip). (AC 1,4,5,7) — verify: canary Go module needing a gfs-bifrost private module → module appears in `govulncheck.json`; same without key → ⚠️ summary; fuse-mocker `secops.yaml` pinned to the branch → `govulncheck.json` + verdict diffed equal to its last `main` run.
- [ ] 3. `docker-build-push`: replace inline mint with the composite (pair resolution above), add BuildKit secret `repo_read_gitconfig` alongside existing `repo_read_token` (first-org token, kept for CXD-719). README Dockerfile pattern stays `GIT_CONFIG_*` env scoped to one `RUN`. (AC 1,2,3,5,7) — verify: canary Dockerfile pulling a gfs-bifrost module builds; `docker history --no-trunc`, `docker inspect`, `docker save | grep x-access-token` empty; named CXD-719 consumer (per UNRESOLVED above) green; one no-input caller unchanged.
      gate: Darren confirms the `repo_read_*` interface's callers and the alias approach
            [ ] confirmed
- [ ] 4. `secops-container`: same swap as inc 3 (npm `--build-arg` untouched — that's the 0.3 follow-up). (AC 1,2,3,5) — verify: same canary Dockerfile scans green; layer/history grep empty; one existing caller unchanged.
- [ ] 5. `terragrunt` (0.2 only): composite with owners `private_module_owners || gh_app_owner`; pass gitconfig **content** via step env and have pre-exec write it to the container's `~/.gitconfig`; `gh_token` PAT fallback keeps today's global rule. (AC 1,2,3,5,7) — verify: canary stack sourcing `ilg-platform/terraform-modules` + a gfs-bifrost module plans inside the container; `git -C .terraform/modules/<m> remote -v` shows no token; one `gh_app_private_key` consumer and one `gh_token`-only consumer (named from code search) unchanged; then `gcp-config` (`gh_app_owner: gfs-sre`, can't fetch ilg-platform modules today) planned with `private_module_owners: gfs-sre,ilg-platform`.
- [ ] 6. `secops-terraform`: step-env include on the Trivy step; policy-bundle checkout `token: fromJSON(steps.auth.outputs.tokens || '{}')['ilg-platform'] || github.token`, always minting for `ilg-platform`; remove the "tracked as a follow-up" comment. (AC 1,6,7) — verify: canary summary shows custom policy bundle "wired"; Trivy log has no private-module download warning; a no-key caller still fails open as today.

## Verification
<!-- The single authority for evidence. Increment lines carry `— done: <sha>` and nothing else.
     Check-selection order lives in verification-menu.md — do not restate it here. -->

### Evidence
<!-- Newest first, dated. One bullet per check actually run, opening with what it discharges.
     "Suite green" alone is not evidence. Sign-off requires at least one dated bullet here. -->

### Not verified
<!-- Stated, not papered over. "(none)" is a deliberate claim, and a fine one. -->
- Everything — plan stage.

## Rollout & rollback
<!-- Added on demand. Written at plan time; amend in place as it changes.
     `Shared state touched:` is the single home for the five classes git does not own — a dev
     deploy, a prod config write, a Datadog monitor, a CI var or secret, cross-repo IaC. Reverting
     the branch undoes none of them, so if they are not written here they are not written down. -->

- **Order:** inc 1 (composite) must be on `0.2-bonbon` before inc 2-6 merge — they ref it literally (G2). Inc 2-6 are mutually independent; ship docker-build-push (inc 3, prod deploy path) on its own tag move, never batched.
- **Flags/config:** none — all new inputs default empty; behaviour only changes for callers that pass `gh_app_id`/`gh_app_private_key`/`private_module_owners`.
- **One-way doors:** none on the code side. Each force-move is reversible by moving `0.2-bonbon` back to the previous sha (record it before each move).
- **Rollback:** per increment: `git push -f origin <prev-sha>:refs/tags/0.2-bonbon` (immediate fleet effect), then revert the PR on `main`.
- **Shared state touched:** the `0.2-bonbon` rolling tag (every 0.2 caller across the enterprise); canary repo `ilg-platform/github-actions-canary` repo-level var + secret holding the app key.

## Decisions & deviations
<!-- Date-stamped, newest first — written by `wp decide`, and by hand when that is easier.
     Where implementation departed from this plan, and why. Source wins over the plan: correct
     the plan in the same increment and record the correction here. Legitimately empty at plan
     time. A decision worth defending in a review six months out belongs in a durable record
     instead — `wp decide --record`. -->
- 2026-11-03 — Split out of scope into separate follow-ups: rollout/governance ([[enterprise-ci-github-app-rollout-rename-install-]]); a future `0.3` tag (remove `repo_read_*`/`gh_app_owner` aliases, govulncheck fail-closed, auto-on via `secrets: inherit`, drop secops-container `--build-arg GITHUB_TOKEN`, bump all internal refs incl. the new ones); optional `0.1-affogato` backport. Reason: increment-structure review — one plan was ~10 increments across three release lines.
- 2026-11-03 — Opt-in, not default-on, on 0.2 (G1: changed default = breaking). Overrides the user's "use it by default" phrasing for the 0.2 line only; default-on lands at 0.3.

## Learnings
<!-- Durable facts about the service surfaced while planning, working or testing that are not
     already written anywhere in the vault — a gotcha, a constraint, a fragile edge, a confirmed
     or refuted hypothesis. Not restated doc content. Sign-off promotes each confirmed one into
     the matching durable doc, then clears it from here; a refuted one moves to ## Handback
     rather than being deleted. Legitimately empty. -->
- CXD-719 / #40 (Darren Rielly, 2026-11-03) added opt-in `repo_read_app_id`/`repo_read_owner`/`repo_read_repositories` + secret `repo_read_app_private_key` to docker-build-push and secops-container (BuildKit secret `repo_read_token`); `0.2-bonbon` moved to 7d03e30 the same day. Not in the ledger.
- `0.1-affogato` is now 2e47b65 (carries #36, #39); `architecture.md` still says d52202b. The `0-1-affogato` branch has no secops-container and only the `node-setup`/`secops-report` actions.
- `secops-dep-go` is false-green on any module-load failure: `set +e` at :67-71 and check-allowlist.mjs returns `[]` on read, empty **or parse** failure (:191-201) → ✅ summary + `outcome: success` to ingest.
- No mint in the repo narrows permissions, so every module-fetch token carries the app's full set (live 2026-11-03: checks:read, contents:read, metadata:read, packages:write, pull_requests:write). The vault's 2026-10-28 fuse-devtools note omits packages:write.
- `sarif-summary`, `audit-ci-summary`, `gitleaks-summary` are JS (node24) actions, not composites.
- Repo CLAUDE.md auth section is stale: `docker-build-push` already passes npm as `--secret id=github_token` (:121); only secops-container uses `--build-arg` (:115).
- 0.1 terragrunt interpolates the token straight into shell (`0-1-affogato` terragrunt.yaml:207-208) rather than via env.
- `docker-build-push@0.2-bonbon` requests job permission `packages: read`; a caller not granting it gets startup_failure (from ilg-merak ledger; not in this service's vault).
