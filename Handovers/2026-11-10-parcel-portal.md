---
tags: [handover]
status: resumed
workstream: Parcel Portal programme — per-account Selector services shipped; FedEx booking fixed on dev (single parcel); debug MCP (#128) merged; multi-parcel booking open with Selector (Oliver Wilders)
programme: Parcel Portal
repo: ilg-merak/parcel-portal
from: laptop
to: hjf.shell.platform.ilg.software
session_id: a1c66d35-5bf7-4f34-9d21-dac5ddb5fabe
resumed_by: 3e3bf683-a529-4b8f-afc1-7733d6a995ea
updated: 2026-11-11T12:57Z
---
# Handover: Parcel Portal (laptop → workstation)

## Where things stand
Dev runs svc and gateway at `2938b41` (#128) and ui at `7628c78` (#127), all Ready, in project `ilg-merak-dev-b5e3`, us-central1, checked 12:56Z from the VM. **Prod is held at D1.** The newest parked run, 43024078471, is for `2938b41` and waits at `docker-push-prod`. Older parked runs show cancelled once a newer run arrives. None is approved or ever to be. Migrations are at **018** and the portal contract is **5.12.0**. Earlier history is in [[Handovers/2026-11-03-parcel-portal]]. Confluence write-up of the Selector work: Merak Project page 357007366.

| Unit | What it delivered | PRs | State |
| --- | --- | --- | --- |
| Per-account Selector services list | Table, API, enforcement, save-time check, status fields, UI card, methods editor | #116 #118–#123 | ✅ On dev |
| Booking fixes found driving dev | Shipment goods description; Selector's own fault text in logs; the shipment-level `Cost` Selector's FedEx booking needs | #124 #125 #126 | ✅ On dev. Single-parcel FedEx books on FGR, FGHD and FIGR (mock; no real FedEx shipment) |
| Debug MCP, dev access | `debug_invokers` grants `roles/run.invoker` on svc in dev only (prod ignores it) | #127 | ✅ Merged 7628c78 |
| Debug MCP | `apps/svc/cmd/debug-mcp`, 20 tools, dev only | #128 | ✅ Merged `2938b41` (12:52Z). A local tool, not part of the deployed images |
| C22 incs 1–4, C23–C25, scans, SHIP-1110 | Label preview, panel and batch-result fixes, runtime-image ignores, test-carrier switch | #106–#115 | ✅ On dev. C22 inc 5 waits on Harry; SHIP-1110 inc 6 still owed |

## In flight
| Work | PR / branch | State | To close it |
| --- | --- | --- | --- |
| **Multi-parcel FedEx booking** | Oliver Wilders's thread (laptop DM `D0ALESDKC86`, parent ts `1794391490.825169`) | Thread read at 12:20Z (the Slack MCP is signed in on the VM): two replies. Oliver's, at 11:32Z: no live TCA FedEx booking has more than one parcel, one shipment per call since 28 Oct, and TCA is likely to test multi-parcel soon. Ours, at 12:00Z: the repro and the stack-trace request. **No reply to the 12:00Z ask yet**, so there is nothing to answer | Re-read the thread (`slack_read_thread`, channel `D0ALESDKC86`, ts `1794391490.825169`) for his trace. **Don't reply to him from the VM**; a nudge is drafted under Waiting on Harry. If he finds the cause, the fix is Selector's. The portal-side stopgap is one shipment per parcel (a model change: an order would hold several shipments), which needs Harry's go |
| SHIP-1110 increment 6: drive the carrier choice on dev | #115 merged | Blocked on the workstation having no dev admin login | Unchanged: needs `~/parcel-portal-dev-admin.txt` (not on the VM, see On the target) and [[Handovers/2026-11-10-parcel-portal.carrier-choice.spec.ts.txt]]. Don't start it without the file |

## Waiting on Harry
- **Multi-parcel.** Wait for Oliver's trace. If he can't fix it soon, say yes or no to booking each parcel as its own shipment (recommended: only if TCA's multi-parcel test is imminent; otherwise wait for Selector's fix). No reply from Oliver to our 12:00Z repro as of 12:20Z, and nothing to answer. If he is still silent tomorrow, a nudge to send from your own Slack (nothing has been sent from the VM): "Hi Oliver, did you get a chance to run the two-parcel FedEx repro with a stack trace on? If the fix is on Selector's side, a rough date would help, since TCA may test multi-parcel soon."
- **Secrets for the VM.** `~/parcel-portal-dev-admin.txt` (dev admin login) and `~/.config/parcel-debug/selector.env` (the Selector test login, mode 600) exist only on the laptop and were **not copied**. Without them the debug MCP's portal and replay tools, SHIP-1110 inc 6 and any dev drive can't run on the VM. The MCP itself is installed and registered on the VM: `deploy_status` ran live there at 12:43Z.
- **The test carrier stays ungated by the services list** (recommended: yes). The stack merged on that basis; say if you want it gated.
- **C22 increment 5, ZPL in the browser.** Recommended: **A**, keep ZPL accounts download-only until a ZPL customer is confirmed. The other options are B, Labelize (a third-party download needing his OK, after a render test) and C, PDF on thermal. An A6 sandbox check was offered.
- **The dev smoke login.** Every deploy's `smoke-dev` and the nightly fail at sign-in (`smoke-test@parcel-portal.invalid`). The repo has the `DEV_SMOKE_ADMIN_PASSWORD` secret but no `DEV_SMOKE_ADMIN_EMAIL` **variable**. Recommended: create a dedicated GFS admin on dev for the smoke, then set the variable and secret. Get Harry's OK for the repo secret and variable write first. That also opens C19 incs 6–8 and SHIP-1110's AC 6.
- **C19 increments 6–8** (stale acting cookie, stale tabs, actions carry the page's customer) were proposed and not answered. They're gated on the smoke login.
- **A name and branding** for the portal. Suggested: **Merak**, Volt, Flare, Dart. Avoid Relay, Spark, Bolt and Stamp.
- **Prod D1** is unchanged: held until G7 (Oli Denton), the customer's SFTP key and the customer gates.

## Next up
1. *(Done at 12:52Z, see Closed: #128 landed and the owed records written.)*
2. **Rebuild the platform runtime images** `go-runtime` and `node24-runtime` (ilg-platform, with a patched `datadog-init` and `zlib1g` `+deb13u1`) **before 16 Nov**. Otherwise `.trivyignore.yaml`'s entries expire and every container scan goes red again. Needs Harry's go (another repo).
3. **C26–C33**, the small fixes found in the C23–C25 sweeps. `wp programme status "Parcel Portal"` says next: C26, C27, C28, C29. Each row in `Bifrost/Parcel Portal/Migration State.md` carries its cause and file:line.
4. **C20** acting-as clearer Settings: plan `acting-as-clearer-settings`, active, not started. It's meant to follow C19.
5. **Dependabot PRs** are open: ui npm group, svc go group, the actions group, and node 26 for ui.
6. **C15 P7** (Cloud Armor and rate limits on the gateway, a gateway monitor, publishing `public-openapi.yaml`) and the API follow-ups.

## How work is done here
- **Sources of truth:**
  - The vault's `Bifrost/Parcel Portal/Migration State.md` (load the `waypoint-programme` skill).
  - The ledger `Engineering/parcel-portal/ledger.md`.
  - Plans in `Engineering/parcel-portal/plans/`.
  - The repo's `AGENTS.md`. Guardrails: G1 tenant-scoped queries, G2 at-most-once dispatch, G3 openapi first, G4 never manifest on the shared Selector sandbox (never call CommitShipments, PrintManifest or ProcessCarrierDispatch against it).
- **Recording:** every PR gets `wp ledger parcel-portal --programme "Parcel Portal"`. There's no MKP Jira: PRs say "Ticket: none".
- **Autonomy (Harry, 6 Nov: "be pragmatic – only ask if this breaks. otherwise, full steam ahead"; "we may merge whatever we want"; 11 Nov: dev has no users, so he is happy for the tooling to have all the read and write access it needs there, and the PR size limit only matters if humans review):**
  - Merge Parcel PRs once the gates and CI pass.
  - For Terraform, read the dev plans yourself and merge when they show only what the change intends.
  - **Never approve a prod gate.**
  - Raise real blockers: missing access, a red check with no known cause, a destroy or a prod change.
  - **Datadog goes to the GFS org only** (never ask for an ILG key).
  - These are in the laptop's memory dir (`feedback_parcel_portal_autonomy.md`, `feedback_parcel_portal_datadog_gfs_only.md`). Recreate them on the VM if missing.
- **Outward contact:** no contact with TCA, Yusen US or Despatch Cloud. On the laptop, Harry had me message Oliver Wilders from his Slack account, naming myself as Claude. **An unattended session must not**: draft instead. Slack posts otherwise go through Bifrost Support Bot only, and no deploy announcements.
- **Secrets:** never print or write the dev admin password or the Selector test login; read them only inside scripts or environment variables. The Selector login came from Harry's DM with Oliver.
- **CI facts:**
  - Terraform PR plans for **prod always fail** while prod is held ("topic not found", "bucket does not exist"). Every iac PR shows this, including #104, #115 and #127.
  - Dev plans show the `:plan` placeholder image, plus a standing re-render of the scaling and env blocks.
  - Every on-push workflow includes `iac/env/**`, so a tfvars change deploys all four apps to dev.
- **Repo mechanics:**
  - Worktrees only (`<repo>/.claude/worktrees/<slug>` off `origin/main`, then `git branch --unset-upstream`). Never touch the main checkout. Stage explicit paths.
  - Use `env -u GITHUB_TOKEN gh …`, and push with `git -c credential.helper= -c credential.helper='!env -u GITHUB_TOKEN gh auth git-credential' push -u origin <branch>`.
  - The `comment-density` hook wants single-line comments.
  - Gates: apps/svc `make check` (its `gen-check` reads uncommitted edits as stale; commit first), `make test-integration` (needs `TEST_POSTGRES_URL`), `make contract-check BASE_REF=origin/main`; apps/ui `pnpm run lint`, `pnpm run build:check`, `next build`.
  - Merge PRs as merge commits, as main's history does.
- **Deploy check:** each on-push run's `terraform-apply-dev` must succeed, and `gcloud run services list --project ilg-merak-dev-b5e3` must show `dev-<sha>`. To try a branch on dev before merging, run `gh workflow run svc-manual-deploy.yaml` or `ui-manual-deploy.yaml` with `--ref <branch>`.
- **Reviews:** `review-panel`, or `/ship`'s four-lens self-review, before merging anything non-trivial.

## On the target
Checked 12:20Z over SSH, names only:
- **Present:** `claude`, `gh`, `gcloud` (signed in as Harry), `git`, `go`, `node`, `docker`, `python3`, `jq`, `tmux`; the vault; `session-handover`; `~/code/merak/parcel-portal`; Claude's `defaultMode` is `auto`; a Claude login. tmux has `main` (4 windows) and `monitors`.
- **Missing:** `pnpm`, `terraform` and `gitleaks` (not needed for svc work or for PR plans, which CI runs; `pnpm` is needed for UI work; CI is the authority for the secret scan), `~/code/selector` (the Selector source, laptop only, not a git repo), `~/parcel-portal-dev-admin.txt` and `~/.config/parcel-debug/selector.env`. The debug MCP is installed and registered now; it wasn't at 12:20Z.
- **Confirmed on arrival (12:18Z to 12:38Z):** `git fetch` shows `origin/main` at `7628c78`. The main checkout is on `main`, 98 behind, and was left alone. `gh api rate_limit` reset at 12:37:35Z (4,984 of 5,000 after). The VM clock is NTP-synced and matches GitHub's `Date` header. `gh auth status` was not run, as the launch note said it can mislead while the limit is exhausted.

## Gotchas
- **svc is private.** Only the UI's runtime service account and (dev only, #127) Harry's user can invoke it. The dev region is **us-central1**; `gcloud run … --region europe-west2` shows an empty policy.
- **GitHub API limit.** `gh run watch` and `gh pr checks --watch` at 20 s intervals across several PRs used the hourly 5,000. Poll slowly, and use `gh api rate_limit` (it doesn't count) to see the reset.
- **Selector's FedEx booking needs the shipment-level `<Cost>`** or it throws a null reference after the carrier step (0030). A package-level cost, version 5.0.1, a Shipper block, dimensions and package contents change nothing. Package code is **`YOUR`**, not `YP`. In ASMX the element order matters: `Cost` goes after `CustomsDetails`, and `Shipper` after `CarrierService`.
- **Two-parcel FedEx fails in Selector** with 0030 "Index was outside the bounds of the array", for every FedEx service, even in TCA's live request shape. One parcel books. Re-pack an order as one parcel to book it.
- **version-test is a mock.** Its FedEx URL points at a service on the same box, so no FedEx shipment exists and labels are test labels. Live TCA calls use the batch `ProcessShipments`, version 5.0.1, `ShipperId` 0 and a `Shipper` block; the portal's `ProcessShipment` 5.0.0 works with `Cost`.
- **A local svc has no carrier key,** so any save that stores a carrier password answers 503. Use dev or the e2e harness.
- **A shipment booked by one backend can't be closed through the other.** That's why a carrier switch is refused while anything is open.
- **The booking log's `testCarrier` must come from `carrier.Test(conn)`, not the column.**
- **The orders list pages at 25.** Filter it (e.g. Needs packing) before selecting a row by its label in Playwright.
- **zsh doesn't word-split unquoted variables.** A loop over run ids needs an array or `${=ids}`.
- **`gh run view --log-failed` refuses while a run waits at a prod gate.** Read a finished job with `gh api --allow-escape-sequences repos/ilg-merak/parcel-portal/actions/jobs/<id>/logs`.
- **React siblings sharing a key orphan DOM nodes, and production builds don't warn.** Prefix each key with its component.
- **sonner replays active toasts to a remounted Toaster.** Dismiss them on a customer switch instead.
- **gitleaks scans the whole history** (186 commits on #128), so a placeholder in a pushed commit can't be cleared by editing the file in a later commit. Use a rule-and-path allowlist in `.gitleaks.toml` (precedent: 0737122), or fix it before the first push. A redaction test that feeds a fake value under a key named `apiKey` trips `generic-api-key`.
- **The auto-mode classifier refuses a push that edits a scanner allowlist to clear a red check** (`CI Bypass`). It needs Harry's explicit yes. Don't route around it with the GitHub MCP or a second PR.
- **`updateConfluencePage` replaces the whole body and needs `getContentFormatGuide` first.** Read the page, keep its HTML, and send all of it.

## Closed since handover
| When (UTC) | Work | Result |
| --- | --- | --- |
| 2026-11-11 12:56 | svc deploy run 43024078471 for `2938b41` | `terraform-apply-dev` succeeded. Dev serves `dev-2938b411` on svc and gateway, both Ready; ui stays on `7628c78` (#128 touched no ui files; inferred, path filter not read). `smoke-dev` failed, which matches the known smoke-login gap (this run's log not opened). `docker-push-prod` is **waiting** at its gate: parked, not approved, not touched. The earlier parked run for `7628c78` now shows cancelled; I cancelled nothing, and the runs for `b9fa8b5` and `ccdc34f` show the same, so a newer run appears to supersede an older parked one |
| 2026-11-11 12:53 | Confluence 357007366, the #128 row | Version 6: the #128 row, and the closing line no longer says #128 runs on dev |
| 2026-11-11 12:52 | #128 debug MCP | Merged as a merge commit, `2938b41`, 12:52:13Z, after Harry said yes ("yes, happy to merge up") to the `.gitleaks.toml` allowlist. `aa6cea4` was pushed 12:46:20Z. All 32 checks passed on it, `secret_scan / gitleaks` included. PR body Evidence has the live-tested and not-tested lists, a CI section and the scoped review note. Worktree and local branch removed; the remote branch is kept. Ledger entry already existed |
| 2026-11-11 12:43 | Other owed records after #128 | Confluence 357007366 at version 5 (the #127 row, the one-parcel FGHD booking, Oliver's answers). The plan's Not verified section brought up to date; its evidence already had the re-pack. The ledger already had #127 and #128. `wp signoff` not run, as two-parcel FedEx is still open |
| 2026-11-11 12:20 | Oliver's thread read | Two replies, no answer yet to the 12:00Z repro. Nothing sent from the VM |
| 2026-11-11 11:55 | #127 let a named developer call svc directly in dev | Merged 7628c78. The dev apply added one IAM member; confirmed with `gcloud run services get-iam-policy`. Prod run parked, not approved. |
| 2026-11-11 10:50 | #126 send the shipment cost | Merged b9fa8b5, on dev. Fixes the 0030 null reference. mdlb-1 (FGR) and mdlb-3 (FIGR) booked with tracking numbers; mdlb-2 re-packed as one parcel booked. |
| 2026-11-10 20:40 | #125 log Selector fault text | Merged ccdc34f, on dev. |
| 2026-11-10 20:20 | #124 goods description | Merged ec8bdc5, on dev. |
| 2026-11-10 | #116, #118–#123 per-account Selector services | Merged, on dev (migration 018, contract 5.12.0). |
