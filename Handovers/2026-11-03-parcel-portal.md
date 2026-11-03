---
tags: [handover]
status: open
workstream: Parcel Portal programme — SFTP users, UX review fixes, REST API, file layout rework
programme: Parcel Portal
repo: ilg-merak/parcel-portal
from: laptop
to: hjf.shell.platform.ilg.software
session_id: 80a57909-179d-48c7-a6cb-da766abb7a8a
resumed_by: ""
updated: 2026-11-03T16:30Z
---
# Handover: Parcel Portal

## Where things stand
Dev runs main at `10b6b0d` (svc-parcel-dev and ui-parcel-dev, project `ilg-merak-dev-b5e3`, us-central1), and the SFTP host runs the per-user build from #59/#66. Prod is held at D1: nothing deployed there, every prod gate stays parked (don't approve `docker-push-prod` / `terraform-*-prod` jobs). Dev database migrations are at 014.

| Unit | What it delivered | PRs | State |
| --- | --- | --- | --- |
| C13 | CSV mapping editor, preview, tabbed settings | #47 #48 #49 #51 #52 | Live on dev; being reworked as C17 |
| C14 | Per-user SFTP logins: users + keys in Postgres, svc publishes `sftp-users.json`, host signs in only against it, each user confined to its own `<slug>/inbound/` | #53 #54 #55 #57 #58 #59 #63 #66 | ✅ Verified on the live host: unknown user/key refused, `..` can't escape, a disabled user refused 27 s later, canary PASS as `_canary` |
| C16 A–E | Customer Overview checklist; packaging + bench printers as customer tabs; GFS staff (admins add admins); order page led by its next step; customer switcher (`X-Acting-Tenant`); per-customer demo printer; admins dispatch while acting | #60 #61 #62 #64 #65 #67 | Live on dev |
| C15 P1–P2 | Per-customer API keys: store (migration 014), core (`ppk_` tokens, sha256 only, `Authenticate`), admin API, API keys tab | #69 #70 #71 | Live on dev; nothing calls the API yet |

