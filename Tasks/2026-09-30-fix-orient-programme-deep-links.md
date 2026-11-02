---
tags: [adhoc-task]
date: 2026-09-30
tldr: "orient: fixed programme deep links; cut /today 17s stall (persisted SWR doctor cache); web now a prod systemd service; new /plans list page"
session_id: 23b5e93e-157f-4ed1-a359-8c9f7e233cc9
status: done
---
# Fix orient programme deep links and slow /today

## Outcome
1. `slugForPath` (`src/lib/doc-href.ts`): all 12 `Migration State.md` files slugged to `migration-state`; state docs now slug to their `Bifrost/<Name>/` folder.
2. `/today` blocked ~17s on `wp doctor --no-fetch` whenever the in-memory adapter cache was cold. `runJson` (`src/adapters/exec.ts`) now has opt-in `staleMaxMs`: persists raw JSON to `~/.local/state/orient/adapter-cache/`, serves stale (<6h) at once and refreshes in the background; only `doctor` opts in. Restart-cold `/today` 17s -> 2.8s, warm 0.4s.
3. Web now runs as `orient-web.service` (prod build in `.next-prod`, port 3000). Dev moved to 3002. Rebuild with `pnpm deploy:web` (~70s, service stopped during build).
4. New `/plans` nav page (`app/plans/page.tsx`, chord `g f`, config.yaml Work group): in flight (Fleet view), settled (uncapped), drafts collapsed; shared `IN_FLIGHT`/`isDraft` moved to `src/domain/plan-lifecycle.ts` and used by /work too. Plan reader deliberately untouched (another agent is refactoring it). Next: tickets page, then Ledger merge (see conversation).
All uncommitted in `~/projects/orient` (shared tree has unrelated edits).
