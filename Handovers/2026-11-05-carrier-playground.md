---
tags: [handover]
status: resumed
workstream: Mock carrier proxies (Royal Mail, UPS, Coll8, FedEx, DPD Europe, Amazon SFP, Amazon Logistics) with dev IaC and DNS in ilg-merak/carrier-playground
programme: none
repo: ilg-merak/carrier-playground
from: laptop
to: hjf.shell.platform.ilg.software
session_id: 945d0e77-3787-450a-a8e6-3635e238a5c9
resumed_by: 9d74d588-1876-4a16-907d-7470c90d25d5
updated: 2026-11-06T15:24Z
---
# Handover: mock carrier proxies (carrier-playground)

## Where things stand
`main` is deployed to ilg-merak dev (SHIP-1106-carrier-playground). Seven mocks are live at
`https://{royalmail,ups,coll8,fedex,dpdeu,amazon-sfp,amazon}.mocks.merak.freightops.dev` (one HTTPS LB, `iac/projects/mock-edge`, which maps
Cloud Run key -> host label). All ship logs to GFS Datadog only (ILG dropped, #6). `amazon` is the Amazon Logistics mock (#8, ADO
`gfs-amazon-logistics-proxy`). Smoke 19/19.

| PR | What | State |
| --- | --- | --- |
| #1 | Royal Mail, UPS, Coll8 + mock-upstreams + dev IaC/CI | merged, deployed |
| #2 | `<carrier>.mocks.merak.freightops.dev` edge LB + DNS | merged, deployed |
| #3 | FedEx (GitHub `fedex-proxy`) | merged, deployed |
| #4 | DPD Europe (ADO `dpd-europe-proxy`) | merged, deployed |
| #5 | Amazon mock from GitHub `amazon-proxy` | merged; repositioned by #6 |
| #6 | That mock is the SFP proxy -> `apps/amazon-sfp-proxy`, `mock-amazonsfp`, `amazon-sfp` name; GFS Datadog only | merged, deployed (edge step failed, fixed by #7) |
| #7 | Keep `amazon` on the edge, drop the mock-amazon teardown | merged, deployed |
| #8 | Amazon Logistics (ADO `gfs-amazon-logistics-proxy`) into `mock-amazon` | merged `23a822f`, deployed |

## In flight
Four more mocks, approved by Harry 6 Nov ("BJS down to OCS"). Sources confirmed against the prod cluster ingresses and DNS. Shared builder brief: scratchpad `brief-common.md` (not synced; the rules mirror the FedEx/DPD pattern).

| Mock | Source (prod) | Port / name | State |
| --- | --- | --- | --- |
| BJS | ADO `GFS Hybrid Services and Carrier Integrations/bjs-proxy` (GKE, `bjs.gfsdeliver.com`; GitHub `bjs-proxy` is an unused newer copy) | 4108 / `bjs` | builder running, worktree `mock-bjs` |
| InPost | GitHub `gfs-hybrid-services/inpost-proxy` (Cloud Run, `inpost.gfsdeliver.com`) | 4109 / `inpost` | builder running, worktree `mock-inpost` |
| Exelot | ADO `GFS Exelot Integration/GFS Exelot Integration` (GKE, `exelot.gfsdeliver.com`) | 4110 / `exelot` | queued |
| OCS | ADO `GFS Hybrid Services and Carrier Integrations/ocs-proxy` (GKE, `ocs.gfsdeliver.com`) | 4111 / `ocs` | queued |

Each: 2-dim review, merge main, PR, merge, deploy (edge adds only), smoke through the name, Datadog check, ledger.

## Waiting on Harry
- None blocking. Tech Services repos: leave them alone (Harry, 5 Nov).

