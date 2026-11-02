---
tags: [adhoc-task]
date: 2026-10-13
tldr: "orient: Work sub-nav (Programmes/Plans/Tickets), PR review CI panel with full job logs, and headless-Claude diagnose/fix of failing CI"
session_id: b8f07bb0-4939-4324-8e00-06a4a4b492d9
status: done
---
# orient: Work sub-nav and PR CI (logs, headless Claude diagnose/fix)

## Outcome
NavView gained `parent`; Sidebar renders children under their parent within a group. New `/tickets` page (open tickets, uncapped; shipped stays in /ledger; chord `g T`). Committed 1a3a35f on orient master and deployed. Vault `config.yaml` nav.groups now lists `tickets` after `plans`; a peer session had overwritten the first edit when adding `prs`.

Later in the session (commits 552e2aa, 4aebeb6, 21fa80b): PR review page gained a CI section (workflow runs, jobs, steps), any job's full log split into groups, and Diagnose / Attempt fix buttons that run a detached `claude -p` per run (state in `~/.local/state/orient/ci-agent/`). Diagnose is read-only in a throwaway worktree; fix works in its own worktree + local branch and cannot push. Verified live end to end against real claude; no PR with red CI existed to test on.
