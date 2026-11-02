---
tags: [adhoc-task]
date: 2026-10-29
tldr: "Shipped remote-compute: Arch Claude Code workstations on GCP; rc-hjf live at hjf.shell.platform.ilg.software with the Applied Computing banner"
session_id: fa1c5513-3492-410e-a830-4bccce518f43
status: done
---
# Plan remote compute VMs for Claude Code

## Outcome
Three draft plans: remote-compute first-workstation (7 increments), images Arch VM image (7), remote-compute day-2 (5). The work is gated on one gcp-config PR and one core-infra PR. All owner questions were answered: tiers, approvers mirroring core-infra, public SSH (durable record), project logging, Arch patching and offboarding by PR. Switched the image from Ubuntu to Arch on Harry's call, which drops OS Login for metadata-served keys. The Waypoint model rubric now maps Fable to the opus tier.
