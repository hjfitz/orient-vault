---
tags:
- waypoint
- bifrost-pubsub
verified: '2026-10-13'
verified_sha: 700a515
verified_paths:
- README.md
- iac
- .github/workflows
title: bifrost-pubsub — architecture
thesis: One topic module creates every topic as a topic plus a .dlt twin; 17 module
  calls in eight domain files give 34 Pub/Sub topics, published as per-topic outputs
  that consumers read from remote state, with deploys that apply dev and prod behind
  GitHub environments.
confidence: high
---
# bifrost-pubsub — architecture

```orient-bluf
{ "v": 1, "bluf": "One topic module creates every topic as a topic plus a .dlt twin; 17 module calls in eight domain files give 34 Pub/Sub topics, published as per-topic outputs that consumers read from remote state, with deploys that apply dev and prod behind GitHub environments.", "confidence": "high", "action": "Never delete or rename a topic or an output before every consumer's Terraform stops referencing it." }
```

## Guardrails

- [contract:G1] Every topic goes through `iac/modules/topic`, which builds `{domain}.{env}.{topic_name}.v{ver}` and a `.dlt` twin. A name change is a new topic, not a rename. `env` must be `prod`, `dev` or `local`.
  — paths: iac/modules/topic/main.tf, iac/modules/topic/variables.tf
- [contract:G2] The `*.outputs.tf` names are a remote-state contract. Before removing a topic or output, clear every consumer's reference and prove it with a fleet-wide grep of the output names. A missing output surfaces as "Unsupported attribute", not a clean diff.
  — paths: iac/projects/bifrost-pubsub
- [technical:G3] Keep cross-entity topics single. `create_record_request`, `create_record`, `confirmation_ready`, `confirmation_made`, `create_acknowledge` and `create_data_failure` carry every record type, discriminated by the `recordType` attribute. Add no per-entity topic.
  — paths: iac/projects/bifrost-pubsub/creation.pubsub.tf, iac/projects/bifrost-pubsub/confirmations.pubsub.tf, iac/projects/bifrost-pubsub/errors.pubsub.tf, iac/projects/bifrost-pubsub/acknowledge.pubsub.tf
- [policy:G4] Declare no subscription and no topic IAM here. The consuming service owns both, and a subscription on a cross-entity topic filters on `attributes.recordType` at the subscription.
  — paths: iac/projects/bifrost-pubsub
- [technical:G5] Prod state lives in `gfs-bifrost-tfstate-prod`. Read it from there. `gfs-bifrost-tfstate/prod/*` is stale.
  — paths: iac/projects/root.hcl
- [technical:G6] `required_version` in `providers.tf` and `tf_version` in every workflow job must agree (`1.3.0`), as must the provider pin (`6.41.0`).
  — paths: iac/projects/bifrost-pubsub/providers.tf, .github/workflows/deploy.yaml, .github/workflows/tf-plan-pr.yaml

## The topic module: every topic is a topic and a DLT

**CONFIRMED** `iac/modules/topic` is the only way a topic is created here. It builds `{domain}.{env}.{topic_name}.v{ver}` (`domain` defaults to `bifrost`, `ver` to `1`) and creates two resources: the topic, and a same-named topic with `.dlt` appended [1][2]. Module outputs are `default_topic_name`, `default_topic_id`, `dlt_topic_name` and `dlt_topic_id` [3]. The project re-exports them as per-topic outputs, and consumers read those under the state prefix `<env>/bifrost-pubsub` [6][7].

