---
tags: [handover]
status: closed
workstream: orient Svelte UI — finish the page waves, deploy them, then Retire (remove Next/React): done
programme: orient Svelte UI
repo: hjfitz/orient
from: laptop
to: hjf.shell.platform.ilg.software
session_id: 0fb571d0-d903-483b-9e8b-1198b51d571f
resumed_by: 8584435d-36a9-464d-bc60-e21c842cfe59
updated: 2026-11-11T15:07Z
---
# Handover: orient Svelte UI
**Closed 15:07Z: the workstream is done.** The page waves, the rail, both Retire-prep changes and Retire itself are deployed (live at `6445727`) and pushed; the programme is complete (23 of 24 units done, the terminal dropped). What is left is Harry's, below.


## Where things stand
**Done.** Live on the VM at **`6445727`** (core, ui and the index watcher, deployed 2026-11-11 15:04Z) and `origin/master` is the same commit. The core on `:3000` is the only web process: it serves the Svelte SPA, `/api/v1/*` and desk's and scribe's routes. **Next, React and `orient-web` are gone** (the unit stopped, disabled and removed at 15:05Z; `:3001` is closed). The last commit that has them is the tag **`next-ui-final`** (`ef8d2c8`, pushed): `git checkout next-ui-final` brings the Next UI back. `.next-prod`, `.next-prod.bak` and `.next-bench` are still on the VM's disk until the cleanup below.
Programme: `wp programme status "orient Svelte UI"` (23 done, U10 dropped) and the newest decision-log entry in `Bifrost/orient Svelte UI/Migration State.md`.

| Unit | Delivered | Commits | State |
| --- | --- | --- | --- |
| U13 cutover | core on :3000, terminal retired | 44c16ee | live |
| W-A1 … W-G | every page moved to the SPA | up to d486509 | live, done |
| Rail unit | SPA sidebar statuses and controls | 47b5412, e47f4c9 | live, reviewed |
| Retire prep | core `/api/reindex` (rebuild in a child process); review draft through `headless.ts` | 6564455 … ef8d2c8 | live, reviewed |
| **Retire** | Next, React, `orient-web`, the proxy and the terminal glue removed; CLAUDE.md rewritten | 29b560e … 6445727 | **live, done, pushed** |

## In flight
Nothing. No agent of this session is running.

