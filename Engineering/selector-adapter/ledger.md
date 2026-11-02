---
tags: [waypoint, ledger]
---
# selector-adapter — work ledger

Agent-facing. Newest first. What meaningful work happened here, and the
context a future agent needs. Not a diary, not release notes, not a diff.

## 2026-10-28 — Read each business's Selector connection from config-service

Read each business's Selector connection from config-service

Delivery Backends B2. ConnectionProvider backed by config-service ?type=SELECTOR; claims keyed by business+backend+shipment; static env connection removed. Verified on dev: one sandbox booking (T003FA0000006609), resend already_booked, non-Selector business never reached the adapter.

PR: gfs-bifrost/selector-adapter#7

## 2026-10-27 — Selector adapter dev spike signed off

Selector adapter dev spike signed off

Spike complete: the Go selector-adapter books one Selector ProcessShipment per create_record sales_order. A Firestore claim per order guards against double-booking (Selector books a repeated reference again), and DailyShipQuery reconciles an unknown outcome. It runs as selector-adapter-dev (dev only), receives nothing until the deduper stamps selector, and publishes nothing. Live dev e2e and config-service connections moved to Delivery Backends B2. Read architecture.md guardrails first. [[Explainers/2026-10-27-selector-adapter-spike-findings]]

PR: gfs-bifrost/selector-adapter#4

## 2026-10-27 — Selector adapter dev spike: SOAP client, booking, push service, dev IaC

Selector adapter dev spike: SOAP client, booking, push service, dev IaC

Stacked draft PRs for the dev-only Selector adapter: Selector ProcessShipment client and sandbox findings (#1), canonical mapping + Firestore claim + DailyShipQuery reconcile (#2), Pub/Sub push service with ID-token check (#3), dev-only Cloud Run/Firestore/filtered create_record subscription and CI (#4). Selector books a repeated reference again, so the claim is the only idempotency guard.

PR: gfs-bifrost/selector-adapter#1
PR: gfs-bifrost/selector-adapter#2
PR: gfs-bifrost/selector-adapter#3
PR: gfs-bifrost/selector-adapter#4