```orient-flow
{ "v": 1, "title": "From module call to consumer",
  "nodes": [
    { "id": "call", "label": "module call", "sub": "topic_name, domain, ver", "kind": "step", "ev": [4] },
    { "id": "mod", "label": "modules/topic", "kind": "step", "tone": "accent", "ev": [1] },
    { "id": "t", "label": "<domain>.<env>.<name>.v1", "kind": "topic", "ev": [1] },
    { "id": "d", "label": "same name + .dlt", "kind": "topic", "ev": [1] },
    { "id": "out", "label": "per-topic outputs", "sub": "name, id, dlt name, dlt id", "kind": "step", "ev": [6] },
    { "id": "st", "label": "tfstate bucket", "sub": "<env>/bifrost-pubsub", "kind": "store", "ev": [7] },
    { "id": "c", "label": "consumer stack", "sub": "terraform_remote_state", "kind": "external", "ev": [11] }
  ],
  "edges": [
    { "from": "call", "to": "mod" },
    { "from": "mod", "to": "t" },
    { "from": "mod", "to": "d" },
    { "from": "mod", "to": "out" },
    { "from": "out", "to": "st" },
    { "from": "st", "to": "c", "label": "reads ids" }
  ] }
```

**CONFIRMED** Nothing here creates a subscription, so a `.dlt` topic holds messages only when a consumer attaches a subscription to it [1]. **ASSESSED** That follows from how Pub/Sub retains messages, not from anything in this repo.

**Two dead-letter patterns coexist in the fleet.** Some consumers point a subscription's `dead_letter_policy` at this repo's topic-level DLT, read through remote state (snap-adapter's `create_record` subscriptions) [22]. Others declare their own DLT topic in their own `pubsub.tf` (replay-service's `create_data_failure`, `confirmation_data_failure` and `confirmation_made` subscriptions) [23]. Do not assume a DLT a consumer references was provisioned here. Check the consumer's `pubsub.tf`.

**CONFIRMED** Output naming is not uniform, which matters when you read them [6][8]:

- Most topics export `<topic>_topic_name`, `_topic_id`, `_topic_dlt_name` and `_topic_dlt_id`.
- `confirmation_ready` and `confirmation_made` export `_dlt_name` and `_dlt_id`, with no `topic` in the middle.
- `entity_error`, `stock_adjustment_ready` and `stock_adjustment_made` export no DLT outputs at all, though their DLT topics exist.

## The topic list at this ref

**CONFIRMED** Seventeen module calls across eight project files. This list is derived from the `.pubsub.tf` files, not the README [4][5][9][10][11][12][13][14].

| File | Topics | Notes |
| --- | --- | --- |
| `creation.pubsub.tf` | `create_record_request`, `create_record` | Cross-entity. Request is pre-gatekeeping, `create_record` is approved and ready for the WMS |
| `release.pubsub.tf` | `release_master_data`, `release_purchase_order`, `release_sales_order` | Per-entity. They clear a held record from the dedupe set |
| `errors.pubsub.tf` | `entity_error`, `ingress_rejection`, `create_data_failure`, `confirmation_data_failure` | `entity_error` is marked temporary in the code and carries a raw, unwrapped payload |
| `confirmations.pubsub.tf` | `confirmation_ready`, `confirmation_made`, `stock_adjustment_ready`, `stock_adjustment_made` | The first two are cross-entity |
| `config.pubsub.tf` | `config_revision` | Published by config-service |
| `acknowledge.pubsub.tf` | `create_acknowledge` | Single topic for create-side acknowledgements |
| `customer_creation.pubsub.tf` | `customer_creation` | Bi-directional. Its payload is the SFTP provisioning auth-status callback, per config-service's own notes |
| `audit.pubsub.tf` | `audit.<env>.fuse.v1` | Domain `audit`, one topic per reporting system. audit-service consumes it |

**ASSESSED** The `customer_creation` payload note comes from config-service's own notes, not from this repo.

The audit topic is the only one outside the `bifrost` domain. The module call sets `domain = "audit"` and `topic_name = "fuse"` [14]. It exposes `audit_fuse_topic_name`, `_id`, `_dlt_name` and `_dlt_id`, and audit-service reads them [10][12].

The legacy topics are gone. The per-entity `create_*` topics and the per-entity PO and SO confirmation topics no longer exist, and PO and SO confirmations ride `confirmation_ready` and `confirmation_made` [15][16].

