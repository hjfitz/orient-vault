---
tags: [support-triage, monitor-investigation]
date: 2026-09-19
business_id: ""
customer: ""
connector: unknown
reporter: "Datadog monitor (no human report)"
channel: ""
thread_url: ""
monitor_url: "https://app.datadoghq.com/monitors/302511456"
opened_at: "2026-09-19T16:45:36Z"
resolved_at: "2026-09-19T19:00:00Z"
minutes_spent: 135
outcome: mundane
ticket: ""
session_id: 9b1b7ebf-5c01-492b-8fdd-fa5777fb9b36
status: resolved
---
# [FUSE][Dedupe Service] Silent publish drop — Re-Triggered, 2026-09-19

## Reported
No human report — this was a re-triggered Datadog monitor (`302511456`,
`sum:fuse.dedupe.event.handled - (fresh + duplicate + blacklisted + invalid +
record.invalid + dropped_config_unavailable) > 30` over a rolling 1h window),
flapping Warn → Recovered → Re-Triggered five times between **16:30 and
18:20 UTC on 2026-09-19**. Same monitor also flapped once each on
**2026-09-12 (17:30)** and **2026-09-13 (15:40)**.

## Root cause
**Not a real record/publish loss.** Every flap this month lines up with a
`sales_order` traffic spike 3–10× the ~600–700/hr baseline (today: `event.handled`
hit 6,269/hr, then a second surge to 2,406–3,391/hr around 16:00–18:00 UTC,
exactly the flap window). No errors, no unhandled rejections, and zero
`sku.blacklisted` / `event.invalid` / `record.invalid` / `dropped_config_unavailable`
events fired in or around the window — the "unaccounted" gap the monitor is
built to catch was empty on every other axis.

The mechanism: `fuse.dedupe.event.handled` increments once per inbound HTTP
push (i.e. per **message**), synchronously on receipt, while
`fuse.dedupe.event.fresh` / `.duplicate` increment once per **record**, after
the dedupe/blacklist work completes — a known shape mismatch between these two
metrics ([[reference_fuse_metric_business_tagging]]). Under normal load the two
settle within the same rolling hour and net to ~0. Under a burst, the async gap
between "handled" and "outcome" widens enough that some of a burst's outcomes
land in the *next* hourly bucket. Confirmed directly in the metric data: the
16:00–17:00 and 17:00–18:00 UTC buckets each showed a positive gap (+42, +31 —
just over the `>30` threshold), and the very next bucket (18:00–19:00) showed
the mirror-image deficit (**-39** more outcomes than handled) — the same
records, just counted one hour later. Nothing was actually dropped.

The `>30` threshold was tuned in July 2026 against a baseline of a few hundred
events/hour ([[project_dedupe_dashboard]]/Migration State doc history); it was
never revisited as sustained `sales_order` volume grew several-fold, so what
was once a comfortable skew allowance is now inside the noise band during any
burst.

## Fix / Resolution
No code or config change made — this was a threshold-tuning gap, not a defect,
and no customer-facing impact was found (nothing was lost; the pipeline is
"apply canonical" not "cancel", so a merely-delayed count reconciles on its own,
[[reference_fuse_no_cancellation_path]]). Flagged to Harry as a monitor-hygiene
follow-up: either widen the evaluation window (e.g. `sum(last_2h)`) so cross-hour
skew nets out before evaluation, or raise the absolute threshold to match
current baseline volume — not filed as a ticket since it's monitor
configuration, not application behaviour.

## Links
- Monitor: https://app.datadoghq.com/monitors/302511456
- Monitor history/design notes: `Bifrost/Dedupe NestJS Migration/Migration State.md`
