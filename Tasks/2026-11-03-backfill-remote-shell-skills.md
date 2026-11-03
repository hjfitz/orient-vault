---
tags: [adhoc-task]
date: 2026-11-03
tldr: "Remote shell sessions inside a repo lost the 27 Fuse workflow skills (datadog-watch etc.); symlinked them into the remote's ~/.claude/skills"
session_id: 57decd09-83e2-4958-a9d0-913422801714
status: done
---
# Backfill Fuse workflow skills on the platform remote shell

## Outcome
The files were already on harry@hjf.shell.platform.ilg.software at ~/code/.claude/skills, but project skills only load when the cwd resolves to ~/code without crossing a git root, so sessions inside ~/code/fuse/<repo> or ~ saw 72 skills instead of 99. Symlinked all 26 repo-level skills plus verify into the remote's ~/.claude/skills (skipped the duplicate "verify (2)"). Verified from config-service and ~: 98 skills, none missing. Already-running remote sessions need a restart to see them.
