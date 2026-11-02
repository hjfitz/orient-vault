---
title: Secrets Hub — Migration State
programme: secrets-hub
status: planning
owner: hjf
services:
- github-config
- core-infra
- github-actions
- pkg-node
- bifrost-pubsub
- audit-service
- terraform-modules
- fapi
created: '2026-10-13'
updated: '2026-10-15'
tags:
- bifrost
- migration-state
---
# Secrets Hub — Migration State

<!-- The single source of truth for PROGRESS. The Overview carries the narrative and the verdict;
     this doc is the live ledger a session reads to know what is done and what is next.
     `wp programme status/next/tick` read and write the `## Unit status` tables below, so keep the
     table shape intact. -->

## Unit status
Legend: ⬜ not started · 🟨 in progress · ✅ merged · ⛔ blocked · ⏸ deferred · ❌ dropped · 🔄 rescoped

### Foundations
| Unit | St | Summary | Deps | Risk | Tier | PR | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **H0** | ✅ | Bootstrap the hub repo | | low | sonnet/low | github-config#19 | `gfs-bifrost/secrets-hub` (working name). github-config, like Audit Service UB: repo, `terraform-dev`/`terraform-prod` environments, package grants (incl. ui-toolkit). Then `waypoint-onboard` it. |
| **H1** | ✅ | `secret_change` audit kind | | low | sonnet/medium | pkg-node#270 | pkg-node `@gfs-bifrost/audit`, minor bump. `z.strictObject` `{ path, key, version?, action }`; no value field can exist. Package Changelog row in agents.md. Gated by G4. |
| **H2** | ✅ | `secrets` audit system | H1 | low | sonnet/low | bifrost-pubsub#16, audit-service#11 | Reports into audit-service under its own `secrets` system, `tenantId` = `<org>/<repo>`. A topic in bifrost-pubsub, plus one `local.systems` entry in audit-service. |
| **H3** | ⏸ | Deployer custom Secret Manager role | H0 | med | opus/medium | | Defined in the hub repo. Deferred: both deployers hold `roles/owner` (verified 2026-10-13), which already includes `versions.access`, so a narrow role adds nothing until owner is removed. Folded into H12. |
| **H4** | 🟨 | Turn on Secret Manager data-access audit logs | | low | sonnet/low | secrets-hub#12 | Per environment project. The backstop for the hub's audit events, since the publisher never blocks. |
| **H5** | 🟨 | Drop fapi's secret version data source | | low | sonnet/low | fapi#172 (draft) | Independent fix. `version = "latest"` in `secret_key_ref` instead, so the config-service API key leaves fapi's state. Can ship any time. |

### Hub
| Unit | St | Summary | Deps | Risk | Tier | PR | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **H6** | 🟨 | Hub API: claim check, refs, writes | H0, H1 | high | opus/high | secrets-hub#1-#5, #7 (draft) | Verify GitHub OIDC (JWKS, `aud`, trusted org), map `terraform-*` environments, return name→secret-id map for `<org>/<repo>/<env>` plus `<org>/_shared`. Write path creates secret, labels, version, audit event. Claim check reviewed by someone who didn't write it. PR plans (no environment claim) get dev's names. Promoted: [[secrets-hub/plans/hub-ci-read-path]]. |
| **H7** | 🟨 | Hub UI and developer login | H6 | med | opus/medium | secrets-hub#6, #8, #9, #10, #14 | Our own UI in the hub repo, built on ui-toolkit. Browse, add, rotate, disable per repo and environment. Group-gated writes, narrower for prod. Promoted: [[secrets-hub/plans/hub-ui-and-writes]]. Login increment gated by G7. |

### Delivery
| Unit | St | Summary | Deps | Risk | Tier | PR | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **H8** | ✅ | Secrets step in `terragrunt.yaml` | H6 | med | opus/medium | github-actions#36, #37 | ilg-platform/github-actions. Opt-in input; mints OIDC with the hub's audience, exports `TF_VAR_secret_refs`. Fails the job if the hub errors (never an empty map). Backward-compatible, so the rolling tag is force-moved. Caller grants `id-token: write`. |

### Pilot
| Unit | St | Summary | Deps | Risk | Tier | PR | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **H9** | ⬜ | Pilot spoke: fapi, dev then prod | H5, H7, H8 | med | opus/medium | | Spoke block plus `depends_on`. Move one secret onto the hub. Evidence: revision env shows a secret reference, the value is absent from state, the audit event lands. |

