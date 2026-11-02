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
title: core-infra — architecture
thesis: 'One Terragrunt stack per environment holds the shared pieces: a GitHub OIDC
  pool trusting three orgs, the config-service secrets and KMS key, peer-environment
  state read grants and two buckets, applied by a CI workflow that gates only prod.'
confidence: high
---
# core-infra — architecture

```orient-bluf
{ "v": 1, "bluf": "One Terragrunt stack per environment holds the shared pieces: a GitHub OIDC pool trusting three orgs, the config-service secrets and KMS key, peer-environment state read grants and two buckets, applied by a CI workflow that gates only prod.", "confidence": "high", "action": "Never rename an output, and treat any change to allowed_repository_owners as granting deploy access to a whole GitHub org." }
```

## Guardrails

- [policy:G1] Add an org to `allowed_repository_owners` only in its own small named commit. The trust is org-wide, so each owner added lets every repository that org owns impersonate the deploy service account.
  — paths: iac/env/global.tfvars, iac/projects/core-infra/workload-identity.tf
- [technical:G2] The tfstate buckets predate Terraform. This stack adds IAM bindings to them by name and never creates, imports or manages the buckets.
  — paths: iac/projects/core-infra/tfstate-access.tf
- [technical:G3] `customer_credential_aes_gcm_key` carries `prevent_destroy`, and the customer-managed-encrypted secret depends on it. Keep the explicit `depends_on` on the Secret Manager service-identity binding, or the secret cannot be created.
  — paths: iac/projects/core-infra/crypto.tf, iac/projects/core-infra/iam.tf
- [contract:G4] Output names are a remote-state contract. `config_service_api_key_ref` and `stock_sync_export_bucket_name` are read by other stacks, and removing or renaming one breaks their plans.
  — paths: iac/projects/core-infra/outputs.tf
- [policy:G5] Add no DNS here. The zone is decommissioned and `dns.tf` awaits removal. New records belong in `ilg-platform/core-infra`.
  — paths: iac/projects/core-infra/dns.tf, iac/projects/core-infra/outputs.tf
- [technical:G6] `required_version` in `providers.tf` and `tf_version` in every `on-push.yaml` job must agree. `mise.toml` pins an older Terraform for local runs only.
  — paths: iac/projects/core-infra/providers.tf, .github/workflows/on-push.yaml, mise.toml

## Layout

**CONFIRMED** One stack, `iac/projects/core-infra`, is applied once per environment by Terragrunt. `root.hcl` sets the state bucket and prefix (`<env>/core-infra`), and loads `env/global.tfvars` then `env/<env>.tfvars` [16]. Dev and every non-prod environment use `gfs-bifrost-tfstate` in `bifrost-dev-global1`. Prod uses `gfs-bifrost-tfstate-prod` in `bifrost-prod-global1` [16].

```
iac/env/{dev,prod,global}.tfvars
iac/projects/root.hcl             state bucket, tfvars wiring
iac/projects/core-infra/
  crypto.tf              KMS key ring + crypto key, three Secret Manager secrets
  workload-identity.tf   GitHub Actions OIDC pool + provider, multi-org trust
  tfstate-access.tf      cross-environment tfstate bucket IAM bindings
  dns.tf                 zone + records, decommissioned (see DNS)
  gcs.tf                 a media bucket (whole-bucket public read) + a private stock-sync export bucket
  iam.tf                 Secret Manager service-identity KMS binding
  main.tf (empty) / providers.tf / variables.tf / outputs.tf / terragrunt.hcl
```

```orient-flow
{ "v": 1, "title": "What the stack provisions",
  "nodes": [
    { "id": "core", "label": "core-infra", "sub": "one stack per env", "kind": "service", "service": "core-infra", "tone": "accent", "ev": [16] },
    { "id": "wif", "label": "WIF pool + provider", "sub": "github-actions / github-oidc", "kind": "store", "ev": [3] },
    { "id": "sa", "label": "Deploy SA", "sub": "named in tfvars, not created here", "kind": "external", "ev": [10, 11] },
    { "id": "kms", "label": "KMS key + keyring", "sub": "prevent_destroy", "kind": "store", "ev": [1] },
    { "id": "sec", "label": "3 Secret Manager secrets", "kind": "store", "ev": [1] },
    { "id": "tfs", "label": "tfstate buckets", "sub": "peer-env objectViewer", "kind": "store", "ev": [4] },
    { "id": "med", "label": "media bucket", "sub": "allUsers read", "kind": "store", "ev": [6] },
    { "id": "exp", "label": "stock-sync export bucket", "sub": "private", "kind": "store", "ev": [6] },
    { "id": "dns", "label": "DNS zone", "sub": "decommissioned", "kind": "store", "tone": "alert", "ev": [5] }
  ],
  "edges": [
    { "from": "core", "to": "wif" },
    { "from": "wif", "to": "sa", "label": "workloadIdentityUser" },
    { "from": "core", "to": "kms" },
    { "from": "kms", "to": "sec", "label": "encrypts one secret" },
    { "from": "core", "to": "tfs", "label": "bindings only" },
    { "from": "core", "to": "med" },
    { "from": "core", "to": "exp" },
    { "from": "core", "to": "dns", "style": "dashed" }
  ] }
```

