---
title: "Charlotte Tilbury EDI Onboarding — Overview"
status: blocked
verdict: go
owner: "hjf"
services: ["sftp-connector", "config-service", "fuse-ui"]
created: "2026-09-30"
updated: "2026-09-30"
tags: [bifrost]
---
# Charlotte Tilbury EDI Onboarding — Overview

## Deliverables
- [[Charlotte Tilbury EDI Onboarding/Migration State|Migration State]] — the live source of truth for progress
- Built on: [[EDI Support/Overview|EDI Support]]
- Jira epic **FUSE-1213** — Charlotte Tilbury SAP (EDIFACT) Integration
- Puig EDI guides: `~/code/fuse/edi-guides/PUIG EDI standards EDIFACT/`; project memory `project_edi_charlotte_tilbury.md`; Confluence 215678985

## Verdict
**Go, but blocked on the customer.** CT's inbound files already ingest. Confirmations need CT's partner mappings (CT2), a returns message agreed with Accenture (CT4), and the capability's prod flags (EDI Support G2).

## Why this needs a programme
It's the first customer on the EDI capability. Its gates are outside engineering (CT, Accenture), and it has to stay a pure config exercise to prove the capability is generic.

## Strategy
- **Config only**: envelope, mappings and `codes.*` on CT's SFTP connector.
- **Prove in dev** against CT's own samples.
- **Go live** by setting CT's connector to `edi` once EDI Support's prod flags are on.

## Scar tissue
CT is config and test fixtures, never code.

## Next
Nothing is actionable until CT supplies mappings (CT2) or Accenture agrees the returns message (CT4).
