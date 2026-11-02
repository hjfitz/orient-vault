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
title: terraform-modules — architecture
thesis: A flat library of twelve one-directory Terraform modules that declare providers
  and never configure them, consumed by git source and a rolling tag; the lone tag
  on origin is 0.1-affogato, and only compute/cloud-run runs on the Terraform version
  Fuse pins.
confidence: high
---
# terraform-modules — architecture

```orient-bluf
{ "v": 1, "bluf": "A flat library of twelve one-directory Terraform modules that declare providers and never configure them, consumed by git source and a rolling tag; the lone tag on origin is 0.1-affogato, and only compute/cloud-run runs on the Terraform version Fuse pins.", "confidence": "high", "action": "Never add a provider block to a module, and never change a lifted module's inputs or outputs without finding its consumers first." }
```

## Guardrails

- [technical:G1] A module never contains a `provider` block. `versions.tf` declares `required_providers`, and the calling stack configures them. Several modules also declare `configuration_aliases`, so the caller must pass `providers = { google = ... }`.
  — paths: compute/cloud-run/versions.tf, iam/service-account/versions.tf, project/iam/versions.tf
- [contract:G2] The eleven lifted modules stay byte-identical to `gfs-sre/terraform-framework`, so a consumer that repoints gets a no-op plan. Change one only for a reason, and expect every consumer to re-plan.
  — paths: compute/cloud-run-service, compute/vm, iam/service-account, networking, project
- [policy:G3] `compute/cloud-run` holds no invoker IAM, load balancer, DNS, Pub/Sub subscription or grant to other resources. Both Datadog sidecars stay mandatory and unconfigurable. A divergent service shape gets a second module, not new flags.
  — paths: compute/cloud-run/main.tf, compute/cloud-run/variables.tf
- [contract:G4] A backward-compatible change force-moves the current tag. A breaking change (renamed or removed input or output, changed default) cuts the next tag. Search the orgs for consumers of the module path before either.
  — paths: CLAUDE.md, README.md
- [technical:G5] One module per `{category}/{name}`, no deeper nesting, with exactly `main.tf`, `variables.tf`, `outputs.tf`, `versions.tf` and `README.md`. Keep the module's README accurate in the same change.
  — paths: CLAUDE.md
- [policy:G6] The four `.keep` placeholders are not modules. Do not invent their surface. A service that needs one raises it in `#platform-engineering` so it gets built once.
  — paths: pubsub, secrets, storage

## Layout

**CONFIRMED** Twelve built modules and four placeholders. `compute/cloud-run` is the only module written for Bifrost. The other eleven came from `gfs-sre/terraform-framework` [1][15].

```
compute/cloud-run/          BUILT, opinionated Bifrost shape
compute/cloud-run-service/  BUILT, generic Cloud Run v2
compute/vm/                 BUILT
iam/service-account/        BUILT
networking/cloud-nat/       BUILT
networking/dns-zone/        BUILT
networking/iap-web/         BUILT
networking/load-balancer/   BUILT
networking/vpc/             BUILT
networking/vpc-connector/   BUILT
project/factory/            BUILT
project/iam/                BUILT
pubsub/topic/               planned (.keep)
pubsub/subscription/        planned (.keep)
secrets/secret/             planned (.keep)
storage/gcs-bucket/         planned (.keep)
```

**ASSESSED** The "byte-identical" claim rests on the commit message of the PR that lifted them, which also says it rewrote only the README usage examples and wrote READMEs for `networking/vpc` and `compute/vm` [15]. The framework repo is not in this checkout, so the diff is unrun here.