## Crypto: KMS key and secrets

**CONFIRMED** `crypto.tf` defines a global key ring (`bifrost-customer-keyring`) with one symmetric crypto key (`aes-gcm-key`, `prevent_destroy = true`). It also defines three Secret Manager secrets named `core-infra-<env>-aes-key`, `core-infra-<env>-api-key` and `core-infra-<env>-customer-credential-aes-key`. Only the last is encrypted with the KMS key; the other two use automatic replication [1]. `iam.tf` grants the Secret Manager service identity `roles/cloudkms.cryptoKeyEncrypterDecrypter` on the key, and the secret waits on that binding through `depends_on` [2]. The stack creates secrets but no secret versions, so values enter out of band.

**CONFIRMED** Of the three outputs (`config_service_aes_key_ref`, `config_service_api_key_ref`, `customer_credential_aes_key_ref`), only `config_service_api_key_ref` has a consumer in the fleet's code [7]. config-service mounts it as `AUTH_API_KEY` [18]. snap-adapter, shopify-connector, sftp-connector and wms-gateway read the same reference [19][20][24][25].

**UNKNOWN** Who reads `aes-key` and `customer-credential-aes-key`. No repository at its default branch references those outputs or secret names, and config-service's code has no KMS or encryption call. The earlier belief that they back config-service's credential encryption has no support in code. The missing evidence is the runtime that fetches the secrets by name.

## Workload Identity Federation

**CONFIRMED** `workload-identity.tf` creates one pool (`github-actions`) and one OIDC provider (`github-oidc`, issuer `token.actions.githubusercontent.com`) per project [3]. The `attribute_condition` joins one `assertion.repository_owner == "<org>"` clause per entry in `allowed_repository_owners` with `||`. `google_service_account_iam_member` binds `roles/iam.workloadIdentityUser` on the environment's deploy service account to each org's `principalSet` [3]. The list is `gfs-bifrost`, `ilg-platform`, `ilg-tech-services` [9]. `ilg-tech-services` is where `route-check` lives, and it gets GCP deploy access through this mechanism. The mapping also exposes `attribute.repository`, `attribute.actor` and `attribute.ref`, but neither the condition nor the bindings use them [3].

**CONFIRMED** Service repos name the provider by project number in their deploy workflows. sftp-connector uses `661226359806` for dev jobs and `793257477381` for the prod job [21].

## Cross-environment tfstate access

**CONFIRMED** The tfstate buckets predate Terraform and are not created here. `tfstate-access.tf` grants each environment's tfstate bucket `roles/storage.objectViewer` to the peer environment's deploy service account, from `cross_env_tfstate_reader_sas` [4]. In dev tfvars the prod deployer (`github-runner@bifrost-prod-global1`) reads dev state, so prod-only stacks such as fuse-mcp can resolve dev outputs. In prod tfvars the dev deployer (`github-integration@bifrost-dev-global1`) reads prod state [10][11]. The purpose is `terraform_remote_state` across environments instead of copying values into CI secrets [4][17].

## DNS: decommissioned

**ASSESSED** This zone no longer serves traffic. The ilg-platform DNS Migration programme moved the zones and central records to `ilg-platform/core-infra` in project `ilg-platform-ec02`, with the same zone names, and cut registrar delegation over on 2026-09-15 and 2026-09-16 [22]. This rests on the programme's own state doc, because nothing in this repo says so. Service repos now read `dns_zone_name` from the ilg-platform stack [18][19][20].

**CONFIRMED** `dns.tf` is still live code at this ref. It creates `<env>-zone` for `var.domain` and a `google_dns_record_set` per `dns_records` entry [5]. Every record is dev-only: `prod` is empty for all of them, so the prod zone carries no records. The dev set is the apex plus `docs`, `royalmail`, `apiky`, `api.apiky`, `web.apiky`, `rest-preview.selector`, `bifrost-tech` and three GitHub verification TXT records [5]. The `dns_zone_name` and `dns_name_servers` outputs remain [7].

