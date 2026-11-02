---
ticket: none
title: Hub CI read path
service: secrets-hub
status: active
created: '2026-10-13'
updated: '2026-10-13'
repo: /home/hjf/code/fuse/secrets-hub
worktree: /home/hjf/code/fuse/secrets-hub/.claude/worktrees/ci-read-path
branch: hjf/ci-read-path
base: origin/main
base_sha: f3108ef85
pr: null
tags:
- waypoint
- plan
programme: Secrets Hub
unit: H6
impl_model: opus
impl_effort: high
---
# Secrets Hub: CI read path

<!-- Guidance is written as HTML comments. SUPERSEDING: one `> SUPERSEDED <date> — …` blockquote above the stale text. -->

## Intent
Build the first half of the hub ([[Secrets Hub/Overview|Secrets Hub]], programme unit H6): a Next.js app on Cloud Run per environment that takes a GitHub Actions OIDC token and returns the secret **references** for that repo's environment plus the org's shared ones for that environment, never values. When this plan is done, a workflow in a `gfs-bifrost` repo can ask its environment's hub for its references and get a correct map back, in dev and then prod. The UI and writes are [[hub-ui-and-writes]].

## Acceptance criteria
- [x] An OIDC token from a `gfs-bifrost` repo with no environment, or with `terraform-dev`, gets the dev hub's map of `KEY → projects/<p>/secrets/<id>` for `<org>/<repo>/dev` and `<org>/_shared/dev`. A repo key wins over a shared key.
> SUPERSEDED 2026-10-13 — a token with no environment gets the hub's own environment (the prod plan job has none), so the prod hub answers it with prod references rather than 403. Names only.
- [ ] The prod hub serves `terraform-prod` tokens the same way from `bifrost-prod-global1`. Each hub rejects an environment it doesn't serve with 403. A hub never reads another environment's project.
- [x] A wrong audience, a bad signature, an untrusted org, an org id that doesn't match its name, a mismatched `repository`, or an unknown environment is rejected (401 or 403). An unknown environment never falls back to dev.
- [x] The secret ID codec is injective and round-trips. No repo name can produce the `_shared` scope, and every ID fits the Secret Manager limits.
- [x] The hub's service account can't read any secret value, and can't change a secret outside the trusted-org prefixes.
- [x] No response, log line or Datadog event contains a token or a value.

## Affected boundaries
- New repo `gfs-bifrost/secrets-hub`. App code in `code/src/{app,use-cases,core,adapters,config,models,exceptions,observability,bootstrap}`. IaC in `iac/projects/secrets-hub` plus `iac/env/*.tfvars`.
- Secret Manager in `bifrost-dev-global1` and `bifrost-prod-global1`: two custom roles and their bindings per project.
- Contract for every consumer workflow: `GET /api/v1/ci/references`, `Authorization: Bearer <OIDC token>`. Audience = the hub's `run.app` URL. Response `{ env, references }`.
- Reusable workflows in `ilg-platform/github-actions`, consumed only: `terragrunt.yaml` and `docker-build-push.yaml` at `0.1-affogato`, `secops-*` at `0.2-bonbon`.
- Fuse MCP: `services.json` and `api-endpoints.json` get a secrets-hub entry at sign-off.

