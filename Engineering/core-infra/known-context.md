---
tags: [waypoint, core-infra]
verified: '2026-08-24'
verified_paths: []
title: core-infra — known context
---

# core-infra — known context

`known-context.md` is exempt from staleness checks — this is interview/investigation
truth, not a claim about current source. Re-verify against code before trusting a
specific implementation detail below.

## Ownership

Wider Fuse team — same shared-ownership pattern as `bifrost-pubsub` and
`pkg-node` (confirmed 2026-08-24), despite this repo holding some of the
fleet's most sensitive plumbing: KMS key material, cross-org GitHub
deploy trust, and cross-environment state access.

## config-service's real credential-encryption key lives here, not there

Verified directly (2026-08-24): the KMS crypto key and Secret Manager
secrets backing config-service's customer-credential encryption
(`config_service_aes_key`, `config_service_api_key`,
`customer_credential_aes_key`) are all defined in this repo's
`crypto.tf`, not in `config-service`'s own IaC. This is exactly the kind
of dependency that's invisible unless you go looking — config-service's
own known-context (in this vault) doesn't mention it, and it should:
anyone touching credential encryption on either side needs to know the
actual key material's home is here.

## The residual DNS records are confirmed still needed, not cruft

`docs`, `royalmail`, `apiky`/`api.apiky`/`web.apiky`,
`rest-preview.selector`, and `bifrost-tech` (plus the apex record and a
couple of GitHub-verification TXT records) are what's left in this zone
after most service DNS was decentralized to per-service IaC. **Confirmed
directly (2026-08-24): these are still live and needed**, not leftover
cruft from before the decentralization — don't propose removing any of
them without checking what currently depends on each one specifically.

## WIF trust has grown org-by-org, each addition a named, deliberate commit

The `allowed_repository_owners` allowlist wasn't designed upfront with
every consumer in mind — it's grown incrementally, each org added in its
own commit (`gfs-platform` in one, `ilg-tech-services` in another). If a
new org needs GCP deploy access via this mechanism, that's the pattern to
follow: a small, explicit, named commit adding one owner to the variable
— not a broader rework.

## Unknowns

- Whether any further orgs are expected to need WIF trust here beyond
  the three currently allowlisted (`gfs-bifrost`, `gfs-platform`/
  `ilg-platform`, `ilg-tech-services`).
