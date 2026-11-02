# SRE Terraform Framework — Bifrost Coexistence

_Written 2026-07-29. Purpose: at some point a Bifrost GCP project + WIF deploy SA will be provisioned through SRE's terraform-framework. This doc is the reference for that day — what their framework actually does, where it collides with our deploy model, the verified-viable arrangement, and the provisioning-day checklist. Everything below was read from **origin main** of the source repos on 2026-07-29 (SSH clones, not local trees); re-verify the load-bearing facts against their `main` before acting, as their framework is under active development (SRE-86/SRE-155)._

## TL;DR — the agreement to reach with SRE

A stack repo provisioning a Bifrost project is fine **iff it is IAM-inert** ("adoption-lite"):

1. It provisions the project, `terraform-runner`, our deploy SA + org-wide WIF binding — and **manages zero project IAM roles** (`project_roles = []` everywhere, `project_iam_bindings = {}`).
2. The deploy SA's roles are granted **additively** (`google_project_iam_member` in the stack root — their own terraform-runner bootstrap pattern), never via `project_roles`.
3. Three fence posts in writing (below), because their tooling's default gravity is "audit and bring every role under management".

One-sentence version: **`gcp-project-iam` and `google_project_iam_member` cannot share a role.** Their module is per-role authoritative (members not listed are removed on every apply); our service stacks grant IAM additively from CI. Any role both sides touch = permanent flip-flop war, and their apply breaks **running** services instantly (IAM is live — a stripped `secretAccessor` doesn't wait for a redeploy).

## State of the world — verified 2026-07-29

| Thing | Fact | Source |
| --- | --- | --- |
| Framework | `gfs-sre/terraform-framework` — modules, shared-config, terraform-core stack, legacy-project-stack template, reusable CI workflow | repo root |
| First live consumer | `gfs-ecm/ecm-prod-uk1-iac` (SRE-155, Ronny Lufwa) — adopted `gfs-ecm-prod-uk1`, IAM audit imported into tfvars, CI enabled | commit `6fa1a9c` 2026-07-29 |
| IAM model | `gcp-project-iam` = `google_project_iam_binding` for_each role — **per-role authoritative**: "members not listed are removed on apply"; undeclared roles untouched | `modules/gcp-project-iam/main.tf` + variable docstring |
| Module contract | Framework feature modules must **not** create `google_project_iam_member` — all project IAM flows through one merge point in the stack root | `docs/PLAN-LEGACY-PROJECT-STACKS.md` §2 |
| WIF | One central pool in `terraform-core-452622`; provider maps `attribute.repository_owner`; condition supports **org-wholesale admission** via `github_organizations_extra` (condition-only — never feeds elevated-SA bindings) | `core-stacks/terraform-core/terraform/wif.tf` |
| State | Shared bucket `gfs-terraform-core-tfstate`, prefix `stacks/<id>/<env>`. Every stack runner gets **unconditional bucket-level `objectAdmin`** (GCS backend lists objects at init; prefix IAM conditions can't allow it — "isolation is by state prefix and trusted project-scoped runners", i.e. trust, not enforcement) | `core-stacks/terraform-core/terraform/stack_state_access.tf` header |
| Bucket coupling | **The reusable workflow never sees the bucket** — it comes from each caller repo's checked-in `shared-config/shared/backend.config.hcl`; workflow passes only the prefix + file path | `reusable-legacy-stack-terraform.yml` init step |
| CI | Their reusable workflow: gitleaks (inline) + checkov + raw terraform plan/apply. **No environment approval gate** (push to main auto-applies; default env `prod`). Callers pin `@main`, no version tags. Cross-org `uses:` works because the repo's Actions access is set to `enterprise` | workflow file + `docs/RUNBOOK-LEGACY-PROJECT-IMPORT.md` §4 |
| Remote-state contract | Stack template reads terraform-core state for WIF; expects outputs named `workload_identity_provider` / `workload_identity_pool_name` / `elevated_sa_email`. Our core-infra publishes `workload_identity_provider_name` — **name mismatch** | stack `main.tf` locals vs core-infra `outputs.tf` |
| Their own precedent for us | The stack template grants terraform-runner's roles via **additive** `google_project_iam_member` in `main.tf` — outside the authoritative merge. The SA module carries `lifecycle ignore_changes [display_name]` explicitly to avoid flip-flop with legacy co-management. They design around dual writers when they choose to | template `main.tf`, `modules/gcp-iam-service-account/main.tf` |

Caveat that bit us: `gh search code` / API consumer sweeps **silently miss SAML-walled orgs** (gfs-ecm) — the live consumer was invisible to an org-wide search until read over SSH. Enumerate consumers accordingly.

## Why default adoption breaks BAU

Their onboarding audit imports **every role it finds** — including roles our runtime SAs already hold (dedupe's Cloud Run SA holds `vpcaccess.user`, `compute.networkUser`, `compute.instanceAdmin` at project level via our service stacks; the pattern is fleet-wide). So on day one the declared set overlaps everything, and then:

1. Their apply strips members our stacks granted → live services lose permissions immediately.
2. Our next terragrunt apply re-creates the member → their next apply strips it again. Both sides show perpetual drift.
3. New grants stop being self-serve: any service PR adding a `google_project_iam_member` on a declared role dies on their next apply — weeks later, looking like random IAM rot.

Granularity trap: even "just manage the deploy SA's roles" pulls **whole roles** into clobber scope — declaring `run.admin = [github-deploy@…]` strips every other member anyone grants on `run.admin` (break-glass humans included). Their ecm tfvars show they've met this class and answered with a hand-maintained exclusion (the velero-svc carve-out) — fine once, unscalable as a default.

## The verified-viable arrangement (adoption-lite)

Verified at module level: `project_roles = []` → the SA module exports empty `iam_requirements`; with `project_iam_bindings = {}` the stack-root merge is `{}` → `gcp-project-iam` manages **zero roles**. The repo is mechanically inert w.r.t. project IAM — not a promise, a property of the config.

```hcl
# stack tfvars — the shape that keeps BAU intact
service_accounts = {
  "github-deploy" = {
    account_id    = "github-deploy"
    project_roles = []   # ← load-bearing: nothing enters the authoritative merge
    service_account_iam_members = [{
      role   = "roles/iam.workloadIdentityUser"
      member = "principalSet://iam.googleapis.com/<terraform-core pool>/attribute.repository_owner/gfs-bifrost"
    }]
  }
}
project_iam_bindings = {}
```

Plus, outside the merge:

- **Deploy SA roles**: additive `google_project_iam_member` in the stack root (their terraform-runner pattern) — or granted from our core-infra; either keeps them out of clobber scope.
- **Org admission**: `gfs-bifrost` added to `github_organizations_extra` in terraform-core's tfvars (provider condition) — no per-repo registration treadmill for new service repos.
- **Our side**: service repo `deploy.yaml`s change only the `workload_identity_provider` + `service_account` input strings. ilg-platform workflows are already fully parameterised; `docker-build-push.yaml`, terragrunt applies, additive runtime-SA IAM, state buckets — all unchanged.

What survives untouched by their model regardless: resource-scoped IAM (topic bindings, per-secret accessors — their design explicitly leaves it alone), runtime SA creation (they manage role bindings authoritatively, not the SA inventory), and our terragrunt state buckets.

## Fence posts (the "no-man's-land" needs writing down)

1. **In the stack repo itself** (tfvars header + README): _this project's IAM is service-CI-managed; never declare roles here; audit-import passes skip this project._ Their audit default imports everything — one well-meaning future PR re-creates the war. Precedent that headers are honoured: the ecm velero note.
2. **Drop `resourcemanager.projectIamAdmin` from terraform-runner** on our projects — the template grants it by default, but in the inert arrangement there is nothing for it to administer, and keeping it leaves a standing cross-team credential that can rewrite exactly what we agreed it won't touch. (Hardening extra: scope `serviceAccountAdmin` per-SA via `google_service_account_iam_member` rather than project-wide — project-wide lets the runner grant itself impersonation on our deploy SA.)
3. **Revoke/timebox the bootstrap grants** to their elevated SA — the runbook hands `project-factory-6046@terraform-core-452622` viewer + serviceAccountAdmin + projectIamAdmin on the target project as a "one-off" and nothing revokes it.

## Provisioning-day checklist

- [ ] Re-read their `main` (template `main.tf`, `gcp-project-iam`, `gcp-iam-service-account`, `wif.tf`) — confirm the facts above still hold.
- [ ] Agree adoption-lite + the role-ownership rule in writing (fence post 1) **before** any audit script runs against our project.
- [ ] tfvars per the sketch: empty `project_roles`, empty `project_iam_bindings`, WIF member by `repository_owner`.
- [ ] Deploy SA roles granted additively; enumerate the role list from an existing project's deploy SA (`gcloud projects get-iam-policy` filtered to `github-integration@`/`github-runner@`) rather than from memory.
- [ ] `gfs-bifrost` in `github_organizations_extra`; confirm the provider condition change applied.
- [ ] Fence posts 2 + 3: runner's `projectIamAdmin` dropped; project-factory's bootstrap grants revoked post-bootstrap.
- [ ] **State bucket**: prefer a per-estate bucket over `gfs-terraform-core-tfstate` — the shared bucket gives every stack runner in their programme read/write on every other stack's state (unconditional bucket-level objectAdmin, by design). Bucket is caller-side (`backend.config.hcl`), so this costs one line + one grant in whatever owns our bucket.
- [ ] If their stack template's remote-state read points at our core state for anything: align output names (`workload_identity_provider` vs our `workload_identity_provider_name`) — remote-state outputs are API surface.
- [ ] Swap provider/SA strings in the consuming service repos' `deploy.yaml`s; one canary service first; verify a full plan/apply cycle + a runtime secret read before fleet rollout.
- [ ] After their first apply: `gcloud projects get-iam-policy` diff against pre-adoption snapshot — expect **zero** binding changes beyond the SAs the stack declares.

## Secondary thread — the reusable-workflow standardisation (separate conversation)

- Their CI gap list: no approval gates, `@main` pinning, checkov config in ecm runs exactly 3 checks, findings invisible to the secops dashboard.
- Cheapest convergence: swap their security job for `secops-secrets.yaml` + `secops-terraform.yaml` (their IaC findings land on the dashboard; zero change our side).
- The genuine platform gap if their stacks should ride our rails: a raw-terraform sibling to `terragrunt.yaml` (`terraform.yaml`: init `-backend-config` / validate / fmt / plan + PR comment / apply, WIF inputs, GH-App module auth with owner+repo scoping, `environment_name` gating). Additive → force-move `0.1-affogato`; docs travel (README + platform-mcp-server `workflows.json`).
- Ownership split that works: **rails in ilg-platform (versioned, gated, scanned); trust roots per estate** (their terraform-core / our core-infra); bucket per estate; contracts explicit (workflow inputs + remote-state output names).

## Sources

- `gfs-sre/terraform-framework` @ main 2026-07-29 — `modules/gcp-project-iam/`, `modules/gcp-iam-service-account/`, `core-stacks/terraform-core/terraform/{wif.tf,stack_state_access.tf,outputs.tf}`, `templates/legacy-project-stack/`, `docs/{PLAN-LEGACY-PROJECT-STACKS,RUNBOOK-LEGACY-PROJECT-IMPORT}.md`, `.github/workflows/reusable-legacy-stack-terraform.yml`
- `gfs-ecm/ecm-prod-uk1-iac` @ `6fa1a9c` — `terraform/{iam.tf,main.tf,variables.tf,envs/prod.tfvars}`, `run.sh`, `.github/workflows/terraform.yml` (SAML org: API search blind, SSH works)
- `ilg-platform/github-actions` @ `0.1-affogato`/`0.2-bonbon` — `terragrunt.yaml`, `secops-terraform.yaml`, `secops-secrets.yaml`; caller example `gfs-bifrost/fapi` `deploy.yml`
- Our side: `core-infra` `iac/projects/core-infra/{workload-identity.tf,outputs.tf}`; additive-IAM example `dedupe-service` `iac/projects/dedupe-service/iam.tf`
