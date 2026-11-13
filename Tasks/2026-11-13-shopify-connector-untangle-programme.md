---
tags: [adhoc-task]
date: 2026-11-13
tldr: "Reviewed shopify-connector's architecture with four independent lenses; created the Shopify Connector Untangle programme (37 units, safeties first) and retired the old rearchitecture programme"
session_id: 9ee5fc6a-bc22-45d1-8746-f3a76be22423
status: open
---
# Review shopify-connector architecture and stand up a refactor programme

## Outcome
- **New programme:** `Bifrost/Shopify Connector Untangle/`. Its north star is 3am debuggability, sequenced see → stop → pin → fix → move → retire.
  - 37 units, four gates and per-PR safeties.
  - Runtime-flag cutover, where flag `false` is the old path.
- **Retired:** `Bifrost/Shopify Connector Rearchitecture/`, marked SUPERSEDED, not deleted. The service's Waypoint docs are repointed.
- **Owed:** Harry's calls on G1 (the outcome convention) and G2 (the slice-layout ADR).
