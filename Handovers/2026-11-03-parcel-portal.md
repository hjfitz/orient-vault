---
tags: [handover]
status: resumed
workstream: Parcel Portal programme — SFTP users, UX review fixes, REST API, file layout rework
programme: Parcel Portal
repo: ilg-merak/parcel-portal
from: laptop
to: hjf.shell.platform.ilg.software
session_id: 80a57909-179d-48c7-a6cb-da766abb7a8a
resumed_by: 7652f0c7-9f02-4c64-b56f-a154250bb016
updated: 2026-11-03T17:47Z
---
# Handover: Parcel Portal

## Where things stand
Dev svc runs main at `2cca2d8` (svc-parcel-dev, revision 00033), and dev ui runs `6b12b7d` (#79 touched no UI). Both are in project `ilg-merak-dev-b5e3`, us-central1. The SFTP host runs the per-user build from #59/#66. Prod is held at D1: nothing is deployed there, and every prod gate stays parked (don't approve the `docker-push-prod` / `terraform-*-prod` jobs). Dev database migrations are at 014. The portal contract is 4.9.0, and the customer API (`public-openapi.yaml`) is 1.0.0.

| Unit | What it delivered | PRs | State |
| --- | --- | --- | --- |
| C14 | Per-user SFTP logins | #53 #54 #55 #57 #58 #59 #63 #66 | ✅ Verified on the live host |
| C16 A–G | UX review fixes, plus site-local dates (F) and bulk Cancel + Pack (G) | #60 #61 #62 #64 #65 #67 #68 #76 #77 | ✅ Live on dev |
| C17 | File layout editor rework | #73 #74 | ✅ Live on dev |
| C15 P1–P2 | Per-customer API keys: store, core, admin API, keys tab | #69 #70 #71 | Live on dev |
| C15 P4a | Customer API contract `public-openapi.yaml` 1.0.0, the `APIKey` middleware (a chi group, before path binding), `GET /v1/order-files/{id}`, `make public-contract-check` in CI | #79 | Live on dev svc. Not reachable from outside until P5. Not hit on dev: this account lacks `run.invoker`; verified locally over HTTP and by a clean revision start |
| C15 P4b | `POST /v1/order-files` (CSV, `Idempotency-Key`), customer API 1.1.0, portal contract **5.0.0** | #80 (draft) | Ready; **held for Harry** (below) |

Dev SFTP users: `tca` (the existing dev test client's key) and `tca-verify` (disabled, left from verification).

## In flight
| Work | PR / branch | State | To close it |
| --- | --- | --- | --- |
| C15 P4b: CSV upload over the API | #80 `hjf/c15-api-upload` (draft; worktree `.claude/worktrees/c15-api-upload`) | Gates green locally. review-panel findings fixed (`0cfa306`). CI: all 31 checks green on `0cfa306`, the UI lint and build included. Draft until Harry answers. | On Harry's yes to 5.0.0: `gh pr ready 80`, merge, confirm the svc+ui dev deploys, then record it here. Main has moved since? Then merge `origin/main` in first, and renumber if a 5.x has landed. |

## Waiting on Harry
- **Portal contract 5.0.0 for P4b (#80).** Recommend yes.
  - Adding `api` to `ImportFile.source` is breaking under oasdiff either way. An enum value added is `response-property-enum-value-added`; moving to `x-extensible-enum` is `response-property-became-not-enum`. Both were checked on 3 Nov.
  - So the earlier "x-extensible-enum plus a minor" can't pass contract-check.
  - A 5.0.0 costs nothing: no 4.x was ever released (only the template's `svc-openapi-v1.0.0`), and the in-repo UI is the only consumer. It makes `source` an `x-extensible-enum` for good.
- **Two small API calls, in #80's Notes.**
  - Should Idempotency-Keys be shared across a customer's API keys (as built, Stripe-style) or per key?
  - Should `problems` on an order file be capped or paged?
- **Any Terraform change.** Share the dev plan (and prod's, once prod exists) before merging; his yes covers that change's merge and its dev gate only. Explain any IAM change first. Next due: the C15 public gateway (P5).
- **Prod** is held at D1 until G7 (Oli Denton: intake here or in Fuse), the customer's SFTP key, `DATADOG_APP_KEY`, and the customer gates.
- **This box's GitHub token can't read GitHub Packages.** It lacks `read:packages`, so `pnpm install` for apps/ui fails here (401 on `@ilg-platform/ui-toolkit`) and the UI gates only run in CI. Fix: `gh auth refresh -s read:packages` (needs a browser, plus SSO for ilg-platform), then `pnpm config set "//npm.pkg.github.com/:_authToken" "$(gh auth token)"`.

## Next up
1. #80 on Harry's yes (above).
2. **C15 P5: the public gateway.**
   - A Cloud Run gateway proxying `/v1` to svc. It sends its own ID token in `X-Serverless-Authorization`, so svc gets the key in `Authorization`.
   - Swagger UI at `/docs`, an LB host `api.parcel.delivery.<domain>`, and rate limiting on the refusal path.
   - **The Terraform plan goes to Harry first.** Publish `public-openapi.yaml` in the release alongside it: `contract-bundle` still ships only `openapi.yaml`.
3. C15 P6: JSON `POST /v1/orders`. P7: Cloud Armor and monitors.
4. **Small:**
   - The customer settings tabs show dates in the acting tenant's zone, not that customer's (from #68's review).
   - UploadPanel's `tenantId`/`tenantName` props are unused.
   - Revoking a revoked API key logs twice.
   - The admin-add-admins path has no UI test.

## How work is done here
- **Source of truth:** vault `Bifrost/Parcel Portal/Migration State.md` (units, gates, decision log, scar tissue — load the `waypoint-programme` skill), ledger `Engineering/parcel-portal/ledger.md`, design doc `Systems/parcel-portal/design.md`. Every PR gets `wp ledger parcel-portal --programme "Parcel Portal"` (`--force` for a second same-day entry). No MKP Jira: PRs are out-of-ticket ("Ticket: none (Parcel Portal programme, unit Cn)").
- **Autonomy:** merge and deploy dev autonomously once local gates + CI are green (the prod `plan (svc|ui, prod)` checks fail by design — prod isn't built). Wait only for deploys and plans. Terraform is plan-then-proceed (above).
- **Repo mechanics:** worktrees only (`<repo>/.claude/worktrees/<slug>`, branch off `origin/main`, `git branch --unset-upstream`); never edit, switch or stash the main checkout (it is stale on purpose); stage explicit paths. `env -u GITHUB_TOKEN gh …`; push with `git -c credential.helper= -c credential.helper='!env -u GITHUB_TOKEN gh auth git-credential' push -u origin <branch>`; zsh doesn't word-split `$G`-style command variables. Gates: apps/svc `make check`, `make test-integration`, `make contract-check`; apps/ui `pnpm run lint`, `pnpm run build:check`. A `comment-density` hook blocks multi-line comment blocks in commits.
- **Deploy check:** for the merge sha, the `terraform-apply-dev` job of `svc-on-push` / `ui-on-push` / `sftp-on-push` must be `success`, and `gcloud run services list --project ilg-merak-dev-b5e3` must show `dev-<sha>`; svc logs "Migrations applied" with `toVersion`.
- **Reviews:** `review-panel` skill before merging non-trivial PRs (forks can't spawn reviewers — they apply the lenses themselves); `ux-review` for UI.
- **Slack:** never post deploy announcements; DMs go via Bifrost Support Bot (`slack-bot` skill). No contact with TCA, Yusen US or Despatch Cloud until Oliver says so.
- **Secrets:** never print them. Dev admin password: `~/parcel-portal-dev-admin.txt` (read in scripts only).

## On the target
Checked 2026-11-03 ~16:40Z on `harry@hjf.shell.platform.ilg.software`; synced with remote-compute's `sync-claude-config` (vault, `~/code`, `~/code/merak` config, skills, MCP servers); this record, `session-handover/SKILL.md` and `Migration State.md` verified identical by sha256.
- **Has:** claude, gh (logged in as harry-fitzgerald_gfsdev), gcloud (harry.fitzgerald@gfsdeliver.com), git, go, node, docker, python3, jq, tmux, mise (pnpm, terraform, terragrunt, gitleaks installed under mise — not on the login PATH until `mise` activates in the repo), `~/.claude/waypoint`, orient at `~/projects/orient`, the vault.
- **Repo:** cloned at `~/code/merak/parcel-portal` (16:47Z, `gh repo clone`; the workstation's gh account sees the open PRs). Claude starts from `~/code/merak`. The dev admin password file `~/parcel-portal-dev-admin.txt` is not synced — ask Harry to place it, or read it from wherever he keeps it; never print it.
- **Local Postgres:** the container `pp-postgres` (postgres:17, `svc`/`svc` on :5432). Started with `docker run` because this docker has no `compose` plugin, so `make deps-up` fails. `psql` isn't installed: use `docker exec -i pp-postgres psql -U svc`. `make tools` puts golangci-lint under mise's Go, so run make targets as `mise x -- make …`.
- **git identity:** set globally to Harry's globalfreightsolutions.com address on 3 Nov; it was unset here.
- **gh token:** no `read:packages` (see Waiting on Harry). There is no `gh stack` extension: merge a native stack with `PUT /repos/<o>/<r>/pulls/<top>/merge-async` (`sha`, `merge_method=merge`), then poll `GET …/merge-async/<uuid>`. It merges the downstack PRs too. OAuth MCP servers (Atlassian, Datadog, Slack, ado-remote) need `/mcp` once; the fuse MCP kept the workstation's own config.
- **Start:** `ssh harry@hjf.shell.platform.ilg.software`, `cd ~/code/merak`, `claude`, then "pick up the Parcel Portal handover".

## Gotchas
- **A native GitHub stack refuses `gh pr merge` and `gh pr edit --base`** ("part of a stack"). Use the async merge API on the top PR (see On the target).
- **oasdiff counts any change to a response `enum` as breaking.** That covers adding a value and switching to `x-extensible-enum`. Declare a response field that may grow as `x-extensible-enum` from its first version.
- **The generated chi wrapper binds path params before its per-route middlewares.** Auth that must come first goes in a `router.Group` `Use` around the generated routes (#79).
- **`gh pr checks --watch` started right after a push can exit on the previous head's finished checks.** Watch the new run (`gh run watch <id>`) or check `headRefOid`.
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
| 2026-11-03 ~17:27 | #79 C15 P4a, the customer API's first route behind API keys | Built on the workstation. review-panel (backend, security, contract) found five issues, all fixed before merge: the key check now runs before path binding and fails closed; 500/503 are declared; the enums are `x-extensible-enum`; an unknown route answers a JSON 404; a refused key gets an API-specific 401. Evidence was gathered over HTTP locally (11 cases, key in the log 0 times). svc gates, integration, contract-check and public-contract-check are green, and CI ran the new step. Merged as `2cca2d8`; svc `terraform-apply-dev` success, `dev-2cca2d8`; revision 00033 applied migrations, is listening, no errors. |
| 2026-11-03 ~17:09 | #76/#77 bulk Cancel + Pack (C16 G) | Merged main (with #68) in and renumbered the contract **4.8.0 → 4.9.0**. Ran review-panel on the stack and fixed what it found. In bulk.go: a portal-side failure (internal or unavailable) is now logged as "Bulk order action failed"; a held order's message now says to dispatch it again to settle it; a stale-read conflict is now coded `order_changed`. In the UI: the preset picker falls back when the chosen preset is gone; the cancel dialog keeps its count while it closes; the order page says "cancelled". svc gates + integration green locally, CI green. **Native GitHub stack:** `gh pr merge` is refused, and the extension isn't installed here, so it merged via `PUT /pulls/77/merge-async` (merges downstack too). Merged as `6b12b7d`; svc+ui `terraform-apply-dev` success, both on `dev-6b12b7d`, svc "Migrations applied" toVersion 14 at 17:08Z. |
| 2026-11-03 ~16:55 | #68 site-local dates (C16 F) | Already had main merged (contract 4.8.0); svc gates + integration green locally, CI green (UI gates from CI: this box's gh token lacks `read:packages`). review-panel: no blockers (follow-up: customer settings tabs show the *acting* tenant's zone, not that customer's). Merged as `5f57837`; svc+ui `terraform-apply-dev` success, both on `dev-5f57837`, svc "Migrations applied" toVersion 14 at 16:54Z. Resumed by the workstation session. |
| 2026-11-03 ~16:30 | C17 file layout editor rework | #73 + #74 merged as `ad72137`; svc+ui dev on `dev-ad72137`; C17 ✅ in Migration State |
