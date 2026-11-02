---
title: "Parcel Portal — Overview"
status: planning
verdict: undecided
owner: "Harry"
services: []
created: "2026-10-28"
updated: "2026-10-28"
tags: [bifrost, merak]
---
# Parcel Portal — Overview

<!-- The narrative and the verdict. PROGRESS lives in the Migration State doc, not here — link it,
     never duplicate its ledger. This doc changes rarely; the state doc changes every session. -->

## Deliverables
- [[Parcel Portal/Migration State|Migration State]], the live source of truth for progress.
- Requirements v0.1 (Oliver Wilders, 28 Oct): `2026-10-28-fuse-csv-ui-first-us-customer-plan.md`, sent in the Harry/Wilders DM ([Slack](https://gfsdeliver-eng.slack.com/archives/D0ALESDKC86/p1793205004687309)). It was meant to be attached to [MKP-2](https://globalfreight.atlassian.net/browse/MKP-2), but isn't yet.
- Huddle, 28 Oct 16:29: orient recording `20261028-162954-d16e` ("Wilders Catch up - beachhead").
- Customer inputs from Phil Bradley-Smith in the same DM: `CSV Example.csv` (DC's 40-column import, one row per product) and `shipments_download_1793179059.csv` (the 17-column DC export Manhattan SCALE reads).
- Reference instance: GFS's white-label Despatch Cloud, https://ship.gfsdeliver.com/. It has a **live account on it, so it's look-only.**
- The Jira side (MKP) follows once this plan is agreed. The DC-clone epic drafted earlier on 28 Oct was dropped.

## What it is
A web portal for **TCA**, shipping from one Yusen US site with 3 to 4 pack stations, FedEx only, US→US and US→CA, with no dangerous goods.
- Manhattan SCALE drops CSVs onto SFTP.
- The portal imports them, validating as it goes. Good rows are kept and bad rows are flagged.
- Staff fix rows in an import queue, label them through Selector, and print.
- Manifesting goes through Selector.
- At day end the portal exports a CSV that Yusen feeds back into Manhattan SCALE.

There are four tabs: **Import queue**, **Labelled**, **Manifested** and **Export**. Selector does the carrier work. The portal adds the strict import, the fix-it loop and the export, which Selector's own CSV import does badly: one bad line fails the whole file.

**Handling:** internal only. Per Wilders' plan, nothing goes to TCA, Yusen US, DC or wider teams until Oliver says so.

## As built (28 Oct, evening)
> Present-tense state of `ilg-merak/parcel-portal` `main`. Progress is in the [[Parcel Portal/Migration State|Migration State]]; the dev test path is in [[Parcel Portal/Dev test checklist|Dev test checklist]].

- **Intake.**
  - The single-user Go SFTP host (`tca`, static IP) writes to the inbound bucket, which notifies svc over Pub/Sub.
  - Import is idempotent per object generation and ignores temp names.
- **Mapping.** A per-tenant DSL mapping (Fuse rules-engine port: rules, defaults, dictionaries, groupBy) is set by the admin API, with built-in `dc-layout` for Despatch Cloud's 40 columns.
- **Validation.**
  - Stage 1 checks the file format and rejects the whole file.
  - Stage 2 checks each row: mandatory fields, US state/ZIP, CA customs, and dims/weight that are never defaulted. Partial import keeps the good rows.
  - Validation re-runs on every edit and packing change, and again before dispatch.
- **Orders screen.**
  - Status badges, plain reasons, search by shipref/consref, and a rejected-files list.
  - Edit address and service before dispatch.
  - Pack into presets or manual dims and assign items to parcels.
  - Dispatch, plus **batch dispatch** (up to 100, per-order results, merged labels) and **check with carrier** on selected orders (C7, #21).
- **Dispatch.** At-most-once per order: claim with a lease, reconcile with `DailyShipQuery`, book, store labels in GCS. The despatch date uses the site's timezone.
- **Shipments screen.** Search (site-local dates), detail, label view/reprint/download, a merged-PDF batch print, void (at Selector first), manifest (`CommitShipments`) and refresh status (picks up auto-commits).
- **Export.** DC's 17-column CSV for Manhattan. The day is the site-local day; consref goes in `Channel Alt ID`; tracking codes are kept as text.
- **Settings.** Packaging presets, and bench printers.
- **Printing.**
  - Print-to-screen everywhere.
  - **Silent WebUSB printing** (C8, #23; real printers tested 29 Oct): it ships as the standalone package `@ilg-merak/label-print` (`packages/label-print`, private for now) and rasterises PDF labels to ZPL `^GFA` or EPL `GW` in the browser, with a demo printer that shows the exact dots without a device. A paired browser auto-prints after Dispatch.
- **Auth and tenancy.**
  - Per-person sessions (opaque, hashed) behind the UI; svc is invokable only by the UI's service account.
  - Every customer-data query is tenant-scoped, and a static test enforces it.
- **Ops.** `docs/runbook.md`, plus 10 Datadog monitors as Terraform (off until `DATADOG_APP_KEY` exists). The SFTP canary runs every 5 minutes.
- **Not built:** admin screens for tenants, users, mapping and carrier (API only), a carrier-service picker, and dark mode.

## Verdict
**Undecided, leaning go.** Two conditions:
- **Direction (G7).** Oli Denton said on 28 Oct that CSV mapping and ingestion belong in Fuse as the one ingestion point. This programme builds outside Fuse. That needs his agreement before prod.
- **Not on the critical path.** DC goes live for TCA on **Mon 9 Nov**. This portal is the parallel route. Switching TCA over is Oliver's call with Oli Denton, if DC hurts in the first days.

## Why this needs a programme
- **New repo, new infrastructure:** a Cloud Run monolith, a Go SFTP host on a MIG, Cloud SQL with IAM auth, and a first tenant.
- **Ports Fuse logic to Go:** the rules-engine DSL and the CSV mapper.
- **Customer-facing and multi-tenant from day one.** One customer seeing another's data is never acceptable.
- **Several requirement gaps are still open with the customer:** row grain, export layout, printers and the US sample file.
- **A hard external date** sits beside it.

## Shape (proposed)
```orient-flow
{ "v": 1, "title": "Parcel Portal",
  "nodes": [
    { "id": "wms", "label": "Manhattan SCALE", "sub": "Yusen US", "kind": "external" },
    { "id": "vm", "label": "portal sftp (Go)", "sub": "MIG + TCP LB, static IP; keys in Secret Manager", "kind": "service" },
    { "id": "gcs", "label": "Inbound bucket", "sub": "per-tenant prefix", "kind": "store" },
    { "id": "app", "label": "portal svc (Go)", "sub": "Cloud Run, go-runtime image", "kind": "service", "tone": "accent" },
    { "id": "db", "label": "Cloud SQL Postgres", "sub": "IAM auth, no passwords", "kind": "store" },
    { "id": "ui", "label": "portal ui (Next)", "sub": "ui-toolkit, GFS brand", "kind": "service" },
    { "id": "sel", "label": "Selector", "sub": "ClientShipService.asmx, FedEx", "kind": "external" },
    { "id": "pr", "label": "Pack-station printers", "sub": "ZPL/EPL, TBC", "kind": "external" }
  ],
  "edges": [
    { "from": "wms", "to": "vm", "label": "CSV over SFTP" },
    { "from": "vm", "to": "gcs", "label": "GCS-native writes" },
    { "from": "gcs", "to": "app", "label": "object notification" },
    { "from": "app", "to": "db" },
    { "from": "ui", "to": "app", "label": "API" },
    { "from": "app", "to": "sel", "label": "validate, book, cancel, commit" },
    { "from": "ui", "to": "pr", "label": "labels (approach TBC)", "style": "dashed" }
  ] }
```

**The monolith (`apps/svc`) is one Go binary.** It holds:
- the HTTP API;
- the import pipeline (parse, stage-1 and stage-2 validation, partial import);
- the DSL and mapper ported from Fuse;
- the Selector client;
- labels and printing;
- the Manhattan export;
- tenancy and auth.

**SFTP is a second command in the same Go module,** `cmd/sftp`, deployed on a MIG behind a TCP load balancer, because Cloud Run serves HTTP only. It's copied from sftp-connector's Go SFTP host (`apps/host`), which replaced the Fuse VM on dev on 2026-10-27. The copy is single-user: the authorised key and the host keys are in Secret Manager, and there's no provisioning. Uploads are written straight to GCS, and a storage notification hands each one to the HTTP svc.

**Fuse building blocks are copied, not depended on:**
- the rules-engine DSL, ported to Go with a conformance corpus taken from the TS engine;
- the CONNECTOR_MAPPING config shape (rules, defaults, dictionaries);
- the Go SFTP host and its `sftp-host` IaC;
- selector-adapter's Go Selector client.

**Platform:**
- ilg-merak `svc-template`: Go `svc` plus Next `ui`, with the `go-runtime` and `node24-runtime` golden images and `terraform-modules` `compute/cloud-run`.
- The IAM-only Cloud SQL module from the [[Config Service Cloud SQL/Overview|Config Service Cloud SQL]] programme (M1/M2).

## Strategy
Sequenced to match Wilders' build phases:
1. **Foundations (A):** the repo, Cloud SQL, tenancy and auth, and the Selector client.
2. **Headless path (B), aimed at 9 Nov:** an SFTP drop to a label with no UI. Done means TCA's 50 test orders run end to end on the new FedEx account, with every failure reported per row.
3. **Customer view (C):** the four tabs and printing.
4. **Prod (D).** There's no cutover inside this programme. Switching TCA from DC is a business call taken outside it.

## Proposed answers to Wilders' G6–G9 (for Thu 29 Oct)
- **G6, logins:**
  - **Tenancy.** One tenant per customer. Every table carries `tenant_id`, enforced in the repositories, and a second dummy tenant proves isolation.
  - **Accounts.** Per-person accounts held in Postgres, created by GFS, with no self-signup. That's cheap, and it records who labelled, cancelled or manifested what.
  - **Fallback.** One login per pack station.
- **G7, manifest:**
  - The Tab 2 button calls Selector `CommitShipments` for the tenant's FedEx service group.
  - Selector's auto-commit stays on as the backstop.
  - Tab 3 reconciles against `DailyShipQuery`, so auto-committed shipments still move across.
  - To confirm with Chris Cumings.
- **G8, who builds and where:**
  - Harry builds it, in an `ilg-merak` repo.
  - Hosted in the ilg-merak GCP projects, which are US-first and suit a US customer.
  - It's "part of, but not in, Fuse".
- **G9, printing:**
  - Selector returns label images in the format its `PrintSpecification` asks for (ZPL or PDF).
  - The baseline is a browser download or print with nothing installed.
  - Silent direct-to-printer printing is a spike once the printer models are known. The candidates are WebUSB from Chrome, and Zebra Link-OS printers dialling out to the service. Both avoid QZ Tray.

## Scar tissue
- **Cloud Run serves HTTP only**, so the SFTP command runs on a MIG, as sftp-connector's host does. Health-check its `/healthz` on 8080, not TCP:22: COS's own sshd answers port 22 while an instance boots.
- **Tracking numbers go into CSV exports as quoted text.** DC's export shows Excel turning them into `1.5501E+13`.
- **Selector's CSV import fails the whole file on one bad line.** That's why the portal validates and imports partially.

## Next
Close the gates the headless path needs: G1 row grain, G3 the US/CA FedEx sample, G7 direction. Agree the stack decisions in the Migration State Decision log. Then **A1** (the repo), driven by `waypoint-programme`.
