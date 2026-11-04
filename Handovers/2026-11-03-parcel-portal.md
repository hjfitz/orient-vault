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
updated: 2026-11-04T11:05Z
---
# Handover: Parcel Portal

## Where things stand
Dev runs main at `059a62a` for svc (revision 00037) and the new **gateway** (`gateway-parcel-dev`, revision 00002), and `2218b15` for ui. Everything is in project `ilg-merak-dev-b5e3`, us-central1. The SFTP host was redeployed routinely by #81. **The customer API is live on dev at `https://api.parcel.delivery.freightops.dev`**: `/docs` (Swagger UI), `/openapi.json` (1.2.0), and `/v1/order-files`, `/v1/order-files/{id}` and `/v1/orders`. Prod is held at D1: nothing is deployed there, and every prod gate stays parked. Migrations are at 014. The portal contract is 5.0.0, and the customer API is 1.2.0.

| Unit | What it delivered | PRs | State |
| --- | --- | --- | --- |
| C14 | Per-user SFTP logins | #53 #54 #55 #57 #58 #59 #63 #66 | ✅ Verified on the live host |
| C16 A–G | UX review fixes, plus site-local dates (F) and bulk Cancel + Pack (G) | #60 #61 #62 #64 #65 #67 #68 #76 #77 | ✅ Live on dev |
| C17 | File layout editor rework | #73 #74 | ✅ Live on dev |
| C15 P1–P2 | Per-customer API keys: store, core, admin API, keys tab | #69 #70 #71 | Live on dev |
| C15 P4a | Customer API contract `public-openapi.yaml` 1.0.0, the `APIKey` middleware (a chi group, before path binding), `GET /v1/order-files/{id}`, `make public-contract-check` in CI | #79 | Live on dev svc. Not reachable from outside until P5. Not hit on dev: this account lacks `run.invoker`; verified locally over HTTP and by a clean revision start |
| C15 P4b | `POST /v1/order-files` (CSV, `Idempotency-Key`), customer API 1.1.0, portal contract 5.0.0 | #80 | Live on dev |
| C15 P5 | Public gateway `cmd/gateway` + `iac/projects/gateway` at `api.parcel.delivery.<domain>` (`/v1` proxy, `/docs`) | #81 | Live on dev. Verified over HTTPS: `/docs` 200 with CSP, `/openapi.json` 200, a keyless `/v1` request gets svc's own 401 (so the gateway passes svc's IAM), and `/admin/*` isn't forwarded (404) |
| C15 P6 | `POST /v1/orders`: up to 100 JSON orders, one request = one import file, the import's own plan and validation, per-order created/replaced/refused | #83 | Live on dev |

