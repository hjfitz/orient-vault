---
tags: [support-triage]
date: 2026-09-23
business_id: LISAUK
customer: "Lisa Eldridge (UK + PL)"
connector: sftp
reporter: "James Godsell"
channel: bifrost-general
thread_url: "https://gfsdeliver-eng.slack.com/archives/C098LD5PS95/p1790148725881649"
opened_at: "2026-09-23T07:32:05Z"
resolved_at: "2026-09-24T14:13:46Z"
minutes_spent: 1841
outcome: config-issue
session_id: c403f819-cede-41e4-ac6e-2055994b565b
status: resolved
---
# Lisa Eldridge goods-out confirmations drained from SNAP with nowhere to deliver

## Reported
Thread opened on DRSAMS ("Confirmation had no originating connector" goods-out failures; Fuse draining the Jitterbit-shared SNAP outbound queue). On 09-24 James Godsell added that Lisa Eldridge showed the same; Danny Williams was chasing SNAP connection failures for LISAUK/LISAPL.

## Root cause
- From 2026-09-18 08:48Z the poller claimed LISAUK/LISAPL goods-out confirmations off the SNAP OBQ, but both SFTP connectors only carry master_data/sales_order/purchase_order use cases — sftp-connector "use case not active", fapi "could not be routed", each stored in replay. ~920 LISAUK + ~710 LISAPL, goods-out only (no stock moves/receipts). Likely the same shared-Jitterbit-queue setup as DRSAMS (hypothesis, not verified in SNAP).
- SNAP returned 401 to the poller for both from 2026-09-23 09:56Z (coincides with DRSAMS credential/link clean-up — cause not confirmed). LISAUK regained access ~10:50Z 09-24 and took 28 more before switch-off; LISAPL 401'd until switch-off. Nothing claimed during 401s.
- Connector `confirmationsEnabled` switched off by ILG side: LISAUK entered poller skip list 13:08Z, LISAPL 13:14Z on 09-24.
- Side finding (not in thread): poller 401 error logs dump the raw request header incl. Basic auth credentials into Datadog (LISAPL, ESCENTRICPL). Flagged to Harry for a defect + credential rotation.

## Fix / Resolution
Confirmations off for both businesses (stopped). Reporter told scope and counts; resending affected confirmations is support's to drive. No platform fix for the drain itself.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C098LD5PS95/p1790148725881649
