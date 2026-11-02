---
tags: [adhoc-task]
date: 2026-10-12
tldr: "Briefed Jack's agent (jaude) on mapping dictionary support for the announcement; verified backend is live in prod and only the Fuse UI flag is outstanding."
session_id: ffb59cf6-a351-4b3c-ae18-0374eab1968f
status: open
---
# Brief jaude on dictionary support for the announcement

## Outcome
Sent a `BRIEFING` as haude to jaude in the Jack DM at 15:10 BST. It covers what dictionaries do, `lookup()` usage, limits, the three paths where they work, the tickets, and status. Verified against `gh` and prod deployment history: the last successful prod deploy of config-service, sftp-connector, shopify-connector and fuse-ui all contain the dictionary commits.
Owed: flip `feature_flag_mapping_dictionaries = true` in fuse-ui's `iac/env/prod.tfvars` (not set on main as of today), and tell jaude when it's live.
