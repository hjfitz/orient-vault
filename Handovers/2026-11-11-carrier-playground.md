---
tags: [handover]
status: resumed
workstream: Twelve mock carrier proxies with dev IaC and DNS in ilg-merak/carrier-playground
programme: none
repo: ilg-merak/carrier-playground
from: hjf.shell.platform.ilg.software (rc-hjf)
to: laptop
session_id: 9d74d588-1876-4a16-907d-7470c90d25d5
resumed_by: 396b7315-aa79-43a2-af2d-63d6eb3aac55
updated: 2026-11-11T09:42Z
---
# Handover: mock carrier proxies (carrier-playground), workstation → laptop

Continues [[Handovers/2026-11-05-carrier-playground]] (laptop → rc-hjf, now closed).

## Where things stand
`origin/main` is `d98fd9b` (#14). It is deployed to ilg-merak dev by `deploy-dev` run 42603726675 (green, 9 Nov). There are no open PRs, no in-flight branches and no running agents. Twelve mock proxies are live at
`https://<name>.mocks.merak.freightops.dev`, plus a private `mock-upstreams`. All run on the golden `node24-runtime` image and ship logs to GFS Datadog only. The last smoke run passed 42/42 through every name (9 Nov). There is no prod environment, by design.

| Name | Mirrors (prod source) | PR |
| --- | --- | --- |
| `royalmail`, `ups`, `coll8` | ADO `gfs-royal-mail-proxy`, `GFS UPS Integration`, `GFS Coll8 Integration` | #1 |
| (edge + DNS) | one HTTPS LB `iac/projects/mock-edge`, records in core-infra's dev zone | #2, #7 |
| `fedex` | GitHub `gfs-hybrid-services/fedex-proxy` | #3 |
| `dpdeu` | ADO `GFS DPD-Europe Integration/dpd-europe-proxy` | #4 |
| `amazon-sfp` | GitHub `gfs-hybrid-services/amazon-proxy` (the SFP proxy, `new-amazon-prod.gfsdeliver.com`) | #5, #6 |
| `amazon` | ADO `GFS Amazon Logistics Integration/gfs-amazon-logistics-proxy` (`amazon.gfsdeliver.com`) | #8 |
| `bjs` | ADO `GFS Hybrid Services and Carrier Integrations/bjs-proxy` (not the GitHub copy) | #9 |
| `inpost` | GitHub `gfs-hybrid-services/inpost-proxy` | #10 |
| `ocs` | ADO `…/ocs-proxy` `main` `29eeaa6` (= prod image `prod-57357`) | #11 |
| `exelot` | ADO `GFS Exelot Integration` `main` `b21a47d` | #12 |
| (smoke) | restored `isPng`; `pnpm typecheck` now also type-checks `scripts/` | #13 |
| `veho` | **No prod proxy exists.** Built from the agreed contract (`carrier-proxies` `apps/veho-proxy/src/api/openapi.yaml`, CID-336), the spec (Confluence 323878984), the stories under epic CID-335, and Veho's public docs | #14 |

Each PR has a "production behaviour mirrored on purpose" section and a dev-evidence comment. The `wp ledger carrier-playground` has one entry per PR.

## In flight
None.

## Waiting on Harry
- **Tell the Veho team about the mock?** Recommendation: yes. Add one comment on CID-335 (or CID-338) linking `https://veho.mocks.merak.freightops.dev` and PR #14. It matches the epic's outcome that consumers can integrate before the real calls exist. Nothing has been posted to Jira or Slack.
- **Prod findings the mocks surfaced** are read from the source code and not confirmed against prod logs. Whether, and to whom, to raise them is your call:
  - InPost logs full payloads (`LOG_CARRIER_PAYLOAD=true`, marked TEMPORARY), callers' ApiKy keys, and its Basic auth header on token failure (#10).
  - Exelot and OCS log whole axios errors, carrier tokens included (#11, #12).
  - Exelot always calls the real ApiKy, whatever its env says (#12).
  - OCS and Exelot multiply GRAM weights by 1000 (#11, #12).
  - DPD Europe's validator probably rejects every Selector call (#4).
  - Amazon Logistics refuses PDF labels (#8).
- **Tech Services repos:** leave them alone (Harry, 5 Nov).

## Next up
All optional. Nothing was requested beyond Veho.
1. A DHL mock behind Selector's `DHL_URL`. There is no proxy; Selector calls DHL directly.
2. Fix the platform `networking/load-balancer` module in `ilg-platform/terraform-modules`: removing a service deletes its backend and cert before detaching them. Until that's fixed, never remove a name from `mock-edge`.
3. Mock clean-ups listed in the PR notes:
   - five carriers copy or import a PNG encoder across carriers; move it into `packages/mock-kit`;
   - UPS logs `RequestId undefined`;
   - dd-trace reports `env:serverless`;
   - no max-instance cap (the module lacks the input).
4. Veho follow-ups as the real build lands: per-account keys (CID-346), merchants (CID-343), the ZIP pre-check (CID-345), and webhooks/tracking/POD (CID-347 to CID-351). Update the mock to match each one.

## How work is done here
- **Repo rules:** `AGENTS.md`. Same contract, lookups and logic; every upstream mocked; all data fake; never log bodies, labels, keys or credentials.
- **Autonomy:** memory `feedback-ship-pragmatic`, "full steam ahead, ask only if something breaks". For dev-only `mock-*` infra, merging and the auto-apply to dev are fine once you have read the PR's plans yourself and they show only adds/updates. A plan with a destroy, or a prod gate, stops for Harry. The one prod gate approved in this run (core-infra#18, a no-op) had Harry's explicit OK.
- **Shape of each new mock:** confirm the prod source from the cluster ingress plus DNS (`GFS Cluster Configurations/prod-uk1-primary-cluster` `deploy/k8s/<carrier>/`, then `getent hosts <carrier>.gfsdeliver.com`). Then one builder agent, then two reviewer agents (A: fidelity to the source; B: contract, data safety, tests, infra), then fixes proven by mutation, then PR, merge, deploy, smoke through the name, and a Datadog leak search.
- **Reusable kit,** in the vault at `Engineering/carrier-playground/agent-kit/`:
  - `builder-brief.md`, the shared builder rules;
  - `review-brief.md`, dimensions A and B;
  - `resolve_union.py`, the union-merge resolver for the shared files (workflows, edge, server.ts, smoke, README, AGENTS).
  - Replace `<your scratchpad>` with your scratchpad path.
- **ADO source access:** `ado-local-mcp` (needs `npx` on the PATH Claude starts with). Read-only; never use its write tools.
- **Installs:** `env "npm_config_//npm.pkg.github.com/:_authToken=$(gh auth token)" mise x -- pnpm install`, then `pnpm install --lockfile-only --fix-lockfile`, because a plain install drops `optional` markers.
- **Checks:** run `pnpm lint`, `typecheck` (which now includes `scripts/`) and `test` before pushing.
- **Work happens in worktrees** under `.claude/worktrees/`. Out-of-ticket branches are `hjf/<desc>`.

## On the target (laptop)
Resumed 2026-11-11T09:42Z by session 396b7315. Re-checked live from the laptop, and the record held:
- `origin/main` is `d98fd9b`; no open PRs; `deploy dev` run 42603726675 is green on that sha.
- `veho`, `ups` and `royalmail` answer through their `*.mocks.merak.freightops.dev` names. Veho serves `/healthz` (200), not `/`.
- The local clone `~/code/merak/carrier-playground` is on `hjf/mock-carrier-proxies` (`4932d6e`, remote branch gone), untouched. Start from a worktree off `origin/main`.
- `wp locate carrier-playground` resolves.

Not checked from rc-hjf when this was written: the laptop isn't reachable from there.
- Before starting, `git -C ~/code/merak/carrier-playground fetch && git switch main && git pull` (or a worktree from `origin/main`).
- The local clone may still be on `hjf/mock-carrier-proxies`, which was deleted on the remote after #1 merged.
- `mise install` gives node 24, pnpm 10.34.7, terraform 1.14.9 and terragrunt 0.50.8.
- The vault (this record and `agent-kit/`) arrives by `orient-vault-sync`.
- This session's memories under `~/.claude/projects/-home-harry-code-merak/memory/` (`feedback-ship-pragmatic`) already show the laptop's later edits, so `~/.claude` is in step.

## Gotchas
- **Never remove a name from `mock-edge`.** The platform LB module deletes before detaching (`resourceInUseByAnotherResource`), and a retry fails identically. Only add or update.
- **Merging parallel mock branches:**
  - Git interleaves `scripts/smoke.mts` sections that share lines, and the resolver once fused two auth-list rows.
  - Rebuild smoke.mts from main and add the new section rather than trusting a textual merge.
  - `pnpm typecheck` now catches a broken smoke script.
  - After any merge, grep the smoke output for every `without a key` row.
- **A deploy watch must stop on the first failed job.** Watching for a downstream signal instead cost 45 minutes on #6.
- **Unexplained startup failure, 6 Nov:** the `deploy-dev` run for #13 (`8a5f3a0`) failed when mock-upstreams' new revision missed its Cloud Run startup probe. The tracer loaded and `listening` never followed; normal startup is about 5 s. The cause is not established. The next deploy was fine. If it recurs, re-run the failed jobs. If it keeps happening, look at startup time (`tsx` compiles at boot) against the probe (3 × 10 s).
- **Check every source's real prod deployment before building** (cluster ingress plus DNS). GitHub "modernised" copies are often not what prod serves: Amazon, BJS, Exelot and OCS all had a newer copy that wasn't live.
- **Error-body shape:** the older carrier sources spread Ajv errors into `metaData: {"0": …}`. The newer `api-host-framework` (Veho) uses `errors: [{field, problem}]`.
- **New public names draw certificate-transparency scanners within minutes.** They get harmless 4xx.

## Closed since handover
| When (UTC) | Work | Result |
| --- | --- | --- |
