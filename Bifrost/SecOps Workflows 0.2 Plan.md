# SecOps Workflows 0.2 Plan

_Updated 2026-07-16 evening (drafted 2026-07-10). Target: land WS1–5 on `ilg-platform/github-actions` main + coordinated `gfs-bifrost/secops` PRs, released on the **`0.2-bonbon`** line — which already exists (minted today at main HEAD by PR #21's pnpm-11 carry). One release, four waves, all five decisions settled._

## State of the world — verified 2026-07-16 evening

Established from `git ls-remote` + `git show origin/main:…` / `git show <tag>:…` — **not** local working trees. (Two earlier same-day "corrections" to this doc claimed tfsec was still the live scanner and `report_enabled` was dead config; both were artifacts of a stale local checkout **and** a stale local tag ref — `git fetch --tags` does not update force-moved tags. Both retracted. Lesson memorialized in agent memory: audit from origin refs and `ls-remote`, never local state.)

**Release lines:**

| Line | Points at | Contains | Consumers |
| --- | --- | --- | --- |
| `0.1-affogato` | `f23d95b` (maintenance branch `0-1-affogato`) | tfsec terraform scan (SARIF out) · working `report_enabled` OIDC reporting on all 5 reusables · pnpm-11 audit fix (#20, cherry-picked) | **whole fleet** |
| `0.2-bonbon` | `619713f` (= main HEAD) | Trivy `config` terraform scan (reports under `tfsec` label deliberately — own dashboard lane) · `trivyignores` input · severity floor→list mapping · pnpm-11 fix (#21) · docker-build-push BuildKit **breaking** change · node-run additions | **none yet** |

**Recent history that reshaped this plan:** npm retired its legacy audit endpoints 2026-07-15 → every fleet nightly's `dependency_audit` failed that morning → fixed same day by PR #20 on the 0.1 maintenance branch + force-moving `0.1-affogato`; PR #21 carried the fix to main and minted/moved `0.2-bonbon`. Caveat from that fix: the bulk audit endpoint returns **GHSA ids, not CVE ids** — CVE-keyed `audit-ci.jsonc` allowlist entries fleet-wide need re-keying as they next come up for triage.

**Reporting:** `report_enabled` is a real input on all 5 reusables (both lines): a separate best-effort `report` job POSTs to the secops ingest API via the `secops-report` composite action, OIDC-authenticated, hardcoded prod URL default. Design detail worth keeping: the report job deliberately has no `permissions` block — it inherits the caller's, so callers without `id-token: write` no-op instead of failing. **Every fleet caller already passes `report_enabled: true` + grants `id-token: write`.** The only exception is the `secops` repo itself, still on its pre-productization bespoke report job (stale header comments).

**Caller inventory (from origin HEADs):** all of config-service, collector, replay, fuse-ui, dedupe-service, sftp-connector, shopify-connector, fapi, snap-adapter, pkg-node call the scanners with reporting on. `terraform_scan` is wired in only dedupe-service, sftp-connector, shopify-connector (shopify-app iac tree only), snap-adapter, secops — **not** config-service / collector / replay / fuse-ui / fapi (all have iac; the first four hold the Mongo Atlas clusters WS5 exists for), and shopify-connector's own iac tree is unscanned. core-infra + bifrost-pubsub have no `secops.yaml` at all. OMS is decommissioned (2026-07-16) — out of scope everywhere below.

## Goals

- **DX-friendly names** — rename scanner files by *what they scan*, not the tool, so the next tool swap never touches a file name.
- **Finish the tfsec retirement** — the engine swap is done on the bonbon line; retire the deliberate `tfsec` reporting label via the `trivy-iac`/`trivy-image` schema split, and migrate caller `.tfsec` configs at adoption.
- **Always-on reporting** — retire `report_enabled`; the fleet unanimously opts in already.
- **Language support** — ts/js (have it), add .NET at full depth (SAST + dep audit + onboard the 3 C# repos), reserve go.
- **Close the third-party-provider blind spot** — custom Trivy Rego checks for `mongodbatlas` (no adapter in any scanner) + GCS lifecycle, **and wire `terraform_scan` into the repos that actually hold the clusters** (without which WS5 scans almost nothing it was designed for).

## Grounding (fleet language survey, 2026-07-10)

- **Go: zero repos** across all orgs — reserve `secops-dep-go`, build nothing.
- **.NET: real but un-onboarded** — 3 C# repos in `gfs-hybrid-services` (`collections`, `WilcoService`, `UploadServiceV2DataBridge`); none call secops yet. Decision 2 (2026-07-16): full depth in this cut — the Technical Services team's services will use .NET.
- Everything else is TypeScript/JavaScript.

## Scope lever — DECIDED: Shape B, in waves (2026-07-16)

Land `github-actions` + `secops` together, per-workstream. Waves sized by whether `secops`'s ingest schema changes. All waves land on main; `0.2-bonbon` force-moves with each (it's unconsumed until announced, so intermediate moves are safe); the announcement (WS4) happens once all four are in.

| Wave | Contents | `github-actions` | `secops` |
| --- | --- | --- | --- |
| **1** | WS1 — rename + retire `report_enabled` + drop vestigial `pnpm_version` | ✅ | — |
| **2** | WS2 — `trivy-iac`/`trivy-image` label split (drops the `tfsec`-label shim) | ✅ | ✅ **coordinated** |
| **3** | WS3 — `secops-dep-dotnet` + `secops-code` .NET preset + 3 C# onboardings | ✅ | ✅ **coordinated** (new scanner type in `ScannerSchema`) |
| **4** | WS5 — custom Atlas/GCS Rego bundle + `terraform_scan` caller onboarding | ✅ | — (rides Wave 2's `trivy-iac` shape) |

## Workstream 1 — Rename by target + retire the reporting flag · Wave 1

| New file | From | Scans | Tool (hidden) |
| --- | --- | --- | --- |
| `secops-secrets.yaml` | `secops-gitleaks.yaml` | committed secrets | gitleaks |
| `secops-container.yaml` | `secops-image-scan.yaml` | container image vulns | Trivy |
| `secops-code.yaml` | `secops-semgrep.yaml` | SAST | Semgrep |
| `secops-terraform.yaml` | `secops-terraform-scan.yaml` | IaC misconfig | Trivy |
| `secops-dep-node.yaml` | `secops-dependency-audit.yaml` | dependency advisories | audit-ci |

- Behaviour-identical rename; drop the `-scan` suffix; no shim files (`0.1-affogato` stays alive for laggards).
- **Retire `report_enabled`** (decision, 2026-07-16, reaffirmed on corrected facts): remove the input and the `if: inputs.report_enabled` condition — the report job always runs. Keep the inherit-permissions design so a caller without `id-token: write` no-ops rather than fails. Every current caller passes `true`, so fleet behaviour is unchanged; callers delete the line when bumping.
- **Drop the vestigial `pnpm_version` input** on `secops-dep-node` — main's fix pins pnpm 11 unconditionally and keeps the input only for tag-line compat; 0.2 is the breaking line, so remove it. Callers delete the line when bumping.
- Update README + CLAUDE.md with the old→new migration table.

## Workstream 2 — Finish the tfsec retirement · Wave 2, coordinated

The engine swap is **done** on the bonbon line (Trivy `config`, severity floor→list mapping, `limit-severities-for-sarif`, `trivyignores` input, SARIF artifact). What remains:

- **Label split:** `secops-terraform` currently reports `scanner: tfsec` on purpose (commented: keeps Terraform its own dashboard lane vs container Trivy). Replace with `trivy-iac`; `secops-container` reports `trivy-image`. Same lane separation, honest labels.
- **`secops` (same PR-pair window):** `ScannerSchema` — remove `tfsec`, replace `trivy` with `trivy-image` + `trivy-iac`; distinct IaC finding variant (AVD id / misconfig shape); ripple through `job-report.types.ts`, `job-report.service.ts`, UI (`lib/secops/types.ts`, `filters.ts`, `fix.ts`, `finding-location.tsx`, `worklist-row.tsx`); backfill/tombstone existing docs.
- **Caller `.tfsec` → `.trivyignore` migration happens at adoption:** each caller's 0.2-bump PR migrates its own config or its previously-suppressed findings go live. dedupe-service (empty exclude) is trivial; **sftp-connector has 6 live suppressions** — translate each long-form rule id to its AVD id (already annotated as comments), preserve `reason`/`safe`/`reviewed` as comments, and **don't carry AVD-GCP-0066 (CMEK) forward verbatim** — FUSE-1041 is closing that gap; re-add with an expiry tied to it or let it go red as a reminder.
- **`secops` repo cleanup:** fold its bespoke `report` job + `report-scan.mjs` script onto the built-in (now always-on) reporting; its "PILOT"/"COVERAGE CAVEAT" header comments predate #13/#14 and are stale.

## Workstream 3 — .NET at full depth · Wave 3, coordinated

- **`secops-code` .NET preset** — `dotnet`/`csharp`/`cs`/`.net` → `p/csharp p/owasp-top-ten`. **Verified 2026-07-16:** both packs exist; C# is GA in Semgrep (up to C# 13); p/owasp-top-ten's 27 C# rules are the identical set to p/csharp (harmless dedupe, keeps preset shape consistent with ts/js/go); no `p/dotnet` exists. Optional richer coverage: `p/default` carries 15 extra C# security rules (SSRF, os-command-injection, insecure deserialization, web.config checks) — layer via the existing `extra_config` input per-repo rather than changing the preset.
- **`secops-dep-dotnet`** — design updated on verified mechanics (2026-07-16): `dotnet list package --vulnerable` **never exits non-zero on findings** (feature request closed won't-fix; exit 1 = report-generation failure only), and Microsoft's canonical CI gate is now **NuGetAudit on restore** (.NET 8+ SDK, on by default; `NU1903;NU1904` as `WarningsAsErrors` = exact high+critical parity with audit-ci; `NuGetAuditMode=all` for transitives; fails restore natively, zero parsing). **Two-layer design:** primary gate = NuGetAudit restore; second layer = `dotnet list package --vulnerable --include-transitive --format json` (SDK ≥ 7.0.200) parsed against a GHSA-URL-keyed allowlist file with `notes` + `expiry` mirroring `audit-ci.jsonc` — because `NuGetAuditSuppress` has **no expiry mechanism** and the org's 5/7-day expiry culture is the point. Gotchas: restore required first; network to api.nuget.org (or `auditSources` → data.nuget.org); `.dcproj`/docker-compose projects break solution-level list (NuGet/Home#12520); severity value is "Moderate" not "Medium".
- **Onboard all 3 C# repos — scope adjusted after reading their actual project files (2026-07-17):**
  - `UploadServiceV2DataBridge` — **net8.0, SDK-style, PackageReference**: full onboarding (`secops-secrets` + `secops-code` .NET + `secops-dep-dotnet`). The only one of the three where the NuGetAudit gate works as designed.
  - `collections` — **.NET Framework v4.8, old-style csproj, but uses PackageReference** (16 refs): `secops-secrets` + `secops-code` now; `secops-dep-dotnet` is **unverified** for it — `dotnet restore`/`dotnet list package` don't reliably support non-SDK-style projects on a Linux runner. Verify during Wave 3; if it doesn't restore, the honest options are an SDK-style csproj migration (owned by Technical Services, not secops) or deferring its dep audit.
  - `WilcoService` — **.NET Framework v4.8.1, zero NuGet packages** (41 direct assembly `<Reference>`s): there is nothing for a dependency audit to scan. `secops-secrets` + `secops-code` only; dep-dotnet is N/A, not deferred.
- **`secops-dep-node`** — rename only (plus the input drops from WS1). audit-ci and its allowlist/expiry culture stay.
- Dependency scanning stays **best-of-breed, not all-in on Trivy** (Node advisory-DB + `--prod` scoping; reachability for future Go). Trivy `fs` remains the documented fallback for other ecosystems.

## Workstream 4 — Release mechanics · after all waves

- Waves land on main in order; `0.2-bonbon` force-moves along (unconsumed until announced). Announce once, after Wave 4.
- Migration guide in README + `#bifrost-forge`: rename table · `report_enabled` + `pnpm_version` line removals · `.tfsec`→`.trivyignore` (with the AVD-id translation note) · **the BuildKit breaking change in `docker-build-push`** — callers bumping ALL their `@0.1-affogato` pins to `@0.2-bonbon` must migrate their dockerfile to the BuildKit secret, or bump only the `secops-*` pins · the GHSA-vs-CVE allowlist re-keying note.
- Update `terraform-template` / `mcp-template` / `ui-toolkit` reference callers to the new names.

## Workstream 5 — Custom Atlas/GCS policies + caller onboarding · Wave 4

**Feasibility confirmed 2026-07-16** (researched + adversarially cross-checked, all claims confirmed from primary sources):

- `trivy-action@v0.36.0` — already the pin on main, and still the latest release — bundles **Trivy v0.70.0**, comfortably past v0.63.0 where `terraform-raw` custom-check support shipped. **No version bump needed.** Pin the Trivy CLI via the action's `version` input for determinism.
- **Wiring:** no dedicated action input exists for custom check paths. Use step-level env vars on the trivy-action step (the README-documented route for flags without inputs): `TRIVY_CONFIG_CHECK=<policies dir>`, `TRIVY_CHECK_NAMESPACES=<namespace>`, `TRIVY_RAW_CONFIG_SCANNERS=terraform`, `TRIVY_MISCONFIG_SCANNERS=terraform` (the raw scanner does not work alone — the terraform misconfig scanner must also be enabled). Alternative: `trivy-config` input + trivy.yaml (`rego.check` / `rego.namespaces` / `misconfiguration.*`).
- **A ruleset, not a plugin:** a bundle of `.rego` files with metadata headers in `ilg-platform/github-actions`, wired into `secops-terraform.yaml`. `mongodbatlas` has no Trivy adapter, so all Atlas checks use the `terraform-raw` input selector.
- **POC DONE (2026-07-17, against Trivy v0.70.0 — the exact binary the action bundles):** a custom `terraform-raw` check against `mongodbatlas_advanced_cluster` works end-to-end. Flags `backup_enabled = false` **and** the attribute-omitted case; zero false positives on a compliant cluster; custom id (`CUSTOM-MONGODB-0001`) + HIGH severity + exact line-range attribution all render; **`.trivyignore` suppresses the custom id and clears the `--exit-code 1` gate** (comments in the ignore file are fine) — so the Wave 4 expiry-suppression rollout mechanism is proven too. Schema facts for whoever authors the remaining checks: blocks expose `kind` / `type` / `name` / `attributes` / `__defsec_metadata` (resource name is `name` — there is **no** `labels` array); `attributes` iterates as objects with `.name`/`.value`; `result.new(msg, block)` attaches location. Bonus DX: annotating `schemas: - input: schema["terraform-raw"]` gets compile-time type-checking of the check — a wrong field reference fails with the list of valid fields. POC artifacts in the session scratchpad (`trivy-poc/`).
- **Checks (1:1 with FUSE-1038):** `backup_enabled` = true · `pit_enabled` = true · every cluster has a `mongodbatlas_cloud_backup_schedule` with `copy_settings` outside its own region · every cluster has `mongodbatlas_encryption_at_rest` (**ships disabled/suppressed until FUSE-1041's tier question resolves** — decision 4) · every customer-data `google_storage_bucket` declares a `lifecycle_rule`.
- **No ingestion work:** custom findings ride the same SARIF with custom ids (`CUSTOM-MONGODB-0001`…) into Wave 2's `trivy-iac` shape.
- _Rejected: Checkov — a second overlapping IaC scanner for one narrow gap._

**Caller onboarding (the other half — without it WS5 scans almost none of its targets):**

- Add a `terraform_scan` job to **config-service, collector, replay, fuse-ui, fapi** (all have iac; the first four hold the Atlas clusters) and a second job for **shopify-connector's own iac tree**.
- Give **core-infra** (KMS keyring — FUSE-1041's subject) a `secops.yaml`; decide bifrost-pubsub while at it.
- Every onboarding PR ships its `.trivyignore` with expiry-tracked suppressions (`reason`/`safe`/`reviewed`/`expiry`) tied to the matching FUSE-1038 ticket's sprint end — a stale suppression is itself the signal the ticket slipped.
- Severity: gate at HIGH once the fleet is clean (decision 3).

## Cut line

- **Wave 1** WS1 rename + retire `report_enabled` + drop `pnpm_version` → **Wave 2** WS2 label split + `secops` schema (coordinated) → **Wave 3** WS3 .NET preset + `secops-dep-dotnet` (coordinated) + 3 C# onboardings → **Wave 4** WS5 policy bundle + POC + `terraform_scan` caller onboarding with expiry suppressions → **WS4** announce `0.2-bonbon`.
- **Dropped:** live-vs-declared drift detection (ex-WS6) — separate initiative if wanted; FUSE-1039 fixes the concrete instance.

## Decisions — all settled 2026-07-16

1. ✅ **Shape B, in waves** — only Waves 2 and 3 need `github-actions`+`secops` coordination.
2. ✅ **.NET full depth in this cut** — preset + `secops-dep-dotnet` + 3 onboardings.
3. ✅ **WS5 gates at HIGH** once the fleet is clean and suppressions expire.
4. ✅ **CMEK check ships disabled/suppressed** until FUSE-1041 resolves.
5. ✅ **Distinct CODEOWNERS entry** for the Rego policy bundle.

## Live security triage — surfaced by the 2026-07-16 health check, not plan scope

1. **dd-trace GHSA-wxqq-gcq8-c443 (HIGH, prod dep, unallowlisted)** — failing dedupe-service + collector nightly `dependency_audit` right now (path includes `@ilg-platform/observability-trace>dd-trace`). Triage per allowlist-first policy or bump dd-trace.
2. **collector's lodash GHSA-r5fr-rjxr-66jc allowlist entry expired 2026-04-28** — re-triage, long overdue.
3. **CVE-2026-12151 (undici, HIGH, inside node:24 base image's bundled npm CLI)** — failing `image_scan` on dedupe/collector/sftp-connector.
4. When re-triaging any of the above: allowlist keys must be **GHSA ids** now (post pnpm-11 fix), not CVE ids.
