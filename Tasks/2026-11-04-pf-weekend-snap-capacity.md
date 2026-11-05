---
tags: [adhoc-task]
date: 2026-11-04
tldr: "Checked snap-adapter's SNAP choke against P&F's 10x weekend peak and audited SNAP-service safety and observability. Two outstanding: attempt-budget gap, and safety telemetry with no dashboard or monitor."
session_id: 3958064e-f29c-4a24-8868-8f726d62feae
status: open
---
# Assess P&F weekend surge and audit SNAP service safety/observability

## Outcome
Choke protects SNAP. The risk is slot timeouts using up the 10-attempt budget (MAX_TRANSIENT_DELIVERY_ATTEMPTS plus the DLQ), so a long backlog fails orders out.
Audit: both breakers tripped on 19 and 21 Oct (41 prod retry_exhausted). There are 1,010 prod slot timeouts in 30 days, with no dashboard widget or monitor for them. The poller breaker has no monitor, the poller has no SNAP request timeout or concurrency cap, and the two breakers disagree on 429.
Shipped observability#85: 3 SNAP safety monitors, a Safety controls tab, and 16 dead widgets repaired; applied to prod 2026-11-05. observability#86/#87: the Snap Maintainers team now owns the 23 SNAP monitors and the dashboard (18 notify @team-snap-maintainers; the team has no members yet).
snap-adapter#318 shipped to prod 2026-11-05: retry budget 10→30 deliveries (~4h), and a nack on a failed failure-publish. The apply also shipped #311 and #314; snap-adapter#319 (golden image) deploys on top of it. Decision recorded: resilience goes through @gfs-bifrost/resilience, and a 429 trips the breaker.
Owed: a retained subscription on the create_record .dlt topics; a decision to retune or retire the dead redelivery monitor 304004530; snap-adapter code changes (unified breaker telemetry, poller timeout and cap, host tag on poll.skipped_circuit_open, poller request latency).
