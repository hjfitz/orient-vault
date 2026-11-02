---
tags: [support-triage]
date: 2026-08-05
business_id: BYOMA
customer: "Byoma (fleet-wide SFTP confirmation customers)"
connector: sftp
reporter: "James Godsell"
channel: bifrost-general
thread_url: "https://gfsdeliver-eng.slack.com/archives/C098LD5PS95/p1785929415879229"
opened_at: "2026-08-05T11:30:15Z"
resolved_at: "2026-08-19T14:29:12Z"
minutes_spent: 20339
outcome: defect
session_id: 535aa793-cf02-4d5b-9169-be8e3c2823f1
status: resolved
---
# Fuse showed no outbound use cases configured for Byoma, yet confirmations were still being sent

## Reported
James Godsell reported (with a Byoma screenshot) that Fuse's SFTP connector showed no outbound use cases configured for a business in production, yet Datadog showed order confirmations were actively being written to that business's SFTP outbound folder. He hadn't had any reports of missing confirmations, but the discrepancy between "nothing configured" and "confirmations flowing" was confusing.

## Root cause
A feature flag (`feature_flag_use_dynamic_confirmation_mapping`) was set to `false` in production, which meant Fuse wrote a confirmation file to every SFTP connector with a username, regardless of whether outbound use cases were actually configured — the use-case config was only going to be consulted once the flag was flipped on. This wasn't unique to Byoma; the same gap applied to every customer receiving confirmations while the flag was off (identified at the time as STUBBLE, EPARFUM, SPORTLUX, WILDSMITH, BFA and BYOMA). Behaviour while the flag was off was over-sending, not under-sending, so no confirmations were being missed by this specific issue.

## Fix / Resolution
Egress use cases and their mapping config were set up for every affected customer (James Godsell configured these over the following two weeks, including a column-ordering side effect that needed correcting), and the flag was flipped live on 19 August, moving all of these customers onto the properly-configured dynamic confirmation mapping.
Note: this thread ran for two weeks with several multi-day idle gaps while configuration work happened — the elapsed time reflects that, not continuous investigation.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C098LD5PS95/p1785929415879229
