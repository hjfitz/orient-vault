---
tags:
- waypoint
- parcel-portal
title: parcel-portal — known context
verified: '2026-10-29'
verified_sha: null
verified_paths: []
---
# parcel-portal — known context

What source can't tell you. Programme progress and the full decision log are in `Bifrost/Parcel Portal/Migration State.md`; this holds the durable context behind the code.

## History
- **Requirements:** Oliver Wilders, v0.1 then v0.2 (28 Oct 2026). The customer is **TCA**, shipping from one Yusen US site with 3–4 pack stations, FedEx only, US→US and US→CA, no dangerous goods. Manhattan SCALE drops CSVs and reads a day-end export back.
- **A parallel route, not the cutover.** Despatch Cloud goes live for TCA on Mon 9 Nov 2026. Switching to the portal is Oliver's call with Oli Denton, if DC hurts.
- **Built in a day and a half** (27–28 Oct) by agents under Harry's standing autonomy, unit by unit (A1–A4, B1–B5, C1–C8, D1 prep), merged with merge commits.
- **Made from `ilg-merak/svc-template`.** The root README and AGENTS.md still describe the template. The first push to `main` deployed the template's ui before `root.hcl` was renamed, and was cancelled before Terraform.
- **Stack choices** (Harry): Postgres on Cloud SQL with IAM auth, not Firestore; the Go SFTP host from sftp-connector, not an OpenSSH VM; one Go module for API and SFTP; Next.js with ui-toolkit and GFS branding.

## Constraints
- **Outside Fuse on purpose, pending G7.** Oli Denton said CSV mapping and ingestion belong in Fuse as the one ingestion point; the portal copies Fuse's pieces instead. Prod (D1) waits on his agreement.
- **Selector is GFS's carrier layer.** The sandbox (`sandbox.gfsdeliver.com/ClientServer_450`, TEST/TEST, HERMES 2DAY, contract 123456) takes **GB addresses only** and is a shared account: book and void only. FedEx, US and CA are untested until TCA's FedEx account exists (MKP-10).
- **Selector's own CSV import fails the whole file on one bad line**, which is the reason the portal does partial import.
- **Customer handling is internal only** until Oliver says otherwise: no contact with TCA, Yusen US or DC.
- **ship.gfsdeliver.com** is GFS's white-label Despatch Cloud with a live account. Look only.
> SUPERSEDED 2026-11-02 — each customer's carrier account is set on the Customers page again (unit C12). The password is stored on the row, encrypted by svc (AES-256-GCM, bound to the tenant) with one key Terraform generates into `svc-parcel-carrier-key` (`prevent_destroy`; losing it loses every stored password).
- **Carrier config is going to environment variables** for the single-customer phase (Harry, 29 Oct 2026); the `carrier_connection` table stays for the multi-customer path (snapshot 2026-10-29).

## Fragility
- **Batch dispatch vs Cloud Run's timeout.** A batch stops starting orders after 3 minutes so the last 60-second call ends inside the 5-minute request timeout. Raising either side without the other breaks that.
- **The ui image builds from the repo root** to include `packages/label-print`. `dockerfile.dockerignore` keeps the rest out; a careless context change bloats or breaks the image.
- **WebUSB on Windows** needs the printer's driver swapped to WinUSB (Zadig) when Windows claims it. Firefox has no WebUSB and always falls back to print-to-screen.
- **Excel turns tracking numbers into `1.5501E+13`.** The export writes them as text (optionally `="…"`).
- **Despatch date is the site's local day** (`tenant.timezone`, default `America/New_York`), not UTC's; Selector and the export both depend on it.
- **The runtime SA has `cloudsqlsuperuser`** so startup migrations can run DDL. A separate migrator SA is a follow-up.

## Surprises
- svc's Cloud Run invoker grant lives in the **ui** project's Terraform, so a fresh env applies svc then ui without a cycle.
- An ilg-merak repo must name `repo` in `iac/projects/root.hcl`; `basename(get_repo_root())` is `workspace` in CI, so a derived repo would share the template's state.
- On COS the OS's own sshd answers TCP:22 while an instance boots, which is why the SFTP health check is HTTP `/healthz` on 8080.

## Unknowns
- **Who is the tenant: the shipper (TCA) or the warehouse operator (Yusen)?** It decides whether a multi-customer portal is *tenant* or *operator → client → site*. Wilders' call.
- **Does intake stay here or move to Fuse (G7)?** Oli Denton's call.
- **TCA's real printers** (models, ZPL vs EPL, DPI). Tested in the office on 29 Oct 2026 with GFS's printers only (snapshot 2026-10-29).
- **Row grain, export layout, US/CA sample, manifest semantics** (gates G1, G2, G3, G5 / MKP-5, 6, 7, 9).
- **Whether it ever replaces Despatch Cloud for other GFS customers.** See `Bifrost/Parcel Portal/Multi-customer.md`.
