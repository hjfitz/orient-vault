---
tags: [handover]
status: resumed
workstream: orient Svelte UI — finish the page waves, deploy them, then Retire (remove Next/React)
programme: orient Svelte UI
repo: hjfitz/orient
from: laptop
to: hjf.shell.platform.ilg.software
session_id: 0fb571d0-d903-483b-9e8b-1198b51d571f
resumed_by: 8584435d-36a9-464d-bc60-e21c842cfe59
updated: 2026-11-11T12:58Z
---
# Handover: orient Svelte UI

## Where things stand
On the VM, orient-core on `:3000` serves the Svelte SPA and proxies the remaining pages to Next on `:3001`.
The **deployed commit is `0cab68a`**, which includes U13, W-A1, W-A2, W-B and W-E. `origin/master` is at `af51670`. W-C, W-D1 and W-D2 are built and reviewed, with their fixes in, but **not deployed**. W-F and W-G are built.
Their review fixes are in flight on the laptop (see below). Programme state: `wp programme status "orient Svelte UI"`,
and the decision log in `Bifrost/orient Svelte UI/Migration State.md`. The newest entry, "resume point", lists
every sha.

| Unit | Delivered | Commits | State |
| --- | --- | --- | --- |
| U13 cutover | core on :3000, Next on :3001, terminal retired | 44c16ee | live |
| W-A1, W-A2, W-B, W-E | reading, doc and editor, delivery, prod pages | up to 0cab68a | live |
| W-C | PR review + CI logs | 288513d, 4931a8d, 9ed53e3 | reviewed, fixes in, not deployed |
| W-D1 | work, plans, programmes | 1db80dc, a516649, c5ddeb7 | reviewed, fixes in, not deployed |
| W-D2 | systems, people, customers, skills, diagrams | 585d9e9, 71b5013 | reviewed, fixes in, not deployed |
| W-F | meetings, recordings, Slack, haude | f2a58f2..ec7b09c, fixes ed2fa5a 2f83b90 af51670 | reviewed, fixes in, not deployed |
| W-G | history, usage, analytics, focus, puzzles | 6ea2c81..ff02169 | both reviews done; 5 findings to fix (In flight) |
| Rail unit | SPA sidebar nav statuses + record/pause/stop + focus controls (`/api/v1/nav-status`) | 47b5412 | built, **not reviewed** (Next up 2b) |
| Lead fixes | write token only on `/api/desk/act` and `/api/write` (bc1ec12); `/pr` lights Pull requests (1457855) | | on master |

## In flight
No laptop agents are running any more. Every remaining item below is yours.

