---
tags: [handover]
status: closed            # superseded by [[Handovers/2026-11-11-carrier-playground]] (rc-hjf → laptop, 11 Nov)
workstream: Twelve mock carrier proxies with dev IaC and DNS in ilg-merak/carrier-playground
programme: none
repo: ilg-merak/carrier-playground
from: laptop
to: hjf.shell.platform.ilg.software
session_id: 945d0e77-3787-450a-a8e6-3635e238a5c9
resumed_by: 9d74d588-1876-4a16-907d-7470c90d25d5
updated: 2026-11-11T09:40Z
---
# Handover: mock carrier proxies (carrier-playground)

## Where things stand
`main` is deployed to ilg-merak dev (SHIP-1106-carrier-playground). Twelve mocks are live at
`https://{royalmail,ups,coll8,fedex,dpdeu,amazon-sfp,amazon,bjs,inpost,ocs,exelot,veho}.mocks.merak.freightops.dev` (one HTTPS LB,
`iac/projects/mock-edge`; records in core-infra's dev zone). All on the golden node24-runtime, GFS Datadog only. Smoke 42/42 through
the names (`scripts/smoke.mts`, now type-checked in CI); Datadog shows no keys, tokens or addresses.

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
| #9 | BJS (ADO `bjs-proxy`) | merged, deployed |
| #10 | InPost (GitHub `inpost-proxy`) | merged, deployed |
| #11 | OCS (ADO `ocs-proxy`) | merged, deployed |
| #12 | Exelot (ADO `GFS Exelot Integration`); metaData spread fixed in BJS/FedEx | merged, deployed |
| #13 | Restore smoke `isPng`; type-check `scripts/` in CI | merged |
| #14 | Veho, built from the agreed contract (no prod proxy yet; epic CID-335) | merged `d98fd9b`, deployed |

## In flight
None.

## Waiting on Harry
- None blocking. Tech Services repos: leave them alone (Harry, 5 Nov).

## Next up
1. Optional: a DHL mock behind Selector's `DHL_URL` (no proxy exists).
2. Optional: fix the platform `networking/load-balancer` module (removed services are deleted before being detached) — ilg-platform/terraform-modules.
3. Optional mock cleanups (PR Notes): shared PNG encoder (coll8/fedex/amazon/dpd/inpost import across carriers) into mock-kit; UPS `RequestId undefined`; `env:serverless` on dd-trace; no max-instance cap.
4. Prod findings the mocks surfaced (code-read, not confirmed against prod logs) — see each PR's "mirrored on purpose" section. Highest-impact: **InPost prod logs full payloads (LOG_CARRIER_PAYLOAD=true, marked TEMPORARY), callers' ApiKy keys, and its InPost Basic Authorization header** (#10); Exelot/OCS log whole axios errors incl. carrier tokens (#11/#12); Exelot always calls the real ApiKy whatever its env says (#12); DPD Europe validation rejects every Selector call (#4); Amazon Logistics refuses PDF labels (#8); GRAM weights ×1000 in OCS/Exelot.

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
- Merging parallel mock branches: git interleaves smoke.mts sections that share lines; rebuild smoke.mts from main and add the new section rather than trusting a textual merge. `pnpm typecheck` now catches a broken smoke script.
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
| 2026-11-09 11:05 | Veho (#14) | Built from the contract/spec/tickets (CID-335) + Veho docs; 2 reviews, 3 blockers fixed (idempotency x2, real Veho tracking host); smoke 42/42 across twelve names. Builder made one read-only call to Veho's public unauthenticated sandbox ZIP endpoint (noted in the PR). |
| 2026-11-06 18:20 | BJS, InPost, OCS, Exelot (#9–#13) | Sources confirmed against prod ingress/DNS; 4 builders, 8 reviews (3 blockers fixed: OCS log test gap, metaData shape in OCS/Exelot + BJS/FedEx); a merge-resolver bug fused two smoke rows and dropped a helper, both fixed and scripts/ now type-checked. Smoke 33/33 across eleven names. |
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
