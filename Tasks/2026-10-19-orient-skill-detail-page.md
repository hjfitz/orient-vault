---
tags: [adhoc-task]
date: 2026-10-19
tldr: "Added /skills/<name> to orient: a page per skill (instructions, frontmatter, files, run box); the name in the list links to it; live on :3000"
session_id: 8f82d53a-e1be-4eb5-9f77-1b4a271218bd
status: done
---
# Add a detail page for each skill in orient

## Outcome
`/skills/<name>` in `~/projects/orient` shows the full description, which root and path it came from, the run box (type input, send to terminal or copy), the SKILL.md instructions rendered, the frontmatter as written and the skill's other files. In the list the name is the link; clicking the description still opens the inline send box. `readSkill` looks the name up in the listing, so nothing outside the skill roots can be read through the URL. Deploy note: a new dynamic route needs an `as never` on its typed href until types regenerate, or the build's type check fails after stopping orient-web.
Owed: nothing.