| Work | State | To close it |
| --- | --- | --- |
| Rail review fixes (47b5412) | **12:58Z: 1 sonnet builder running.** review-panel (frontend + security): security found one hardening gap (recording id unencoded in stop/pause/ignore paths; I fixed it in `ui/src/lib/recordings/actions.ts`, uncommitted, the builder commits it with a test); frontend found a double-send window (pending clears before the rail's read-back), focus loss on disabled buttons, an error with no `role=alert`, no test that the 250 ms tick is released. All verified by reading. | when the builder reports: check its sha, then run the full gates (Next up 3) |

## Waiting on Harry
- **Unpushed commits.** Pushes need the write-enabled key (below). Local-only so far: d6457ee 082af34 d486509 806a824 (plus the rail fixes and everything after, see the final list).
- **Low priority, no action needed unless you disagree:** the rail offers pause/stop for any row that reads `status: recording`, including a read-only one (another machine's, not adopted), where scribe answers 409 and the error shows. On this setup a read-only `recording` row needs a third, un-adopted machine, and the old Next rail behaved the same. Recommendation: leave it.
- **A write-enabled GitHub deploy key for hjfitz/orient on the VM.** The VM pushes with
  `~/.ssh/orient-deploy/orient` (`core.sshCommand`), a read-only deploy key. Add its public key again in GitHub
  (hjfitz/orient → Settings → Deploy keys) with "Allow write access", or add a new write key and point
  `core.sshCommand` at it. Until then the VM session can deploy but can't push.

## Next up
1. Pull `origin/master`. Wait until the three In-flight rows have landed, or finish them as each row says.
2. Apply the W-G backend/frontend findings (In flight row).
   2b. Review the rail unit `47b5412` with review-panel (frontend, plus security on its writes: they reuse the W-F recordings and focus write routes) and fix. Its commit message lists the Next shell files Retire deletes.
3. Clean up across waves until every gate passes, then commit:
   - `pnpm test`;
   - `pnpm typecheck`, which regenerates route types itself, so an error is never "stale types";
   - `pnpm ui:check` and `pnpm ui:build`;
   - `pnpm lint`. Known failures: `tests/unit/core-server.test.ts`, `tests/unit/core-views-failure.test.ts`,
     plus the old `bench/*` and `app/globals.css` failures.
4. **Deploy all five waves (C, D1, D2, F, G) plus the rail** at one named sha. Procedure:
   - Prove the Next build first, with no downtime:
     `rm -rf .next-prod/types && ORIENT_DIST_DIR=.next-prod pnpm exec next typegen`, then
     `ORIENT_DIST_DIR=.next-check pnpm exec next build`, then `rm -rf .next-check && git checkout -- tsconfig.json`.
   - Run `gate_no_runs` (from `. scripts/deploy-lib.sh`), then `mise exec -- pnpm deploy:all`.
   - Drive every moved page through a browser (playwright-core is in node_modules). Check:
     - each page has data and the SPA bundle;
     - no console errors;
     - a link from the SPA to a page still in Next does a full load;
     - `/monitors`, `/tools` and `/team` answer 308.
5. Mark W-C, W-D1, W-D2, W-F and W-G done (`wp programme tick … --status done --pr <range>`) and add a decision
   log entry.
6. **Retire prep, safe to land now** (both keep Next working):
   - Give `/api/reindex` a core home. The SPA palette calls it; see `docs/waves/Retire.md`.
   - Move the PR review draft's own spawn (`src/adapters/claude-review.ts`) onto `src/adapters/headless.ts`, so
     a draft never blocks `deploy:core`.
   Review with review-panel, then deploy.
7. **Stop at gate G8: a week on the full Svelte UI. G8 blocks Retire** (Migration State `## Gates`). Do not delete
   Next, React or `orient-web` until Harry ticks G8. When he does, Retire works from `docs/waves/Retire.md`:
   - delete Next, React and `orient-web`;
   - drop the proxy;
   - rewrite the CLAUDE.md invariants;
   - review with review-panel and deploy;
   - stop `orient-web` (install-units).
   Remove `.next-prod*` and `.next-bench` only a day after that.

## How work is done here
- **Rules:** repo rules are in `CLAUDE.md`. The wave playbook is `docs/waves/README.md`; follow its "Mistakes …
  caught" list.
- **Programme:** waypoint-programme skill. Advance the ledger with `wp programme tick`.
- **Reviews:** every review uses the `review-panel` skill with Sonnet panelists, at most 4, one diff per lens. The
  lead verifies each high finding by reading the code before sending fixes.
- **Delegation:** right-size agents per `/orchestrate`. Mechanical waves on sonnet, judgement on opus, at most 3
  builders at once in the shared checkout. No worktrees in orient.
- **Git:** stage explicit paths only (`git add <paths>`, then `git commit -m … -- <paths>`). Never `git add -A`,
  stash or reset others' files. Push after `git fetch -q && git status -sb | head -1` shows only "ahead". Commits
  end with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- **Deploying:** you are on the production host. `pnpm deploy:all` deploys whatever is checked out, so deploy a
  named sha (`git merge --ff-only <sha>`), never a half-landed wave.
- **Never:**
  - write to the real vault in tests (scratch vaults come from `git clone ~/Documents/obsidian <dir>`);
  - call scribe `:3013` from tests;
  - bind 0.0.0.0;
  - expose the write token or the hub token to the browser.

## On the target
Checked 2026-11-11T12:2xZ:
- **Claude:** 2.1.322, logged in (credentials present), `defaultMode: auto`.
- **Tools:** gh, git, node, jq, python3, tmux and mise. pnpm is **only via `mise exec -- pnpm`**.
- **Skills:** session-handover, waypoint-programme, review-panel; `wp.py` is present.
- **Vault:** `~/Documents/obsidian` is present.
- **orient checkout:** `~/projects/orient` at `0cab68a`; its push key is read-only, so see Waiting on Harry.
- **tmux:** session `main`.
- **Services:** orient-core, orient-web, orient-index, orient-scribe and orient-vault-sync run here as user units.
- Agents testing on the VM must use side ports (3031–3044) and scratch state, exactly as on the laptop.

## Gotchas
- **Typed routes:** Next's `typedRoutes` broke the build once pages moved. It's off now.
- **Stale generated types:** `.next*/types` validators and `link.d.ts` go stale. `pnpm typecheck` clears and
  regenerates them, and on the VM `rm -rf .next-prod/types` goes before a check build.
- **The check build edits tsconfig:** `ORIENT_DIST_DIR=.next-check next build` adds includes to `tsconfig.json`.
  Run `git checkout -- tsconfig.json` afterwards.
- **A failed `deploy:web` leaves Next down:** restore with `systemctl --user stop orient-web; rm -rf .next-prod;
  cp -a .next-prod.bak .next-prod; systemctl --user start orient-web`. `.next-prod.bak` is the pre-cutover build.
- **javascript: links:** Svelte renders `javascript:` hrefs, and React refused them. Every data link goes through
  `appHref`/`safeHref`, and the layout click guard is only a backstop.
- **Detail pages:** a `[param]` page reuses its component, so wrap its body in `{#key param}`. Otherwise an open edit
  box saves onto the next item.
- **Failures cached as success:** inside a cached loader, throw. Never fold a failure into the DTO.
- **The write token:** opens only `/api/desk/act` and `/api/write`. Tests write as the page (Origin + `X-Orient: 1`
  + JSON).
- **Headless runs:** each starts in its own `systemd-run --user --scope`, so a deploy never kills one. The deploy
  gates fail closed.

## Closed since handover
| When (UTC) | Work | Result |
| --- | --- | --- |
| 2026-11-11T12:30Z | Rail unit (SPA sidebar statuses and controls) | built and pushed, 47b5412; review owed (Next up 2b) |
| 2026-11-11T12:2xZ | W-G backend/frontend review | 5 findings, written into In flight; security review clean |
| 2026-11-11T12:57Z | W-G review fixes (5 findings) | **done**, local only, not pushed: d6457ee (history parse cache + giant-turn clip), 082af34 (focus-watch: overdue settle on look, backoff, reopen watchers), d486509 (usage watcher gated on a /usage read, mem/cpu out of the fingerprint; Space on the focus page only on the timer tab), 806a824 (stale doc comment). Deviation from the brief, correct: the usage page needs no 60 s interval of its own, because `Query.start()` already polls every 60 s while the tab is visible. Consequence: cpu/mem in the session list refresh every 60 s, not 5 s |
| 2026-11-11T12:39Z | Resume on the VM | session 8584435d took over; master ff'd to af51670 (clean tree, deployed is still 0cab68a); `gh` on the VM is logged out (token invalid), so no `gh pr`/`gh api` here; pushes go by the deploy key |
| 2026-11-11T12:33Z | W-F review fixes (6 items) | pushed: ed2fa5a, 2f83b90, af51670; full suite flaky only under load |
