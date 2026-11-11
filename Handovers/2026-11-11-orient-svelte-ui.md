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
updated: 2026-11-11T14:11Z
---
# Handover: orient Svelte UI
**Reopened 14:11Z: Harry waived G8 ("let's tag and delete") and the write key is sorted. Retire is in progress (see In flight). Earlier text below describes the state at the G8 stop.**


## Where things stand
**Parked at gate G8.** Live on the VM at **`ef8d2c8`** (core, ui and the index watcher, deployed 2026-11-11 13:57Z from the VM's local checkout; Next, `orient-web`, is still the `64d7ef9` build because nothing it is built from changed since). The core on `:3000` serves every page from the Svelte SPA; Next on `:3001` serves no pages at all, only `/api/*` and its own dead `/` and `/today`. W-C, W-D1, W-D2, W-F, W-G, the rail and both Retire-prep changes are live, reviewed with review-panel, and ticked in the programme ledger (22 of 24 units done; Retire is the only open unit, blocked by G8).
**`origin/master` is still `af51670`: 13 commits (d6457ee..ef8d2c8) exist only on the VM** because the deploy key is read-only. Programme state: `wp programme status "orient Svelte UI"` and the newest decision-log entry in `Bifrost/orient Svelte UI/Migration State.md`.

| Unit | Delivered | Commits | State |
| --- | --- | --- | --- |
| U13 cutover | core on :3000, Next on :3001, terminal retired | 44c16ee | live |
| W-A1, W-A2, W-B, W-E | reading, doc and editor, delivery, prod pages | up to 0cab68a | live |
| W-C | PR review + CI logs | 288513d..9ed53e3 | live, done |
| W-D1 | work, plans, programmes | 1db80dc..c5ddeb7 | live, done |
| W-D2 | systems, people, customers, skills, diagrams | 585d9e9..71b5013 | live, done |
| W-F | meetings, recordings, Slack, haude | f2a58f2..af51670 | live, done |
| W-G | history, usage, analytics, focus, puzzles | 6ea2c81..d486509 (+ 806a824) | live, done; its 5 review findings fixed |
| Rail unit | SPA sidebar statuses + record/pause/stop + focus controls | 47b5412, fixes e47f4c9 | live, reviewed |
| Retire prep (a) | `POST /api/reindex` served by the core, rebuild in a child process | 6564455, e656208, ef8d2c8 | live, reviewed, verified live |
| Retire prep (b) | PR review draft starts through `headless.ts` in its own scope | b61d565, e5edcff, a8c1ec5 | live, reviewed; a real `claude` draft not yet run |
| Test and gate fixes | manifest/adopt tests machine-independent, diagram parity skip | fa069be, 64d7ef9 | live |
| Retire | remove Next, React, orient-web | | **blocked by G8** (a week on the full Svelte UI; Harry ticks it) |

## In flight
| Work | State | To close it |
| --- | --- | --- |
| **Retire (Next, React, orient-web removed)** | **14:11Z: 3 sonnet builders running** on disjoint files: A = delete `app/`, `src/components`, React tests, deps/config (moving `app/globals.css` to `ui/src/globals.css` first: the SPA's stylesheet imports it); B = core proxy and `ORIENT_NEXT_URL` out, unserved paths answer the SPA's 404 or 404 JSON under `/api`, SPA routing helpers and their tests; C = deploy scripts, `install-units.sh` (stops, disables, removes `orient-web`), units, README/INSTALL/Retire.md. I write the `CLAUDE.md` rewrite myself. Tag `next-ui-final` (ef8d2c8) is pushed. | integrate → `pnpm install --frozen-lockfile` (prunes node_modules) → full gates on a quiet host → review-panel on the non-deletion diff → `pnpm deploy:all` at one named sha → `install-units.sh` stops orient-web → drive pages → `rm -rf .next-prod .next-prod.bak .next-bench` a day later |

## Waiting on Harry
In order of importance, each with my recommendation.
1. ~~A write-enabled deploy key~~ **Done 14:11Z** (Harry re-added it with write access): `origin/master` is `ef8d2c8` and the tag `next-ui-final` is pushed. Pushes from the VM work now; push Retire after it is deployed.
2. ~~Gate G8~~ **Waived by Harry on 2026-11-11 ("trusting my gut")**, recorded in Migration State. Retire is running.
3. **Run one real PR review draft** (open any PR in orient and use its draft review) and confirm it completes. The new spawn path was exercised through the real `systemd-run` scope with a fake claude and by unit tests, but not with the real `claude` (it costs a sonnet run). If it fails, the draft shows the cause now (`claude not found at …` or `Could not start Claude: …`); the binary is `ORIENT_CLAUDE_BIN ?? ~/.local/bin/claude`, which exists on the VM.
4. **Deploy mid-draft (decision; recommendation: accept).** Since b61d565 a PR review draft runs in its own systemd scope, so `deploy:all` no longer refuses while one runs, as intended. The cost: a deploy or restart mid-draft loses that draft (its record shows "interrupted"), the `claude` process runs on unattended until it ends (nothing times it out), a Retry starts a second billed run, and the run dir (it holds the PR's diff, 0700 under `~/.local/state/orient/review-runs/`) stays until the next draft's one-hour sweep. A fuller fix is a pid file beside the run dir so the next draft adopts or stops the orphan. Not built.
5. **Scribe Go source changed, not built or deployed** (a8c1ec5, the withheld-credentials list gains `DATADOG_API_KEY` and `DATADOG_APP_KEY`). `make install` in `scribe/` applies it; the running scribe binary is unchanged. Recommendation: build it at the next scribe change, no hurry (the list is a second line of defence).
6. **`orient-writers/skills/explain/diagram-rules.mjs` is not tracked in orient-writers** (the laptop copy is probably untracked there), so `tests/unit/diagram-presets.test.ts` now skips on the VM instead of failing. Recommendation: commit the file in orient-writers if it belongs there. I did not touch that repo (it holds your uncommitted work).
7. **Optional: the VM's Playwright browser.** playwright-core 1.65 wants `chromium_headless_shell-1254`; this host has 1148. The three browser UI test files ran through a symlink shim to `/usr/bin/chromium` (see Gotchas). `pnpm exec playwright-core install chromium-headless-shell` would make them work unaided (a download, so your call).
8. **Low priority, leave unless you disagree:** (a) the rail offers pause/stop for any row reading `status: recording`, including a read-only one (another machine's, not adopted), where scribe answers 409 and the error shows; that state needs a third un-adopted machine and the old Next rail behaved the same. (b) The Systems tab links each system (`ecm`, `fuse`, `ilg-platform`, `carrier-integrations`) to `/service/<name>`, which answers "No service called …" for a system with no service entity; the old Next page did the same through the same `serviceOverview()`. (c) The rebuild child is not tied to the core's lifetime: under systemd the cgroup stop kills it; a side-port core killed by pid can leave an orphan (Gotchas).
9. **`gh` on the VM is logged out** (its token is invalid). Nothing here needed it (orient has no PRs).

## Next up
Items 1 to 6 of the laptop's list are done (see Closed since handover). What is left:

7. **Stop at gate G8: a week on the full Svelte UI. G8 blocks Retire** (Migration State `## Gates`). Do not delete
   Next, React or `orient-web` until Harry ticks G8. When he does, Retire works from `docs/waves/Retire.md`:
   - delete Next, React and `orient-web`;
   - drop the proxy;
   - rewrite the CLAUDE.md invariants;
   - review with review-panel and deploy;
   - stop `orient-web` (install-units).
   Remove `.next-prod*` and `.next-bench` only a day after that.

What Retire should know from this session (add to `docs/waves/Retire.md` when it starts):
- `POST /api/reindex` is the core's (`legacy.ts`, over `src/ops/reindex.ts` and `src/core/reindex-child.ts`, `scripts/reindex-run.ts`). `app/api/reindex/route.ts` and the React palette's `fetch` (`src/components/CommandPalette.tsx`) die with Next; `src/ops/reindex.ts` stays (the child script calls it).
- `tests/unit/core-proxy.test.ts` uses `/api/tmux/paste` as its stand-in for a Next-only route; deleting `app/api/tmux` means it needs another, or the proxy tests go with the proxy.
- The review draft's run dir logic lives in `src/adapters/claude-review.ts`; `runToolLess` (focus suggest and ideate, meeting prep, recording ask) still spawns a piped child in the service's cgroup: short runs, same fix if wanted.
- The browser tour driver and its notes are in the Gotchas below; rerun it (with Next gone, every non-SPA path must be the SPA's 404 or 404 JSON under `/api`).

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
- **Stopping a side-port core mid-reindex:** the rebuild child is not tied to the core's lifetime. Under systemd the cgroup stop kills it; for a `pnpm core` side port, stop it with Ctrl-C (the child shares the process group) or check `pgrep -f reindex-run`; otherwise an orphan can race the next rebuild on `index.sqlite.rebuild.tmp`.
- **Run `pnpm test` on a quiet host.** At host load above ~15 (22 cores; a full run itself drives load to ~28) 4–8 timing-sensitive UI tests fail (`focus-page`, `slack`, `today`, `usage`, `sprint`, `meetings`) and pass in isolation and on a re-run at load ~2. Do not run gates back to back with builds; wait for `cat /proc/loadavg` to fall below ~3.
- **Measure a freeze in the real process, not a bare script.** `monitorEventLoopDelay` in a bare tsx script said 1.7 s; the real core, polled over HTTP, froze for ~34 s. The recipe is in the scratchpad (`side-core-reindex.sh`: the real core on side port 3037 against a scratch vault clone, `git clone --no-hardlinks ~/Documents/obsidian <dir>` because /tmp is another filesystem, a poll loop on `/api/v1/usage/live`, `--cpu-prof` via `node --import tsx`).
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
| 2026-11-11T14:04Z | DM to Harry | sent through the slack-bot skill (Bifrost Support Bot; `auth.test` ok on this host; Harry's user id from his own Slack profile; DM channel already open): what is live, what is left, what waits on him |
| 2026-11-11T14:02Z | Final browser tour and palette Reindex on ef8d2c8 | 60 page loads, non-GET aborted: all pages 200 from the SPA with data; the only fails are `/service/<system>` (known) and `/usage` and `/pr/...` showing their cold-load state right after the restart, both full within ~1 s on a recheck. The SPA palette's "Reindex the vault" clicked in a real browser: "Indexed 1388 documents." after 38 s, one POST with `origin`, `x-orient`, `content-type`, no console errors |
| 2026-11-11T13:57Z | **Deploy of the reindex fix at ef8d2c8** | live (13:57:11–13:57:26Z; core, ui, index record ef8d2c8; `deploy:all` skipped the Next rebuild because nothing Next is built from changed, so `web` stays 64d7ef9). Gates: typecheck clean, `ui:check` 0/0, `ui:build` clean, lint at baseline, `pnpm test` 386 files passed / 1 skipped on a quiet host. **Live proof:** during one real 37 s rebuild, 131 polls of the core, slowest 0.34 s, none over 1 s (the freeze had been 4 polls and a 20 s timeout); 403/403/403/421 refusals as before; a second call inside 30 s answered from the throttle in 0.5 s |
| 2026-11-11T13:50Z | review-panel on the child-process reindex (ef8d2c8) | security: no findings. backend: one medium, an orphaned rebuild child can race a new core's rebuild when a core is signalled by pid outside systemd (not reachable under the unit's cgroup stop); left, in Gotchas and Waiting on Harry 8c |
| 2026-11-11T13:38Z | **Incident (mine): the in-core reindex froze the core** | at 64d7ef9 the first live Reindex took 36 s and requests to the core timed out at 20 s. I had accepted the in-core rebuild after a bare-script loop-lag measurement (worst stall 1.7 s), which was misleading. Replicated on a side-port core with scratch data (twice) and profiled (`--cpu-prof` via `node --import tsx`: the loop never idle for 33 s). Window: 13:36:26Z to 13:57:26Z, one palette Reindex by me, none by Harry that I know of. Fixed by ef8d2c8 |
| 2026-11-11T13:36Z | **Deploy of the Retire-prep changes at 64d7ef9** | live (deploy 13:35:52–13:36:26Z; core, ui, index, web all record 64d7ef9; services active). Gates were green on a quiet host: typecheck, `ui:check`, `ui:build`, lint at baseline, `pnpm test` 384 files passed / 1 skipped. Before it: Next check build passed (BUILD_ID 8IgHlnuiab_OE4kHuhHRJ), run gates OK, and the review draft's new path was exercised through the real `systemd-run` scope with a fake claude (ok, its dir removed, an orphan from a crashed attempt kept as designed). **Not yet exercised: a real `claude` draft** (cost); the first real draft after this deploy is the proof. Live check of `POST /api/reindex`: 403 without headers, 403 with Origin but no `X-Orient`, 403 foreign Origin, 421 bad Host, 200 with the page's headers (1,388 docs in 36 s), second call within 30 s answered from the throttle in 0.6 s. **But the rebuild froze the core: see In flight** |
| 2026-11-11T13:25Z | Retire-prep review (backend, security, tests) and fixes | review-panel on 6564455 + b61d565: fixed e656208 (settle before answering, 30 s throttle, React palette sends the write headers, five test gaps), e5edcff (named missing-claude error, cause kept, sweep and 0700-dir tests, CLAUDE.md and Retire.md lines), a8c1ec5 (`DATADOG_API_KEY`/`DATADOG_APP_KEY` withheld), 64d7ef9 (a type error in a test fixture). Left on purpose: the orphan-after-restart behaviour (Waiting on Harry) |
| 2026-11-11T13:15Z | Programme ticks and decision log | W-C, W-D1, W-D2, W-F, W-G ticked done with their commit ranges (`wp programme tick`); decision-log entry added to Migration State. `wp programme status` says "next: Retire", which is gate-blind: G8 still blocks it |
| 2026-11-11T13:12Z | Browser tour of the live pages | 60 page loads in headless Chromium against :3000 with every non-GET aborted: all moved pages 200 from the SPA with data, no Next bundle, no console errors after triage; detail pages (plan, programme, person, meeting, recording, history, PR, Jira, doc, customer, ticket) load; `/monitors`→`/health`, `/tools`→`/skills`, `/team`→`/sprint` are 308 and land on 200 SPA pages; the rail draws rec/focus controls and `/api/v1/nav-status` answers; a link to a path the SPA doesn't own is a full page load. Seen and left: `/service/<system>` is 404 for a system with no service entity (ecm, fuse, ilg-platform, carrier-integrations), linked from the Systems tab, same `serviceOverview()` as the old Next page. The page-view beacon and every other write were blocked, so nothing was written |
| 2026-11-11T13:01Z | **Deploy of C, D1, D2, F, G and the rail at fa069be** | live. Next check build passed first (`.next-check`, BUILD_ID V24Hq5Mvc3FkdsPL6J4ji, removed, tsconfig.json restored); `gate_no_runs` OK for orient-web and orient-core; `pnpm deploy:all` 13:00:57–13:01:32Z; core down ~3 s at its restart (13:01:07–13:01:10, 0 restarts after); all five deployed parts record fa069be; `.next-prod.bak` untouched and not needed |
| 2026-11-11T13:01Z | Gate cleanup | **done**, fa069be: five manifest/adopt tests assumed the machine is the laptop (the vault config names `laptop` as the only manifest writer and this host id is `vm`), so they now start from an empty `XDG_CONFIG_HOME`; `diagram-presets.test.ts` imported `orient-writers/skills/explain/diagram-rules.mjs`, which is not tracked there, and now skips when it is absent |
| 2026-11-11T13:00Z | Rail review (frontend + security) and its fixes | **done**, local only: e47f4c9. security: recording id now `encodeURIComponent`'d in stop/pause/ignore paths; frontend: a write waits for the rail's read-back, `aria-disabled` instead of `disabled`, focus moves to Pause after rec/start, errors are `role=alert` and clear on a state change, the 250 ms tick has release tests. Residual: `Query.refetch()` coalesces with an in-flight fetch, so the read-back await can resolve one request early (a one-request window; fixing needs `refetch()` to return the follow-up's promise) |
| 2026-11-11T12:57Z | W-G review fixes (5 findings) | **done**, local only, not pushed: d6457ee (history parse cache + giant-turn clip), 082af34 (focus-watch: overdue settle on look, backoff, reopen watchers), d486509 (usage watcher gated on a /usage read, mem/cpu out of the fingerprint; Space on the focus page only on the timer tab), 806a824 (stale doc comment). Deviation from the brief, correct: the usage page needs no 60 s interval of its own, because `Query.start()` already polls every 60 s while the tab is visible. Consequence: cpu/mem in the session list refresh every 60 s, not 5 s |
| 2026-11-11T12:39Z | Resume on the VM | session 8584435d took over; master ff'd to af51670 (clean tree, deployed is still 0cab68a); `gh` on the VM is logged out (token invalid), so no `gh pr`/`gh api` here; pushes go by the deploy key |
| 2026-11-11T12:33Z | W-F review fixes (6 items) | pushed: ed2fa5a, 2f83b90, af51670; full suite flaky only under load |
| 2026-11-11T12:30Z | Rail unit (SPA sidebar statuses and controls) | built and pushed, 47b5412; review owed (Next up 2b) |
| 2026-11-11T12:2xZ | W-G backend/frontend review | 5 findings, written into In flight; security review clean |
