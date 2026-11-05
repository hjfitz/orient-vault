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
Owed: an observability PR (safety row on the snap-adapter dashboard plus monitors), and code tickets for unified breaker telemetry and the poller timeout and cap.
