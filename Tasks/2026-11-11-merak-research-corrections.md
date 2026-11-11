---
tags: [adhoc-task]
date: 2026-11-11
tldr: "Resumed the Merak replacement-pages handover on rc-hjf and, on Harry's approval, applied three edits to MPK pages: Polling Connectors v12, Tracking Events and Webhooks v4, ECM Platform v3. No feedback was owed. Two optional rewordings wait on a yes or no."
session_id: d94837dd-a7bc-4aac-99e6-6a3f03c9f046
status: open
---
# Apply the owed Merak research corrections

## Outcome
Resumed [[Handovers/2026-11-09-merak-replacement-pages]] on `rc-hjf` (live MPK tree matched the record) and applied what Harry approved on 2026-11-11, all as ADF through the MCP update tool with no API token. Polling Connectors (353697880, v12) now puts the `FindOneAndUpdate` lease in batch-creator. Tracking Events and Webhooks (355074077, v4) now says `raw_tracking.v1` carries the raw code only. ECM Platform (357662721, v3) points at Central Firebird. Each page was re-fetched, and the Lucid macro on Polling Connectors survived. Vault copies and [[Systems/ecm/known-context]] match.

Owed: Harry's yes or no on two rewordings in row 1 of Tracking Events and Webhooks ("at least six definitions" of delivered, and "throws its own mapping away"). Access-gated answers are still open, as listed in the handover.
