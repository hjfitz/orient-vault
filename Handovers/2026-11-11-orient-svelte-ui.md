---
tags: [handover]
status: open
workstream: orient Svelte UI — finish the page waves, deploy them, then Retire (remove Next/React)
programme: orient Svelte UI
repo: hjfitz/orient
from: laptop
to: hjf.shell.platform.ilg.software
session_id: 0fb571d0-d903-483b-9e8b-1198b51d571f
resumed_by: ""
updated: 2026-11-11T12:36Z
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
| W-G review fixes | **review done; fixes not started, yours** | 1. **[high]** `src/core/modules/usage/index.ts:82-100`: the usage watcher runs for any open tab, and its fingerprint includes `cpuPct`/`memMb`. So a live session republishes `usage:live` every 5 s and reruns the eager `spendOp` with nobody on /usage. Drop cpu/mem from the fingerprint and gate the watcher on a /usage read in the last ~2 min. 2. **[med]** `focus-watch.ts:59-89`: the phase-end timer is a monotonic `setTimeout`, so after a suspend the block is logged ~20 min late. In `look()`, settle when `endsAt() <= now()`. 3. **[med]** `src/ops/history.ts:78-82` + `domain/history.ts:173-178`: every 60-turn page re-parses and redacts the whole transcript on the event loop. Cache parsed turns per file mtime (bounded, e.g. 4 files), or slice before redacting. Clip giant turn text in the DTO. 4. **[med]** `routes/focus/+page.svelte:38-41`: Space starts the timer on `?tab=breathe`; in Next it did nothing there. Enter the scope only when `tab === 'timer'`. 5. **[low]** `focus-watch.ts:69-77`: a persistent settle error makes a once-a-second publish loop (back off, cap at 60 s). A watcher closed by an error or a missing dir at boot is never reopened (reopen it on the next poll). Security review: clean. |

## Waiting on Harry
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
| 2026-11-11T12:33Z | W-F review fixes (6 items) | pushed: ed2fa5a, 2f83b90, af51670; full suite flaky only under load |
