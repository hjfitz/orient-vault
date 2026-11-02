---
tags:
- waypoint
- github-actions
verified: '2026-10-13'
verified_sha: af46124
verified_paths:
- .github
- policies
- README.md
- CLAUDE.md
title: github-actions — architecture
thesis: 'The repo is YAML and zero-dependency Node scripts on two diverging tag lines:
  main is 0.2-bonbon, and 0-1-affogato is 0.1-affogato. A fix lands on each line separately,
  and callers see it only through the tag they pin.'
confidence: high
---
# github-actions — architecture

```orient-bluf
{ "v": 1, "bluf": "The repo is YAML and zero-dependency Node scripts on two diverging tag lines: main is 0.2-bonbon, and 0-1-affogato is 0.1-affogato. A fix lands on each line separately, and callers see it only through the tag they pin.", "confidence": "high", "action": "Never force-move a tag for a breaking change, and bump every internal self-reference with the tag." }
```

## Guardrails

- [contract:G1] A backward-compatible change force-moves the existing rolling tag. A breaking change (renamed or removed input or secret, changed default, incompatible behaviour) bumps the tag number. Search the org for the tag's callers before moving it.
  — paths: .github/workflows, .github/actions
- [contract:G2] Every internal `uses: ilg-platform/github-actions/...@<tag>` and the policy checkout `ref:` name the same tag as the workflow containing them. GitHub resolves each literally, so a stale ref silently runs the old action.
  — paths: .github/workflows/secops-code.yaml, .github/workflows/secops-container.yaml, .github/workflows/secops-dep-dotnet.yaml, .github/workflows/secops-dep-go.yaml, .github/workflows/secops-dep-node.yaml, .github/workflows/secops-secrets.yaml, .github/workflows/secops-terraform.yaml
- [contract:G3] Renaming or removing a workflow file leaves a deprecation shim at the old path. A missing reusable file is a startup failure with no log. The shim redeclares the old inputs as optional with their original types, then fails with one `::error`.
  — paths: .github/workflows/secops-dependency-audit.yaml, .github/workflows/secops-gitleaks.yaml, .github/workflows/secops-image-scan.yaml, .github/workflows/secops-semgrep.yaml, .github/workflows/secops-terraform-scan.yaml
- [technical:G4] The `report` job in every `secops-*` workflow carries no `permissions:` block and never gates CI. A static `id-token: write` would fail every non-granting caller at startup.
  — paths: .github/workflows/secops-code.yaml, .github/workflows/secops-container.yaml, .github/workflows/secops-dep-node.yaml, .github/workflows/secops-secrets.yaml, .github/actions/secops-report/report-scan.mjs
- [technical:G5] The npm path takes `secrets.npm_token || github.token`, never an App token, because GitHub Packages rejects App tokens. `docker-build-push` hands the token to the build as a BuildKit secret, not a build arg.
  — paths: .github/workflows/node-run.yaml, .github/workflows/docker-build-push.yaml, .github/workflows/secops-container.yaml
- [contract:G6] A scanner label is a three-way lockstep: `VALID_SCANNERS` and the parse dispatch in `report-scan.mjs`, the workflow's own `scanner:` literal, and `job-report.schema.ts` in `secops-reporting`. A miss makes the ingest 4xx, which is logged and silently dropped.
  — paths: .github/actions/secops-report/report-scan.mjs, .github/workflows/secops-dep-go.yaml, .github/workflows/secops-terraform.yaml

## Layout — everything under `.github/`, plus `policies/`

There is no `src/`, `package.json`, `mise.toml` or lockfile. Ten files are reusable workflows, five are shims, one is a trigger, and seven are actions [18].

