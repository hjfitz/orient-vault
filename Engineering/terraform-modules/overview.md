---
tags:
- waypoint
- terraform-modules
verified: '2026-10-13'
verified_sha: 10b40f9
verified_paths:
- CLAUDE.md
- README.md
- compute
- iam
- networking
- project
- pubsub
- secrets
- storage
title: terraform-modules — overview
thesis: 'terraform-modules is the platform''s shared Terraform module library: twelve
  built GCP modules, one Fuse-shaped Cloud Run module among them, versioned by a rolling
  git tag. No running Fuse service consumes it yet.'
confidence: high
---
# terraform-modules — overview

```orient-bluf
{ "v": 1, "bluf": "terraform-modules is the platform's shared Terraform module library: twelve built GCP modules, one Fuse-shaped Cloud Run module among them, versioned by a rolling git tag. No running Fuse service consumes it yet.", "confidence": "high", "action": "Pin to the rolling tag that exists on origin, and change a module's inputs or outputs only after searching the orgs for consumers." }
```

## Responsibility

- **A module library.** It holds twelve built modules under `{category}/{name}` [1][2]. Pure HCL, no application code.
- **The Fuse Cloud Run shape.** `compute/cloud-run` builds a Cloud Run v2 service with two mandatory Datadog sidecars and its own service account [3].
- **The lifted modules.** Eleven more came from `gfs-sre/terraform-framework`: a generic Cloud Run service, a VM, a service account, networking, project factory and project IAM [1][8].
- **Four placeholders.** `pubsub/topic`, `pubsub/subscription`, `secrets/secret` and `storage/gcs-bucket` are empty `.keep` files [1].

## Why it exists separately

A shared module gives a service the platform's conventions through a tag bump. Each service then stops hand-rolling and drifting its own `google_*` resources. The repo sits in `ilg-platform` because it serves the whole platform, not only Fuse. Fuse consumes it and never the reverse [1].

## Neighbours

```orient-flow
{ "v": 1, "title": "terraform-modules in context",
  "nodes": [
    { "id": "fw", "label": "gfs-sre/terraform-framework", "sub": "source of 11 modules", "kind": "external", "ev": [8] },
    { "id": "tm", "label": "terraform-modules", "sub": "12 built, 4 placeholders", "kind": "service", "service": "terraform-modules", "tone": "accent", "ev": [1] },
    { "id": "tag", "label": "tag 0.1-affogato", "sub": "only tag on origin, at main", "kind": "step", "ev": [7] },
    { "id": "ga", "label": "github-actions", "sub": "terragrunt.yaml mints the fetch token", "kind": "service", "service": "github-actions", "ev": [6] },
    { "id": "tpl", "label": "repo-template", "sub": "pins ?ref=v0.1.0", "kind": "external", "ev": [5] },
    { "id": "cons", "label": "gcp-config, ilg-tech-services-iac", "sub": "to repoint from the framework", "kind": "external", "ev": [8] },
    { "id": "fuse", "label": "Fuse service repos", "sub": "hand-roll Cloud Run", "kind": "external", "ev": [9] }
  ],
  "edges": [
    { "from": "fw", "to": "tm", "label": "lifted byte-identical" },
    { "from": "tm", "to": "tag" },
    { "from": "tag", "to": "tpl", "label": "git source", "style": "dashed" },
    { "from": "tag", "to": "cons", "label": "git source", "style": "dashed" },
    { "from": "ga", "to": "tm", "label": "App token fetch" },
    { "from": "tm", "to": "fuse", "label": "no consumer", "style": "dashed" }
  ] }
```

The tag `repo-template` pins does not exist on origin (see [[architecture]]). **ASSESSED** `gcp-config` and `ilg-tech-services-iac` are the intended consumers of the lifted modules, from the commit message that brought them in [8]. Neither repo is in this checkout, so their adoption is **UNKNOWN**.

## Where the reference lives

`CLAUDE.md` in the repo is the deep reference. Each module also has a `README.md` with usage and inputs. [[architecture]] holds the module table, conventions and the tag state at this ref. [[known-context]] holds the adoption history.

Three things in the repo's own docs are wrong. They name `v0.1.0` as the current tag, and that tag is absent from origin. Eleven module READMEs show `?ref=v0.2.0`, which does not exist. The Fuse MCP catalog says Fuse service IaC consumes the library, and none does [1][2][7][9].

## What deliberately isn't here

- **CI and tooling.** No pipeline, tests or lint run in this repo [1].
- **Invoker IAM, load balancers, DNS and subscriptions in `compute/cloud-run`.** The caller owns them, because some are security boundaries [1].
- **Configurable Datadog sidecars.** Both always run, and no input changes them [3][4].
- **Provider configuration.** Modules declare providers in `versions.tf`, and the caller configures them [1].

## Evidence

```orient-evidence
{ "v": 1, "items": [
  { "id": 1, "kind": "code", "ref": "CLAUDE.md@10b40f9" },
  { "id": 2, "kind": "code", "ref": "README.md@10b40f9" },
  { "id": 3, "kind": "code", "ref": "compute/cloud-run/main.tf@10b40f9" },
  { "id": 4, "kind": "code", "ref": "compute/cloud-run/variables.tf@10b40f9" },
  { "id": 5, "kind": "url", "ref": "https://github.com/ilg-platform/repo-template/blob/1a5f0b7/iac/projects/service-name/cloud-run.tf", "note": "the only consumer found" },
  { "id": 6, "kind": "url", "ref": "https://github.com/ilg-platform/github-actions/blob/d52202b/.github/workflows/terragrunt.yaml", "note": "App token and url.insteadOf rewrite" },
  { "id": 7, "kind": "log", "ref": "git ls-remote --tags origin (2026-10-13): 10b40f92 refs/tags/0.1-affogato, and no other tag" },
  { "id": 8, "kind": "pr", "ref": "ilg-platform/terraform-modules#2" },
  { "id": 9, "kind": "doc", "ref": "fuse://services", "note": "terraform-modules entry: consumed by the Fuse service IaC" }
] }
```
