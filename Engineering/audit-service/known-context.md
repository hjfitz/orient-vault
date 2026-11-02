---
tags:
- waypoint
- audit-service
verified_paths: []
title: audit-service — known context
verified: '2026-10-12'
---
# audit-service — known context

Exempt from staleness checks: investigation and decision truth, not a claim about current
source. Re-verify a specific implementation detail against code before relying on it.

## Decisions that shape it

- **`AuditMessage`, not `BifrostMessage`.** The envelope must work outside the Bifrost suite, so
  it carries no `customer`/`recordType`; `producer` (not `source`, which means the ingress
  connector in Fuse) names the emitter.
- **One topic per system** (`audit.<env>.<system>.v1`), not one shared topic with a filter. A
  noisy or broken system can't starve another's subscription, and adding a system is additive IaC.
- **Full snapshots in `details`, masked by the reader** (programme gate G3). Producers send full
  before/after snapshots and the service stores them as given, which is why payloads are never
  logged; a reader (fuse-ui) masks secrets server-side before anything reaches a browser.
> SUPERSEDED 2026-10-22 — not quite: since audit-service#12, `sftp_login` events get `expireAt` = occurredAt + 365 days (no backfill). Everything else is kept forever.
- **Kept forever.** Totals are capped at 1000 so a count never costs a full scan of a history
  that only grows.
- **Legacy ids preserved.** Imported fuse-ui rows keep their ObjectId hex (or the `eventId`
  fuse-ui minted) as `_id`, so existing deep links resolve after cutover. The envelope's
  `eventId` therefore accepts a UUID or 24-hex id.

## Gotchas

- **A `gcloud auth print-identity-token` user token passes Cloud Run IAM but the app's verifier
  rejects it (401).** Its audience is gcloud's client, not the service. To test end to end, mint an
  SA token with `--audiences=<service URL>`.
- **`gcloud run services update --update-env-vars "^@^…"` breaks on values containing `@`**
  (emails, e.g. `READ_CALLERS`). Use another delimiter, e.g. `^;^`.
- **The generated Go `eventId` pattern is case-sensitive.** Zod's `/i` flag doesn't survive into
  JSON Schema. Producers mint lowercase ids, so it doesn't bite in practice.
- **The tf-plan PR check races a concurrent deploy for the dev state lock** and fails with a 412.
  Rerun it.
- **A PR that is part of a GitHub stack can only be merged with `PUT …/pulls/N/merge-async`.**
  `gh pr merge` fails, as does PATCHing a stack member's base; GitHub retargets the child itself.
- **`make gen-check` diffs against the git index**, so an uncommitted edit to the generated file
  is silently overwritten and passes; only committed (or staged) staleness fails it, which is
  the CI case.
- **Prod ingest was proven with a system-mismatched message only**, so no synthetic row sits in
  the permanent history. Keep doing that: anything stored in prod is stored forever.
- **A wrong audience gets a 401 HTML page from Cloud Run, not the app's `{message}` JSON.** The
  verifier leaves the audience check to Cloud Run (`verifier.go`), so callers must handle a non-JSON
  401/403.
- **A read `limit` above 100 is silently clamped to 100** (`query.go`), even though the OpenAPI
  `maximum: 100` suggests a 400.
- **`import-legacy -source-db` defaults to `fuse-ui`, but fuse-ui's database is `fuse-ui-app`.**
  Always pass `-source-db fuse-ui-app`.

- **A reader on `api_readers` can read every system**, not just the one it was added for: `READ_CALLERS` guards all of `/api/v1/systems/*` (`routes.go`). The Fuse MCP's grant therefore covers `secrets` too; its code reads `fuse` only. Readers: fuse-ui (masks server-side) and the Fuse MCP (`fuse-mcp-prod-sa`, prod, per-kind allow-list projection), per the 2026-10-22 decision.
- **A new reader's first calls get Cloud Run's HTML 403 for ~30s** after the apply, while IAM propagates. The app's own refusal is JSON `{"message":"caller not allowed"}`.
- **Deploy runs share one concurrency group without cancel-in-progress**, so a run parked at `terraform-prod` blocks every later one, and approving a gate ships all of `main` since the live sha.

## Fuse specifics

- **fuse-ui dev's Cloud Run service is `fuse-ui-app-dev`**, database `fuse-ui-app`. Its
  `audit_log` held 702 rows, all of which map (snapshot 2026-10-12).
- fuse-ui still writes its own `audit_log` until the programme's UF cutover flips
  `AUDIT_SINK=service` and `AUDIT_READ_SOURCE=service`; the legacy import runs once, by a human,
  after that (snapshot 2026-10-12).

## Unknowns

- How long fuse-ui's `audit_log` is kept after cutover before it is dropped (programme gate G6).
- Whether "org-wide" means gfs-bifrost only or ILG-wide; it decides who else gets a topic and a
  reader allow-list entry.
- Who owns the SFTP connector VM that will report user-lifecycle events (programme gate G7).