## Next up
1. Optional: fix the platform `networking/load-balancer` module so a removed service is detached before deletion (URL map needs a real dependency on the backends) — ilg-platform/terraform-modules, not this repo.
2. Optional follow-ups from the self-reviews (each PR's Notes): shared PNG encoder (coll8/fedex/amazon) into mock-kit; UPS body-parse errors log `RequestId undefined`; no max-instance cap (module lacks the input); `env:serverless` on dd-trace.
3. Likely prod bugs the mocks surfaced (unconfirmed against prod logs): DPD Europe validation (phone `+`, nulls, KG/CM, float weights; #4); Amazon Logistics `notes` -> 200 `{}`, PDF refused, `-SIG` refused (#8).

## How work is done here
- **Harry, 6 Nov:** be pragmatic, only ask if something breaks; otherwise full steam ahead (memory `feedback-ship-pragmatic`).
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
- **Never remove a name from `mock-edge`.** The platform `networking/load-balancer` module (0.1-affogato) deletes a removed service's backend and cert before detaching them from the URL map/HTTPS proxy; GCP refuses (`resourceInUseByAnotherResource`) and every retry fails identically. Add/update only, or fix the module first (URL map needs a real dependency on the backends).
- A monitor or background watch on a deploy must stop on the first failed job, not wait for a downstream signal (cost 45 min on #6).
- Plain `pnpm install` can drop `optional: true` markers from the lockfile; follow with `pnpm install --lockfile-only --fix-lockfile`.
- CI installs: use setup-node `registry-url`/`scope` + `NODE_AUTH_TOKEN`; the `npm_config_//…:_authToken` env var isn't picked up by pnpm on the runner. (The dockerfiles still use the env-var form; it works in the Docker build, unverified in `deploy-dev`.)
- A pushed commit can fail to sync to the PR (no push event, no checks). A fresh push (empty commit) fixes it.
- zsh reads `$a:local` as a modifier: write `${a}` in tags.
- The SDK logger is a class: mock-kit binds its methods, because the UPS proxy passes `logger.warn` around unbound.
- Under ESM, dd-trace must be preloaded with `--import ./apps/<app>/node_modules/dd-trace/initialize.mjs`. The dockerfiles do this; the bare specifier doesn't resolve from `/app`.
- Your account can't write the dev state bucket, which is correct. For a local plan, use a scratch copy with a local backend.
- Mock-upstreams can scale past one instance. The mocks are stateless, except Royal Mail's manifest totals and `/__calls`.

## Closed since handover
| When (UTC) | Work | Result |
| --- | --- | --- |
| 2026-11-06 15:45 | Amazon Logistics mock (#8) | From ADO `gfs-amazon-logistics-proxy` (access granted by Harry); 2-dim review, no blockers, 3 fixes; deployed into `mock-amazon`; smoke 19/19 across seven names; Datadog clean. |
| 2026-11-06 14:40 | #6 + #7 | Amazon mock repositioned as SFP; GFS Datadog only; edge removal bug hit and worked around by keeping `amazon`. Smoke 16/16. |
| 2026-11-06 12:55 | Amazon Logistics mock (PR #5) | Prod located via the k8s config (`amazon-logistics-proxy`, image from ADO project `GFS Amazon Logistics Integration`, unreadable here). Built from the GitHub modernised copy; 2-dim review, no blockers, flag/cap/doc fixes. Deployed `5737fee`; cert served; smoke 16/16. |
| 2026-11-06 12:40 | DPD Europe mock (PR #4) | From ADO `dpd-europe-proxy` via `ado-local-mcp` (Harry fixed the MCP). Review blocker (lockfile metadata) fixed plus 3 more. Deployed `8eb6850`; cert ~5 min. Likely cause of prod's validation failures documented in the PR. |
| 2026-11-06 11:25 | core-infra#18 (merak namespace comment) | Merged; dev 0/0/0; prod gate approved by Harry; prod 0/0/0. |
| 2026-11-06 11:02 | FedEx mock (PR #3) | Built by a subagent from `gfs-hybrid-services/fedex-proxy` (prod, GCP); 2-dim self-review, no blockers, 3 small fixes. Deployed `fee2c49`; `fedex.mocks.merak.freightops.dev` cert ACTIVE in ~6 min; smoke 10/10 through all names. CT-log scanners hit new public names within minutes (400s, harmless). |
| 2026-11-06 10:40 | DNS (PR #2) | `iac/projects/mock-edge`: one global HTTPS LB (platform `networking/load-balancer`), cert per name, A records in `core-infra-dev-zone` (ilg-merak dev SA already has project-scoped dnsRecordWriter). 19 added; certs ACTIVE in ~8 min. |
| 2026-11-06 10:10 | SHIP-1106: PR #1 merged and deployed | Self-review (4 dims + delta) found one blocker, a UPS-mock process crash on non-WinAnsi label text, fixed with the other findings in `8b2e683`. `deploy-dev` can't be dispatched before the workflow is on `main`, so the merge was the first deploy (approved). Applied 2+4+4+4, 0 destroyed. Smoke, liveness, private upstreams (403), Łódź label 201, Datadog with no keys or bodies: [evidence comment](https://github.com/ilg-merak/carrier-playground/pull/1#issuecomment-6682328667). Ledger entry written. |
| 2026-11-05 16:28 | `_preflight` secrets | All present at ilg-merak org level and visible to the repo: `DATADOG_API_KEY`, `DATADOG_API_KEY_ILG`, `PLATFORM_CI_APP_PRIVATE_KEY`, `SLACK_WEBHOOK_URL`, `GH_TOKEN` (plus `DATADOG_APP_KEY`), and var `PLATFORM_CI_APP_ID`. Nothing missing; nothing created. |
| 2026-11-05 16:28 | PR #1 Terraform plans | Run 42064459100 (same as 16:10 run). mock-upstreams: **2 to add** (`google_cloud_run_v2_service` `mock-upstreams-cp-dev`, `google_service_account` `mock-upstreams-cp-dev-cloudrun`), us-central1, project `ilg-merak-dev-b5e3`, ingress all, min 0 instances. mock-royalmail / mock-ups / mock-coll8: **fail as expected** on `data.google_cloud_run_v2_service.upstreams` (`mock-upstreams-cp-dev not found`); each got as far as 1 to add (its service account) first. IaC unchanged. |
| 2026-11-05 16:27 | PR #1 `ci` | Green at `d6c8fc2` (run 42064458271). It failed at 16:10 with a 401 from GitHub Packages: pnpm sent no auth header from the `npm_config_//npm.pkg.github.com/:_authToken` env var in CI (it does locally). Fixed in `69bbe0c` by switching to setup-node `registry-url` + `scope` with `NODE_AUTH_TOKEN`, as parcel-portal's node-run does. GitHub dropped that push's PR sync; empty commit `d6c8fc2` re-triggered it. |
