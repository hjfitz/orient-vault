---
title: "Parcel Portal — multi-customer (ideas)"
status: ideas
owner: "Harry"
created: "2026-10-29"
tags: [bifrost, merak, parcel-portal]
---
# Parcel Portal — multi-customer (ideas)

Thinking, not a plan. Harry, 29 Oct 2026: stay single-customer for now (carrier config in environment variables), but think about building this for many customers, like SaaS. System docs: `Systems/parcel-portal/`.

## Already multi-customer
- Every table carries `tenant_id`, queries take the tenant from the request context, and a static test enforces it.
- Per-person accounts with `customer` and `gfs_admin` roles; an email belongs to one tenant.
> SUPERSEDED 2026-11-02 — the carrier account is per tenant again, set on the Customers page, with its password encrypted on `carrier_connection` (unit C12).
- Per-tenant settings: mapping, timezone, export options, packaging presets, bench printers. The `carrier_connection` table stays for the per-tenant path even while the account comes from environment variables.
- Imports find their tenant by folder (`<slug>/inbound/`).
- WebUSB printing doesn't care which tenant is signed in.

## What breaks at customer #2
1. **SFTP is single-user.** The username, key and tenant are fixed in the host's config. sftp-connector's host, which this one was copied from, is multi-user: bring back a user → tenant table, keys per user and provisioning.
2. **Setup is engineer work.** Tenants, users and mapping are API only, and the mapping is the biggest cost per customer. This needs a GFS-run admin console, not self-signup, because the carrier contracts are GFS's.
> SUPERSEDED 2026-11-02 — done in unit C12: an admin sets each customer's account on the Customers page, and svc encrypts the password onto `carrier_connection` (AES-256-GCM, one Terraform-generated key; no KMS).
3. **Carrier credentials.** Hand-made secrets don't scale. Either the admin page that writes the Secret Manager secret and the row in one step, or an encrypted column (Cloud KMS).
4. **Customers that aren't TCA-shaped.**
   - **Carrier:** several services per account, a list to pick from, and rules for choosing (destination, weight).
   - **Export:** a per-tenant layout, which means an outbound mapping in the same DSL.
5. **One site per tenant.** The timezone is on `tenant`. A second warehouse needs a site level for the timezone, origin address, carrier account, printers and SFTP drop. That's much cheaper to add before more tables hang off `tenant`.

## Decisions first
- **Who is the tenant: shipper or operator?** Gate G10 ([MKP-32](https://globalfreight.atlassian.net/browse/MKP-32)), Wilders. If Yusen's staff would use one login across clients, the model is operator → client → site.
- **Intake here or in Fuse?** G7, Oli Denton. One shape: Fuse does SFTP intake and mapping, and the portal becomes labelling, manifest and export over Fuse's canonical sales orders. Building multi-user SFTP and a mapping editor here builds a second Fuse, so this comes before items 1 and 2.
- **Are we replacing Despatch Cloud?** A multi-customer version is what GFS buys from DC today, which makes it a product decision for Oliver.

## Cheap now, expensive later
- **Postgres row-level security** as a second check behind the static test.
- **The tenant on every log line and metric**, so monitors and support can filter by customer.
- **No more per-site columns on `tenant`.**
- Later: per-tenant quotas (batch size, Selector rate), usage from `shipment` for billing, an audited "view as tenant" for support, and data residency once a non-US customer arrives (everything runs in `us-central1`).
