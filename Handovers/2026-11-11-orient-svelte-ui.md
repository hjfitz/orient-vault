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
updated: 2026-11-11T13:52Z
---
# Handover: orient Svelte UI

## Where things stand
Live on the VM at **`fa069be`** (deployed 2026-11-11 13:01Z from the VM's local checkout): core on `:3000` serves the Svelte SPA for every page, and Next on `:3001` now serves no pages at all (only `/api/*` and its own dead `/` and `/today`). W-C, W-D1, W-D2, W-F, W-G and the rail are live and ticked done in the programme ledger (22 of 24 units done; Retire is the only open unit and gate G8 blocks it).
`origin/master` is still at `af51670`: **everything after it is local to the VM** (the deploy key is read-only); see Waiting on Harry for the shas. Programme state: `wp programme status "orient Svelte UI"` and the newest decision-log entry in `Bifrost/orient Svelte UI/Migration State.md`.

| Unit | Delivered | Commits | State |
| --- | --- | --- | --- |
| U13 cutover | core on :3000, Next on :3001, terminal retired | 44c16ee | live |
| W-A1, W-A2, W-B, W-E | reading, doc and editor, delivery, prod pages | up to 0cab68a | live |
| W-C | PR review + CI logs | 288513d..9ed53e3 | live (fa069be), done |
| W-D1 | work, plans, programmes | 1db80dc..c5ddeb7 | live, done |
| W-D2 | systems, people, customers, skills, diagrams | 585d9e9..71b5013 | live, done |
| W-F | meetings, recordings, Slack, haude | f2a58f2..af51670 | live, done |
| W-G | history, usage, analytics, focus, puzzles | 6ea2c81..d486509 (+ 806a824) | live, done; all 5 review findings fixed |
| Rail unit | SPA sidebar statuses + record/pause/stop + focus controls | 47b5412, review fixes e47f4c9 | live, reviewed |
| Retire prep | `/api/reindex` in the core; review draft onto headless.ts | in progress | not deployed |
| Retire | remove Next, React, orient-web | | blocked by G8 (a week on the full Svelte UI, Harry ticks it) |

## In flight
| Work | State | To close it |
| --- | --- | --- |
| Retire prep review fixes | **13:50Z: 2 sonnet builders running.** review-panel (backend, security, tests) on 6564455 + b61d565 found, all verified: (reindex) the frozen React palette's bare `fetch` is refused by the core's write guard (fix: send `X-Orient` + JSON); `void invalidate` should be `await kernel.settle(['index'])`; a 30 s throttle after a successful rebuild (36 s of CPU in the front door); five test gaps (failure status, Next-vs-core parity, token branch not pinned, rebuild args, vacuous mode test). (draft) opaque failure when claude is not at `~/.local/bin/claude` (now named, like slack-runs); sweep-throws and mode test gaps; CLAUDE.md/Retire.md lines. Already fixed and committed: **a8c1ec5** withholds `DATADOG_API_KEY`/`DATADOG_APP_KEY` (orient's real names; the lists only had `DD_*`) in `headless.ts` and the scribe copy (Go source changed and tested, **not deployed**: the scribe binary is unchanged). | builders report → check shas → `pnpm typecheck`, `pnpm test`, `ui:check`, `ui:build`, lint → deploy |
| Deploy of the two prep changes | not started | one named sha, `pnpm deploy:all` (Next changes, so a `deploy:web` rebuild: prove it in `.next-check` first), then drive `/` palette reindex (a POST: only with Harry's data in mind, see Gotchas) |

## Waiting on Harry
- **Deploy mid-draft (decision, recommendation: accept).** Since b61d565 a PR review draft runs in its own systemd scope, so `deploy:all` no longer refuses while one runs, as intended. The cost: a deploy or restart mid-draft loses that draft (its record shows "interrupted"), the `claude` process runs on unattended until it ends (nothing times it out), a Retry starts a second billed run, and the run dir (holding the PR's diff, 0700 under `~/.local/state/orient/review-runs/`) stays until the next draft's hour-old sweep. A fuller fix is a pid file beside the run dir so the next `startDraft` adopts or stops the orphan. I did not build it.
- **Scribe Go source changed, not built or deployed** (a8c1ec5, the withheld-credentials list). `make install` in `scribe/` would apply it; the running binary is unchanged and the change only matters once it is rebuilt.
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
- **Browser tests on the VM:** playwright-core 1.65 wants `chromium_headless_shell-1254`, this host has 1148 and no download was made. `ui/tests/{keymap,overlays,routing}.test.ts` ran with `PLAYWRIGHT_BROWSERS_PATH=$HOME/.cache/orient-pw` (a symlinked `chromium_headless_shell-1254/chrome-headless-shell-linux64/chrome-headless-shell` → `/usr/bin/chromium`). Without it they fail with "Executable doesn't exist". The permanent fix is `pnpm exec playwright-core install chromium-headless-shell` (a download: Harry's call).
- **Driving live pages:** `chromium.launch({executablePath:'/usr/bin/chromium', args:['--no-sandbox']})` works with playwright-core; abort every non-GET (`page.route`) so the page-view beacon and writes cannot fire; allow only `POST /api/v1/diagrams/preview` and `/api/v1/puzzles/next` (pure loads) or `/diagrams` and `/puzzles` show errors. The first load of `/usage` and `/pr/...` right after a restart is thin (cold scans): wait and reload.
- **zsh on this host:** `set -- $var` does not word-split and `PIPESTATUS` is `pipestatus`; run scripts that need bash with `bash -c`. `gate_no_runs` sourced in zsh prints a `runs_in` noise line; run it under bash.
- **`gh` on the VM is logged out** (token invalid): no `gh pr`/`gh api` here. Not needed: orient has no PRs, and pushes use the deploy key.
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
| 2026-11-11T13:00Z | Rail review (frontend + security) and its fixes | **done**, local only: e47f4c9. security: recording id now `encodeURIComponent`'d in stop/pause/ignore paths; frontend: a write waits for the rail's read-back, `aria-disabled` instead of `disabled`, focus moves to Pause after rec/start, errors are `role=alert` and clear on a state change, the 250 ms tick has release tests. Residual: `Query.refetch()` coalesces with an in-flight fetch, so the read-back await can resolve one request early (a one-request window; fixing needs `refetch()` to return the follow-up's promise) |
| 2026-11-11T13:15Z | Programme ticks and decision log | W-C, W-D1, W-D2, W-F, W-G ticked done with their commit ranges (`wp programme tick`); decision-log entry added to Migration State. `wp programme status` says "next: Retire", which is gate-blind: G8 still blocks it |
| 2026-11-11T13:12Z | Browser tour of the live pages | 60 page loads in headless Chromium against :3000 with every non-GET aborted: all moved pages 200 from the SPA with data, no Next bundle, no console errors after triage; detail pages (plan, programme, person, meeting, recording, history, PR, Jira, doc, customer, ticket) load; `/monitors`→`/health`, `/tools`→`/skills`, `/team`→`/sprint` are 308 and land on 200 SPA pages; the rail draws rec/focus controls and `/api/v1/nav-status` answers; a link to a path the SPA doesn't own is a full page load. Seen and left: `/service/<system>` is 404 for a system with no service entity (ecm, fuse, ilg-platform, carrier-integrations), linked from the Systems tab, same `serviceOverview()` as the old Next page. The page-view beacon and every other write were blocked, so nothing was written |
| 2026-11-11T13:01Z | **Deploy of C, D1, D2, F, G and the rail at fa069be** | live. Next check build passed first (`.next-check`, BUILD_ID V24Hq5Mvc3FkdsPL6J4ji, removed, tsconfig.json restored); `gate_no_runs` OK for orient-web and orient-core; `pnpm deploy:all` 13:00:57–13:01:32Z; core down ~3 s at its restart (13:01:07–13:01:10, 0 restarts after); all five deployed parts record fa069be; `.next-prod.bak` untouched and not needed |
| 2026-11-11T13:01Z | Gate cleanup | **done**, fa069be: five manifest/adopt tests assumed the machine is the laptop (the vault config names `laptop` as the only manifest writer and this host id is `vm`), so they now start from an empty `XDG_CONFIG_HOME`; `diagram-presets.test.ts` imported `orient-writers/skills/explain/diagram-rules.mjs`, which is not tracked there, and now skips when it is absent |
| 2026-11-11T12:57Z | W-G review fixes (5 findings) | **done**, local only, not pushed: d6457ee (history parse cache + giant-turn clip), 082af34 (focus-watch: overdue settle on look, backoff, reopen watchers), d486509 (usage watcher gated on a /usage read, mem/cpu out of the fingerprint; Space on the focus page only on the timer tab), 806a824 (stale doc comment). Deviation from the brief, correct: the usage page needs no 60 s interval of its own, because `Query.start()` already polls every 60 s while the tab is visible. Consequence: cpu/mem in the session list refresh every 60 s, not 5 s |
| 2026-11-11T12:39Z | Resume on the VM | session 8584435d took over; master ff'd to af51670 (clean tree, deployed is still 0cab68a); `gh` on the VM is logged out (token invalid), so no `gh pr`/`gh api` here; pushes go by the deploy key |
| 2026-11-11T12:33Z | W-F review fixes (6 items) | pushed: ed2fa5a, 2f83b90, af51670; full suite flaky only under load |
