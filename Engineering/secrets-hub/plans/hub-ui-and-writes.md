---
ticket: none
title: Hub UI and writes
service: secrets-hub
status: active
created: '2026-10-13'
updated: '2026-10-13'
repo: /home/hjf/code/fuse/secrets-hub
worktree: /home/hjf/code/fuse/secrets-hub/.claude/worktrees/ui-and-writes
branch: hjf/ui-and-writes
base: origin/main
base_sha: f3108ef85
pr: null
tags:
- waypoint
- plan
programme: Secrets Hub
unit: H7
impl_model: opus
impl_effort: medium
---
# Secrets Hub: UI and writes

<!-- Guidance is written as HTML comments. SUPERSEDING: one `> SUPERSEDED <date> — …` blockquote above the stale text. -->

## Intent
The second half of the hub ([[Secrets Hub/Overview|Secrets Hub]], programme unit H7), built on [[hub-ci-read-path]]. Developers log in with GitHub and see their repos. They can create, update, disable, enable and delete secrets in each environment's hub, with access decided by their live GitHub permission on the repo. Every write is audited, and no value is ever shown. When this plan is done, adding a secret means using the UI and then redeploying.

## Acceptance criteria
- [ ] A logged-out request is redirected to GitHub login. After login, a user sees the `gfs-bifrost` repos the App is installed on. A scope page lists names, versions, state and timestamps, and never a value.
- [ ] Write rights follow live GitHub permission:
  - push can write dev;
  - maintain or admin can also write prod;
  - org owners can write `<org>/_shared/<env>`.
   Anything else is denied, with a reason.
- [ ] Create and update add a Secret Manager version through the codec. The next CI references call reflects the change, and disabling a secret drops it from that call.
- [ ] Every write publishes one `secret_change` event to `audit.<env>.secrets.v1`. The event passes `SecretsAuditMessageSchema` before it's published, and its details carry no value. The write waits for the publish to finish before returning.
- [ ] Delete and disable warn that running services referencing the secret will fail to start new instances.
- [ ] The value never appears in a log, an error, a response or the session cookie.

## Affected boundaries
- `code/src/app` (pages, server actions, `api/auth/github/*`), `use-cases/*`, `core/write-policy.ts`, `core/audit-event.ts`, `adapters/{github,session.cookie,audit.publisher}.ts`, and the Secret Manager adapter's write methods.
- IaC: the GitHub App secret containers, a `random_bytes` session key secret, and `pubsub.publisher` on `audit.<env>.secrets.v1` through `iam_member`.
- `@gfs-bifrost/audit@^0.2.0` subpaths `./secrets` and `./publisher`. [[audit-service/overview]] ingests by system.

## Assumptions & uncertainty
- **Login is a GitHub App using a user-to-server token** (programme G6, decided 2026-10-13). The App must have "Expire user authorization tokens" on, giving an 8h token. The session is a JWE cookie (jose `dir`/A256GCM) keyed from a Terraform `random_bytes` secret. fuse-ui's HS256 session (`session.ts:10-11`) is not the model.
- **That `GET /repos/{o}/{r}` returns `permissions.{push,maintain,admin}` for a Metadata-read user-to-server token is UNVERIFIED in the docs.** Increment 2 checks it with a real token before the policy relies on it.
- **The App is private to `gfs-bifrost`.** Supporting more orgs later means making it installable on other accounts.
- **Shared writes are org owners only** (`GET /user/memberships/orgs/{org}` role `admin`). The draft's `SHARED_ADMIN_TEAMS` was dropped to keep to what G6 decided.
- **`createAuditPublisher` only validates the generic envelope** (`pkg/audit/src/publisher/audit-publisher.ts:64`). The adapter runs the strict `SecretsAuditMessageSchema.safeParse` first, as fuse-ui does (`audit-publisher.ts:46-53`).
- **A deleted and re-created secret loses the `iam_member` grants that services added.** The hub never calls `setIamPolicy`, so the UI warns instead.

## Increments
- [x] 1. **GitHub App and session secret containers.** Terraform creates `secrets-hub-github-app-{client-id,client-secret}` with no versions, a `random_bytes` session key with a version, and `secretAccessor` granted to the hub's service account through `iam_member` on those three secrets only. Nothing references them yet, so dev deploys stay green. — secrets-hub#6: 3 containers in dev, accessor = hub SA only; dev session key v1 added via gcloud — done: 3f1ef24
  - verify: dev apply is green; `gcloud secrets list --filter=secrets-hub-` shows all three; `get-iam-policy` on each shows only the hub's service account plus the deployer's owner role.