| Path | Kind | What it does |
| --- | --- | --- |
| `docker-build-push.yaml` | reusable | Build and push an image to Artifact Registry; optional prod approval gate and Slack notice [1] |
| `terragrunt.yaml` | reusable | Run a terragrunt command; PR plan comment; up to 5 extra `TF_VAR_*`; App-backed git-module auth [2] |
| `node-run.yaml` | reusable | Checkout, set up node and pnpm or npm, install, run one script [3] |
| `secops-dep-node.yaml` | reusable | `audit-ci@7` against a required `audit-ci.jsonc` [8] |
| `secops-secrets.yaml` | reusable | gitleaks v8.30.1 over the history reachable from the checked-out ref [9] |
| `secops-container.yaml` | reusable | In-runner image build and Trivy scan; reports as `trivy-image` [5] |
| `secops-code.yaml` | reusable | Semgrep SAST in the `semgrep/semgrep` container; `lang` preset plus `extra_config` [4] |
| `secops-terraform.yaml` | reusable | Trivy `config` scan plus the custom Rego bundle; reports as `trivy-iac` [10] |
| `secops-dep-dotnet.yaml` | reusable | NuGetAudit gate plus a GHSA-keyed allowlist gate; reports as `nuget-audit` [6] |
| `secops-dep-go.yaml` | reusable | `govulncheck` plus a GO-id allowlist gate on call-reachability; reports as `govulncheck` [7] |
| `on-tag.yaml` | triggered | Slack release notice on `v*` push tags only [12] |
| `secops-{dependency-audit,gitleaks,image-scan,semgrep,terraform-scan}.yaml` | shims | Pre-0.2 filenames; fail with one `::error` naming the replacement [11] |
| `node-setup` | composite action | Checkout, node, pnpm or npm and an optional install, as a job step [17] |
| `secops-report` | composite action | Normalise one scanner's report and POST it to the ingest API [13] |
| `sarif-summary`, `audit-ci-summary`, `gitleaks-summary` | JS actions (`node24`) | Render a report to the step log, job summary and capped annotations; always exit 0 [15] |
| `dotnet-audit-gate`, `govulncheck-gate` | composite actions | Allowlist gates; `govulncheck-gate` is the sole pass or fail authority for the Go audit [16] |

`policies/` holds Rego checks for the MongoDB Atlas provider. `CUSTOM-MONGODB-0004` ships inert, behind a literal `false`. `CODEOWNERS` still names the placeholder `@TODO-assign-policy-bundle-owner` for `/policies/` [20].

```orient-flow
{ "v": 1, "title": "A secops scan run, end to end",
  "nodes": [
    { "id": "c", "label": "Caller job", "sub": "uses: …secops-*.yaml@0.2-bonbon", "kind": "external", "ev": [22] },
    { "id": "s", "label": "Scan job", "sub": "the real gate", "kind": "step", "service": "github-actions", "tone": "accent", "ev": [4, 8] },
    { "id": "r", "label": "Renderer", "sub": "log, summary, annotations; exit 0", "kind": "step", "ev": [15] },
    { "id": "u", "label": "Report artifact", "kind": "store", "ev": [8] },
    { "id": "j", "label": "report job", "sub": "no permissions block", "kind": "step", "tone": "alert", "ev": [8] },
    { "id": "m", "label": "report-scan.mjs", "sub": "OIDC token, else key, else skip", "kind": "step", "ev": [14] },
    { "id": "i", "label": "secops-reporting", "sub": "ingest API", "kind": "service", "service": "secops-reporting", "ev": [14] }
  ],
  "edges": [
    { "from": "c", "to": "s", "label": "workflow_call" },
    { "from": "s", "to": "r", "label": "always()" },
    { "from": "s", "to": "u", "label": "on failure" },
    { "from": "u", "to": "j", "label": "download" },
    { "from": "j", "to": "m", "label": "secops-report@tag" },
    { "from": "m", "to": "i", "label": "POST; exit 1 only on network or 5xx" }
  ] }
```

