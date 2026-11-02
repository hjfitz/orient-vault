---
tags: [datadog-triage]
date: 2026-10-20
monitor: "[FUSE][Platform] Elevated production error rate (2m window)"
service: snap-adapter
business_id: PURDYFIGG
snap_instance:
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1792499807060079"
opened_at: "2026-10-20T12:35:37Z"
resolved_at: "2026-10-20T12:38:15Z"
minutes_spent: 3
severity_assessed: P4
flapping: true
outcome: monitor_mistuned
escalated_to:
ticket:
session_id: 7b50d12c-31a0-425c-913d-8c963cd91233
status: resolved
---
# Prod error-rate monitor tripped by known PURDYFIGG Email rejects + one tracking-service nack

## Fired
Monitor 180072217 (`count > 2` over the last 2m) fired at 12:35:37Z, after INC-40 had been resolved.

## Investigation
- There were exactly 3 matching lines in 12:33:37–12:35:37Z:
  - 2× `snap_adapter` "Entity creation in SNAP failed", one each for PURDYFIGG #6565591 (12:35:08Z) and #6531052 (12:35:09Z). Both are Snap 400 CONTACT_UPDATE, Email MANDATORY.
  - 1× `tracking-service` "store failed; nacking for redelivery" (12:35:07Z), a Firestore Unauthenticated error (`mint used too late`, a credential token used past its expiry).
- The tracking-service error is the only one since 12:03Z, and differs from the 11:58–12:03Z burst of 1,537 Firestore `Aborted` contention nacks.
- There was no Redis or cache recurrence: 0 prod lines matched redis / failing open / ETIMEDOUT / 504 / ECONNREFUSED / cache unavailable between 12:15 and 12:50Z.
- The PURDYFIGG pair re-fails on every ~5-min re-poll (12:30:10/18Z, 12:35:08/09Z). That puts exactly 2 lines in the window, which is the threshold, so any one extra error trips the monitor.
- Since 10:00Z, snap_adapter errors by order were PURDYFIGG #6531052 ×27 and #6565591 ×16. DOCKBAY (8) and STUBBLE (1) errors occurred only around 11:31–11:35Z.
- The monitor logged 25 alert events (trigger/recover) in 24h, mostly during INC-40.
- Not established: whether tracking-service event 22062681442639849 was applied on redelivery, and the monitor's recovery time.

## Outcome
P4, no new impact. Recommended either excluding the PURDYFIGG Email MANDATORY rejection from the query (the fulfillment-ID one is already excluded) or raising the threshold; it is Terraform-managed, so the change goes in the observability repo. @fuse-support was pinged to fix the contact email on both held orders and replay them.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1792499807060079
