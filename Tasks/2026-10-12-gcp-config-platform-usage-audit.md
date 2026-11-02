---
tags: [adhoc-task]
date: 2026-10-12
tldr: "Audited platform-tech use in gcp-config and tech-services-iac; moved gfs-ecm/cx onto Terragrunt and platform workflows (draft PR gfs-ecm/cx#7, both plans show no changes)"
session_id: 4ba8f380-7cde-4d7e-ae8f-5fdb17df2216
status: open
---
# Audit platform-tech usage in the gcp-config repos

## Outcome
- **gcp-config**: `terragrunt.yaml@0.1-affogato`, secops pinned to `@main`. All modules come from `ilg-platform/terraform-modules@0.1-affogato`. State is in SRE's `gfs-terraform-core-tfstate` via a generated backend. Still on the shared WIF provider `547960417467`.
- **ilg-tech-services-iac**: `@0.2-bonbon` everywhere, plus a supersede/concurrency guard. 6 platform modules. cloud-run, cloud-run-service, load-balancer, iap-web and dns-zone are vendored into `iac/modules/`, with the upstream list in its README; no upstream PRs since terraform-modules#2.
- **Stale records**: iac#45 merged 09-02 (memory still says open). `PLATFORM_CI_APP_ID=4035291` in both repos; the leftover `TERRAFORM_FRAMEWORK_GITHUB_APP_ID` should be deleted. No `v0.2.0` module tag exists. These vault docs still say open/not-started and need updating: Platform Terraform Alignment Overview, Tech Services IaC Remediation State, terraform-modules ledger.
- **Lost history**: transcripts from the August migration are gone (retention goes back to ~09-02). The explainer `2026-08-26-gcp-config-antipattern-audit` is the surviving record.
- **gfs-ecm/cx**: branch `hjf/terragrunt-platform-structure` (d651d48) is pushed. It moves cx to Terragrunt, `terraform-modules@0.1-affogato` and `github-actions@0.2-bonbon`. Local plans for dev and prod both show No changes. Draft PR gfs-ecm/cx#7 is open. Ledger entry written under cx; the wp symlink bug was worked around by calling wp.py directly. CI is green: both plans show No changes, using the gfs-ecm org-level CI app values. Repo-level copies of those two values were set on 10-12; they duplicate the org values and are not needed. Not going to Wolf.
