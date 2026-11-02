---
tags: [adhoc-task]
date: 2026-10-06
tldr: "EDI + mapping-dictionaries flags on in dev for sftp-connector (FEATURE_FLAG_EDI) and fuse-ui (FEATURE_FLAG_EDI_EGRESS and FEATURE_FLAG_MAPPING_DICTIONARIES, both newly wired in IaC); prod untouched, prod Deploy runs parked at terraform-prod gate"
session_id: 2c3a36ea-8aa3-44b2-9b4d-424c9c4e9a51
status: done
---
# Turn the EDI flag on in dev

## Outcome
Pushed direct to default branch per Harry. sftp-connector 933d71f (dev rev 00838-8dr, FEATURE_FLAG_EDI=true); fuse-ui 0b593e1 (dev rev 00350-t8g, FEATURE_FLAG_EDI_EGRESS=true; var + env block added, default false).
Prod flags stay false. Prod Deploy runs for both pushes are parked at the terraform-prod gate, unapproved.
fuse-ui cf16f8f wires FEATURE_FLAG_MAPPING_DICTIONARIES the same way (dev rev 00351-5g6, true; default false). Its prod Deploy run is parked too.
