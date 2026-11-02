---
tags: [waypoint, ledger]
---
# secrets-hub — work ledger

Agent-facing. Newest first. What meaningful work happened here, and the
context a future agent needs. Not a diary, not release notes, not a diff.

## 2026-11-02 — Clear the next and zod advisories failing the dependency audit and image scan

Clear the next and zod advisories failing the dependency audit and image scan

next 16.3.8 (two critical, one high) and zod 4.4.3 (high) failed the audit and image scan on main and on the Renovate bump. Exact pins moved to next 16.4.3 and zod 4.6.7.

PR: gfs-bifrost/secrets-hub#21

## 2026-10-15 — Ask for single sign-on instead of failing with a 500

Ask for single sign-on instead of failing with a 500

GitHub App user tokens issued without an SSO session are refused (403 'SAML enforcement') on every gfs-bifrost resource. Adapter raises SsoRequiredError for that (checked in request(), so getOrgRole no longer reads it as 'not a member'); pages render a sign-in-again page with the org SSO link.

PR: gfs-bifrost/secrets-hub#16

## 2026-10-15 — Say which GitHub call failed and why

Say which GitHub call failed and why

UpstreamError from the GitHub adapter now carries the request path and GitHub's message; the first real dev login 403'd on listInstallationRepos with no detail.

PR: gfs-bifrost/secrets-hub#15

## 2026-10-15 — Turn on developer login in dev

Turn on developer login in dev

Mounts the GitHub App client id/secret and session key into the dev hub from Secret Manager (latest), behind login_enabled (dev only). Hold merge until the client-secret version exists, or the revision won't start.

PR: gfs-bifrost/secrets-hub#14

## 2026-10-13 — Turn on Secret Manager data-access audit logs

Turn on Secret Manager data-access audit logs

Programme H4: DATA_READ/DATA_WRITE audit config for secretmanager.googleapis.com; verified a read lands in cloudaudit data_access in dev. Prod via #7.

PR: gfs-bifrost/secrets-hub#12

## 2026-10-13 — Add hub login, writes, lifecycle and audit (inert until the GitHub App)

Add hub login, writes, lifecycle and audit (inert until the GitHub App)

Plan hub-ui-and-writes inc 1-4 code: app-secret containers (values via gcloud, never state), GitHub App login (PKCE, JWE session), read-only UI, create/update, disable (soft annotation)/enable/delete, strict secret_change audit to audit.<env>.secrets.v1. Live verification blocked on G7 (GitHub App).

PR: gfs-bifrost/secrets-hub#6, gfs-bifrost/secrets-hub#8, gfs-bifrost/secrets-hub#9, gfs-bifrost/secrets-hub#10

## 2026-10-13 — Build the Secrets Hub CI read path in dev

Build the Secrets Hub CI read path in dev

Plan hub-ci-read-path inc 1-5: app shell + CI, dev Cloud Run, custom Secret Manager roles (no versions.access, conditional on gfs-bifrost-- prefix; verified by impersonation), id codec (59 tests), GET /api/v1/ci/references (live OIDC smoke 200/200/401/403). Prod rollout #7 held as draft for Harry's QA.

PR: gfs-bifrost/secrets-hub#1, gfs-bifrost/secrets-hub#2, gfs-bifrost/secrets-hub#3, gfs-bifrost/secrets-hub#4, gfs-bifrost/secrets-hub#5, gfs-bifrost/secrets-hub#7
