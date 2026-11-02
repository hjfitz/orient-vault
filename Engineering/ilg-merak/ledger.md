---
tags: [waypoint, ledger]
---
# ilg-merak — work ledger

Agent-facing. Newest first. What meaningful work happened here, and the
context a future agent needs. Not a diary, not release notes, not a diff.

## 2026-10-28 — Name svc-template's deployed apps <app>-<system>-<env>

Name svc-template's deployed apps <app>-<system>-<env>

Adds a system name to svc-template's root.hcl so apps deploy as <app>-<system>-<env>; the template's services become svc-template-{dev,prod} and ui-template-{dev,prod}.

Ship: SHIP-1027-merak-gh-setup
PR: ilg-merak/svc-template#6

## 2026-10-27 — Grant packages: read to svc-template's svc image build jobs

Grant packages: read to svc-template's svc image build jobs

Ship: SHIP-1027-merak-gh-setup. svc deploy failed with startup_failure because docker-build-push@0.2-bonbon asks for packages: read and the svc callers granted only id-token/contents; the ui jobs already granted it. Merged as 5ed784e; svc deploy now starts and stops at preflight on the missing Datadog org secrets. Same run, by hand: created svc-template's terraform-prod environment (Harry + Ronny reviewers, main only, mirroring gcp-config merak-prod) and deleted gcp-config's unused TERRAFORM_FRAMEWORK_GITHUB_APP_ID/_PRIVATE_KEY. Owed: org secrets DATADOG_API_KEY + DATADOG_API_KEY_ILG (GFS key in both for now; logs land twice in GFS) and GH_TOKEN (read:packages PAT SSO'd for ilg-platform), set by an org admin; svc-template main has no branch protection.

PR: ilg-merak/svc-template#5

## 2026-10-27 — Move the Merak app platform to the US and take in #4

Move the Merak app platform to the US and take in #4

Merak starts in the US (UK/EU later), so the services registry and the <project>-tfstate app state bucket move to the us multi-region before first use, with names matching svc-template#1. Replaces #4 and #5's empty europe-west2 bucket and merak registry. Adds the Cloud Run and Pub/Sub APIs and runner iam.serviceAccountUser from #4. Plan per env: 5 add, 0 change, 2 destroy (both empty). Prompted by Oli Wilders' region comment on #4.

PR: ilg-merak/gcp-config#6

## 2026-10-27 — Ship per-env Terraform state bucket and Artifact Registry

Ship per-env Terraform state bucket and Artifact Registry

Merged as dba80a3 (admin merge, BAU). Deploy run 40487674146 applied 4 added / 0 changed / 0 destroyed in dev and in prod (merak-prod gate approved after the plan matched the agreed one). Live: ilg-merak-dev-tfstate and ilg-merak-prod-tfstate (europe-west2, versioned, PAP enforced, UBLA); Docker repo merak in each project. Probed as each env's runner: state object write/read/delete and an image push/delete both worked; probes removed. Next: drop ilg-merak from ilg-platform/gcp-config state_stacks (own plan). Follow-ups: image cleanup policy, state version lifecycle rule.

PR: ilg-merak/gcp-config#5

## 2026-10-27 — Add per-env Terraform state bucket and Artifact Registry

Add per-env Terraform state bucket and Artifact Registry

Each Merak project (dev, prod) now hosts its own state bucket (ilg-merak-<env>-tfstate) and Docker repo (merak, europe-west2) for every Merak service in that env. The stack's own state stays in gfs-terraform-core-tfstate. Plan: 4 add per env, no new IAM.

PR: ilg-merak/gcp-config#5

## 2026-10-24 — Bind the Merak terraform-runners to the ilg-merak org

Bind the Merak terraform-runners to the ilg-merak org

Each env's terraform-runner workloadIdentityUser binding moves from attribute.repository/ilg-merak/gcp-config to attribute.repository_owner/ilg-merak (var allowed_repository_owners, for_each), mirroring gfs-bifrost/core-infra. Harry's call: per-repo binding is too much friction. Accepted cost: any ilg-merak repo/branch can act as the owner-equivalent runner, including prod's, outside the merak-prod gate. Plans: 1 add / 1 destroy per env, the binding swap only. Pool already admits the org (terraform-framework#51).

PR: ilg-merak/gcp-config#3

## 2026-10-24 — Ship the ilg-merak gcp-config platform move to prod

Ship the ilg-merak gcp-config platform move to prod

Ship: SHIP-1024-merak-terragrunt. Squash-merged as 5deb110 (admin merge, Harry's call: BAU, main needs 1 approval and the only other admin is Ronny Lufwa). Deploy run 40122334940: dev and prod both applied 0 added / 0 changed / 0 destroyed; prod gate approved via pending_deployments. Repo settings applied the same day: PLATFORM_CI_APP_ID/PLATFORM_CI_APP_PRIVATE_KEY on the repo (no org-level values on ilg-merak); environments merak-dev (no gate) and merak-prod (reviewers Harry + Ronny, main only, self-review allowed so a two-person reviewer list can't deadlock); main's required checks now plan-dev / terragrunt, plan-prod / terragrunt, checkov, secret_scan / gitleaks, terraform_scan / Terraform Security Scan. Leftover: TERRAFORM_FRAMEWORK_GITHUB_APP_ID / _PRIVATE_KEY are now unused and can be deleted.

PR: ilg-merak/gcp-config#2

## 2026-10-24 — Move ilg-merak gcp-config to Terragrunt and the ilg-platform reusable workflows

Move ilg-merak gcp-config to Terragrunt and the ilg-platform reusable workflows

Moved ilg-merak/gcp-config off gfs-sre/terraform-framework's reusable-legacy-stack-terraform.yml@main and onto the platform stack, the same shape as gfs-ecm/cx#7. Terragrunt layout at iac/projects/ilg-merak with a generated backend at stacks/ilg-merak/<env>, so state is unchanged. Module now comes from ilg-platform/terraform-modules project/factory@v0.1.0 (the documented current tag; .tf files identical to framework gcp-project@main). CI runs github-actions@0.2-bonbon: dev then prod deploy behind merak-dev/merak-prod, PR plans, manual deploy, and secops with Checkov kept. Local plans as each env's runner show No changes for both. Before merge the repo needs: PLATFORM_CI_APP_ID + PLATFORM_CI_APP_PRIVATE_KEY (no org-level values on ilg-merak, so CI plans fail at module fetch until set), the merak-dev/merak-prod environments (none exist; today prod applies ungated), and main's required checks swapped from the legacy dev/prod Plan + Security Scan names.

PR: ilg-merak/gcp-config#2