```orient-flow
{ "v": 1, "title": "Two tag lines, and who pins what",
  "nodes": [
    { "id": "m", "label": "main", "sub": "af46124", "kind": "step", "service": "github-actions", "tone": "accent", "ev": [21] },
    { "id": "bb", "label": "0.2-bonbon", "sub": "tag, same commit as main", "kind": "step", "ev": [21] },
    { "id": "ab", "label": "0-1-affogato", "sub": "branch, d52202b", "kind": "step", "ev": [21] },
    { "id": "af", "label": "0.1-affogato", "sub": "tag, same commit as branch", "kind": "step", "ev": [21] },
    { "id": "c1", "label": "terragrunt, docker-build-push", "sub": "39 repo pins, plus old secops names", "kind": "external", "ev": [22] },
    { "id": "c2", "label": "Renamed secops scans", "sub": "most callers", "kind": "external", "ev": [22] },
    { "id": "c3", "label": "@main and branch pins", "sub": "template repo, route-check, pkg-node", "kind": "external", "tone": "alert", "ev": [22] }
  ],
  "edges": [
    { "from": "m", "to": "bb", "label": "same commit" },
    { "from": "ab", "to": "af", "label": "same commit" },
    { "from": "m", "to": "ab", "label": "diverged at ed195e6", "style": "dashed" },
    { "from": "c1", "to": "af", "label": "pin" },
    { "from": "c2", "to": "bb", "label": "pin" },
    { "from": "c3", "to": "m", "label": "tracks head" }
  ] }
```

## Versioning — two tag lines, not one history

Callers pin a rolling tag with no `v` prefix. `0.2-bonbon` is `main`. `0.1-affogato` is the separate `0-1-affogato` branch, which diverged from `main` at `ed195e6` [21]. `CLAUDE.md` calls 0.1 untouched, and it is not: the branch carries backports [18].

- **A fix lands twice.** The deploy-notify change is #35 on the 0.1 branch and #34 on `main`. The pnpm 11 audit fix is #20 and #21. A `main`-only fix never reaches a 0.1 caller [21].
- **0.1 still has the old `terragrunt` and `docker-build-push`.** The 0.1 `terragrunt` writes secret values into `GITHUB_ENV` through inline `${{ secrets.* }}` in a shell line. `main` moved them to `env:` with a random delimiter [24].
- **Moving `docker-build-push` to 0.2 is a Dockerfile change.** 0.2 passes a BuildKit secret, and the old build arg gets no value. The Dockerfile must mount `github_token` [1][23].
- **A caller on `@main` or a branch skips the tag.** It takes every merge to `main` as it lands, including breaking ones [22].
- **Force-moving a tag reaches every pinned caller on its next run.** Verify against a real caller first.
- **`on-tag.yaml` never fires for a rolling tag.** It needs a `v*` tag, so announcing a tag move is manual [12].

## Callers — derived from code, not memory

Each cell counts repos among 27 local checkouts, read at `origin/HEAD` [22]. The org-wide caller set is **UNKNOWN**: the other orgs were not searched.

| Workflow | `@0.1-affogato` | `@0.2-bonbon` | Other pin |
| --- | --- | --- | --- |
| `terragrunt` | 21 | 0 | 0 |
| `docker-build-push` | 18 | 1 | 0 |
| `node-run` | 3 | 2 | 1 on `hjf/node-run-pnpm-filter` |
| `secops-secrets`, `-dep-node`, `-container`, `-code` | 0 | 15, 13, 11, 8 | 1 each on `@main` |
| `secops-terraform`, `-dep-go` | 0 | 7, 2 | 0 |
| Shims (`gitleaks`, `dependency-audit`, `image-scan`, `semgrep`, `terraform-scan`) | 5, 5, 3, 1, 1 | 0 | `gitleaks` and `dependency-audit` on `@main` |

The `@main` shim callers are in `repo-template-ilg`, where the shims fail by design. `pkg-node` pins `node-run` to a feature branch that adds a pnpm `filter` input. `main` has no such input.

