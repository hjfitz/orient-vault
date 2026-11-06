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
Programme Bifrost/SNAP Resilience Normalisation is active (22 units). Group A shipped: pkg-node#302 published @gfs-bifrost/resilience 0.2.0 and snap 0.4.2; G2 cleared; fuse-mcp shared-packages updated (8461a94).
Peak-day sitrep (Fri 06 Nov, 14:00): 2,045 P&F creates so far, about 6x the same window last week but far below the 22k/day forecast. Backlog max 4, 0 breaker opens, 0 retry-budget exhaustions, 6 slot timeouts all redelivered, hourly p95 1–3 s. Poller: 28.4k reads, 0 failures. No change needed. Last Friday, 80% of volume came after 14:00.
Programme 2026-11-06: A2a, A2b, Q1, A3 and Q2 shipped to prod (snap-adapter#322–#326), every behaviour change behind a switch that is off until G1.
Evening 2026-11-06: phase 1 code complete. Q4, Q5, Q2b and Q3a shipped (snap-adapter#327–#330), all switches off. Phase 2 resequenced: S1 is startable now, and the X1 flip after G1 needs a Terraform plan shared first.
Owed: a retained subscription on the create_record .dlt topics; a decision to retune or retire the dead redelivery monitor 304004530; snap-adapter code changes (unified breaker telemetry, poller timeout and cap, host tag on poll.skipped_circuit_open, poller request latency).
