---
title: "EDI Support — Overview"
status: active
verdict: go
owner: "hjf"
services: ["pkg-node", "sftp-connector", "config-service", "fuse-ui", "snap-adapter", "fuse-mocker", "fapi", "shopify-connector", "collector"]
created: "2026-09-30"
updated: "2026-09-30"
tags: [bifrost]
---
# EDI Support — Overview

## Deliverables
- [[EDI Support/Migration State|Migration State]] — the live source of truth for progress
- Customer onboardings that build on this: [[Charlotte Tilbury EDI Onboarding/Overview|Charlotte Tilbury EDI Onboarding]]
- `@gfs-bifrost/edi` (pkg-node `pkg/edi`) — parser, normalizers (INSDES/PRICAT/ORDERS/RECADV in), EANCOM D.96A serializers (DESADV/RECADV/OSTRPT/INVRPT out), interchange wrapper
- Umbrella egress plan: `Engineering/sftp-connector/plans/edifact-confirmation-egress-desadv-recadv-behind.md`
- Customer-agnostic decision: `Engineering/sftp-connector/decisions/2026-09-24-edi-egress-is-customer-agnostic-partners-are-config-never-co.md`

## Verdict
**Go.** Fuse can ingest EDIFACT over SFTP (sales orders, master data, purchase orders) and write every confirmation type except returns as EDIFACT over SFTP. It's customer-agnostic, config-driven, and in prod behind `FEATURE_FLAG_EDI` (one flag for ingress and egress since 2026-09-30), which is off. What's left for a *general* capability:
- the ingress rough edges: qualifier profiles and charset;
- inbound DESADV;
- a returns message once a partner defines one;
- turning it on.

## Why this needs a programme
- It's a platform capability spanning eight services.
- Rollout-order hazards break silently: consumers must accept a new file type before config can store one, and the poller must carry data before a message can use it.
- Every future EDI customer builds on it, so it's worth tracking separately from any one onboarding.

## Strategy
- **The capability is generic EANCOM D.96A.** Every partner-varying value is config: the envelope, mapping rules (rule names are message paths), `codes.*` overrides, dictionaries, and later an inbound profile.
- **Ingress** reuses the CSV mapping pipeline on a flattened intermediary.
- **Egress** builds from the connector's own confirmation mapping and writes create-only, idempotent files.
- **Enablement is two flags**, sftp then fuse-ui. They're inert until a connector is set to `edi`, so the capability can go GA independently of any customer.

## Scar tissue
See the State doc's `## Scar tissue`. Load-bearing: **customer-agnostic, always**; **one message per file**.

## Next
- `wp programme next "EDI Support"`.
- The live decisions: whether inbound DESADV (I4) is back in scope, and whether the dev flag (G1) can go on now that onboarding is tracked separately.
- The unticketed candidates (I5, I6, E13, E14, H3, G3) need a keep/drop pass.
