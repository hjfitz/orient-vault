---
tags: [adhoc-task]
date: 2026-09-30
tldr: "create-pr skill now links stacked PRs as a native GitHub Stack via gh stack link; verified on snap-adapter #264/#266/#267 (stack #268)"
session_id: 0b571021-75ea-4817-810c-bcfdff4fcbb5
status: done
---
# Make create-pr use native GitHub stacks

## Outcome
`.claude/skills/create-pr/SKILL.md` Stacked PRs section: PRs still opened with `gh pr create --base`, then linked with `gh stack link` (no `--open`, bottom→top, run in worktree); body diagram is now fallback-only; `[Stacked: N/M]` title prefix kept. Installed the `gh-stack` extension locally. Verified end-to-end: `gh stack link 264 266 267` created stack #268; drafts and bases unchanged.
