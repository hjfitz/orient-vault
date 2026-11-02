---
title: "ilg-platform DNS Migration — Overview"
status: signed-off-decommission-pending
verdict: shipped
owner: "Harry Fitzgerald"
services: ["core-infra", "gcp-config", "collector", "config-service", "distraction-dashboard", "fapi", "fuse-mcp-server", "fuse-mocker", "fuse-ui", "ilg-secure-notes", "replay-service", "sandbox", "secops-reporting", "sftp-connector", "shopify-connector", "snap-mcp-server", "fuse-billing"]
created: "2026-09-14"
updated: "2026-09-16"
tags: [bifrost, ilg-platform, dns, cloud-dns, migration, terraform]
---
# ilg-platform DNS Migration — Overview

Move the Cloud DNS hosting for **`freightops.dev`** (dev) and **`ilg.software`** (prod) out of the
Bifrost projects (`bifrost-dev-global1` / `bifrost-prod-global1`, zones `core-infra-dev-zone` /
`core-infra-prod-zone`, owned by `gfs-bifrost/core-infra`) and into **`ilg-platform-ec02`**, owned by
the new `ilg-platform/core-infra` stack — so the platform team's project owns the platform's domains.

## Deliverables
- [[ilg-platform DNS Migration/Migration State|Migration State]] — the live source of truth for progress
- Both zones live in `ilg-platform-ec02`, Terraform-managed by `ilg-platform/core-infra` (`dev/core-infra`
  and `prod/core-infra` state paths in `ilg-platform-tfstate`), exposing `dns_zone_name` /
  `dns_name_servers` outputs exactly as `gfs-bifrost/core-infra` does today
- Every consuming service creates its record in the new zone, reading the zone name from ilg-platform's
  state; `gfs-bifrost/core-infra` no longer holds a DNS zone

## Verdict
**Shipped, signed off 2026-09-16** (Harry). Both domains cut over with zero client-visible downtime; all
18 real consuming services adopted (16 found by the original per-repo survey, 2 — `developer-portal`,
`fuse-billing` — found late by a broader GitHub-code-search sweep after the survey missed them). The two
go/no-go conditions from the original verdict both held: the state-only adoption mechanism proved clean on
the pilot (**C01**, fuse-mocker) and every unit after, and the nameserver-shard question (**R3**) resolved
cleanly (new zones landed on distinct shards from the old, confirmed empirically on both envs).

**Sign-off does not cover D (decommission).** That's a separate, already-scoped tail task gated on **G6**
(a 7-day quiet clock on the old zones, earliest 2026-09-22) — nothing to action until then. See the State
doc's Unit status for what D1/D2 still require, including the cross-org check below.

**One real miss, corrected, not swept under**: this programme's own completeness checks were scoped to
`gfs-bifrost` and `ilg-platform` only. A third org, `ilg-tech-services`, also depends on both zones
(`route-check` → `routes.*`, `tools-api` → `tools.ilg.software`) and was missed entirely — the resulting
outage was root-caused and fixed by `ilg-tech-services`' own Kyle Chandler, not by this programme. Full
account in the State doc's 2026-09-16 decision log entry. **D1 must not assume this ledger's "no unowned
records" claim is complete** — it wasn't, once.

## Why this needs a programme
The zone is one resource, but its records are not centralised: **16 Terraform project directories across
15 repos** each create their own `google_dns_record_set` against it, every one with
`project = var.gcp_project` (their own Bifrost project) and the zone name read from
`gfs-bifrost/core-infra`'s remote state. Relocating the zone therefore means a cross-org IAM grant per
deploy identity, a state-read grant onto `ilg-platform-tfstate`, one PR per project directory, and a
registrar nameserver flip that is a **one-way door** for every public hostname on both domains at once.
The two domains are also the dev/prod split of the same fleet, so the prod flip has a rehearsal available
— the dev domain — and the programme is sequenced to use it.

## Strategy
**Dual-host, mirror, then flip; adopt records afterwards with state-only surgery.**

