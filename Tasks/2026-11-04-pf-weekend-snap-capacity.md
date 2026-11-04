---
tags: [adhoc-task]
date: 2026-11-04
tldr: "Checked whether snap-adapter's SNAP choke holds against Purdy & Figg's ~10x weekend peak. It protects SNAP fine; the gap is slot timeouts using up the 10 delivery attempts."
session_id: 3958064e-f29c-4a24-8868-8f726d62feae
status: open
---
# Assess P&F weekend surge against snap-adapter SNAP throttle

## Outcome
P&F is on ilg005live. 14 days of prod data: SNAP latency doesn't rise with our load (busiest 5 min, 3.9 rps, had 1.0s avg latency), so tightening concurrency would only lengthen the backlog.
The risk is prod slot_timeout (50–160 a day already). Each one counts against the hard-coded MAX_TRANSIENT_DELIVERY_ATTEMPTS=10 and the DLQ's 10 attempts, so a long backlog fails orders out without SNAP ever seeing them.
Owed: decide on raising or excluding pre-dispatch failures from the attempt budget before Fri 06/11.
