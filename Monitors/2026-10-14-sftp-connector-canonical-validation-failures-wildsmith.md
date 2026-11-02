---
tags: [datadog-triage]
date: 2026-10-14
monitor: "[FUSE][SFTP Connector] Canonical validation failures"
service: sftp-connector
business_id: WILDSMITH
snap_instance:
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1791990250996769"
opened_at: "2026-10-14T15:03:08Z"
resolved_at: "2026-10-14T15:07:00Z"
minutes_spent: 4
severity_assessed: P3
flapping: false
outcome: real_minor
escalated_to:
ticket:
session_id: 4fc06c6b-d424-4da8-b551-fb874e9c6e96
status: resolved
---
# WILDSMITH master-data SKU 3304990000 fails validation for the 4th time (1, 6, 8, 14 Oct)

## Fired
Monitor 324087068 (any `Records failed CSV validation` line in 15m) fired at 15:03:08Z. Trigger log: WILDSMITH, create_master_data, CanonicalMasterDataSchema, 1 failed row, `product.lifecycle.life: expected int, received number; product.dimensions.box.height: expected number, received NaN`. Third firing in about 30h, but a third different business.

## Investigation
- Trigger log, correlationId `39953fee-890d-4b75-a205-cb7ab7327ca3`: file `wildsmith-20261014-150302.csv` at 15:03:04Z, `Records validated` valid 3 / invalid 1, `create_data_failure` 204, build `4e1593e`. Record dropped: recordId `3304990000`.
- Held record (replay-get-failure `3313bb10-7fc3-4b89-b71b-f03abc5c46ca`, production): attempts 0, `replayable: false`, blockingIssues life + box.height. Field values are misaligned with their mapped meaning (`identifiers.businessId` = "1L Professional Vitality Body Oil Black Pepper Ginger Cedarwood", `description` = "GB", `box.height` = "NON", `life` = "22.6756", `item.height` = "5060484545058"). Because the businessId is the product name, replay-list-failures filtered by WILDSMITH and createdAt 2026-10-14 returns 0; it is found by recordId search.
- Repeat: DDSQL `Record dropped` WILDSMITH 30d returns recordId 3304990000 on 1 Oct (build `75bd776`), 6 Oct (`648ee6e`), 8 Oct (`648ee6e`), 14 Oct (`4e1593e`); identical sampleError each time (search of `Records failed CSV validation`, WILDSMITH, 30d: exactly these 4). Each time 1 invalid in a file of 3 to 11 rows. 53 WILDSMITH create_master_data files in 30d, only these 4 had an invalid row. Not a build regression.
- Recordid search 3304990000 in replay (production) returns only today's record; the three earlier ones are not held now.
- Three firings compared (monitor events 3d and trigger logs): LISAUK 13 Oct, sales_order, `dates.dueOut` undefined, build `28c514e`; DISCOVERED 14 Oct 08:23Z, purchase_order, `lines.*.quantities` undefined, build `28c514e`; WILDSMITH 14 Oct 15:03Z, master_data, lifecycle/box.height, build `4e1593e`. Builds seen in `Records validated`: `648ee6e` to 12 Oct 15:43Z, `28c514e` 12 Oct 15:43Z to 14 Oct 08:24Z, `4e1593e` from 14 Oct 08:34Z. Different customer, record type, field and file each time: independent customer data gaps; no shared build, field or file found. The shared element is only the monitor.
- DISCOVERED PO follow-up: replay-list-failures DISCOVERED (production) still lists PO `EU0000836404` (`d680cf5b-37ab-4788-9678-0f399a01a269`) attempts 0, created 08:22:45Z. DDSQL `Records validated` for DISCOVERED from 08:00Z: no create_purchase_order after 08:22:44Z; later files are sales orders `143550.csv` (10:32Z), `143551.csv` (12:45Z), `143557.csv` (13:45Z), all valid 1/0. So not resent through sftp.
- Monitor history (events, 3d): triggers 13 Oct 09:30Z, 14 Oct 08:23Z, 14 Oct 15:03Z; recoveries 13 Oct 09:45Z and 14 Oct 08:38Z. Not flapping. Monitor message "only occurrence in the past 7 days" text is stale. The 15:03Z firing had not yet recovered when the verdict was posted, so the posted "each recovered on its own" was true of the first two only.
- Customer context: Customers/WILDSMITH has config snapshot and overview only, no known-context.md, nothing to say whether this SKU row is a known issue.
- Is it us: no. Failure is at our canonical boundary on the customer's data. Vendor: no (never reached Snap).

## Outcome
P3, real_minor. One WILDSMITH product master row held in replay, none reached Snap; same SKU has failed identically 4 times. DISCOVERED PO still held and not resent. Nothing changed (read-only). Verdict posted with broadcast. No ticket filed.

Not established: why the 3 earlier WILDSMITH holds are no longer in replay; the source CSV row (not read) and why its columns are misaligned; why the DISCOVERED PO had empty `iOrderLines_*`; whether the DISCOVERED PO arrived by another route (API, other filename); whether the LISAUK holds (207 per the 14 Oct morning record) have changed since.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1791990250996769
- Verdict reply: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1791990387349489
- Monitor: https://app.datadoghq.com/monitors/324087068
- Prior records: Monitors/2026-10-13-sftp-connector-canonical-validation-failures-lisauk.md, Monitors/2026-10-14-sftp-connector-canonical-validation-failures-discovered.md
