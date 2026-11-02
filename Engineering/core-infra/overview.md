---
tags:
- waypoint
- core-infra
verified: '2026-10-13'
verified_sha: 684535e
verified_paths:
- README.md
- iac/projects/core-infra
- iac/projects/root.hcl
- iac/env
- .github/workflows
- mise.toml
title: core-infra — overview
thesis: 'core-infra is the Terraform stack for Fuse trust and secrets that no single
  service owns: the GitHub deploy trust, the config-service API key secret, cross-environment
  state reads and two storage buckets.'
confidence: high
---
# core-infra — overview

```orient-bluf
{ "v": 1, "bluf": "core-infra is the Terraform stack for Fuse trust and secrets that no single service owns: the GitHub deploy trust, the config-service API key secret, cross-environment state reads and two storage buckets.", "confidence": "high", "action": "Treat its outputs as a contract: renaming one breaks every service that reads this stack's remote state." }
```

## Responsibility

- **GitHub deploy trust.** One Workload Identity pool trusts every repository owned by three GitHub orgs. Those runs can impersonate the environment's deploy service account [2][10].
- **Secrets.** It creates the config-service API key secret, which at least five services read by reference [1][6][8][9]. It also creates a KMS key and two further secrets, whose readers are not in the fleet's code (see below) [1].
- **Cross-environment state reads.** Each environment's deploy identity can read the other environment's Terraform state bucket [3].
- **Two buckets.** A public media bucket, and a private stock-sync export bucket that snap-adapter and the Shopify egress service use [4][9].
- **DNS: dead code.** `dns.tf` still builds a zone, but registrar delegation moved to `ilg-platform/core-infra` [5].

## Why it exists separately

Fleet-wide trust and key material needs a home that is not one service's `iac/`. Putting it in a service repo would make that service the accidental owner of the whole fleet's deploy trust. Every service reads from here by `terraform_remote_state`, so one stack holds the shared values and CI secrets need no copies [3][7].

## Neighbours

```orient-flow
{ "v": 1, "title": "core-infra in context",
  "nodes": [
    { "id": "gh", "label": "GitHub Actions", "sub": "gfs-bifrost, ilg-platform, ilg-tech-services", "kind": "external", "ev": [10] },
    { "id": "core", "label": "core-infra", "sub": "Terraform + Terragrunt", "kind": "service", "service": "core-infra", "tone": "accent", "ev": [2] },
    { "id": "wif", "label": "WIF pool github-actions", "sub": "org-level trust", "kind": "store", "ev": [2] },
    { "id": "sec", "label": "config-service API key secret", "kind": "store", "ev": [1, 6] },
    { "id": "kms", "label": "KMS key + 2 AES secrets", "sub": "no reader in fleet code", "kind": "store", "ev": [1] },
    { "id": "bkt", "label": "stock-sync export bucket", "kind": "store", "ev": [4] },
    { "id": "tfs", "label": "tfstate buckets", "sub": "peer-env read grants", "kind": "store", "ev": [3] },
    { "id": "cs", "label": "config-service", "kind": "service", "service": "config-service", "ev": [8] },
    { "id": "cons", "label": "snap-adapter, shopify-connector, sftp-connector, wms-gateway", "kind": "external", "ev": [9] },
    { "id": "dns", "label": "dns.tf zone", "sub": "decommissioned", "kind": "store", "tone": "alert", "ev": [5] }
  ],
  "edges": [
    { "from": "gh", "to": "wif", "label": "OIDC token" },
    { "from": "core", "to": "wif" },
    { "from": "core", "to": "sec" },
    { "from": "core", "to": "kms" },
    { "from": "core", "to": "bkt" },
    { "from": "core", "to": "tfs", "label": "IAM only" },
    { "from": "core", "to": "dns", "style": "dashed" },
    { "from": "sec", "to": "cs", "label": "AUTH_API_KEY" },
    { "from": "sec", "to": "cons", "label": "secret ref" },
    { "from": "cons", "to": "bkt", "label": "write / read exports" }
  ] }
```

config-service mounts the API key as `AUTH_API_KEY` [8]. The other four read the secret reference from this stack's state [9]. snap-adapter and the Shopify egress service read the bucket name the same way [9].

## Where the reference lives

[[architecture]] holds the resources, the guardrails and the CI flow. [[known-context]] holds ownership and the DNS history. No `CLAUDE.md` exists.

The `README.md` is mostly the generic repository template. Only its "Cross-environment tfstate access" section is real. The rest names `on-pr.yaml`, a `code/` directory and a `GOOGLE_CREDENTIALS_JSON` secret that this repo does not have [7]. Do not trust it.

## What deliberately isn't here

- **DNS zones and records.** `ilg-platform/core-infra` owns them, and each service owns its own record.
- **The tfstate buckets.** They predate Terraform. This stack only adds IAM bindings to them by name [3].
- **The deploy service accounts' roles.** The tfvars name the accounts. Their project roles are **UNKNOWN** from this repo.
- **Any application.** Nothing here runs, so there is no runtime to observe.

## Evidence

```orient-evidence
{ "v": 1, "items": [
  { "id": 1, "kind": "code", "ref": "iac/projects/core-infra/crypto.tf@684535e" },
  { "id": 2, "kind": "code", "ref": "iac/projects/core-infra/workload-identity.tf@684535e" },
  { "id": 3, "kind": "code", "ref": "iac/projects/core-infra/tfstate-access.tf@684535e" },
  { "id": 4, "kind": "code", "ref": "iac/projects/core-infra/gcs.tf@684535e" },
  { "id": 5, "kind": "code", "ref": "iac/projects/core-infra/dns.tf@684535e" },
  { "id": 6, "kind": "code", "ref": "iac/projects/core-infra/outputs.tf@684535e" },
  { "id": 7, "kind": "code", "ref": "README.md@684535e" },
  { "id": 8, "kind": "url", "ref": "https://github.com/gfs-bifrost/config-service/blob/63babd7/iac/projects/config-service/remote.tf", "note": "config-service reads config_service_api_key_ref" },
  { "id": 9, "kind": "url", "ref": "https://github.com/gfs-bifrost/snap-adapter/blob/b16942a/iac/projects/snap-queue-polling-service/remote.tf", "note": "reads the API key ref and the export bucket name" },
  { "id": 10, "kind": "code", "ref": "iac/env/global.tfvars@684535e" }
] }
```