Dev SFTP users: `tca` (the existing dev test client's key) and `tca-verify` (disabled, left from verification).

## In flight
None.

## Waiting on Harry
- **Nothing blocks.** Harry's 3 Nov evening answer: "P6, breaking changes, deployments: all fine. there are no users until we are done". So the P6 design calls were made here: one request is one file, a resend replaces the order unless it's dispatched, there's no Idempotency-Key for JSON, and a contract violation is a 400 for the whole request.
- **Any further Terraform change.** Share the dev plan before merging (and prod's, once prod exists). Explain any IAM change first. The agent's merge of a Terraform PR may be refused by the auto-mode classifier; #81 went through once Harry had OK'd deployments in-session.
- **Prod** is held at D1 until G7 (Oli Denton: intake here or in Fuse), the customer's SFTP key, `DATADOG_APP_KEY`, and the customer gates.
- **This box's GitHub token can't read GitHub Packages.** It lacks `read:packages`, so the UI gates run in CI only. Fix: `gh auth refresh -s read:packages`.

## Next up
1. **C15 P7:**
   - Cloud Armor and rate limiting in front of the gateway. A refused key costs one DB lookup and one log line.
   - A Datadog monitor for the gateway.
   - Publish `public-openapi.yaml` in the release (`contract-bundle` ships only `openapi.yaml`).
2. **API follow-ups from the reviews:**
   - Line and parcel problems in `/v1/orders` carry `lines.hsCode`, with no index for which line.
   - A packaging name in a parcel isn't resolved to a preset; the file path doesn't resolve it either.
   - Zero or negative weights pass validation on both paths.
3. **Small:**
   - The customer settings tabs show dates in the acting tenant's zone, not that customer's.
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
| 2026-11-04 ~11:00 | #90, demo customer and sample order file | Harry asked whether upload → pack → label was easy to test; it wasn't. On dev and local only (fake carrier; 403 elsewhere): **Try the portal → Create a demo customer** sets up a complete customer and switches you to acting for it on Orders, and **Download a sample file** gives ready, needs-packing and flagged orders with new references each time. Dev test checklist rewritten in the vault. review-panel findings fixed (a half-made demo is cleaned up; same-second refs). Merged as `a6b0bae` through more GitHub 5xx; svc and ui `terraform-apply-dev` success. **Waiting on Harry:** the browser smoke test needs a dedicated GFS admin login and a `DEV_SMOKE_ADMIN_PASSWORD` repo secret. |
| 2026-11-04 ~10:05 | #87 + #88 + #89 (stack), user management, customer soft-delete, generated SFTP folders | Harry: "add the option for the gfs admin to manage users as well as (soft-) delete customers", then generate the SFTP folder from the name. #87: edit name/email, enable, set password (revokes sessions); disable revokes sessions; no self-disable. #88: `tenant.deleted_at` (migration 015). Sign-in, sessions, API keys, the SFTP snapshot, slug lookup and acting-as all refuse a deleted customer, and restore undoes it. #89: folder from the name + 4 random chars on create; migration 016 backfills (8 chars); the folder is read-only in the UI. review-panel (backend, frontend, security, data; then backend for #89) findings fixed before merge. Contract 5.4.0. Folded #89→#88→#87, then merged as `610f028` during a GitHub PR outage, retried until it landed. |
| 2026-11-04 | #86, one Access tab | Harry: merge Users, SFTP users and API keys, make them intuitive, link Swagger and share the SFTP host. Access tab: Portal users / SFTP (host with copy, port 22, `/inbound`, key-only) / API (address, Swagger docs link, bearer key); old tab URLs redirect to `access#users|sftp|api`; stale "not live yet" notes removed. ui Terraform: `SFTP_HOST` (only where `sftp_host_enabled`) and `CUSTOMER_API_URL` env vars from `dns_domain`; Harry OK'd the dev plan (0/1/0, in-place on ui-parcel-dev). Prod plans fail on lookups of never-applied prod resources (pre-existing, prod held). review-panel: no findings. Merged as `f943d4e`; ui `terraform-apply-dev` success. The agent's account can't read dev Cloud Run (`run.services.get`), so the env values weren't read back. |
| 2026-11-04 | #85, layout editor follow-up and Selector config | Harry's feedback after #84: drop "Your file's columns" (column names typed, with suggestions), keep group-by, Order / Each product line as tabs with to-do counts, the Carrier account tab renamed Selector config. review-panel (frontend) findings fixed before merge: duplicate suggestions, unlabelled tab counts, blank grouping inputs piling up, every grouping input marked red. Merged as `c60d4ee`; ui `terraform-apply-dev` success. Prod held. |
| 2026-11-03 ~23:30 | #84 C18, layout editor matches columns by name | Harry asked whether the CSV mapping UX was now good; it wasn't yet. Name matching (svc `POST /admin/mapping/suggest`, contract 5.1.0), to-dos instead of red errors, needed-for badges, direct If blank / Translate links. review-panel (backend, frontend, contract) findings fixed before merge: HS/customs columns went to SKU/name; a lone Weight made a half parcel; a matching race and a stuck status. Merged as `8d9a2dc`; svc and ui `terraform-apply-dev` success; prod jobs wait at the `terraform-prod` gate (held). Harry skipped screenshots: "better to experience these things in the browser". |
| 2026-11-03 ~20:22 | #83 C15 P6, JSON orders | Harry: "P6, breaking changes, deployments: all fine". review-panel (backend+data, contract) found the following, all fixed before merge: a failed store left the file at processing (now finished as rejected); CSV wording in messages; untrimmed text; the decimal pattern stricter than the file path; an empty `lines` accepted; 422 `file_too_large` undocumented. Merged as `059a62a`; svc and gateway `terraform-apply-dev` success, both on `dev-059a62a`; the live `/openapi.json` is 1.2.0 with `/v1/orders`. |
| 2026-11-03 ~19:55 | #81 C15 P5, the public gateway | Merged by the agent as `4aa7721` after Harry OK'd deployments in-session. The earlier attempt had been refused as an IaC apply. gateway, svc and sftp `terraform-apply-dev` all success. The plan applied as recorded (15 to add). The managed cert was live by about 20:20Z, and the HTTPS checks pass (see Where things stand). |
| 2026-11-03 ~19:28 | #82, an API key revoke logged once | `RevokeAPIKey` reports whether this call revoked the key. Merged as `8ed8744`; svc `terraform-apply-dev` success, `dev-8ed8744`, revision 00035 applied migrations with no errors. |
| 2026-11-03 ~18:46 | #80 C15 P4b, CSV upload over the API | Harry answered the stop DM in-session, about 17:50Z: "happy to continue with the lot overnight". Taken as yes to portal contract 5.0.0, with the two API questions kept at their defaults (keys per customer, problems uncapped). Merged as `2218b15`; svc and ui `terraform-apply-dev` success, both on `dev-2218b15`, revision 00034 applied migrations with no errors. |
| 2026-11-03 ~17:27 | #79 C15 P4a, the customer API's first route behind API keys | Built on the workstation. review-panel (backend, security, contract) found five issues, all fixed before merge: the key check now runs before path binding and fails closed; 500/503 are declared; the enums are `x-extensible-enum`; an unknown route answers a JSON 404; a refused key gets an API-specific 401. Evidence was gathered over HTTP locally (11 cases, key in the log 0 times). svc gates, integration, contract-check and public-contract-check are green, and CI ran the new step. Merged as `2cca2d8`; svc `terraform-apply-dev` success, `dev-2cca2d8`; revision 00033 applied migrations, is listening, no errors. |
| 2026-11-03 ~17:09 | #76/#77 bulk Cancel + Pack (C16 G) | Merged main (with #68) in and renumbered the contract **4.8.0 → 4.9.0**. Ran review-panel on the stack and fixed what it found. In bulk.go: a portal-side failure (internal or unavailable) is now logged as "Bulk order action failed"; a held order's message now says to dispatch it again to settle it; a stale-read conflict is now coded `order_changed`. In the UI: the preset picker falls back when the chosen preset is gone; the cancel dialog keeps its count while it closes; the order page says "cancelled". svc gates + integration green locally, CI green. **Native GitHub stack:** `gh pr merge` is refused, and the extension isn't installed here, so it merged via `PUT /pulls/77/merge-async` (merges downstack too). Merged as `6b12b7d`; svc+ui `terraform-apply-dev` success, both on `dev-6b12b7d`, svc "Migrations applied" toVersion 14 at 17:08Z. |
| 2026-11-03 ~16:55 | #68 site-local dates (C16 F) | Already had main merged (contract 4.8.0); svc gates + integration green locally, CI green (UI gates from CI: this box's gh token lacks `read:packages`). review-panel: no blockers (follow-up: customer settings tabs show the *acting* tenant's zone, not that customer's). Merged as `5f57837`; svc+ui `terraform-apply-dev` success, both on `dev-5f57837`, svc "Migrations applied" toVersion 14 at 16:54Z. Resumed by the workstation session. |
| 2026-11-03 ~16:30 | C17 file layout editor rework | #73 + #74 merged as `ad72137`; svc+ui dev on `dev-ad72137`; C17 ✅ in Migration State |
