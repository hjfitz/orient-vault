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
updated: 2026-11-03T17:14Z
---
# Handover: Parcel Portal

## Where things stand
Dev runs main at `ad72137` (svc-parcel-dev and ui-parcel-dev, project `ilg-merak-dev-b5e3`, us-central1), and the SFTP host runs the per-user build from #59/#66. Prod is held at D1: nothing deployed there, every prod gate stays parked (don't approve `docker-push-prod` / `terraform-*-prod` jobs). Dev database migrations are at 014.

| Unit | What it delivered | PRs | State |
| --- | --- | --- | --- |
| C13 | CSV mapping editor, preview, tabbed settings | #47 #48 #49 #51 #52 | Live on dev; being reworked as C17 |
| C14 | Per-user SFTP logins: users + keys in Postgres, svc publishes `sftp-users.json`, host signs in only against it, each user confined to its own `<slug>/inbound/` | #53 #54 #55 #57 #58 #59 #63 #66 | ✅ Verified on the live host: unknown user/key refused, `..` can't escape, a disabled user refused 27 s later, canary PASS as `_canary` |
| C16 A–E | Customer Overview checklist; packaging + bench printers as customer tabs; GFS staff (admins add admins); order page led by its next step; customer switcher (`X-Acting-Tenant`); per-customer demo printer; admins dispatch while acting | #60 #61 #62 #64 #65 #67 | Live on dev |
| C17 | File layout editor rework: one card, columns first, group-by picker, field dropdowns, translate values, required columns derived on save, extra columns ignored for a customer's own layout (DC built-in stays strict), shipping methods for every layout (contract 4.7.0) | #73 #74 | Live on dev |
| C15 P1–P2 | Per-customer API keys: store (migration 014), core (`ppk_` tokens, sha256 only, `Authenticate`), admin API, API keys tab | #69 #70 #71 | Live on dev; nothing calls the API yet |

