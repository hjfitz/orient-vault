---
tags: [adhoc-task]
date: 2026-11-10
tldr: "Created the 5 missing from_ilg folders for all 5 CT dev SFTP users; prod has no CT user yet; directories.json update to follow"
session_id: 7d291878-abac-48c9-98c1-55f49b04450b
status: open
---
# Create standard SFTP directories for Charlotte Tilbury (dev/prod)

## Outcome
Dev: the 5 CT users (CHARTIL, CHARTILPL, CTSAPPL, CTSAPUK x2) in gs://sftp-connector-dev-storage now have all 15 use-case folders (placeholders created by hand). Added: from_ilg/{return_goods_authorization,pick_confirmation,pack_confirmation,stock_adjustment}_confirmations and from_ilg/stock_sync.
Owed: prod has no CT business/user (folders hang off the per-env FUSE_<hash> prefix, so nothing can be created yet; the host creates the folders when the user is provisioned). Plan the apps/host/internal/directories/directories.json update so these 5 are standard for all users.
