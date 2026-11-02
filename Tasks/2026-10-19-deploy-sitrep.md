---
tags: [adhoc-task]
date: 2026-10-19
tldr: "Deploy sitrep: 14/15 at dev tip; snap-mcp missing #22/#23 (Deploy never triggered 10-02); secops-reporting prod deploys failing since 09-17"
session_id: e04a3381-9ad4-48de-9bb1-1c139eca54de
status: open
---
# Run deploy sitrep across Fuse services

## Outcome
14 of 15 services checked have prod at the dev tip; most were deployed together on 2026-10-16.
- snap-mcp is 2 commits behind (#22 axios bump, #23 per-connection client cache). They were merged 2026-10-02, but no Deploy run was ever created for them, and the workflow only triggers on push.
- secops-reporting (ilg-platform org, which the script can't reach) is stuck at f04b372 (09-15). Both later Deploy runs failed on 09-17 at the docker build and pubsub terragrunt steps.
- The script's 12 failure flags are stale. It counts cancelled and failed runs even when a successful deploy came after them.
