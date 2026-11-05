---
tags: [handover]
status: open
workstream: Mock carrier proxies (Royal Mail, UPS, Coll8) with dev IaC in ilg-merak/carrier-playground
programme: none
repo: ilg-merak/carrier-playground
from: laptop
to: hjf.shell.platform.ilg.software
session_id: 945d0e77-3787-450a-a8e6-3635e238a5c9
resumed_by: ""
updated: 2026-11-05T16:12Z
---
# Handover: mock carrier proxies (carrier-playground)

## Where things stand
New repo `ilg-merak/carrier-playground`. `main` is one initial commit (`bfd6247`). All the work is on
`hjf/mock-carrier-proxies` (`4932d6e`) in **PR #1**, which is open and not merged. Nothing is deployed:
merging runs `deploy-dev.yaml`, which applies Terraform to ilg-merak dev.

| Unit | What it delivered | PR | State |
| --- | --- | --- | --- |
| Scaffold | pnpm workspace (mise: node 24, pnpm 10.34.7, terraform 1.14.9, terragrunt 0.50.8), `packages/apiky-client`, `packages/mock-kit`, `apps/mock-upstreams` | #1 | done |
| Royal Mail mock | `apps/royal-mail-proxy` (source ADO `gfs-royal-mail-proxy`), Sapient mock; 133 tests | #1 | done |
| UPS mock | `apps/ups-proxy` (source ADO `GFS_UPS_Integration`), stepping-stone XML and V2 JSON, UPS mock; 83 tests | #1 | done |
| Coll8 mock | `apps/coll8-proxy` (source ADO `GFS_Coll8_Integration`), Coll8 mock; 103 tests | #1 | done |
| IaC and CI | `iac/projects/mock-{upstreams,royalmail,ups,coll8}` (Cloud Run `mock-*-cp-dev`, state `carrier-playground/mock-*`), dockerfiles on the golden `node24-runtime`, `@ilg-platform/observability` and dd-trace, `ci.yaml`, `tf-plan-pr.yaml`, `deploy-dev.yaml`, `scripts/smoke.mts` | #1 | done; CI and plans were pending at handover |

Verified on the laptop: lint, typecheck and 374 tests pass. All four images built. `pnpm smoke` passed
against them in Docker, and the logs held no labels, keys or tokens. A local plan of mock-upstreams
against a scratch backend showed 2 to add (the service and its service account).

## In flight
| Work | PR / branch | State | To close it |
| --- | --- | --- | --- |
| PR #1 CI (`ci`: lint, typecheck, test) | #1 / `hjf/mock-carrier-proxies` | pending at 16:10Z | `gh pr checks 1 --repo ilg-merak/carrier-playground`. If it fails, fix on the branch, push, and re-check. Likely causes: the `GH_TOKEN` secret for `@ilg-platform/*` installs, and pnpm `onlyBuiltDependencies`. |
| PR #1 Terraform plans (`tf-plan-pr.yaml`) | #1 | pending | Read the plan comments. Expect mock-upstreams 2 to add. **The three proxy plans will fail** until mock-upstreams exists, because each reads `mock-upstreams-cp-dev` through a data source. That's expected; don't "fix" it by removing the data source. Summarise the plans for Harry. |
| `_preflight` secrets | #1 | unknown | `deploy-dev.yaml` needs ilg-merak org secrets `DATADOG_API_KEY`, `DATADOG_API_KEY_ILG`, `PLATFORM_CI_APP_PRIVATE_KEY`, `SLACK_WEBHOOK_URL` and `GH_TOKEN`, plus var `PLATFORM_CI_APP_ID`. Parcel Portal uses the same ones at org level. Report any that are missing; don't create secrets. |

## Waiting on Harry
- **Merge PR #1 (deploys to dev).** Plan-then-proceed: share the plan output first. Merging is Harry's call, after he has seen the plans. Recommendation: the first deploy is `gh workflow run deploy-dev.yaml --ref hjf/mock-carrier-proxies` (dev only, all mock), then re-run the PR plans so the proxies plan cleanly, then merge.
- **Add Amazon and DPD Europe as proxies 4 and 5?** Asked, not answered. Recommendation: yes.
  - **Amazon:** two consumers (Selector labels, and ECM tracking through the internal copy); prod runs the Azure DevOps copy, which isn't cloned yet; the GitHub `amazon-proxy` has no prod traffic; its tracking route takes the company from the URL.
  - **DPD Europe:** `ado/dpd-europe-proxy`; all prod calls fail validation; credentials are KMS-encrypted in MongoDB.
  - **DHL:** has no proxy, because Selector calls DHL directly. A DHL mock (for `DHL_URL`) is a follow-up.
- **Tech Services repos:** leave them alone (Harry, 5 Nov). Don't PR the knowledge vault.

## Next up
1. Get PR #1 green, and report the plans (In flight).
2. Only if Harry says yes: Amazon and DPD Europe mocks, on the same pattern. Briefs as in this session: AGENTS.md rules, one builder per proxy, each owning `apps/<proxy>/**`, `apps/mock-upstreams/src/<carrier>/**` and `fixtures/apiky/<carrier>.json`. Add a Terraform project `iac/projects/mock-<carrier>` copied from `mock-coll8`, plus the deploy and plan matrix rows.

## How work is done here
- Repo rules: `AGENTS.md`: same contract, lookups and logic; every upstream mocked; all data fake; never log bodies, labels, keys or credentials. Per-proxy details are in `apps/*/README.md`.
- Infra pattern copied from `ilg-merak/parcel-portal` (`iac/projects/gateway`, workflows). Names must stay `mock-*`, with state under `carrier-playground/mock-*` (Harry's rule).
- **Terraform plan-then-proceed:** no apply, merge or deploy-approval until Harry has seen the plan.
- Out-of-ticket work: the branch is `hjf/<desc>`, with no ticket keys. Ledger: `wp ledger carrier-playground` (an entry exists for PR #1).
- **Commit hook:** `~/.claude/hooks/comment-density.sh` blocks multi-line comment blocks. Comments are one line of non-obvious why, or none.
- Installs need a GitHub Packages token: `env "npm_config_//npm.pkg.github.com/:_authToken=$(gh auth token)" pnpm install` (zsh can't `export` that name).

## On the target
Checked 16:10Z:
- **Has:** claude 2.1.318, gh (harry-fitzgerald_gfsdev), gcloud (harry.fitzgerald@gfsdeliver.com), docker, mise, node, jq. Auto mode is on, and `~/.claude/.credentials.json` exists.
- **Missing:** pnpm and terraform, which `mise install` in the repo provides.
- **Repo:** cloned to `~/code/merak/carrier-playground` during the handover.

## Gotchas
- zsh reads `$a:local` as a modifier: write `${a}` in tags.
- The SDK logger is a class: mock-kit binds its methods, because the UPS proxy passes `logger.warn` around unbound.
- Under ESM, dd-trace must be preloaded with `--import ./apps/<app>/node_modules/dd-trace/initialize.mjs`. The dockerfiles do this; the bare specifier doesn't resolve from `/app`.
- Your account can't write the dev state bucket, which is correct. For a local plan, use a scratch copy with a local backend.
- Mock-upstreams can scale past one instance. The mocks are stateless, except Royal Mail's manifest totals and `/__calls`.

## Closed since handover
| When (UTC) | Work | Result |
| --- | --- | --- |
