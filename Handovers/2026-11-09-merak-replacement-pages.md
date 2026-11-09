---
tags: [handover]
status: open
workstream: ECM and Selector research, now feeding Merak (a new despatch and shipping platform that replaces both). Finish and publish two MPK design pages
programme: none
repo: none (vault + Confluence MPK; read-only GitHub and Azure DevOps)
from: rc-hjf
to: next session, any machine
session_id: 9ef32451-f6a6-429e-88df-add8e5d83ddf
resumed_by: ""
updated: 2026-11-09T11:58Z
---
# Handover: Merak replacement pages (continues the carrier-integrations research)

Continues [[Handovers/2026-11-06-carrier-integrations]], which is closed. Read that record for the earlier waiting items.

## Where things stand
The ECM and Selector research is finished, checked claim by claim on 2026-11-09, and published to MPK and the vault. Harry now frames Merak as a new despatch and shipping platform that replaces ECM and Selector. **The Parcel Portal is not part of that.** Two design pages for MPK "1. Architecture & Design" (page 351502339) are drafted but **unverified and unpublished**. The verification run was killed at the session limit and returned nothing. Harry has not yet seen the full text.

| Unit | What it delivered | Where | State |
| --- | --- | --- | --- |
| Journey page | One shipment from label to POD, what changes it later, status codes, volumes | MPK 354975746, v2 | Live. 36 claims checked: 19 held, 17 partly right, none refuted |
| POD page | `gfs-pod-service`; GFS address only on v2, v1 keeps the carrier's | MPK 353861642, v3 | Live |
| Ingress and Egress pages | Names from GFS's side: ingress = carrier to GFS, egress = GFS to carrier | MPK 353206337 v5, 353697822 v6, 353468499 v5, 353206310 v6 | Live |
| Explainers | Journey and diagnosis, rewritten with the checked facts | `Explainers/2026-11-06-life-of-a-shipment-through-ecm.md`, `...-ecm-event-world-where-its-a-mess.md` | Done, lint clean |
| POD docs and idea | Address and cache correction. POD-at-ingress idea as a draft plan | `Engineering/gfs-pod-service/` (`ideas-log.md`, `plans/`) | Done. The open plan makes `wp doctor` stricter for this service |
| Draft page 1 | **Selector and ECM Coupling**: six seams, what breaks if either goes first, duties nobody wrote down, three cut points | `Handovers/2026-11-09-merak-replacement-pages.page1-selector-ecm-coupling.md` | Drafted, lint passes, unverified |
| Draft page 2 | **Tracking Events and Webhooks: What v1 Needs**: ten requirements from ECM's failures | `Handovers/2026-11-09-merak-replacement-pages.page2-tracking-events-webhooks.md` | Drafted, lint passes, unverified |
| Page 3 | Dropped. It existed only to answer a Parcel Portal gate | n/a | Hidden duties moved into page 1 |

## In flight
None of this session's workflows or agents is running (checked 2026-11-09 11:53Z). The sessions `ListAgents` shows are Harry's other sessions: leave them alone.

| Work | Where | State | To close it |
| --- | --- | --- | --- |
| Verify drafts 1 and 2 | `Handovers/2026-11-09-merak-replacement-pages.verify-workflow.js.txt` | Killed, no results | Copy it to a `.js` file and run `Workflow({scriptPath})`. It uses two Sonnet-high verifiers per page, an Opus-high judge and a cross-page critic. Its CONTEXT names scratchpad clone paths that no longer exist, so tell agents to clone fresh. Apply the corrections to the two draft files |
| Fix lint warnings | Draft 1 (4 long sentences), draft 2 (1) | Open | `python3 ~/.claude/skills/plainly/lint.py <file>` |
| Show Harry the full text, then publish on his word | MPK, space id 338526210, parent 351502339 | Not started | `mcp__Atlassian__createConfluencePage` in markdown, then link both pages from "1. Architecture & Design" and from [Carrier Services](https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/353468499/Carrier+Services) |

## Waiting on Harry
- **Review the two drafts before anything is published.** Recommendation: verify, fix, show the text, then publish both under "1. Architecture & Design".
- **Keep or drop one link.** Page 2 links Jack's "Idea: Developer promise" page in one line. Recommendation: keep it. Harry said the Parcel Portal was irrelevant, not the MPK product pages.
- **Which further pages he wants.** Proposed, not approved: the carrier layer for Merak's five carriers; proof of delivery for UPS and FedEx; exceptions, queries and claims today; identity and tenancy lessons from ECM. Check each is relevant first. Two earlier proposals were anchored on Parcel Portal gates (MKP-9, MKP-32) and are dropped.
  - **POD facts in hand:** the UK UPS module asks for the signature image and delivery photo, and the FedEx module fetches the signature PNG. Each uses one GFS credential. The FedEx module never reads a GPS point and had no requests in 15 days.