```orient-flow
{ "v": 1, "title": "Where the modules come from and who fetches them",
  "nodes": [
    { "id": "fw", "label": "gfs-sre/terraform-framework", "sub": "11 modules", "kind": "external", "ev": [15] },
    { "id": "tm", "label": "terraform-modules", "sub": "main @ 10b40f9", "kind": "service", "service": "terraform-modules", "tone": "accent", "ev": [1] },
    { "id": "tag", "label": "0.1-affogato", "sub": "only tag on origin", "kind": "step", "ev": [16] },
    { "id": "old", "label": "v0.1.0", "sub": "local only, 3 commits behind", "kind": "step", "tone": "alert", "ev": [16] },
    { "id": "tg", "label": "terragrunt.yaml", "sub": "App token, url.insteadOf", "kind": "step", "service": "github-actions", "ev": [18] },
    { "id": "tpl", "label": "repo-template", "sub": "?ref=v0.1.0", "kind": "external", "ev": [17] }
  ],
  "edges": [
    { "from": "fw", "to": "tm", "label": "lifted" },
    { "from": "tm", "to": "tag", "label": "points at main" },
    { "from": "tm", "to": "old", "style": "dashed" },
    { "from": "tg", "to": "tm", "label": "git fetch" },
    { "from": "old", "to": "tpl", "label": "pinned, absent on origin", "style": "dashed" }
  ] }
```

## What a built module looks like

**CONFIRMED** Five files per module, and no module configures a provider [1]. The set differs in Terraform and provider floors:

| Module group | `required_version` | `google` provider |
|---|---|---|
| `compute/cloud-run` | `>= 1.3.0` | `>= 6.41.0` |
| the eleven lifted modules | `>= 1.14` | `>= 5.41` (some also `google-beta`) |

[5][9]. **ASSESSED** Fuse stacks run Terraform `1.9.0`, the reusable workflow's default `tf_version`, so a Fuse stack cannot use a lifted module until it moves to 1.14. Only `compute/cloud-run` fits today [18].

## compute/cloud-run: the Bifrost shape

**CONFIRMED** One Cloud Run v2 service named `${project_name}-${env}`, running as a service account it creates (`${project_name}-${env}-cloudrun`) [3]. It holds three containers on a shared in-memory `emptyDir` at `/shared-volume`: the app, `datadog-sidecar-gfs` and `datadog-sidecar-ilg`. The sidecars use `gcr.io/datadoghq/serverless-init:latest` with health ports 12345 and 12346, 512Mi and 1 CPU each. The app container has an HTTP startup probe on `health_check_path:container_port` [3]. **ASSESSED** The `run.googleapis.com/container-dependencies` annotation is keyed `main-app`, but the app container is named `${project_name}`, so the key matches no container unless `project_name` is `main-app` [3]. How Cloud Run treats an unmatched key is unverified here. `deletion_protection = false` [3].

- **Required inputs:** `project_name`, `env`, `gcp_project`, `gcp_region`, `image`, `github_sha` (sets sidecar `DD_VERSION`), and two sensitive Datadog keys, `datadog_api_key_gfs` and `datadog_api_key_ilg` [4].
- **Optional inputs:** `container_port` (3000), `health_check_path` (`/health/liveness`), `env_vars` (`{}`), `secret_env_vars` (`[]`, items of `{name, secret, version}`), `ingress` (`INGRESS_TRAFFIC_ALL`), `min_instance_count` (`null` means no scaling block), `vpc_connector_id` (`null` means no VPC egress), and `vpc_egress` (`ALL_TRAFFIC`, applied only with a connector) [4].
- **Outputs:** `service_name`, `service_uri`, `service_account_email`, `service_account_name`, `service_id`.
- **Left to the caller:** invoker bindings, load balancers, DNS, Pub/Sub subscriptions, and any grant to other resources, such as `secretmanager.secretAccessor` for `secret_env_vars` [1].

## The generic modules

**CONFIRMED** Two Cloud Run modules coexist on purpose. `compute/cloud-run-service` takes the name, service account and image from the caller. It ignores changes to the deployed image, because a separate pipeline deploys through WIF. It defaults `ingress` to `INGRESS_TRAFFIC_INTERNAL_ONLY` and creates a `roles/run.invoker` member per `invoker_members` entry [6][7]. Reconciling the two is open work [1].