## Cross-check with the Fuse MCP

**CONFIRMED** I compared this list with `data/pubsub-topology.json` at `origin/master` of `fuse-mcp` (`d455b6e`). All 17 topics appear there under the same names, including `audit_fuse` [17]. Differences:

- **Six retired entries.** The MCP keeps the six deleted per-entity `create_*` topics with a `retired` block dated 2026-07-21. They are absent here, so this matches its own stated rule.
- **Four topics this stack does not own.** `snap_poll_schedule`, `snap_poll_customer`, `stock_sync_schedule` and `stock_sync_due` are in the MCP. They are declared in the poller's own IaC, not here [18]. The MCP's scope is wider than this repo.
- **Naming convention string.** The MCP states `bifrost.{env}.{topic_name}.v{version}`. The module also takes a `domain`, and the audit topic uses `audit` [2][14]. Its `audit_fuse` entry has the right full name.
- **Audit publishers.** The MCP lists none for `audit_fuse`. fuse-ui already grants its Cloud Run service account `roles/pubsub.publisher` on the topic, outside preview environments [19]. **ASSESSED** The MCP is behind, since its own description says producers start at the fuse-ui cutover.
- **Envelopes.** The MCP says `confirmation_made` is `BifrostMessage<T>` and `stock_adjustment_ready` is `BifrostBulkMessage<CanonicalStockAdjustment>`. The README says the opposite for both [8][17]. Terraform defines no envelope, so this is **UNKNOWN** from this repo.
- **Working tree.** The `fuse-mcp` working copy is on a stale branch (`hjf/dedupe-mcp-tools`). It still lists the removed PO and SO confirmation topics and has no `audit_fuse`. Use `origin/master`.

## Envelopes live elsewhere

This repo provisions transport, not schema. The envelope types (`BifrostMessage<T>`, `BifrostBulkMessage<T>`, `BifrostMessageMetadata`, `BifrostEntityError`) live in `@gfs-bifrost/types` under `pkg-node/pkg/types/src/pubsub/`. The audit message lives in `@gfs-bifrost/audit` and is deliberately not a `BifrostMessage`. The README's envelope section still reads as accurate [8].

## Build and deploy

- **CONFIRMED** Terraform `1.3.0` and provider pins `google` and `google-beta` at `6.41.0`, with a GCS backend [5]. State sits in `gfs-bifrost-tfstate` for dev and `gfs-bifrost-tfstate-prod` for any other env, under `<env>/bifrost-pubsub`, with project `bifrost-<env>-global1` [7].
- **CONFIRMED** `deploy.yaml` runs on pushes to `main` or `master`. It plans dev, applies dev with `environment_name: terraform-dev`, plans prod, and applies prod with `terraform-prod`. `terraform-apply-prod` needs only `terraform-plan-prod`, so it does not wait for the dev apply [20].
- **CONFIRMED** `tf-plan-pr.yaml` runs a dev plan on pull requests that touch `.tf` or `.hcl` files and comments it on the PR [21].
- **CONFIRMED** Every job calls the reusable `terragrunt.yaml` in `ilg-platform/github-actions` at the rolling tag `0.1-affogato`, authenticates by Workload Identity (dev: `github-integration@bifrost-dev-global1`, prod: `github-runner@bifrost-prod-global1`) and passes no service-account key [20][21].
- **CONFIRMED** No secops workflow exists, only the two above. Whether that was deliberate is **UNKNOWN**.

## Security notes