Dev SFTP users: `tca` (the existing dev test client's key) and `tca-verify` (disabled, left from verification).

## In flight
Each was started as a fork in the laptop session; each merges and deploys itself. If the laptop session ends first, finish the row from the target with "To close it".

| Work | PR / branch | State (16:30Z) | To close it |
| --- | --- | --- | --- |
| Site-local dates (C16 F): tenant time zone on `/me` (acting tenant's when acting), one named-zone formatter, Export day picker | #68 `hjf/c16-local-dates` | Open, CI running | Contract version → next free minor after main (4.6.0); merge; confirm svc+ui `terraform-apply-dev` success and image tags = merge sha |
| File layout editor rework (C17): one card, columns first, group-by picker, field dropdowns, translate values, required columns derived, extra columns ignored for a customer's own layout, shipping methods for every layout | #73 `hjf/c17-layout-svc` → #74 `hjf/c17-layout-editor` (stack) | Open | Merge bottom-up (`gh stack merge 74 --yes --merge` from the repo root); confirm deploys; ux-review before/after screenshots in the PR; add/tick C17 in Migration State |
| Bulk Cancel + Pack-with-preset on Orders (C16 G) | `hjf/c16-bulk-actions` (not yet pushed at 16:30Z) | Building | If unpushed when the laptop stops: restart from the design in Migration State's C16 row / this record's Next up |

## Waiting on Harry
Nothing is blocked on him now. These come back to him before proceeding:
- **Any Terraform change** — share the dev plan (and prod's, once prod exists) before merging; his yes covers that change's merge and dev gate only. Explain any IAM change first. Next due: the C15 public gateway (P5).
- **C15 contract change** — `ImportFile.source` gains `api`; contract-check calls that breaking, so it needs a deliberate major or `x-extensible-enum`. Recommend `x-extensible-enum` + minor.
- **Prod** — held at D1 until G7 (Oli Denton: intake here or in Fuse), the customer's SFTP key, `DATADOG_APP_KEY`, and the customer gates. The API is approved for dev with prod behind G7.

## Next up
1. Close the In flight rows.
2. **C15 P4–P7** (design: Migration State C15 row; the full design-agent report is summarised there): P4 public `/v1` contract (`public-openapi.yaml` v1.0.0) + `apiKey` middleware + CSV upload via the inbound bucket with `Idempotency-Key`; P5 public gateway Cloud Run + Swagger UI at `/docs` + LB host `api.parcel.delivery.<domain>` (**Terraform plan to Harry**); P6 JSON `POST /v1/orders`; P7 Cloud Armor/monitors (optional). Parse tokens with `core/apikeys`'s pattern (base64url secrets contain `_`).
3. C17 follow-ups from its PR's ux-review findings.
4. Small: UploadPanel's unused `tenantId`/`tenantName` props; revoking a revoked API key logs twice; the admin-add-admins path has no UI test.

## How work is done here
- **Source of truth:** vault `Bifrost/Parcel Portal/Migration State.md` (units, gates, decision log, scar tissue — load the `waypoint-programme` skill), ledger `Engineering/parcel-portal/ledger.md`, design doc `Systems/parcel-portal/design.md`. Every PR gets `wp ledger parcel-portal --programme "Parcel Portal"` (`--force` for a second same-day entry). No MKP Jira: PRs are out-of-ticket ("Ticket: none (Parcel Portal programme, unit Cn)").
- **Autonomy:** merge and deploy dev autonomously once local gates + CI are green (the prod `plan (svc|ui, prod)` checks fail by design — prod isn't built). Wait only for deploys and plans. Terraform is plan-then-proceed (above).
- **Repo mechanics:** worktrees only (`<repo>/.claude/worktrees/<slug>`, branch off `origin/main`, `git branch --unset-upstream`); never edit, switch or stash the main checkout (it is stale on purpose); stage explicit paths. `env -u GITHUB_TOKEN gh …`; push with `git -c credential.helper= -c credential.helper='!env -u GITHUB_TOKEN gh auth git-credential' push -u origin <branch>`; zsh doesn't word-split `$G`-style command variables. Gates: apps/svc `make check`, `make test-integration`, `make contract-check`; apps/ui `pnpm run lint`, `pnpm run build:check`. A `comment-density` hook blocks multi-line comment blocks in commits.
- **Deploy check:** for the merge sha, the `terraform-apply-dev` job of `svc-on-push` / `ui-on-push` / `sftp-on-push` must be `success`, and `gcloud run services list --project ilg-merak-dev-b5e3` must show `dev-<sha>`; svc logs "Migrations applied" with `toVersion`.
- **Reviews:** `review-panel` skill before merging non-trivial PRs (forks can't spawn reviewers — they apply the lenses themselves); `ux-review` for UI.
- **Slack:** never post deploy announcements; DMs go via Bifrost Support Bot (`slack-bot` skill). No contact with TCA, Yusen US or Despatch Cloud until Oliver says so.
- **Secrets:** never print them. Dev admin password: `~/parcel-portal-dev-admin.txt` (read in scripts only).

## On the target
Not yet checked — **ship** fills this in.

## Gotchas
- **Terraform: never read a bucket name from a `google_storage_bucket_iam_member`'s `.bucket`.** It's `b/<name>` and unknown until apply, so the Cloud Run / instance template update fails with the provider's "inconsistent final plan" — and a rerun hands the service an unreadable name. Read the bucket resource's or data source's `.name` (#63, #66).
- **Local Postgres `svc` database has schema drift** from old branch runs (e.g. `carrier_connection` predates 010): use a fresh database + `BOOTSTRAP_ADMIN_EMAIL/PASSWORD` for local e2e. No local bucket, so seed orders with SQL (parcel units `in`/`lb`).
- **The dev admin can't create logins on dev unprompted** — the auto-mode classifier blocks some dev writes; ask Harry when it does.
- **`next dev` never reaches network idle** in puppeteer (HMR socket): wait for a selector, not `networkidle0`.
- **SFTP host key:** a stale IP entry in `~/.ssh/known_hosts` fails checks; test with `-o CheckHostIP=no -o GlobalKnownHostsFile=/dev/null` and a fresh `UserKnownHostsFile`.
- **Next.js `redirect()` inside try/catch is swallowed** — keep role redirects outside the try.
- **`GButton` defaults to `ghost`** — primary actions need `variant="default"`.

## Closed since handover
| When (UTC) | Work | Result |
| --- | --- | --- |
