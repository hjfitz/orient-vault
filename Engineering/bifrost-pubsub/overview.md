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
title: bifrost-pubsub — overview
thesis: 'bifrost-pubsub is the one Terraform stack that creates every Fuse Pub/Sub
  topic and its dead-letter twin: 17 topics at this ref. Services read topic ids from
  its remote state and own their own subscriptions.'
confidence: high
---
# bifrost-pubsub — overview

```orient-bluf
{ "v": 1, "bluf": "bifrost-pubsub is the one Terraform stack that creates every Fuse Pub/Sub topic and its dead-letter twin: 17 topics at this ref. Services read topic ids from its remote state and own their own subscriptions.", "confidence": "high", "action": "Remove or rename a topic or output only after every consumer's Terraform stops referencing it." }
```

## Responsibility

- **Every topic.** The stack declares 17 topics through one module, and each gets a `.dlt` dead-letter twin: 34 Pub/Sub topics per environment [1][4].
- **Naming.** A topic is `{domain}.{env}.{topic_name}.v{ver}`. Sixteen use the `bifrost` domain. The audit topic uses `audit` [2][5].
- **Outputs.** Each topic's name and id are Terraform outputs. Consumers read them by `terraform_remote_state` [3][6].
- **Transport only.** The stack holds no schema, no envelope definition and no subscription [1].

## Why it exists separately

One stack owns the topic taxonomy, so structure enforces the naming rule, not habit. A service cannot provision a colliding topic because it never provisions one. Consumers add subscriptions and IAM against ids they read from here. The cost is coupling. A removed topic or output breaks every consumer's next plan, with no compile-time signal.

## Neighbours

```orient-flow
{ "v": 1, "title": "bifrost-pubsub in context",
  "nodes": [
    { "id": "bp", "label": "bifrost-pubsub", "sub": "Terraform + Terragrunt", "kind": "service", "service": "bifrost-pubsub", "tone": "accent", "ev": [1] },
    { "id": "topics", "label": "17 topics + 17 DLTs", "sub": "bifrost.<env>.<name>.v1, audit.<env>.fuse.v1", "kind": "topic", "ev": [4, 5] },
    { "id": "state", "label": "tfstate buckets", "sub": "prod state in gfs-bifrost-tfstate-prod", "kind": "store", "ev": [7] },
    { "id": "cons", "label": "Fuse service stacks", "sub": "config-service, dedupe-service, fapi, sftp-connector, snap-adapter and more", "kind": "external", "ev": [9] },
    { "id": "aud", "label": "audit-service", "sub": "reads audit_fuse outputs", "kind": "service", "service": "audit-service", "ev": [9] },
    { "id": "ui", "label": "fuse-ui", "sub": "publisher IAM by topic name", "kind": "service", "service": "fuse-ui", "ev": [10] }
  ],
  "edges": [
    { "from": "bp", "to": "topics", "label": "creates" },
    { "from": "bp", "to": "state", "label": "outputs" },
    { "from": "state", "to": "cons", "label": "remote state read" },
    { "from": "state", "to": "aud" },
    { "from": "cons", "to": "topics", "label": "subscribe, publish", "style": "dashed" },
    { "from": "ui", "to": "topics", "label": "publish", "style": "dashed" }
  ] }
```

At least ten service stacks read this stack's state. They include `collector`, `config-service`, `dedupe-service`, `fapi`, `replay-service`, `sftp-connector`, `shopify-connector`, `snap-adapter` and `wms-gateway` [11]. `fuse-ui` skips the read and builds the audit topic name itself, so a rename breaks it silently [10].

## Where the reference lives

Read the `*.pubsub.tf` files for the live topic list. [[architecture]] re-derives that list at this ref and cross-checks it with the Fuse MCP. [[known-context]] holds the recordType asymmetry and the dead-letter ownership notes.

The `README.md` is wrong on topics. It lists six deleted per-entity create topics as live, and omits `create_data_failure`, `confirmation_data_failure` and `audit.<env>.fuse.v1`. Its `AGENTS.md` link is dead. Its envelope section is still accurate [8].

## What deliberately isn't here

- **Subscriptions and their IAM.** The consuming service owns its filter, ack deadline and retry policy [1].
- **The envelope schema.** `@gfs-bifrost/types` in `pkg-node` defines it, and `@gfs-bifrost/audit` defines the audit message.
- **Topic IAM.** No `google_pubsub_topic_iam_*` resource exists in this stack [1].
- **Snap polling topics.** `snap_poll_*` and `stock_sync_*` live in the poller's own IaC, not here.
- **Application code or telemetry.** Nothing runs here.

## Evidence

```orient-evidence
{ "v": 1, "items": [
  { "id": 1, "kind": "code", "ref": "iac/modules/topic/main.tf@700a515" },
  { "id": 2, "kind": "code", "ref": "iac/modules/topic/variables.tf@700a515" },
  { "id": 3, "kind": "code", "ref": "iac/modules/topic/outputs.tf@700a515" },
  { "id": 4, "kind": "code", "ref": "iac/projects/bifrost-pubsub/creation.pubsub.tf@700a515" },
  { "id": 5, "kind": "code", "ref": "iac/projects/bifrost-pubsub/audit.pubsub.tf@700a515" },
  { "id": 6, "kind": "code", "ref": "iac/projects/bifrost-pubsub/confirmations.outputs.tf@700a515" },
  { "id": 7, "kind": "code", "ref": "iac/projects/root.hcl@700a515" },
  { "id": 8, "kind": "code", "ref": "README.md@700a515" },
  { "id": 9, "kind": "url", "ref": "https://github.com/gfs-bifrost/audit-service/blob/ddefd56/iac/projects/audit-service/remotes.tf", "note": "reads bifrost-pubsub state; the other stacks use the same prefix" },
  { "id": 10, "kind": "url", "ref": "https://github.com/gfs-bifrost/fuse-ui/blob/ca5962f/iac/projects/fuse-ui/iam.tf", "note": "audit publisher IAM built by name" },
  { "id": 11, "kind": "log", "ref": "grep bifrost-pubsub in iac of default branches (2026-10-13): audit-service, collector, config-service, dedupe-service, fapi, replay-service, sftp-connector, shopify-connector, snap-adapter, snap-queue-polling-service, wms-gateway" }
] }
```