- **CONFIRMED** The stack has no `google_pubsub_topic_iam_*` resource and no subscription. Who can publish or subscribe is decided by each consumer's IAM [1].
- **CONFIRMED** `tf-plan-pr.yaml:12-26` runs `plan` on the PR branch with `id-token: write` and the dev deploy service account. A plan runs the branch's Terraform, so a branch author gets dev deploy credentials. The trigger is `pull_request`, so fork PRs get none [21]. **ASSESSED** The pool trusts three whole GitHub orgs, so the same credentials are reachable from other repos (see core-infra).
- **CONFIRMED** Prod apply is gated by the `terraform-prod` environment (`deploy.yaml:84`), and the reusable workflow is pinned by a mutable tag (`deploy.yaml:17,37,57,77`) [20].
- **CONFIRMED** No credential is committed. `.gitignore` excludes `.gcp-creds.json`, `terraform.tfstate*` and `.terraform.lock.hcl` [20].
- **CONFIRMED** Topics set no message retention, schema or customer-managed key. They use the Pub/Sub defaults [1].

## Evidence

```orient-evidence
{ "v": 1, "items": [
  { "id": 1, "kind": "code", "ref": "iac/modules/topic/main.tf@700a515" },
  { "id": 2, "kind": "code", "ref": "iac/modules/topic/variables.tf@700a515" },
  { "id": 3, "kind": "code", "ref": "iac/modules/topic/outputs.tf@700a515" },
  { "id": 4, "kind": "code", "ref": "iac/projects/bifrost-pubsub/creation.pubsub.tf@700a515" },
  { "id": 5, "kind": "code", "ref": "iac/projects/bifrost-pubsub/providers.tf@700a515" },
  { "id": 6, "kind": "code", "ref": "iac/projects/bifrost-pubsub/confirmations.outputs.tf@700a515" },
  { "id": 7, "kind": "code", "ref": "iac/projects/root.hcl@700a515" },
  { "id": 8, "kind": "code", "ref": "README.md@700a515" },
  { "id": 9, "kind": "code", "ref": "iac/projects/bifrost-pubsub/release.pubsub.tf@700a515" },
  { "id": 10, "kind": "code", "ref": "iac/projects/bifrost-pubsub/audit.outputs.tf@700a515" },
  { "id": 11, "kind": "url", "ref": "https://github.com/gfs-bifrost/config-service/blob/63babd7/iac/projects/config-service/remote.tf", "note": "a consumer reading the state prefix" },
  { "id": 12, "kind": "url", "ref": "https://github.com/gfs-bifrost/audit-service/blob/ddefd56/iac/projects/audit-service/remotes.tf", "note": "reads the audit_fuse outputs from the prod bucket" },
  { "id": 13, "kind": "code", "ref": "iac/projects/bifrost-pubsub/errors.pubsub.tf@700a515" },
  { "id": 14, "kind": "code", "ref": "iac/projects/bifrost-pubsub/audit.pubsub.tf@700a515" },
  { "id": 15, "kind": "pr", "ref": "gfs-bifrost/bifrost-pubsub#13" },
  { "id": 16, "kind": "pr", "ref": "gfs-bifrost/bifrost-pubsub#14" },
  { "id": 17, "kind": "doc", "ref": "fuse-mcp data/pubsub-topology.json at origin/master d455b6e" },
  { "id": 18, "kind": "url", "ref": "https://github.com/gfs-bifrost/snap-adapter/blob/b16942a/iac/projects/snap-queue-polling-service/pubsub.tf", "note": "declares snap_poll_* topics" },
  { "id": 19, "kind": "url", "ref": "https://github.com/gfs-bifrost/fuse-ui/blob/ca5962f/iac/projects/fuse-ui/iam.tf", "note": "audit publisher IAM" },
  { "id": 20, "kind": "code", "ref": ".github/workflows/deploy.yaml@700a515" },
  { "id": 21, "kind": "code", "ref": ".github/workflows/tf-plan-pr.yaml@700a515" },
  { "id": 22, "kind": "url", "ref": "https://github.com/gfs-bifrost/snap-adapter/blob/b16942a/iac/projects/snap-adapter/pubsub.tf", "note": "dead_letter_topic = this repo's create_record DLT" },
  { "id": 23, "kind": "url", "ref": "https://github.com/gfs-bifrost/replay-service/blob/43380eb/iac/projects/replay/pubsub.tf", "note": "declares its own DLT topics" }
] }
```