## Auth model — three paths, do not conflate them

- **GitHub App token, `terragrunt.yaml` only.** It fetches private `git::https` module sources. It is gated on the `PLATFORM_CI_APP_ID` org variable and the `gh_app_private_key` secret both being present. It falls back to the `gh_token` PAT, then to nothing. The token goes into the job's global git config [2].
- **npm registry, `node-run`, `docker-build-push`, `secops-container`.** Not App-backed. `github.token` reads same-org packages. A PAT `npm_token` is only for cross-org packages. `github_token` is a reserved secret name. `node-run` exports the token as both `NODE_AUTH_TOKEN` and `GITHUB_TOKEN` [3]. `secops-container` still passes a build arg, but only to a throwaway scan image [5].
- **secops reporting.** A GitHub OIDC token with audience `secops-ingest`, else the static `secops_ingest_api_key`, else the step skips [14].
- **GCP.** `docker-build-push` and `terragrunt` authenticate with Workload Identity or `gcp_credentials_json`. `terragrunt` has no `permissions:` block, so the caller must grant `id-token: write` [1][2].

## SecOps reporting — unconditional, never gates CI

The `report` job always runs. A caller controls auth quality, not whether reporting happens. Granting `id-token: write` gives OIDC; without it the step no-ops [8][14]. `report-scan.mjs` exits non-zero only on a network error or a 5xx. The scanner is the gate.

Each workflow calls `secops-report@0.2-bonbon` by rolling tag, not by working tree. That is the self-reference in G2. Renderers are tag-pinned JS actions with real script files, because a reusable workflow runs from the caller's checkout and no loose script exists there. `sarif-summary` is a JS action so it runs inside the semgrep container, which has no Node. `gitleaks-summary` never prints `Match` or `Secret` [15].

## Failure-output rendering — a deliberate DX contract

A red scan must be diagnosable from the run page. Each scanner workflow renders findings three ways: a step-log block per finding, a job-summary table, and capped `::error` annotations. Annotations carry `file=` and `line=` only when the report's locations are repo paths. Rendering runs with `continue-on-error: true`, and the script always exits 0 [4][5][15]. Artifact names and scanner labels are the machine interface to ingest, so renderers must not change them.

## Verified defaults — trust the YAML

- **Node `22`** in `node-run`, `node-setup`, `secops-dep-node` and `secops-report`. The README table still says `20` in two places [3][19].
- **`pnpm_version` `9`** in `node-run` and `node-setup`. `secops-dep-node` has no such input: it installs `pnpm@11` and deletes the repo's `packageManager` pin, because pnpm 10 and earlier call retired audit endpoints [8].
- **`environment_name: terraform-prod`** gates `docker-build-push` and `terragrunt` behind an approval. Empty means no gate. Slack headers go `[PROD]` on an exact `prod` match, on `environment` in one and `tf_var_env` in the other [1][2].
- **`secops-dep-go`.** `go_version` `1.25`. `govulncheck`'s exit code is discarded, and `govulncheck-gate` decides on symbol-level findings only [7][16].
- **`secops-container`.** Severity `CRITICAL,HIGH`, scanner `vuln`, `ignore_unfixed` true. **`secops-code`**: severity `ERROR`. **`secops-terraform`**: floor `HIGH` [4][5][10].
- **The Rego bundle can be absent for callers.** `secops-terraform` checks it out from this repo with `continue-on-error`, and a caller's `GITHUB_TOKEN` cannot read an internal repo. **ASSESSED** from the step's own comment, which records a reproduced failure across 0.2 consumers. Repo access settings sit outside the code [10].

## Trust boundaries

