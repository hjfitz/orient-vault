---
tags:
- system
- parcel-portal
verified: '2026-10-29'
title: parcel-portal — known context
---
# parcel-portal — known context

## People
- **Oliver Wilders** owns the requirements (v0.1, v0.2) and the customer relationship, and decides the MVP cut (G9) with Phil Bradley-Smith.
- **Phil Bradley-Smith** supplied TCA's sample CSV and DC's export.
- **Oli Denton** holds the platform direction: CSV ingestion belongs in Fuse (G7). Prod waits on his agreement.
- **Chris Cumings** is the Selector contact for manifest semantics (G5).
- **Harry** builds it, through agents under standing autonomy.
- **Darren Rielly** owns the frontend principles for ilg-merak repos (still TODO in the repo).

## Business context
- DC goes live for TCA on Mon 9 Nov 2026; the portal is the fallback if DC hurts in the first days. Switching is Oliver's call with Oli Denton.
- Customer contact is internal only: nothing goes to TCA, Yusen US, DC or wider teams until Oliver says so.
- A multi-customer version is effectively what GFS buys from DC today, which makes it a product decision, not just a roadmap.

## Open questions
- **Who is the tenant: TCA (the shipper) or Yusen (the warehouse operator)?** It decides the multi-customer data model.
- **Does intake stay here or move into Fuse?** (G7)
- The remaining gates are tracked in `Bifrost/Parcel Portal/Migration State.md` and the MKP Jira project.

Service-level history and fragility: `Engineering/parcel-portal/known-context.md`.
