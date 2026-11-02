---
tags:
- waypoint
- ilg-secure-notes
verified: '2026-10-01'
verified_sha: 67115b4
verified_paths:
- .github/workflows
- iac/projects/ilg-secure-notes
title: ilg-secure-notes — operations
---
# ilg-secure-notes — operations

## Deploy — prod-only, no staging, verification is mandatory not optional

Commit straight to `master` (org-level PR-flow exception: no PR, no
changelog row, no Slack post). A push triggers `deploy.yaml` → Docker
build/push → `terraform apply` against **prod** (`bifrost-prod-global1`,
`europe-west2`), gated by the `terraform-prod` environment. **There is no
staging environment anywhere in this pipeline.**

Because of that, the repo's own CLAUDE.md prescribes an exact
verification sequence to run **before every push**, not after:

1. `pnpm run lint:fix` + `pnpm run build` (needs
   `GITHUB_TOKEN=$(gh auth token)` for the GitHub Packages install).
2. **Full E2E against a scratch dev GCS bucket**: create a throwaway
   bucket in `bifrost-dev-global1`, run `pnpm start` locally with
   `GCS_BUCKET_NAME` pointed at it and a random `CRYPTO_KEY`/`CRYPTO_IV`
   (via `openssl`), then drive the real UI with headless Chrome:
   create → reveal (assert the text) → verify the burn. Delete the
   scratch bucket afterward.
3. **After deploy**: a live smoke test against the real
   `ots.ilg.software` — create a real secret via `POST /api/secrets`,
   reveal it in a browser, confirm the burn.

## Observability

No dedicated dashboard identified during this pass. Standard Cloud Run
logging; no Datadog-specific instrumentation found in the app code.

## Real failure modes

- **A CSS class split silently kills the background gradient** — happened
  for real, ran in prod unnoticed for months. See [[known-context]].
- **The cleanup scheduler failing silently**: if the Cloud Scheduler job
  or the `/api/cleanup` route breaks, expired/over-viewed secrets stop
  being purged on schedule — but the reveal path itself still enforces
  the view-limit/expiry check at read time, so this degrades to "storage
  accumulates unpurged burned secrets," not "burned secrets become
  readable again."
- **A dev-environment SFTP-connector-creation flow in fuse-ui minting a
  real production secret** — not a bug, but a real operational fact:
  there is no dev-scoped instance of this app to isolate that traffic
  from prod. See [[known-context]].
- **The GitHub Packages install token leaking into a runtime image**:
  explicitly guarded against — the Dockerfile scopes `GITHUB_TOKEN` to
  the deps build stage only. Don't restructure the Dockerfile in a way
  that widens that scope.

## Cross-checking

There's no dedicated MCP or tooling for this app beyond direct
`curl`/browser access to `https://ots.ilg.software` and its `/api/docs`
OpenAPI document.