- **No workflow uses `pull_request_target`, `workflow_run` or `issue_comment`.** Each is `workflow_call`, apart from `on-tag.yaml`, which fires on a `v*` tag push [12]. Trigger safety belongs to each caller.
- **Inputs reach shell lines unescaped.** `node-run` runs `${{ inputs.package_manager }} run ${{ inputs.script }}`. `secops-container`, `secops-dep-node` and `docker-build-push` interpolate `dockerfile`, `working_directory` and `region` the same way. Callers pass constants. A caller that feeds branch or PR text into those inputs makes them injectable [1][3][5][8].
- **Tooling is fetched at run time without a pin or checksum.** `govulncheck@latest`, `audit-ci@7` through `npx`, `pnpm@11`, the unpinned `semgrep/semgrep` image, and gitleaks by `curl` from a pinned URL with no checksum. Third-party actions pin to tags, not SHAs [7][8][9].
- **`report_api_url` receives the OIDC token.** It defaults to the prod ingest URL. A caller that overrides it sends the token, and any static key, to that host [14].

## Evidence

```orient-evidence
{ "v": 1, "items": [
  { "id": 1, "kind": "code", "ref": ".github/workflows/docker-build-push.yaml@af46124" },
  { "id": 2, "kind": "code", "ref": ".github/workflows/terragrunt.yaml@af46124" },
  { "id": 3, "kind": "code", "ref": ".github/workflows/node-run.yaml@af46124" },
  { "id": 4, "kind": "code", "ref": ".github/workflows/secops-code.yaml@af46124" },
  { "id": 5, "kind": "code", "ref": ".github/workflows/secops-container.yaml@af46124" },
  { "id": 6, "kind": "code", "ref": ".github/workflows/secops-dep-dotnet.yaml@af46124" },
  { "id": 7, "kind": "code", "ref": ".github/workflows/secops-dep-go.yaml@af46124" },
  { "id": 8, "kind": "code", "ref": ".github/workflows/secops-dep-node.yaml@af46124" },
  { "id": 9, "kind": "code", "ref": ".github/workflows/secops-secrets.yaml@af46124" },
  { "id": 10, "kind": "code", "ref": ".github/workflows/secops-terraform.yaml@af46124" },
  { "id": 11, "kind": "code", "ref": ".github/workflows/secops-dependency-audit.yaml@af46124" },
  { "id": 12, "kind": "code", "ref": ".github/workflows/on-tag.yaml@af46124" },
  { "id": 13, "kind": "code", "ref": ".github/actions/secops-report/action.yaml@af46124" },
  { "id": 14, "kind": "code", "ref": ".github/actions/secops-report/report-scan.mjs@af46124" },
  { "id": 15, "kind": "code", "ref": ".github/actions/sarif-summary/action.yaml@af46124" },
  { "id": 16, "kind": "code", "ref": ".github/actions/govulncheck-gate/check-allowlist.mjs@af46124" },
  { "id": 17, "kind": "code", "ref": ".github/actions/node-setup/action.yaml@af46124" },
  { "id": 18, "kind": "code", "ref": "CLAUDE.md@af46124" },
  { "id": 19, "kind": "code", "ref": "README.md@af46124" },
  { "id": 20, "kind": "code", "ref": ".github/CODEOWNERS@af46124" },
  { "id": 21, "kind": "log", "ref": "git ls-remote origin: refs/heads/0-1-affogato d52202b, refs/tags/0.1-affogato d52202b, refs/tags/0.2-bonbon af46124 (= main); git log origin/main..0.1-affogato lists #20 and #35 only; merge-base ed195e6" },
  { "id": 22, "kind": "log", "ref": "git -C ~/code/fuse/<repo> grep -E 'github-actions/\\.github/(workflows|actions)/[^ ]+@[^ ]+' origin/HEAD -- .github, over 27 repo checkouts excluding worktrees, 2026-10-13" },
  { "id": 23, "kind": "pr", "ref": "ilg-platform/github-actions#8" },
  { "id": 24, "kind": "log", "ref": "git diff 0.1-affogato origin/main -- .github/workflows/terragrunt.yaml (inline secrets.* in run on 0.1; env: plus delimiter on main)" }
] }
```