Dev SFTP users: `tca` (the existing dev test client's key) and `tca-verify` (disabled, left from verification).

## In flight
The laptop's forks were **stopped at 16:42Z** (Harry logging off). Both had pushed everything; their laptop worktrees are clean and not reachable from here — work from the pushed branches. Finish each row:

| Work | PR / branch | State (16:45Z) | To close it |
| --- | --- | --- | --- |
| Site-local dates (C16 F): tenant time zone on `/me` (acting tenant's when acting), one named-zone formatter, Export day picker | #68 `hjf/c16-local-dates` (head `b7e5381`) | Open, CI running; **behind main** — main moved to contract 4.7.0 (C17) | In a worktree off the branch: `git merge origin/main`, resolve `apps/svc/openapi.yaml` to **4.8.0** (next free minor), `make gen`, svc + ui gates, push; wait for CI; merge; confirm svc+ui `terraform-apply-dev` success + image tags; record in Closed |
| Bulk Cancel + Pack-with-preset on Orders (C16 G) | #76 `hjf/c16-bulk-actions-svc` → #77 `hjf/c16-bulk-actions-ui` (stack, head `c0226f9`) | Open, CI running; clean on top of main | If #68 merges first, re-check the stack's contract version doesn't collide (renumber to the next free minor); then `gh stack merge 77 --yes --merge` from the repo root; confirm svc+ui dev deploys; ledger entries exist from the fork — check with `grep -F "#76" ~/Documents/obsidian/Engineering/parcel-portal/ledger.md`, add if missing |

## Waiting on Harry
Nothing is blocked on him now. These come back to him before proceeding:
- **Any Terraform change** — share the dev plan (and prod's, once prod exists) before merging; his yes covers that change's merge and dev gate only. Explain any IAM change first. Next due: the C15 public gateway (P5).
- **C15 contract change** — `ImportFile.source` gains `api`; contract-check calls that breaking, so it needs a deliberate major or `x-extensible-enum`. Recommend `x-extensible-enum` + minor.
- **Prod** — held at D1 until G7 (Oli Denton: intake here or in Fuse), the customer's SFTP key, `DATADOG_APP_KEY`, and the customer gates. The API is approved for dev with prod behind G7.

## Next up
1. Close the In flight rows.
2. **C15 P4–P7** (design: Migration State C15 row; the full design-agent report is summarised there): P4 public `/v1` contract (`public-openapi.yaml` v1.0.0) + `apiKey` middleware + CSV upload via the inbound bucket with `Idempotency-Key`; P5 public gateway Cloud Run + Swagger UI at `/docs` + LB host `api.parcel.delivery.<domain>` (**Terraform plan to Harry**); P6 JSON `POST /v1/orders`; P7 Cloud Armor/monitors (optional). Parse tokens with `core/apikeys`'s pattern (base64url secrets contain `_`).
3. C17 follow-ups: none owed from its ux-review (all four findings fixed); evidence screenshots on `hjf/c17-layout-editor-evidence` (keep until the PR bodies no longer need them).
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
Checked 2026-11-03 ~16:40Z on `harry@hjf.shell.platform.ilg.software`; synced with remote-compute's `sync-claude-config` (vault, `~/code`, `~/code/merak` config, skills, MCP servers); this record, `session-handover/SKILL.md` and `Migration State.md` verified identical by sha256.
- **Has:** claude, gh (logged in as harry-fitzgerald_gfsdev), gcloud (harry.fitzgerald@gfsdeliver.com), git, go, node, docker, python3, jq, tmux, mise (pnpm, terraform, terragrunt, gitleaks installed under mise — not on the login PATH until `mise` activates in the repo), `~/.claude/waypoint`, orient at `~/projects/orient`, the vault.
- **Repo:** cloned at `~/code/merak/parcel-portal` (16:47Z, `gh repo clone`; the workstation's gh account sees the open PRs). Claude starts from `~/code/merak`. The dev admin password file `~/parcel-portal-dev-admin.txt` is not synced — ask Harry to place it, or read it from wherever he keeps it; never print it. No local Postgres yet: `cd apps/svc && make deps-up` (docker is there). OAuth MCP servers (Atlassian, Datadog, Slack, ado-remote) need `/mcp` once; the fuse MCP kept the workstation's own config.
- **Start:** `ssh harry@hjf.shell.platform.ilg.software`, `cd ~/code/merak`, `claude`, then "pick up the Parcel Portal handover".

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
| 2026-11-03 ~17:09 | #76/#77 bulk Cancel + Pack (C16 G) | Merged main (with #68) in and renumbered the contract **4.8.0 → 4.9.0**. Ran review-panel on the stack and fixed what it found. In bulk.go: a portal-side failure (internal or unavailable) is now logged as "Bulk order action failed"; a held order's message now says to dispatch it again to settle it; a stale-read conflict is now coded `order_changed`. In the UI: the preset picker falls back when the chosen preset is gone; the cancel dialog keeps its count while it closes; the order page says "cancelled". svc gates + integration green locally, CI green. **Native GitHub stack:** `gh pr merge` is refused, and the extension isn't installed here, so it merged via `PUT /pulls/77/merge-async` (merges downstack too). Merged as `6b12b7d`; svc+ui `terraform-apply-dev` success, both on `dev-6b12b7d`, svc "Migrations applied" toVersion 14 at 17:08Z. |
| 2026-11-03 ~16:55 | #68 site-local dates (C16 F) | Already had main merged (contract 4.8.0); svc gates + integration green locally, CI green (UI gates from CI: this box's gh token lacks `read:packages`). review-panel: no blockers (follow-up: customer settings tabs show the *acting* tenant's zone, not that customer's). Merged as `5f57837`; svc+ui `terraform-apply-dev` success, both on `dev-5f57837`, svc "Migrations applied" toVersion 14 at 16:54Z. Resumed by the workstation session. |
| 2026-11-03 ~16:30 | C17 file layout editor rework | #73 + #74 merged as `ad72137`; svc+ui dev on `dev-ad72137`; C17 ✅ in Migration State |