| Module | What it creates | Defaults worth knowing |
|---|---|---|
| `compute/vm` | Instance, optional OS Login metadata and IAM, IAP tunnel access | no external IP; scopes `cloud-platform`; project default service account if none given [8] |
| `iam/service-account` | Service account and SA-level bindings | ignores `display_name` drift; `project_roles` is declarative only and creates no binding [14] |
| `project/iam` | One `google_project_iam_binding` per role | authoritative, so unlisted members are removed on apply [10] |
| `project/factory` | A project via the public project-factory module `~> 18.2` | `group_role` defaults to `roles/editor`; `deletion_policy` `PREVENT`; default service account `disable` [11] |
| `networking/vpc` | Custom-mode VPC, subnets, internal and IAP-SSH firewall rules | internal rule allows icmp, tcp and udp from the three RFC1918 ranges [12][20] |
| `networking/load-balancer` | One shared external HTTPS LB with a serverless NEG, backend, managed cert and host rule per service | HTTP to HTTPS redirect on; no security policy or SSL policy resource [13] |
| `networking/iap-web` | `roles/iap.httpsResourceAccessor` per service and member | an empty member list fails closed |
| `networking/cloud-nat`, `dns-zone`, `vpc-connector` | Router and NAT with a static IP; public DNS zone and records; Serverless VPC Access connector | none |

## Consuming a module

```hcl
module "cloud_run" {
  source = "git::https://github.com/ilg-platform/terraform-modules.git//compute/cloud-run?ref=<tag>"
}
```

**CONFIRMED** `//<path>` picks the module directory and `?ref=` picks the tag, branch or commit. The repo is private and in `ilg-platform`, while consumers sit in `gfs-bifrost`. A workflow's default `github.token` cannot fetch it. The reusable `terragrunt.yaml` mints a GitHub App token and rewrites `https://github.com/` through `git config url.insteadOf`, falling back to a PAT [18]. A bare `terraform init` with only `github.token` fails. The org rename leaves `gfs-platform` strings in some READMEs. GitHub redirects them, and they are not to be mass-rewritten [1].

## Versioning and tags

**CONFIRMED** The convention is a rolling tag. A compatible change force-moves the tag. A breaking change cuts the next one, and the callers opt in [1][2]. One tag covers the whole repo. A force-moved tag reaches a consumer only on `terraform init -upgrade`, because Terraform caches the resolved ref in `.terraform/modules/`. A reviewed `plan` is the safety net [1][2].

**CONFIRMED** The tags at this ref do not match what the docs say:

- **Origin has one tag.** `git ls-remote --tags origin` returns only `0.1-affogato`, a lightweight tag at `10b40f9`, the head of `main` [16].
- **`v0.1.0` is local-only.** It is an annotated tag by Harry Fitzgerald dated 2026-04-17, at `b5a4284`, three commits behind `main` and without any lifted module. It is not on origin [16].
- **The docs name a tag origin lacks.** `CLAUDE.md` and `README.md` say the current tag is `v0.1.0`. `repo-template` pins `?ref=v0.1.0` [1][2][17].
- **Eleven module READMEs show `?ref=v0.2.0`.** No tag of that name exists anywhere.

**UNKNOWN** Whether `v0.1.0` was ever pushed and later deleted, and which tag the intended consumers use. `gcp-config` and `ilg-tech-services-iac` are not in this checkout.

## Consumers

**CONFIRMED** A search of every default branch in the local Fuse checkouts finds one consumer: `repo-template`, the scaffold for new services, which sources `compute/cloud-run` [17]. No running Fuse service sources the module, so each still hand-rolls its Cloud Run resource. This is expected. New services adopt it through the template, and migrating old ones is not a priority. The Fuse MCP catalog says the Fuse service IaC consumes this repo, and that is wrong [19]. A different repo, `gfs-hybrid-services/terraform-modules` (a `labels` module, used by apiky), is unrelated.

**ASSESSED** `gcp-config` and `ilg-tech-services-iac` consumed the eleven lifted modules from `gfs-sre/terraform-framework` by branch, and the lift lets them pin a tag instead [15].

## Security notes