**CONFIRMED** `dns.tf` also holds `google_dns_managed_zone_iam_member.zone_admins`: zone-scoped `roles/dns.admin`, one additive member grant per entry in `dns_zone_admin_members`. It is a member grant, so it cannot strip a grant made outside Terraform. The one entry is the shared `ilg-tech-services` terraform-runner service account [5][9]. The variable text forbids `allUsers` and `allAuthenticatedUsers` [8].

**ASSESSED** Removal (the programme's D1 unit) deletes `dns.tf` and the two DNS outputs, and waits on a quiet-period check and on confirming `ilg-tech-services` is off the zone [22]. The code is still present at this ref, so D1 has not landed here.

## GCS

**CONFIRMED** `gcs.tf` creates two buckets, both with uniform bucket-level access and `force_destroy = false` [6]:

| Bucket | Public access | IAM |
|---|---|---|
| `core-infra-<env>-media` | `inherited`, plus `allUsers` `roles/storage.objectViewer` on the whole bucket | no other bindings |
| `core-infra-<env>-stock-sync-export` | `enforced` (private) | `objectCreator` per `stock_sync_export_writer_sas`, `objectViewer` per `stock_sync_export_reader_sas` |

**CONFIRMED** There is no `public/` prefix condition. The `media_bucket_url` output appends `/public`, but the grant covers every object [6][7]. **ASSESSED** No repository at its default branch reads `media_bucket_name` or `media_bucket_url`, so its consumer is **UNKNOWN**.

**CONFIRMED** Writers per environment are snap-queue-polling-service's and the Shopify egress service's Cloud Run SAs (`snap-polling-service-<env>-cr`, `shopify-egress-<env>-cr`). The reader is the Shopify egress SA only [10][11]. The egress service reads the poller's export and writes Shopify's bulk-mutation result beside it. Both services take the bucket name from the `stock_sync_export_bucket_name` output [19][20]. `iam.tf` is otherwise only the KMS binding above [2].

## Build and deploy

- **CONFIRMED** Two workflows only. `on-push.yaml` ("Deploy") runs on pushes to `main` or `master`. It applies dev, plans prod, then applies prod with `environment_name: terraform-prod` as the approval gate [12]. `tf-output.yaml` runs a dev `plan` on pull requests that touch `*.tf` or `*.hcl` and comments it on the PR [13]. There is no code-quality, secops or manual-deploy workflow, since there is no application code.
- **CONFIRMED** Terraform `1.9.0` in `providers.tf` and every `tf_version`. Providers `google` and `google-beta` are both pinned to `6.41.0` [14]. `mise.toml` pins Terraform `1.3` and Terragrunt `0.50.8` for local runs [15].
- **CONFIRMED** Both workflows call the reusable `terragrunt.yaml` in `ilg-platform/github-actions` at the rolling tag `0.1-affogato` [12][13]. The reusable workflow authenticates with `credentials_json` unless a `workload_identity_provider` input is set, and these callers set none [23]. They pass `GOOGLE_DEV_SERVICE_ACCOUNT_JSON` or `GOOGLE_PROD_SERVICE_ACCOUNT_JSON`, so CI deploys with long-lived service-account keys [12][13].
- **CONFIRMED** The `README.md` is the generic template apart from its cross-environment state section. It names `on-pr.yaml`, `GOOGLE_CREDENTIALS_JSON` and a `code/` directory that do not exist [17]. No `CLAUDE.md` exists.

## Security notes

- **CONFIRMED** The WIF trust is org-wide with no repository, ref or environment condition [3]. Any workflow in any repository of `gfs-bifrost`, `ilg-platform` or `ilg-tech-services` can mint a token for the deploy service account of the project whose pool it targets. `workload-identity.tf:20-22` builds the condition, and `workload-identity.tf:29-35` binds the principal set. **ASSESSED** The service accounts' project roles are set outside this repo, so the blast radius is **UNKNOWN**.
- **CONFIRMED** Each environment's deploy identity reads the other environment's whole state, secrets included. `prod.tfvars:8` gives the dev deployer read on prod state, and `tfstate-access.tf:12-18` makes the binding. The README states this [4][11][17]. **ASSESSED** Combined with the org-wide trust above, a workflow in any trusted org that can reach the dev deployer can read prod state.
- **CONFIRMED** `gcs.tf:11-15` grants `allUsers` `objectViewer` on the whole media bucket, which also allows listing its objects [6].
- **CONFIRMED** `tf-output.yaml` runs on `pull_request`, not `pull_request_target`, so fork PRs get no secrets. A branch in this repo does get `GOOGLE_DEV_SERVICE_ACCOUNT_JSON`, and `plan` runs provider code from that branch [13].
- **CONFIRMED** The dev apply on push has no environment gate (`on-push.yaml:8-25`). Only prod apply does (`on-push.yaml:55`) [12].
- **CONFIRMED** The reusable workflow is pinned by a mutable tag, not a SHA (`on-push.yaml:12,31,48`, `tf-output.yaml:13`) [12][13].
- **CONFIRMED** No credential is committed. The tfvars hold only service account emails and org names, and the DNS records hold public IPs and verification tokens [5][9][10][11].

## Evidence

```orient-evidence
{ "v": 1, "items": [
  { "id": 1, "kind": "code", "ref": "iac/projects/core-infra/crypto.tf@684535e" },
  { "id": 2, "kind": "code", "ref": "iac/projects/core-infra/iam.tf@684535e" },
  { "id": 3, "kind": "code", "ref": "iac/projects/core-infra/workload-identity.tf@684535e" },
  { "id": 4, "kind": "code", "ref": "iac/projects/core-infra/tfstate-access.tf@684535e" },
  { "id": 5, "kind": "code", "ref": "iac/projects/core-infra/dns.tf@684535e" },
  { "id": 6, "kind": "code", "ref": "iac/projects/core-infra/gcs.tf@684535e" },
  { "id": 7, "kind": "code", "ref": "iac/projects/core-infra/outputs.tf@684535e" },
  { "id": 8, "kind": "code", "ref": "iac/projects/core-infra/variables.tf@684535e" },
  { "id": 9, "kind": "code", "ref": "iac/env/global.tfvars@684535e" },
  { "id": 10, "kind": "code", "ref": "iac/env/dev.tfvars@684535e" },
  { "id": 11, "kind": "code", "ref": "iac/env/prod.tfvars@684535e" },
  { "id": 12, "kind": "code", "ref": ".github/workflows/on-push.yaml@684535e" },
  { "id": 13, "kind": "code", "ref": ".github/workflows/tf-output.yaml@684535e" },
  { "id": 14, "kind": "code", "ref": "iac/projects/core-infra/providers.tf@684535e" },
  { "id": 15, "kind": "code", "ref": "mise.toml@684535e" },
  { "id": 16, "kind": "code", "ref": "iac/projects/root.hcl@684535e" },
  { "id": 17, "kind": "code", "ref": "README.md@684535e" },
  { "id": 18, "kind": "url", "ref": "https://github.com/gfs-bifrost/config-service/blob/63babd7/iac/projects/config-service/remote.tf", "note": "API key ref and the ilg-platform DNS read" },
  { "id": 19, "kind": "url", "ref": "https://github.com/gfs-bifrost/snap-adapter/blob/b16942a/iac/projects/snap-queue-polling-service/remote.tf", "note": "API key ref and export bucket name" },
  { "id": 20, "kind": "url", "ref": "https://github.com/gfs-bifrost/shopify-connector/blob/e9aef9e0/iac/shopify-egress-service/projects/shopify-egress-service/remote.tf", "note": "API key ref and export bucket name" },
  { "id": 21, "kind": "url", "ref": "https://github.com/gfs-bifrost/sftp-connector/blob/a8d34bf/.github/workflows/deploy.yaml", "note": "a service workflow naming the provider" },
  { "id": 22, "kind": "doc", "ref": "Bifrost/ilg-platform DNS Migration/Migration State.md" },
  { "id": 23, "kind": "url", "ref": "https://github.com/ilg-platform/github-actions/blob/d52202b/.github/workflows/terragrunt.yaml", "note": "reusable workflow at 0.1-affogato" },
  { "id": 24, "kind": "url", "ref": "https://github.com/gfs-bifrost/sftp-connector/blob/a8d34bf/iac/projects/bifrost-sftp-connector/remote.tf", "note": "reads config_service_api_key_ref" },
  { "id": 25, "kind": "url", "ref": "https://github.com/gfs-bifrost/wms-gateway/blob/a23a517/iac/projects/wms-gateway/remotes.tf", "note": "reads config_service_api_key_ref" }
] }
```