## Assumptions & uncertainty
- **One hub per environment, each managing only its own project.** The draft had the prod hub also write dev. That broke the Overview's "no cross-project IAM" rule and split one secret's audit trail across two topics. Decided 2026-10-13, see Decisions. CI picks the hub by its environment: terraform-dev jobs and PR plans call the dev hub, terraform-prod jobs call the prod hub.
- **Shared secrets are per environment**: `<org>/_shared/<env>/<KEY>`, ID `<org>--_shared--<env>--<KEY>`. This supersedes the Overview's "shared has no env". Decided 2026-10-13.
- **`gfs-bifrost` is the only trusted org at launch**, pinned by login and numeric id. Adding the other two is config.
- **Org-wide, any `gfs-bifrost` repo can already act as the deployer, which holds `roles/owner`.** The hub's scoping is a convenience boundary, not a hard one (programme R2, H12 deferred). Established: core-infra `workload-identity.tf:19-35`, plus a live IAM read on 2026-10-13.
- **`secretmanager.secrets.create` is checked on the parent project, so an IAM Condition can't narrow it.** The hub can create a secret with any ID. It can't modify or delete one outside the trusted-org prefixes, and the app validates IDs. Accepted. Source: the factual-grounding review, from the Secret Manager REST reference.
- **The GitHub environments `terraform-dev`/`terraform-prod` already exist on the repo, each with one protection rule** (`gh api …/environments`, 2026-10-13). A smoke job bound to an environment may wait for approval.
- **Prod is deployed only after dev QA passes** (standing rule). `deploy.yaml` is dev-only until increment 6.
- **The Dockerfile passes the npm token as an `ARG` in a discarded deps stage, not as a BuildKit secret mount.** The Overview prefers the mount, but `docker-build-push.yaml@0.1-affogato` only passes `--build-arg GITHUB_TOKEN` (lines 84-86). The token never reaches the shipped stage. An accepted deviation; the upstream secret-mount input is a follow-up on the platform surface.