### Adopt
| Unit | St | Summary | Deps | Risk | Tier | PR | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **H10** | ⏸ | Move `tf_var_extra_N` secrets per service | H9 | med | sonnet/medium | | One row per service once the pilot is signed off. Each removes values from state. |
| **H11** | ⏸ | Datadog API keys off TF variables | H9 | med | sonnet/medium | | `TF_VAR_datadog_api_key_*` in `terragrunt.yaml`, and `compute/cloud-run`'s plain `DD_API_KEY` in terraform-modules. Org-shared secrets. |
| **H12** | ⏸ | De-privilege the deployers | | high | opus/high | | Closes R2. Replace `roles/owner` on `github-integration@bifrost-dev-global1` and `github-runner@bifrost-prod-global1` with scoped roles (H3's custom role among them), and move WIF trust from org-wide to per-repo (`attribute.repository`). Platform-wide; its own decision. |

## Gates
- [x] **G1 — Hub repo home and name** — blocks H0. `gfs-bifrost` for now (Harry, 2026-10-13). Working name `secrets-hub`.
- [x] **G2 — UI host** — blocks H7. Our own UI in the hub repo, built on ui-toolkit (Harry, 2026-10-13).
- [x] **G6 — Developer login, write groups and value display** — blocks H7. Decided by Claude on Harry's "build it autonomously" (2026-10-13): login through a GitHub App; write rights follow the user's live GitHub permission on the repo (push → dev, maintain/admin → prod, org owner → `_shared`); the UI never shows values; environments `dev` and `prod`.
- [x] **G7 — GitHub App created** — blocks H7. App `bifrost-vault` (id 5315617), owned by the gfs-dev enterprise, installed on gfs-bifrost (all repos), Metadata + Members read. Dev client id, client secret and session key in Secret Manager; mounted by secrets-hub#14 (2026-10-15). Prod needs its own callback URL and versions before `login_enabled` goes true there.
- [x] **G3 — Deployer role location and shape** — blocks H3. The custom role lives in the hub repo (Harry, 2026-10-13). Both deployers turned out to be `roles/owner`, so H3 is deferred into H12.
- [x] **G4 — Audit system for secret events** — blocks H1, H2. The Bifrost audit-service (Harry, 2026-10-13), under its own `secrets` system.
- [x] **G5 — PR plan policy** — blocks H6. PR plans may list dev's names (Harry, 2026-10-13).

## Risks
- **R1 ★ The claim check is wrong** — a repo is handed another repo's references and grants itself access. Small pure function, adversarial tests (path escape, missing environment, wrong `aud`, untrusted org), independent review — open.
- **R2 ★ The deployers are project owners, reachable from every repo** — `github-integration@bifrost-dev-global1` and `github-runner@bifrost-prod-global1` both hold `roles/owner` (verified 2026-10-13), and WIF trust is org-wide. Any repo in the trusted orgs can read any secret value, hub or not. The hub's scoping prevents mistakes and gives an audit trail; it is not a security boundary until H12 — standing.
- **R3 Hub error wipes a service's secrets** — an empty map would make Terraform remove every secret env var. The workflow step fails the job on any hub error — open.
- **R4 IAM propagation lag** — a new grant can take a short while, so a deploy adding a secret can fail once. A short retry in the workflow — open.
- **R5 Hub outage blocks deploys** — not runtime: Cloud Run reads Secret Manager directly — standing.
- **R6 Rotation needs new instances** — `latest` resolves at instance start, so a rotated value takes effect on the next deploy or restart — standing.
- **R7 Moving an existing secret without an outage** — the env var name is unchanged but its source switches. Do it in one apply per service and verify on dev first — open.

## Decision log
- **2026-10-13** — Built autonomously to the gates (Harry: "do everything autonomously until we can't"). Dev hub live at `https://secrets-hub-dev-661226359806.europe-west2.run.app`: CI references verified with real OIDC tokens (200/200/401/403), roles verified by impersonation (no value reads, no foreign secrets, no IAM changes), data-access logs on. UI login, writes, disable/enable/delete and audit merged but inert until G7. `terragrunt.yaml` gained `secrets_hub_url` on both tag lines (canaried, tags moved). Each hub defaults an environment-less token to its own environment so the prod plan job sees prod references. Side fix: github-config#20 (repo environments raced the admin-team grant and came up with no reviewers).
- **2026-10-13** — Hub planned as two plans after a draft and three adversarial reviews: [[secrets-hub/plans/hub-ci-read-path]] (H6) and [[secrets-hub/plans/hub-ui-and-writes]] (H7). Each environment runs its own hub that manages only its own project, which keeps the no-cross-project rule. Shared secrets are per environment. `gfs-bifrost` is the only trusted org at launch. Shared writes are for org owners only. The CI audience is each hub's `run.app` URL. Nothing goes to prod before dev QA.
- **2026-10-13** — Harry: build the hub "full-fat" (API and UI together, one plan) and largely autonomously. G6 decided accordingly: GitHub App login so write access follows repo permission (keeps scoping implicit, matching how CI is scoped); write-only UI so the hub's service account never holds `versions.access`. Single Next.js app on Cloud Run.
- **2026-10-13** — H12 skipped until every other unit is built (Harry). R2 stays standing until then.
- **2026-10-13** — Gates answered (Harry): hub in `gfs-bifrost`; our own UI on ui-toolkit; deployer role defined in the hub repo; events into audit-service; PR plans may list dev's names. Checking G3 found both deployers are `roles/owner`, so the narrow role is deferred into H12 and R2 restated.
- **2026-10-13** — GCP Secret Manager is the store, behind a thin hub API and UI. Self-hosted Vault and OpenBao rejected for the opex of a stateful cluster. A GCS-backed store rejected: Secret Manager already gives encryption, versioning, IAM and native Cloud Run delivery.
- **2026-10-13** — CI authenticates with the GitHub Actions OIDC token, verified by the hub. No static per-repo tokens.
- **2026-10-13** — CI gets references, never values. They reach Terraform as `TF_VAR_secret_refs` and become `secret_key_ref` env entries. Values stay out of state, plans, logs and revisions.
- **2026-10-13** — Each spoke grants its own runtime service account access in Terraform (`for_each` `iam_member`). Hub-side granting rejected: no SA naming convention to derive from, and it breaks a new service's first deploy.
- **2026-10-13** — `secret_change` audit kind approved (Harry).

## Scar tissue
- References only, never values, across CI and Terraform — values in state are readable cross-environment.
- `iam_member` only on hub-managed secrets — `iam_binding`/`iam_policy` replace every other service's grant on shared secrets.
- Target state (H12): the deployer never holds `versions.access` on hub-managed secrets — otherwise every repo in the org can read every secret. Not true today; see R2.
- The workflow step never exports an empty map after a hub error — Terraform would strip every secret from the service.