1. **Foundations (A)** — unblock `ilg-platform/core-infra`'s CI (WIF admission in `gcp-config`; the
   app-key secret is a manual gate), create the two zones there with `core-infra`'s own central records
   ported, and grant the two Bifrost deploy SAs (`github-integration@bifrost-dev-global1`,
   `github-runner@bifrost-prod-global1`) read on `ilg-platform-tfstate` and **zone-level** record-write
   on the new zones — mirroring `gfs-bifrost/core-infra`'s `tfstate-access.tf`, one org over.
2. **Mirror & cutover, dev first (Bd, then Bp)** — seed the new zone with a one-shot, unmanaged copy of
   every record in the old zone; diff the two zones and query the new nameservers directly for every
   name; flip NS at the registrar; watch propagation until a gate clears. Both zones serve identical
   answers for the whole window, so a resolver on either NS set gets the same result — that is what makes
   the flip safe. `ilg.software` does not start until the dev pilot has proven the adoption mechanism.
3. **Service adoption (C)** — one PR per project directory: repoint the remote-state read to
   `ilg-platform-tfstate` (`${env}/core-infra`), set `project = "ilg-platform-ec02"`, and adopt the
   already-seeded record with an `import` block plus a `removed { destroy = false }` block for the old
   one. **No service PR creates or destroys a DNS record** — pure state surgery, order-independent, and
   the old zone stays intact underneath. Services on both envs use the existing deploy flow: merge once
   dev propagation is done (dev auto-applies), hold the `terraform-prod` approval until prod propagation
   is done.
4. **Decommission (D)** — only when every C unit is merged and both propagation gates are long past:
   remove the zones, records and `dns_*` outputs from `gfs-bifrost/core-infra`.

Alternatives considered are in the State doc's decision log (dual-write per service — twice the PRs;
transitional ownership in `core-infra` — double-ownership hazard or two PRs per service).

## Downtime posture
Nothing client-visible changes: no IP, hostname, certificate or load balancer moves — only which
nameservers answer. Dual-hosting means a resolver on either NS set gets the same answer. Downtime can
therefore come from exactly five places, each with a named control in the State doc:

| Path | Control |
|---|---|
| Mirror incomplete (a name missing in the new zone) | Bd2/Bp2 type-complete diff, re-run last thing before the flip |
| Drift while dual-hosted — a service writes to the old zone (R2) | Freeze scoped seed→C-merge, hourly diff as monitor, C landed as one batch |
| Registrar typo at the flip (R9) | `dig +trace` within minutes; old NS set recorded as the rollback |
| Nameserver shard collision on zone creation (R3) | Dev first, watched `dig`, delete-the-empty-zone revert in seconds |
| Old zone deleted while resolvers are still on it (R10) | Gate G6 — elapsed time plus per-zone query-count metric |

The per-service adoption step (C) is state-only and cannot cause downtime by construction.

## Scar tissue
- **Nothing touches a record in the OLD zone until that domain's propagation gate is ticked.** The old
  zone is authoritative for some resolvers until then; a destroyed record there is an outage.
- **Adoption is state-only.** `import` + `removed(destroy = false)`, never a replace. A plan showing a
  DNS create or destroy in a C unit is wrong by definition.
- **The registrar flip is a one-way door** — revertible only by flipping back, with the same propagation
  lag. Confirm with Harry before each flip (`waypoint-programme` stop condition).
- **dev domain end-to-end before prod starts.** `freightops.dev` is the rehearsal; `ilg.software` waits
  on the pilot.
- **Anything created in `ilg-platform/core-infra` carries `var.env` in its name** — both env state paths
  target the same project (see that repo's `root.hcl`). Zone names are `core-infra-${env}-zone`.
- **The two zones have real consumers outside `gfs-bifrost`/`ilg-platform`.** `ilg-tech-services` (at
  least `route-check` and `tools-api`, via `ilg-tech-services-iac`) reads and writes these same zones
  through the `dnsRecordWriter` custom role (see `ilg-platform/core-infra#5`). Any future zone-level
  change — and D1 specifically — must not assume the two-org service list in this doc is the complete
  consumer set.

## Next
**Nothing active.** D1/D2 are scheduled, not started — gated on **G6** (earliest 2026-09-22). When that
clears, drive them with `waypoint-programme`, and confirm the `ilg-tech-services` cross-org check above
before deleting either old zone.
