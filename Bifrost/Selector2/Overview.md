---
title: "Selector2 — Overview"
status: planning
verdict: go
owner: "Harry"
services: ["carrier-playground"]
created: "2026-11-11"
updated: "2026-11-11"
tags: [bifrost, merak]
---
# Selector2 — Overview

## Deliverables
- [[Selector2/Migration State|Migration State]] — the live source of truth for progress
- A new `ilg-merak` repo (working name `selector2`): a NestJS backend and a SvelteKit frontend, deployed to dev
- A new MPK Confluence subsection: similarities and differences to Legacy Selector, an overview of the mock carrier proxies, and an overview of selector2

## Verdict
Go, as a dev-only build. It rides on two conditions: the mock carrier proxies in `ilg-merak/carrier-playground` stay the egress, and no step touches prod. Nothing is cut over, because nothing in production moves to it.

## Why this needs a programme
Selector's label-getting is spread across CSS's 35 SOAP operations and a 10k-line validation chain. Replicating its wire contract in a new stack, behind two APIs, with twelve carrier adapters, a database and a UI, is about two dozen shippable units. Several carry design risk: tenancy, SOAP fidelity and the validation scope.

## Strategy
Build it in five groups: foundations (repo, infra, mock access), the core domain (schema, tenancy, validation, numbering, carrier adapters, use-cases), the APIs (REST v1, SOAP, then a terser REST v2), the UI (login, a shipment playground, read-only admin, CSV export, mock scenarios) and docs.

- **Replacement, not port.** The five label operations keep CSS's and selector-rest-proxy's wire contracts. The inside is a clean Postgres model (Drizzle) in one multi-tenant database.
- **Self-contained.** No Firebird events and no upload. CSV export from the UI is the only way data leaves.
- **Egress is the mocks.** selector2 reads each mock proxy's URL from Terraform outputs and calls it with a Cloud Run ID token. The mocks stay public for now.

Context for a new reader: [[Systems/selector/overview|the selector system]], [[Engineering/selector-rest-proxy/overview|selector-rest-proxy]] and the Confluence *Legacy Selector* tree (MPK page 351764483).

## Scar tissue
- The mocks' public names are never removed from `mock-edge`.
- Every row carries a `tenant_id`.
- Selector2 follows the Parcel Portal pattern for Cloud SQL, `cloud-sql-iam`, and shares the Selector contract it relies on.

## Next
A3 (carrier-playground IAM path and outputs) and E2 (the mock proxies page, once G3 clears) have no dependencies and can start now. A1 waits for G1. G4 (what a repeated reference does) needs a decision before B4 and B9. Driven by `waypoint-programme`.