- [ ] 2. **Login, session and read-only UI.**
  - Login with `state` and PKCE, then a callback that exchanges the code.
  - A JWE session holding `{githubId, login, userToken, exp}`.
  - Middleware that redirects to login.
  - A repo picker from the installation's repositories.
  - Scope pages `[org]/[repo]` (dev or prod per hub) and `[org]/shared`. The URL avoids Next's `_folder` private-folder rule.
  - Cloud Run reads the App secrets through `secret_key_ref`.
  - verify:
    - unit tests mapping GitHub responses to `RepoPermission`;
    - one real-token check that `GET /repos/{o}/{r}` returns `permissions.maintain`;
    - dev screenshots: logged-out redirect, repo list, and a scope page showing SMOKE_TEST with no value;
    - devtools showing the cookie is `HttpOnly; Secure`. (AC 1,6)
        gate: G7, the GitHub App is created (private to gfs-bifrost, token expiry on, dev callback URL, installed on all repos) and its client id and secret have been added as versions
              [ ] confirmed
- [ ] 3. **Create and update, with audit.**
  - `core/write-policy.ts`, which decides from permission booleans, not `role_name`.
  - `core/audit-event.ts`.
  - Use-case `put-secret-value`: check GitHub live, then the policy, then `createSecret` plus `addSecretVersion` (labels, and annotations using the etag), then build the audit event, then `await` the publish.
  - The audit adapter: strict parse, then the publisher. On a failed publish it logs and increments `secrets_hub.audit.publish_failed`.
  - `pubsub.tf` grants the hub publisher on the audit topic.
  - verify:
    - the policy suite (push/maintain/admin/owner × dev/prod/shared, and an environment this hub doesn't serve);
    - a logger spy never sees the value;
    - on dev, a push-only user creates and updates SMOKE_TEST and `gcloud secrets versions list` shows the new version;
    - a shared write by a non-owner is denied (screenshot);
    - a temporary pull subscription on `audit.dev.secrets.v1` shows the `secret_change` events, whose details are `{org,repo,env,key,version}` only;
    - the CI smoke from [[hub-ci-read-path]] returns the new key. (AC 2,3,4,6)
        gate: programme H2 is applied in dev, meaning bifrost-pubsub#16 (the topic) and audit-service's `local.systems.secrets` entry (the subscription)
              [ ] confirmed
- [ ] 4. **Disable, enable and delete.** These use-cases run through the same policy and audit path. Delete and disable require a confirmation that names the risk to running services.
  - verify: disabling SMOKE_TEST drops it from the CI smoke and enabling it restores it; delete removes it; each action produces one audit event; screenshot of the warning dialog. (AC 3,4,5)
- [ ] 5. **Prod rollout of the UI and writes.** Add the prod App callback URL and secret versions, the prod session key, and the prod audit publisher grant.
  - verify:
    - a maintain user writes a prod secret and a push-only user is denied (screenshots);
    - the prod audit path is proven with a system-mismatched message rather than a stored synthetic event, per audit-service's known-context;
    - a prod CI smoke returns the new key. (AC 2,3,4)
        gate: Harry has QA'd the dev UI (increments 1–4), [[hub-ci-read-path]] is in prod, and H2 is applied in prod
              [ ] confirmed

## Verification

### Evidence
- 2026-10-13 [inc 4] secrets-hub#10: 141 tests (annotation set/clear, delete, audit action, refused change never touches the secret, view use-case canWrite matrix incl. push-only on prod hub = no write). Code merged; inert until login exists.
- 2026-10-13 [inc 3] secrets-hub#9: policy matrix, strict-schema event test, use-case suite (created/updated, value never in audit, refused write never reaches Secret Manager, audit failure counted not fatal); dev apply granted `pubsub.publisher` on `audit.dev.secrets.v1` to the hub SA only (verified via `gcloud pubsub topics get-iam-policy`).
- 2026-10-13 [inc 2] secrets-hub#8: local `next start` — login off: home explains, login 503; login on (dummy App): pages 307 → login, authorize URL has PKCE S256 + state, oauth cookie HttpOnly/SameSite=lax/600s, forged state 400, forged session → login. Dev after deploy: home shows "not configured", login 503, CI path unaffected (401 without token).
- 2026-10-13 [inc 1] secrets-hub#6: three containers in dev, each IAM policy = hub SA only; dev session key v1 added via gcloud from /dev/urandom.

### Not verified
- Real GitHub login, the `permissions.maintain` field for a Metadata-read user token, and live create/update/disable/delete with audit events in `audit.dev.secrets.v1` — all need G7 (the GitHub App) plus a follow-up wiring its client id/secret and the session key into Cloud Run via `secret_key_ref`.

## Decisions & deviations

- **2026-10-13** — Session key is a versionless Terraform container with its value added via gcloud from /dev/urandom, not random_bytes: random_bytes would put the key in Terraform state, which this programme exists to stop.
- 2026-10-13 — Write authority comes from GitHub repo permission through the user's own token, not an installation token. That keeps the private key unused, and the permission check is the user's literal access.
- 2026-10-13 — `SHARED_ADMIN_TEAMS` is dropped: shared writes are for org owners only, per G6.

## Learnings
- `createAuditPublisher` validates only the generic `AuditMessageSchema`, so a producer must run its system's strict union itself, or strict details like `secret_change` are never enforced.
