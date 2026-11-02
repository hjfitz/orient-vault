---
tags: [adhoc-task]
date: 2026-10-14
tldr: "orient PR page: Claude findings are now accept/reject suggestions; new resolve-conflicts skill + headless 'Resolve conflicts' button (local merge commit, no push)"
session_id: a5c8be0e-ce6d-4ac2-b014-871544579fdc
status: done
---
# Add accept/reject to Claude PR review and headless conflict resolution

## Outcome
orient commits 5cf77a5 (suggestions: accept/reject/edit per finding, accept-all/reject-all, undecided ones not sent) and d0c5b2b (`conflicts` agent mode + button on a dirty PR of your own). Skill is `~/.claude/skills/resolve-conflicts` (user-level: worktrees are their own git root so `~/code/.claude/skills` isn't discovered). Verified headless on a scratch repo: aborts on competing change, resolves + commits locally otherwise.
Owed: delete `~/code/fuse/zz-conflict-scratch` (rm was blocked); two pre-existing biome format errors on master (`src/actions/slack.ts`, `src/domain/jira-issue.ts`).
Slack reactions on /slack (orient 14c12df): hover picker per message plus toggle on chips; bifrost-forge gets ✅/❌/💬 (approved/changes requested/comments), other conversations 👍/👀/✅. Needs the orient Slack app's reactions:write scope; not yet clicked in a browser.