## Waiting on Harry
In order of importance, each with my recommendation.
1. **Send the note to Darren.** It is saved as a draft in your Slack DM with him (the answer to his "LoC before and after?"; voice skill, terse register; I can only draft). Frontend only: 39.4k non-blank lines of React/Next before, 33k of Svelte now, about 16% less, for about the same pages and components. If he pushes back: the whole UI-serving stack is about 18% bigger (41.6k to 49.1k) because the SPA needs the core service, ops and API shapes behind it.
2. **Tomorrow (about 15:05 UTC, a day after the deploy): delete the old Next build.** On the VM: `rm -rf ~/projects/orient/.next-prod ~/projects/orient/.next-prod.bak ~/projects/orient/.next-bench`. That removes the quick rollback (`.next-prod.bak`); after it, the way back is the tag `next-ui-final`. On any other checkout that ever ran Next (the laptop): `rm -f next-env.d.ts`, and `git pull` there first: **the laptop's `master` is behind `origin/master` by everything in this handover**, so pull before deploying or editing anything.
3. **Run one real PR review draft** (open a PR in orient and use its draft review) and confirm it completes. The new spawn path (own systemd scope) was exercised with a fake claude through the real `systemd-run`, and by tests, but not with the real `claude` (it costs a sonnet run). If it fails, the draft now says why (`claude not found at …` or `Could not start Claude: …`).
4. **Decision (recommendation: accept):** a deploy mid-draft now loses that draft, the `claude` process runs on unattended until it ends, a Retry starts a second billed run, and the run dir (it holds the PR's diff, 0700 under `~/.local/state/orient/review-runs/`) stays until the next draft's one-hour sweep. A fuller fix is a pid file beside the run dir. Not built.
5. **Delete the stale terminal secret** (I was blocked from doing it): `rm ~/.local/state/orient/pty-secret` (64 bytes, 0600, written 2026-11-03 for the retired terminal; nothing reads it; the bench setup script mints its own).
6. **Dead code I left because it needs your call** (recommendation: delete it all in one cleanup; it is the prompt-tool feature you dropped on 2026-11-10): `src/domain/tools.ts` (about 500 lines; only `toContextDoc` is used, by `meeting.ts`) with `src/prompt/fields.ts` and `src/edit/templates/**/*.mdx`, `src/adapters/cust.ts` (never imported), `Skill.invocation` in `src/domain/skills.ts` (set, never read), and `knownPages()` in `src/domain/page-use-view.ts`, which still scans a gone `app/` directory.
7. **Scribe Go source changed, not built or deployed** (a8c1ec5: the withheld-credentials list gains `DATADOG_API_KEY` and `DATADOG_APP_KEY`). `make install` in `scribe/` applies it; the running binary is unchanged. Recommendation: build it at the next scribe change.
8. **`orient-writers/skills/explain/diagram-rules.mjs` is not tracked in orient-writers**, so `tests/unit/diagram-presets.test.ts` skips on the VM. Recommendation: commit it there if it belongs. I did not touch that repo (it has your uncommitted work).
9. **Optional:** the VM's Playwright browser (playwright-core wants `chromium_headless_shell-1254`, the host has 1148; the browser UI tests ran through a symlink shim to `/usr/bin/chromium`, see Gotchas). `pnpm exec playwright-core install chromium-headless-shell` fixes it properly (a download, your call).
10. **Low priority, leave unless you disagree:** (a) the rail offers pause/stop for a read-only `recording` row (needs a third un-adopted machine; the old rail did the same). (b) The Systems tab links each system (`ecm`, `fuse`, `ilg-platform`, `carrier-integrations`) to `/service/<name>`, which answers "No service called …"; the old page did the same. (c) A rebuild child can be orphaned if a side-port core is killed by pid (under systemd it dies with the unit). (d) `/today/x` and the bare parents of `[param]` routes (`/doc`, `/jira`, `/pr`) answer 200 with the SPA's not-found page instead of a 404 status. (e) SvelteKit leaves its navigating flag stuck when a cross-origin link's unload prompt is cancelled (its own behaviour; the same-origin case in the editor is fixed). (f) `tests/integration/ticket-run-cycle.test.ts` failed once on a quiet host and passed alone and on a rerun: a timing flake (stubbed claude must still be running when the second start is tried). (g) `gh` on the VM is logged out; nothing here needed it.

## Next up
Nothing is queued for the programme: it is complete. Owed follow-ups are in Waiting on Harry (the day-later cleanup, the real review draft, the dead-code cleanup). If the Svelte UI grows a new page: `docs/waves/README.md`'s "Mistakes … caught" list still applies, and `CLAUDE.md` describes the guard rails.

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
  end with the model's own `Co-Authored-By` line (the VM session used `Claude Sonnet 5.5`).
- **Deploying:** you are on the production host. `pnpm deploy:all` (install if the lockfile changed, `deploy:ui`, `deploy:core`, restart orient-index) deploys whatever is checked out, so deploy a named sha, never a half-landed change. Run `bash -c '. scripts/deploy-lib.sh; gate_no_runs orient-core.service'` first (the scripts are bash; sourced in zsh the gate prints a harmless error line).
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
- **orient checkout:** `~/projects/orient` at `6445727`, equal to `origin/master`; its deploy key now has write access.
- **tmux:** session `main`.
- **Services:** orient-core, orient-index, orient-scribe (role server) and orient-vault-sync (+ timer) run here as user units. `orient-web` was removed on 2026-11-11. `install-units.sh` here is run as `SCRIBE=server HEADLESS=1 scripts/install-units.sh` (no desk on the VM).
- Agents testing on the VM must use side ports (3031–3044) and scratch state, exactly as on the laptop.

## Gotchas
- **A long-lived reader keeps the old index after a full rebuild.** A Claude session's orient MCP server holds `index.sqlite` open; a rebuild (palette Reindex, `pnpm index:build`) renames a new file in, and that session then reports "idx STALE: watcher down" from the unlinked old file. The real watcher was healthy (`pnpm index:status`). Restart the session or the MCP server to see the new index.
- **Stopping a side-port core mid-reindex:** the rebuild child is not tied to the core's lifetime. Under systemd the cgroup stop kills it; for a `pnpm core` side port, stop it with Ctrl-C (the child shares the process group) or check `pgrep -f reindex-run`; otherwise an orphan can race the next rebuild on `index.sqlite.rebuild.tmp`.
- **Run `pnpm test` on a quiet host.** At host load above ~15 (22 cores; a full run itself drives load to ~28) 4–8 timing-sensitive UI tests fail (`focus-page`, `slack`, `today`, `usage`, `sprint`, `meetings`) and pass in isolation and on a re-run at load ~2. Do not run gates back to back with builds; wait for `cat /proc/loadavg` to fall below ~3.
- **Measure a freeze in the real process, not a bare script.** `monitorEventLoopDelay` in a bare tsx script said 1.7 s; the real core, polled over HTTP, froze for ~34 s. The recipe is in the scratchpad (`side-core-reindex.sh`: the real core on side port 3037 against a scratch vault clone, `git clone --no-hardlinks ~/Documents/obsidian <dir>` because /tmp is another filesystem, a poll loop on `/api/v1/usage/live`, `--cpu-prof` via `node --import tsx`).
- **Browser tests on the VM:** playwright-core 1.65 wants `chromium_headless_shell-1254`, this host has 1148 and no download was made. `ui/tests/{keymap,overlays,routing}.test.ts` ran with `PLAYWRIGHT_BROWSERS_PATH=$HOME/.cache/orient-pw` (a symlinked `chromium_headless_shell-1254/chrome-headless-shell-linux64/chrome-headless-shell` → `/usr/bin/chromium`). Without it they fail with "Executable doesn't exist". The permanent fix is `pnpm exec playwright-core install chromium-headless-shell` (a download: Harry's call).
- **Driving live pages:** `chromium.launch({executablePath:'/usr/bin/chromium', args:['--no-sandbox']})` works with playwright-core; abort every non-GET (`page.route`) so the page-view beacon and writes cannot fire; allow only `POST /api/v1/diagrams/preview` and `/api/v1/puzzles/next` (pure loads) or `/diagrams` and `/puzzles` show errors. The first load of `/usage` and `/pr/...` right after a restart is thin (cold scans): wait and reload.
- **zsh on this host:** `set -- $var` does not word-split and `PIPESTATUS` is `pipestatus`; run scripts that need bash with `bash -c`. `gate_no_runs` sourced in zsh prints a `runs_in` noise line; run it under bash.
- **`gh` on the VM is logged out** (token invalid): no `gh pr`/`gh api` here. Not needed: orient has no PRs, and pushes use the deploy key.
- **Next gotchas are history.** Typed routes, stale `.next*/types`, the check build's tsconfig edit and a failed `deploy:web` left Next down: all went with Next (read them at the tag `next-ui-final` if it ever returns).
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
| 2026-11-11T15:07Z | Handover and programme closed | `wp programme tick … Retire done` (29b560e..6445727), decision-log entry added, this record closed. A `pty-secret` removal was blocked by the permission classifier and is left to Harry (Waiting on Harry 5) |
| 2026-11-11T15:06Z | Final tour on 6445727 and push | 60 page loads, non-GET aborted: same as before (every page from the SPA; the known `/service/<system>` 404; `/usage` and the PR page show their cold state right after a restart and are full within ~1 s). `git push`: `origin/master` is 6445727; the tag `next-ui-final` is on GitHub |
| 2026-11-11T15:05Z | **orient-web removed** | `SCRIBE=server HEADLESS=1 scripts/install-units.sh`, exit 0 in under a second: "removing orient-web", "orient-web removed". Afterwards orient-web inactive, not-found, unit file gone, listeners only :3000 and :3013; core, index, scribe and the vault-sync timer kept their start times (scribe since 11-09, not restarted) |
| 2026-11-11T15:04Z | **Deploy of Retire at 6445727** | `pnpm deploy:all` 15:04:30–15:04:46Z; core, ui, index record 6445727 (the `web` record stays 64d7ef9: nothing writes it now). Pre-checks: tree clean, both run gates OK. Live: pages 200 from the SPA, `/nope` 404 (shell), `/api/nope` and `/_app/…` 404 JSON, `//api/desk` 404, legacy `/api/desk` 200, bad Host 421, an unserved write 403 without the page's headers and 404 JSON with them; the core's log line no longer says "Next behind it" |
| 2026-11-11T15:03Z | Final gates on 6445727 | typecheck (plain `tsc`), `ui:check` 0/0, `ui:build` clean, lint 47 errors (baseline: `bench/*`, `scribe/eval`), `pnpm test` 352 files passed / 1 skipped on a quiet host (one earlier run had a single timing flake in `ticket-run-cycle`, green alone and on rerun) |
| 2026-11-11T14:55Z | review-panel on Retire, fixes | backend, frontend, ops-script, security (tests lens dropped: builders mutation-checked). Security: none. Fixed: c637e8d (`//api/…` served the shell with 200), 3069dee (a dirty editor leaving for a non-SPA path cancels first: SvelteKit left its navigating flag stuck after a cancelled unload prompt, silencing the guard), 8ec671e (`install-units.sh` fails if orient-web is still active after the stop, before any `rm`), c040a5f (tsconfig excludes a stale `next-env.d.ts`), 23d6fbe + 6445727 (the history refusal text and 32 files of stale comments) |
| 2026-11-11T14:40Z | **Retire built** | 3 sonnet builders on disjoint files (A: deletions, deps, configs; B: core proxy, SPA routing, tests; C: scripts, units, docs), CLAUDE.md by me, then a cleanup builder (66 renderer tests ported from the deleted React tests, the deleted route tests' guards re-pinned on the core, dead modules removed). My brief was wrong once: `/doc/resolve` is the core's redirect, not an unserved path; builder B caught it. 20 commits 29b560e..6445727; 245 files changed (+837 / −18,550) before the review fixes |
| 2026-11-11T14:11Z | Write key sorted; tag pushed | Harry re-added the deploy key with write access; pushed exactly `ef8d2c8` (a fast-forward from af51670) and the tag `next-ui-final` while the Retire builders were committing locally. G8 waived by Harry ("trusting my gut") and recorded in Migration State |
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
