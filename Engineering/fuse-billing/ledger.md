---
tags: [waypoint, ledger]
---
# fuse-billing — work ledger

Agent-facing. Newest first. What meaningful work happened here, and the
context a future agent needs. Not a diary, not release notes, not a diff.

## 2026-11-05 — Run fuse-billing on the golden runtime image

Run fuse-billing on the golden runtime image

Runner moves from node:22-alpine to ilg-platform's node24-runtime (Datadog serverless-init entrypoint); build stages to glibc node:24, Node 24 in CI and @types/node. fuse-billing had no Datadog: the app container now carries the fleet DD_* env (GFS key + ILG dual-ship) from the datadog_api_key_* vars the pipeline already injected. The runner no longer inherits the build stage's ENV, so GITHUB_TOKEN stops being baked into the shipped image. Verified on dev (fuse-billing-dev-00042-wzq, 1 container, logs + metrics in Datadog); BigQuery path verified locally because dev runs in fixture mode with an empty billing_export dataset. Dev-only service, no prod.

PR: gfs-bifrost/fuse-billing#37
