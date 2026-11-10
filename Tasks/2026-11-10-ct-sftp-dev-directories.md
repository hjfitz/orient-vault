---
tags: [adhoc-task]
date: 2026-11-10
tldr: "CT dev folders created by hand; 4 confirmation folders now standard for every SFTP user in dev and prod (gfs-bifrost/sftp-connector#408); stock_sync and prod CT user still open"
session_id: 7d291878-abac-48c9-98c1-55f49b04450b
status: open
---
# Create standard SFTP directories for Charlotte Tilbury (dev/prod)

## Outcome
Dev: the 5 CT users (CHARTIL, CHARTILPL, CTSAPPL, CTSAPUK x2) in gs://sftp-connector-dev-storage were given all 15 folders by hand, including a tentative from_ilg/stock_sync.
Shipped: gfs-bifrost/sftp-connector#408 adds pick, pack, stock_adjustment and return_goods_authorization confirmation folders to directories.json; live in dev and prod (see the FUSE-1351 wp ledger entry).
Owed: stock_sync (name unconfirmed, FUSE-1302); prod CT connector/user does not exist yet; Jack was told "five extras" and "prod needs them by hand", so he needs a correction; Darren to be told when CT folders are in place.
