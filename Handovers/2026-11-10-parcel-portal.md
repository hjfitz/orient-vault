---
tags: [handover]
status: resumed
workstream: Parcel Portal programme — dev carrier choice shipped; its dev check, acting-as UI (C19 6–8, C20), label preview inc 5, small fixes C26–C33
programme: Parcel Portal
repo: ilg-merak/parcel-portal
from: hjf.shell.platform.ilg.software
to: laptop
session_id: a25bb30f-e3fe-44fe-885c-4e0ba8c2cc07
resumed_by: ""
updated: 2026-11-10T14:43Z
---
# Handover: Parcel Portal (workstation → laptop)

## Where things stand
Dev runs main at `7988887` (#115) for svc (`svc-parcel-dev-00051`), ui (`ui-parcel-dev-00059`) and gateway (`gateway-parcel-dev-00014`). The same merge applied sftp. Everything is in project `ilg-merak-dev-b5e3`, us-central1, checked 14:38Z. **Prod is held at D1.** The merge's four deploy runs (svc, ui, gateway, sftp, all at `7988887`) are parked at their prod gates, and are never approved. Older parked runs were superseded. Migrations are at **017**, the portal contract is **5.10.0**, and the customer API is **1.2.0**. History from 3 to 10 Nov is in [[Handovers/2026-11-03-parcel-portal]].

| Unit | What it delivered | PRs | State |
| --- | --- | --- | --- |
| C22 incs 1–4 | Label preview: inline, a Preview dialog, thermal benches shown in the printer's dots, carrier ZPL sent as bytes, pdf.js legacy build | #106–#110 | ✅ On dev. Inc 5 waits on Harry |
| C23 | Each panel once on an order's page | #111 | ✅ |
| C24 | Batch results stay when the list empties | #112 | ✅ |
| C25 | A customer switch clears the previous customer's results and print state | #112 #113 | ✅ C33 is open |
| Scans | x/net v0.62.0; `.trivyignore.yaml` for the platform runtime images | #114 | ✅ The ignore entries expire **16 Nov** |
| SHIP-1110 | On dev, each customer books with the test carrier or its own Selector account (**Book with the test carrier** on the Selector config card). Prod ignores the setting | #115 | ✅ Merged and live on dev. The dev drive (plan inc 6) is still owed |

## In flight
| Work | PR / branch | State | To close it |
| --- | --- | --- | --- |
| SHIP-1110 increment 6: drive the carrier choice **on dev** | #115 merged; no branch left | Plan `dev-choose-the-test-carrier-or-the-configured-co` is **blocked** only because the workstation has no dev admin login. **The laptop has one**: `~/parcel-portal-dev-admin.txt` (bootstrap admin `admin@parcel-portal.invalid`; read it only in scripts, never print it) | Run [[Handovers/2026-11-10-parcel-portal.carrier-choice.spec.ts.txt]] as a Playwright spec (copy it to `e2e/carrier-choice.spec.ts` in a scratch worktree and **don't commit it**, or it joins the smoke suite; run `npx playwright test carrier-choice.spec.ts` with `BASE_URL=https://parcel.delivery.freightops.dev`, `SMOKE_EMAIL=admin@parcel-portal.invalid`, `SMOKE_PASSWORD` from the file). Expect, in order: two demo customers; A's 5 sample orders book TST; untick A → "This customer has 5 booked shipments … Close them before switching carrier"; B on the sandbox account (TEST/TEST, HERMES, GB) saves; B's Check connection says "The carrier accepted the account."; B's Shipments has Manifest off with the sandbox reason; B ticked back saves; both demo customers are deleted. Then: paste the evidence into the plan's Verification, `wp tick … --increment 6`, confirm its gate, tick AC 1, `wp plan set-status … --status active`, `wp signoff`, and promote the plan's Learnings. AC 6 stays open until the smoke login works (below) |

## Waiting on Harry
- **C22 increment 5, ZPL in the browser.** Recommended: **A**, keep ZPL accounts download-only until a ZPL customer is confirmed. The other options are B, Labelize (a third-party download needing his OK, after a render test) and C, PDF on thermal. An A6 sandbox check was offered.
- **The dev smoke login.** Every deploy's `smoke-dev` and the nightly fail at sign-in ("That email and password don't match" for `smoke-test@parcel-portal.invalid`). The repo has the `DEV_SMOKE_ADMIN_PASSWORD` secret but no `DEV_SMOKE_ADMIN_EMAIL` **variable**. Recommended: with the laptop's dev admin login, create a dedicated GFS admin on dev for the smoke, then set the variable and secret to it. Get Harry's OK for the repo secret and variable write first. That also opens the gates on C19 incs 6–8 and SHIP-1110's AC 6.
- **C19 increments 6–8** (a stale acting cookie cleans itself up, stale tabs, actions carry the page's customer) were proposed and not answered. They're gated on the smoke login.
- **A name and branding** for the portal. Suggested: **Merak** (my pick: the Plough's "pointer" star), Volt, Flare, Dart. Avoid Relay (Amazon Relay), Spark (Walmart Spark), Bolt and Stamp (Stamps.com). A brand board was offered once SHIP-1110 shipped.
- **Prod D1** is unchanged: held until G7 (Oli Denton), the customer's SFTP key and the customer gates.

## Next up
1. SHIP-1110 increment 6 on dev (In flight).
2. **Rebuild the platform runtime images** `go-runtime` and `node24-runtime` (ilg-platform, with a patched `datadog-init` and `zlib1g` `+deb13u1`) **before 16 Nov**. Otherwise `.trivyignore.yaml`'s entries expire and every container scan goes red again.
3. **C26–C33**, the small fixes found in the C23–C25 sweeps. `wp programme status "Parcel Portal"` says next: C26, C27, C28, C29. Each row in `Bifrost/Parcel Portal/Migration State.md` carries its cause and file:line.
4. **C20** acting-as clearer Settings: plan `acting-as-clearer-settings`, active, not started. It's meant to follow C19.
5. **Dependabot PRs #92–#95** are open: ui npm group, svc go group, the actions group, and node 24 → 25 for ui.
6. **C15 P7** (Cloud Armor and rate limits on the gateway, a gateway monitor, publishing `public-openapi.yaml`) and the API follow-ups are listed in the previous record's Next up and the C15 row.

## How work is done here
- **Sources of truth:**
  - The vault's `Bifrost/Parcel Portal/Migration State.md` (load the `waypoint-programme` skill).
  - The ledger `Engineering/parcel-portal/ledger.md`.
  - Plans in `Engineering/parcel-portal/plans/`.
  - The repo's `AGENTS.md`. Guardrails: G1 tenant-scoped queries, G2 at-most-once dispatch, G3 openapi first, G4 never manifest on the shared Selector sandbox.
- **Recording:** every PR gets `wp ledger parcel-portal --programme "Parcel Portal"`. There's no MKP Jira: PRs say "Ticket: none".
- **Autonomy (Harry, 6 Nov: "be pragmatic – only ask if this breaks. otherwise, full steam ahead"; "we may merge whatever we want"):**
  - Merge Parcel PRs once the gates and CI pass.
  - For Terraform, read the dev plans yourself and merge when they show only what the change intends.
  - **Never approve a prod gate.**
  - Raise real blockers: missing access, a red check with no known cause, a destroy or a prod change.
  - These two Parcel memories were written on the workstation and may be missing from the laptop's memory dir; recreate them if so. This bullet is the first; **Datadog goes to the GFS org only** (no ILG dual-shipping; never ask for an ILG key) is the second.
- **CI facts:**
  - Terraform PR plans for **prod always fail** while prod is held: data sources can't find prod's never-applied SFTP topic and bucket. Every iac PR since 5 Nov shows this.
  - Dev plans show only the `:plan` placeholder image, plus a standing re-render of the scaling and env blocks.
  - Every on-push workflow includes `iac/env/**`, so a tfvars change deploys all four apps to dev, and the sftp host template is replaced.
- **Repo mechanics:**
  - Worktrees only (`<repo>/.claude/worktrees/<slug>` off `origin/main`, then `git branch --unset-upstream`). Never touch the main checkout. Stage explicit paths.
  - Use `env -u GITHUB_TOKEN gh …`, and push with `git -c credential.helper= -c credential.helper='!env -u GITHUB_TOKEN gh auth git-credential' push -u origin <branch>`.
  - The `comment-density` hook wants single-line comments.
  - Gates: apps/svc `make check`, `make test-integration` (needs `TEST_POSTGRES_URL`), `make contract-check BASE_REF=origin/main`; apps/ui `pnpm run lint`, `pnpm run build:check`, `next build`.
  - Merge PRs as merge commits, as main's history does.
- **Deploy check:**
  - For the merge sha, each on-push run's `terraform-apply-dev` must succeed (`watch-deploy.sh` logic in the previous record), and `gcloud run services list --project ilg-merak-dev-b5e3` must show `dev-<sha>`.
  - svc logs "Migrations applied" (`toVersion`) and "The test carrier is offered".
  - To try a branch on dev before merging, run `gh workflow run svc-manual-deploy.yaml` or `ui-manual-deploy.yaml` with `--ref <branch>`.
- **Reviews:** `review-panel`, or `/ship`'s four-lens self-review, before merging anything non-trivial.
- **Slack:** use Bifrost Support Bot only, and post no deploy announcements. No contact with TCA, Yusen US or Despatch Cloud.

## On the target
Not checked from here: the workstation has no route to the laptop. The vault reaches it by `orient-vault-sync`. The `~/.claude` sync only runs laptop → workstation, so nothing under `~/.claude` comes back. Check on arrival:
- **The vault has this record** (`ls ~/Documents/obsidian/Handovers/2026-11-10-parcel-portal*`), plus the spec attachment and the plan `Engineering/parcel-portal/plans/dev-choose-the-test-carrier-or-the-configured-co.md` with its `carrier-choice-screens/`.
- **`~/parcel-portal-dev-admin.txt`** is present (check by name only).
- **`~/code/merak/parcel-portal`** has been `git fetch`ed, and main is at `7988887` or later.
- **The two memories** under How work is done.
- **On the workstation side:** all its Parcel worktrees were removed after confirming each was merged, with no unique commits. A local Postgres container `pp-postgres` stays running there with the `svc_preview` database.

## Gotchas
- **A local svc has no carrier key,** so any save that stores a carrier password answers 503. To drive an own-account save locally, run a throwaway `cmd/` main that calls `bootstrap.Build(…, bootstrap.WithCarrierKey(key))`, and never commit it. Otherwise use dev or the e2e harness.
- **A shipment booked by one backend can't be closed through the other.** Selector refuses a TST consignment, and the test carrier "voids" a Selector booking only in the portal. That's why a carrier switch is refused while anything is open.
- **The switch guard is a check, not a lock.** A dispatch already under way during a switch strands its shipment, which needs an engineer (documented in the svc README).
- **The booking log's `testCarrier` must come from `carrier.Test(conn)`, not the column.** Migration 017 set every older row, prod's included, to `true`.
- **The orders list pages at 25.** Filter it (e.g. Needs packing) before selecting a row by its label in Playwright.
- **zsh doesn't word-split unquoted variables.** A loop over run ids needs an array or `${=ids}`.
- **`gh run view --log-failed` refuses while a run waits at a prod gate.** Read a finished job with `gh api --allow-escape-sequences repos/ilg-merak/parcel-portal/actions/jobs/<id>/logs`.
- **React siblings sharing a key orphan DOM nodes, and production builds don't warn.** Prefix each key with its component (C23, C25).
- **sonner replays active toasts to a remounted Toaster.** Dismiss them on a customer switch instead.
- **The local `svc_preview` database's `Demo 6 Nov 14:12:31 UTC` was deleted 9 Nov.** Acting for it 404s on `/me` (the stale-cookie error page, not a bug).

## Closed since handover
| When (UTC) | Work | Result |
| --- | --- | --- |