- **Security ticket draft** (offered on 2026-11-06, never raised; draft it for Harry, don't raise it). Class-level items reported by the research agents, not re-checked by me:
  - a committed credentials file in `patina-service-2`'s rollback tool;
  - plaintext secrets in prod and dev manifests, and in the GFS Hub config;
  - TLS verification off on two deployments;
  - carrier credentials in cleartext on Pub/Sub, and a Datadog key in a push URL and Terraform state;
  - committed Terraform state in `gfs-pipelines`;
  - two identities with project-wide Pub/Sub editor, one unclaimed (`tracking-dump@`);
  - personal Gmail addresses with `pubsub.admin` on `gfs-ecm` (SRE-305 is revoking them).
- **DHL Parcel UK (CID-317, Blocked).** DHL rejects about 15 contracts with error 3002. About 850 parcels are re-polled about 70 times a day, and tracking-core never pauses them. Recommendation: nudge the assignee. Nothing was sent.
- **Carry-over from the 11-06 record:** whiteboards need a Confluence API token; the orient plan sign-off; the Datadog MCP endpoint (`/v1/mcp`); R5, Fuse billing.

### Answers owed by others
| Question | Who or what settles it |
| --- | --- |
| The production Firebird triggers on `SHIPMENTS` and `SHIP_PIECES` | A DBA, one read-only query on central `SRV_GFS.fdb` (`RDB$TRIGGERS`) |
| Which carriers `patina-service-2` writes back, and which carriers hold the 1,309 bill-on-scan contracts | Library read on ADO variable group 141 (`gfs-patina-service.prod`); a Billing team query on `CUST_CONTRACTS` |
| Whether any n8n workflow calls a carrier API | A read-scoped n8n API key, or the Oz owners |
| Evri cutover (CID-315): mapping coverage for carrier 16, and the ParcelShop population | The CID-315 assignee |
| Live GCP state: cross-project grants, `raw_tracking.warehouse.v1`, `tracking-dump@` | SRE |
| Whether Client4's SOAP upload carries a file or shipment records | The laptop clone `~/code/selector` (`uSoapUpload.pas`, mode 0) |
| Which host runs the Scan Injector (`MEDC-APP-01-P` in Datadog, `MEDC-APP-12-P` per SRE-126), and the deployed delivered code (default 1003) | SRE; the legacy shipment update service owner |

## Next up
1. Finish pages 1 and 2: verify, fix, lint, show Harry the text, publish on his word.
2. Ask Harry which further pages he wants (see Waiting).

## How work is done here
- **Confluence pages:** use the `plainly` skill. British English, no em dashes, sentences of 25 words or fewer, tables for state, security findings at class level only. Publish only when asked.
- **Merak is unannounced.** Keep content in MPK, with no Slack. Don't anchor Merak pages on the Parcel Portal or its MKP gates (memory `merak-parcel-portal-irrelevant`).
- **Confluence mechanics:** `getConfluencePage` in markdown, `updateConfluencePage` with a `versionMessage`. Confluence stores links by title, so swapping two linked titles needs a temporary one. MCP search results can be huge: they save to a file, so use `jq`.
- **Verification pattern:** Sonnet-high verifiers with a source lens and a runtime lens, an Opus-high judge, an Opus critic. Derived notes, explainers and the pages under test are not evidence.
- **Explainers:** `node ~/.claude/skills/explain/lint-explainer.mjs <file> --mode event|overview|architecture`, then `python3 ~/.claude/waypoint/wp.py index`.
- **Read-only everywhere:** no Jira, Slack or GCP writes, and no edits to Tech Services repos.
- **Log:** this session's id is in `Tasks/2026-11-06-pod-carrier-table.md`. Update it in place.
- **Memories that apply:** `merak-context`, `merak-parcel-portal-irrelevant`, `firebird-ddl-dump`, `reference-ado-orgs`.

## On the target
Checked on rc-hjf, 2026-11-09:
- **Has:** `gh` as `harry-fitzgerald_gfsdev`; `gcloud` as `harry.fitzgerald@gfsdeliver.com`, with no Pub/Sub access to `gfs-ecm-*`; the Atlassian MCP signed in; the Datadog MCP (deprecated endpoint, still works); `ado-local-mcp` reading `globalfreightsolutions` through `repo_file`.
- **Lacks:** `git clone` from Azure DevOps (denied; `repo_file` rejects short shas); the laptop-only clones `~/code/apiky-survey/*` and `~/code/selector/*`; the legacy org `globalfreightsolutons-legacy`. Central Firebird procedure source is readable in `gfs-data-services/gfs-pipelines` (a December 2025 dump).
- **Gone with the session:** every clone and note under `/tmp/claude-2001/.../scratchpad`. The checked facts live in the two explainers and the MPK pages.

## Gotchas
- **Datadog logs keep about 15 days.** Use metrics for longer windows. `gcp.pubsub.*` isn't collected for ECM prod.
- **ADO `search_code` lags HEAD.** Confirm hits with `repo_file`.
- **`carrier.id` is the legacy name and `carrier.idV2` the numeric string.** ECM's catalogue has them swapped.
- **POD "GPS" is GFS's geocoded address.** The v1 API keeps the carrier's address, and v1 and v2 share a cache key.
- **"Delivered" has at least six definitions.** Status 1003 reads as lost in legacy UPS reporting.
- **The Scan Injector runs 06:00 to 23:01 UK time,** not UTC.
- **zsh treats `echo ===` as an error.** Use `printf`.
- **`TaskStop` on an already-killed workflow errors harmlessly.**

## Closed since handover
| When (UTC) | Work | Result |
| --- | --- | --- |