- **CONFIRMED** `compute/cloud-run/main.tf:84` and `:152` pull the Datadog sidecars from `gcr.io/datadoghq/serverless-init:latest`. The tag is mutable and unpinned, so every new revision can pick up a different image [3].
- **CONFIRMED** `compute/cloud-run/main.tf:114-116` and `:182-184` pass `DD_API_KEY` as a plain env value, not a Secret Manager reference. The `sensitive` flag at `variables.tf:33,39` hides it in plan output only. The key sits in Terraform state and in the Cloud Run revision config [3][4].
- **CONFIRMED** `compute/cloud-run/variables.tf:74` defaults `ingress` to `INGRESS_TRAFFIC_ALL`. The module grants no invoker role, so public access depends on the caller [4].
- **CONFIRMED** `compute/cloud-run-service` accepts `allUsers` through `invoker_members` (`variables.tf:93`). Its default ingress is internal-only (`variables.tf:34`), which is the safer default [6][7].
- **CONFIRMED** `project/iam/main.tf:6-10` uses `google_project_iam_binding`, so an apply strips any member of a managed role that the map omits [10].
- **CONFIRMED** `project/factory/variables.tf:69-72` defaults `group_role` to `roles/editor`, and the role applies only when `group_name` is set [11].
- **CONFIRMED** `compute/vm/main.tf:17` defaults service-account scopes to `cloud-platform`, so the attached service account's IAM is the only limit [8].
- **CONFIRMED** No credential, key or token is committed. The repo has no `.github/` directory, so no workflow, `pull_request_target` or unpinned action exists in it [1].

## Evidence

```orient-evidence
{ "v": 1, "items": [
  { "id": 1, "kind": "code", "ref": "CLAUDE.md@10b40f9" },
  { "id": 2, "kind": "code", "ref": "README.md@10b40f9" },
  { "id": 3, "kind": "code", "ref": "compute/cloud-run/main.tf@10b40f9" },
  { "id": 4, "kind": "code", "ref": "compute/cloud-run/variables.tf@10b40f9" },
  { "id": 5, "kind": "code", "ref": "compute/cloud-run/versions.tf@10b40f9" },
  { "id": 6, "kind": "code", "ref": "compute/cloud-run-service/main.tf@10b40f9" },
  { "id": 7, "kind": "code", "ref": "compute/cloud-run-service/variables.tf@10b40f9" },
  { "id": 8, "kind": "code", "ref": "compute/vm/main.tf@10b40f9" },
  { "id": 9, "kind": "code", "ref": "compute/vm/versions.tf@10b40f9" },
  { "id": 10, "kind": "code", "ref": "project/iam/main.tf@10b40f9" },
  { "id": 11, "kind": "code", "ref": "project/factory/variables.tf@10b40f9" },
  { "id": 12, "kind": "code", "ref": "networking/vpc/main.tf@10b40f9" },
  { "id": 13, "kind": "code", "ref": "networking/load-balancer/main.tf@10b40f9" },
  { "id": 14, "kind": "code", "ref": "iam/service-account/main.tf@10b40f9" },
  { "id": 15, "kind": "pr", "ref": "ilg-platform/terraform-modules#2" },
  { "id": 16, "kind": "log", "ref": "git ls-remote --tags origin (2026-10-13): 10b40f92 refs/tags/0.1-affogato, no other tag; local v0.1.0 -> b5a4284" },
  { "id": 17, "kind": "url", "ref": "https://github.com/ilg-platform/repo-template/blob/1a5f0b7/iac/projects/service-name/cloud-run.tf", "note": "pins ?ref=v0.1.0" },
  { "id": 18, "kind": "url", "ref": "https://github.com/ilg-platform/github-actions/blob/d52202b/.github/workflows/terragrunt.yaml", "note": "reusable workflow at 0.1-affogato" },
  { "id": 19, "kind": "doc", "ref": "fuse://services", "note": "catalog says the Fuse service IaC consumes this repo" },
  { "id": 20, "kind": "code", "ref": "networking/vpc/variables.tf@10b40f9" }
] }
```