## Increments
- [x] 1. **App shell and CI, no cloud.** — secrets-hub#1: CI green, container scan 0 HIGH/CRIT, health 200 in docker — done: f37b611
  - Next 16.3.8 (the CVE floor, not latest), React 19, `@ilg-platform/ui-toolkit` ^1.35.3 shell per its `docs/bootstrap.md` §1-5, `/api/health`, and `hub.config.ts` (zod; the only `process.env` reader).
  - pnpm 10.33.x pinned identically in `packageManager`, `mise.toml` and the workflows. Node 22. zod 4.4.3 exact (the audit package's peer).
  - `.npmrc` scopes for `@ilg-platform` and `@gfs-bifrost`. The Dockerfile writes the token to a temporary user npmrc in the deps stage: pnpm 10.34+ ignores `${GITHUB_TOKEN}` in a project `.npmrc`.
  - `code/audit-ci.jsonc`, `code-quality.yaml`, and `secops.yaml` (secrets, dep-node, code `lang: ts`, container).
  - `GH_TOKEN` at all three install sites, plus `packages: read` on every docker job.
  - A CI guard that fails on `accessSecretVersion` anywhere in `code/src`.
  - verify: every check green on the PR, and a local `docker build && docker run` returns `/api/health` 200.
- [x] 2. **Dev Cloud Run and deploy pipeline.** — secrets-hub#2: dev deploy green, run.app /api/health 200, startup log in Datadog via sidecar — done: 72fb212
  - `iac/projects/root.hcl` (audit-service pattern), `secrets-hub` Cloud Run with service account `secrets-hub-dev`, and `allUsers` invoker via `iam_member` (never `iam_binding`).
  - The Datadog sidecar with a shared log volume, and DogStatsD flushed on each request.
  - Workflows: `deploy.yaml` applies **dev only**, plus `tf-plan.yaml` and `manual-deploy.yaml` with notify inputs.
  - verify: the dev deploy is green, `curl <run.app>/api/health` returns 200, a dev screenshot shows the empty shell, and the health request's log line appears in Datadog through the sidecar. (AC 6 groundwork.)
- [x] 3. **Custom roles and conditional bindings, dev.** `secret-manager-roles.tf`: — secrets-hub#3: impersonation matrix — values/foreign secrets/IAM denied, own secrets managed — done: 4f28f89
  - **Lister** (`secrets.list`, `secrets.create`), granted unconditionally.
  - **Manager** (`secrets.get`, `secrets.update`, `secrets.delete`, and `versions.add/enable/disable/destroy/list/get`), granted with a condition that `resource.name` starts with `projects/<number>/secrets/gfs-bifrost--`.
  - Neither role has `versions.access` or `setIamPolicy`.
  - verify, impersonating `secrets-hub-dev`:
    - `gcloud secrets versions access` on any secret returns PERMISSION_DENIED;
    - `versions add` on a secret without the prefix is denied;
    - create, then `versions add`, on `gfs-bifrost--secrets-hub--dev--SMOKE_TEST` succeeds;
    - `gcloud iam roles describe` shows no `versions.access`. (AC 5)
  - **Hard exit:** no read or write code merges before this is verified.
- [x] 4. **Core: path and ID codec, plus a seed script.** Pure code in `core/secret-path.ts` and `core/secret-id.ts`. — secrets-hub#4: 59 adversarial tests incl. round-trip/injectivity; seed created SMOKE_TEST with expected id/labels — done: 9b3b95a
  - **Validation:**
    - org must be trusted;
    - repo must match `^[A-Za-z0-9._-]{1,100}$`, is lowercased, can't be `.` or `..`, and can't start with `_`;
    - env must come from config;
    - KEY must match `^[A-Z][A-Z0-9_]*$`, can't be one of `PORT`/`K_SERVICE`/`K_REVISION`/`K_CONFIGURATION`, and can't start with `X_GOOGLE_`.
  - **Encoding:** the repo segment hex-escapes `.` and `_`, segments are joined with `--`, and the ID is capped at 255 characters.
  - **Labels** `org`/`repo`/`env` (lossy, used only to filter lists). **Annotations** `secrets-hub.path` and `secrets-hub.state`; the keys use `.`, because Secret Manager rejects `/`. Scope is always recovered by decoding the ID.
  - `pnpm seed <path>` creates a secret through the codec, for test fixtures.
  - verify: one-behaviour-per-test adversarial suite:
    - traversal and casing in KEY and repo;
    - `_shared` and `_5fshared` repos;
    - `a--b`, and `a.b` vs `a_b`;
    - a round-trip property and injectivity over a generated set;
    - the length cap, and `X_GOOGLE_`. (AC 4)
- [x] 5. **CI references on the dev hub.** — secrets-hub#5: live OIDC smoke 200/200/401/403; no tokens in DD logs — done: 1a8ca0d
  - `core/ci-scope.ts`, from verified claims and config:
    - `repository_owner` and `repository_owner_id` must match a trusted org;
    - `repository` must be exactly `owner/repo`;
    - no environment maps to dev;
    - `terraform-*` names are mapped case-insensitively;
    - an unknown environment, or one this hub doesn't serve, is rejected.
  - `core/ci-references.ts`: repo and shared are merged with repo winning, and disabled secrets are dropped.
  - Adapters: the jose JWKS verifier (exact issuer, `aud`, RS256) and a Secret Manager list-only adapter. Plus the use-case and `GET /api/v1/ci/references`. Errors log `errorName`/`errorMessage` only.
  - `oidc-smoke.yaml` (`workflow_dispatch`, `id-token: write`).
  - verify, with SMOKE_TEST seeded via `pnpm seed`:
    - the unit suite for every reject path in AC 3;
    - smoke runs: no environment and `terraform-dev` both return SMOKE_TEST, a wrong audience gets 401, and `terraform-prod` gets 403 from the dev hub;
    - the Datadog log for those requests shows no token. (AC 1,3,6)
- [ ] 6. **Prod rollout.** Add the prod plan and apply, behind the `terraform-prod` environment, to `deploy.yaml`, plus `prod.tfvars` and the prod roles. README documents the CI contract: hub URLs per environment, `aud`, the response shape, the environment mapping, and that PR plans get dev's names.
  - verify:
    - the increment 3 negative tests repeated as `secrets-hub-prod`;
    - a prod `oidc-smoke` with `terraform-prod` returns a seeded prod SMOKE_TEST;
    - a no-environment token gets 403 from the prod hub. (AC 2,5)
        gate: Harry has QA'd the dev hub (increments 1–5) and agreed the prod plan
              [ ] confirmed

## Verification

### Evidence
- 2026-10-13 [inc 5] Live `oidc-smoke.yaml` on dev with real GitHub OIDC tokens: no environment → 200 with SMOKE_TEST (run 38427921192); `terraform-dev` → 200 (38427934306); wrong audience → 401 `ERR_JWT_CLAIM_VALIDATION_FAILED` (38427945826); `terraform-prod` → 403 "not served by this hub" (38427958572). Datadog `service:secrets-hub "ci references"`: one resolved/refused line per request, no token anywhere. (AC 1,3,6)
- 2026-10-13 [inc 5] Unit suite 88 tests incl. every AC 3 reject path; local `next start`: no auth → 401, garbage JWT → 401 `ERR_JWS_INVALID`, unknown kid → 401 `ERR_JWKS_NO_MATCHING_KEY`.
- 2026-10-13 [inc 4] 59 codec tests (round-trip + injectivity over all repo names ≤4 chars of `[az0-._]`, `_shared`/`_5fshared`, length cap); `pnpm seed` created `gfs-bifrost--secrets-hub--dev--SMOKE_TEST` with labels `org/repo/env` and `secrets-hub.path`. (AC 4)
- 2026-10-13 [inc 3] Impersonating `secrets-hub-dev` (temporary, time-boxed tokenCreator for Harry, removed after): read hub value DENIED, read core-infra value DENIED, add version / delete on non-hub secret DENIED, setIamPolicy DENIED; list, create, add version and delete on `gfs-bifrost--` secrets OK. (AC 5)
- 2026-10-13 [inc 2] Dev deploy green; `curl https://secrets-hub-dev-661226359806.europe-west2.run.app/api/health` → 200; "secrets-hub started" in Datadog via the sidecar with the deployed sha.
- 2026-10-13 [inc 1] secrets-hub#1 CI green; container scan 0 HIGH/CRITICAL after dropping npm/corepack from the runtime image; no token in the runtime image or its history.

### Not verified
- AC 2 (prod hub) — increment 6, gated on Harry's dev QA.

## Decisions & deviations

- **2026-10-13** — default_ci_env is per hub (dev→dev, prod→prod), not a global dev: the prod plan job in every deploy chain runs with no GitHub environment and must see prod references on the prod hub.
- 2026-10-13 — Each environment gets its own hub, managing only its own project. This replaces the draft's prod-hub-manages-dev topology: it keeps the Overview's no-cross-project rule, removes the bootstrap ordering, and keeps each secret's audit trail on one topic. The cost is two UI URLs, linked from each other.
- 2026-10-13 — Shared secrets are per environment, so there's no cross-project fan-out and no partial-failure state.
- 2026-10-13 — The planner, three reviewers and Harry's "build it autonomously" split the full hub into two plans: this one, then [[hub-ui-and-writes]].

## Learnings
- github-config's `repository` module can create `terraform-dev`/`terraform-prod` with required reviewers *before* the admin team has repo access; GitHub then silently stores an empty reviewer list and nobody can approve a deploy. Seen on secrets-hub's first apply; fixed by re-PUTting the team.
- The node:22-alpine base ships npm and corepack whose bundled deps (brace-expansion, pacote, sigstore, ip-address, picomatch) fail the container scan; the runtime stage must delete them.
- jose's error classes are minified in a Next production build — read `error.code`, not `error.name`.
- `secretmanager.secrets.create` is authorised on the parent project, so a `resource.name` IAM Condition can never restrict which IDs a principal creates.
- Secret Manager annotation keys allow only letters, digits, `-`, `_` and `.` (no `/`), up to 63 characters, with a 16 KiB total cap.
- Cloud Run also reserves every env var name starting with `X_GOOGLE_`.
- `secops-dep-node.yaml@0.2-bonbon` fails hard if there's no `<working_directory>/audit-ci.jsonc`. It installs pnpm 11 and strips `packageManager`.
