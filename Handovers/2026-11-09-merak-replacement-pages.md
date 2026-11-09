---
tags: [handover]
status: resumed
workstream: ECM and Selector research, now feeding Merak (Harry frames it as a new despatch and shipping platform that replaces both). Finish and publish two MPK design pages
programme: none
repo: none (vault + Confluence MPK; read-only GitHub and Azure DevOps)
from: rc-hjf
to: next session, any machine
session_id: 9ef32451-f6a6-429e-88df-add8e5d83ddf
resumed_by: ""
updated: 2026-11-09T12:01Z
---
# Handover: Merak replacement pages (continues the carrier-integrations research)

Continues [[Handovers/2026-11-06-carrier-integrations]], which is closed. Read that record for the earlier waiting items.

## Where things stand
The ECM and Selector research is published to MPK and the vault. On 2026-11-09 a 31-agent review checked 36 claims on the first journey page: 19 confirmed, 17 partly right, none refuted. All 17 were corrected. Harry now frames Merak as a new despatch and shipping platform that replaces ECM and Selector. **The Parcel Portal is not part of that.**

Two design pages for MPK "1. Architecture & Design" (page 351502339) are drafted but **unverified and unpublished**. The verification run was killed at the session limit and returned nothing. Harry has not yet seen the full text.

| Unit | What it delivered | Where | State |
| --- | --- | --- | --- |
| Journey page | One shipment from label to POD: what changes it, status codes, volumes | MPK "Shipment Journey Through ECM" 354975746, v2 | Live, corrected after the review |
| POD page | `gfs-pod-service`: GFS address on v2 only, v1 keeps the carrier's | MPK "Proof of Delivery Service" 353861642, v3 | Live |
| Ingress and Egress pages | Names from GFS's side: ingress = carrier to GFS, egress = GFS to carrier | MPK Carrier Ingress Services 353206337 (v5), Carrier Egress Services 353697822 (v6), Carrier Services 353468499 (v5), Carrier Integration Uses 353206310 (v6) | Live |
| Explainers | Journey and diagnosis, rewritten with the checked facts | `Explainers/2026-11-06-life-of-a-shipment-through-ecm.md`, `Explainers/2026-11-06-ecm-event-world-where-its-a-mess.md` | Done, lint clean |
| POD docs and idea | Address and cache correction. POD-at-ingress idea kept as a draft plan | `Engineering/gfs-pod-service/` (`ideas-log.md`, `plans/`) | Done. The plan stub counts as open for `wp doctor`. To drop it: `wp plan set-status gfs-pod-service --plan capture-pods-at-ingress-and-serve-them-from-a-st --status abandoned` |
| Draft page 1 | **Selector and ECM Coupling**: six seams, what breaks if either goes first, duties nobody wrote down, three cut points | `Handovers/2026-11-09-merak-replacement-pages.page1-selector-ecm-coupling.md` | Drafted, unverified. No lint errors, 4 long-sentence warnings open |
| Draft page 2 | **Tracking Events and Webhooks: What v1 Needs**: ten requirements from ECM's failures | `Handovers/2026-11-09-merak-replacement-pages.page2-tracking-events-webhooks.md` | Drafted, unverified. No lint errors, 1 long-sentence warning open |
| Page 3 | Dropped. It only answered MKP-9, a Parcel Portal gate | n/a | Hidden duties moved into page 1 |

## In flight
None of this session's workflows or agents is running (checked 2026-11-09 11:53Z). The sessions `ListAgents` shows are Harry's other sessions: leave them alone.

| Work | Where | State | To close it |
| --- | --- | --- | --- |
| Verify drafts 1 and 2 | `Handovers/2026-11-09-merak-replacement-pages.verify-workflow.js.txt` | Killed, no results | Needs Harry's go-ahead for multi-agent work. Copy the script to a `.js` file and run it with `Workflow({scriptPath})`. It uses two Sonnet-high verifiers per page (source and runtime lenses), an Opus-high judge and a cross-page critic. Its CONTEXT points at this session's scratchpad (clones, `review-result.json`), which a new session won't have. Apply the corrections to the two draft files |
| Fix lint warnings | Draft 1 (4 long sentences), draft 2 (1) | Open | `python3 ~/.claude/skills/plainly/lint.py <file>` |
| Show Harry the full text, then publish on his word | MPK, space id 338526210, parent 351502339 | Not started | `mcp__Atlassian__createConfluencePage` in markdown, then link both pages from "1. Architecture & Design" and from [Carrier Services](https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/353468499/Carrier+Services) |

## Waiting on Harry
- **Review the two drafts before anything is published.** Recommendation: verify, fix, show the text, then publish both under "1. Architecture & Design".
- **Confirm that Merak replaces both ECM and Selector.** That is Harry's framing. MPK names "Selector v2 and labelling" as big builds but has no Selector v2 design page and no mention of ECM being replaced. Those were phrase searches, not a full read. Check with Jack and Stef before the pages assume it.
- **Keep or drop one link.** Page 2 links the "Idea: Developer promise" page (349110455) in its opening paragraph. Recommendation: keep it. That page asks for the same v1 webhook features, and the decisions on it stay with Stef.
- **Which further pages he wants.** Four more were proposed on 2026-11-09 and none is approved. Check each against Merak before writing it. The first table below gives the decision each was meant to feed.
- **Security ticket draft.** Offered on 2026-11-06 and not yet written up. Draft it for Harry, at class level only, and do not raise it. These items come from the research agents and I have not re-checked them:
  - a committed credentials file in `patina-service-2`'s rollback tool;
  - plaintext secrets in several prod and dev manifests;
  - TLS verification off on the Shipment Update Service API and collections-service;
  - carrier credentials in cleartext on Pub/Sub feeds;
  - a Datadog key in a push URL and in Terraform state;
  - committed Terraform state in `gfs-pipelines`;
  - project-wide Pub/Sub editor for two identities, one unclaimed (`tracking-dump@`);
  - a personal Gmail address with `pubsub.admin` on `gfs-ecm`, being revoked under SRE-305.
- **DHL Parcel UK (CID-317, blocked).** DHL rejects about 15 accounts with error 3002, and one contract causes 92% of the errors. CID-317 already tracks it, and its monitor only emails individuals. The hand-off to the carriers team is owed from the 11-06 record. Nothing was sent.
- **Carry-over from the 11-06 record.** Whiteboards need a Confluence API token. The orient plan sign-off is `wp plan set-status orient --plan mcp-system-lens-and-correct-service-metadata --status complete`. The Datadog MCP should move to `/v1/mcp`. R5 (Fuse billing) is open.

### Further pages proposed
| Page | Merak decision it was meant to feed | State |
| --- | --- | --- |
| Carrier layer for the five carriers | Which carriers Merak can lean on | Evidence in hand, plus the CID Jira project |
| Proof of delivery for UPS and FedEx | The account-holder row on passing POD through | UK code read; carrier terms need outside research. Check the hook is not Parcel Portal only |
| Exceptions, queries and claims today | The Exceptions and Claims portals; the AI query-automation brainstorm | Evidence in hand |
| Identity and tenancy lessons from ECM | MKP-32 (shipper or warehouse operator as tenant) | MKP-32 is a Parcel Portal gate, so re-anchor on Merak or drop. Evidence: ECM keys tenancy on the company name, which is write-once, so a rename orphans data across about twelve services |

In my 2026-11-09 view, two things are not worth writing. More per-service ECM pages are reference only and feed no decision. The keep, replace or drop list for Selector v2 is a product call for Jack and Stef.

### Answers owed by others
| Question | Who or what settles it |
| --- | --- |
| The production Firebird triggers and procedures on `SHIPMENTS` and `SHIP_PIECES` | One read-only query on central Firebird by a DBA: `SELECT RDB$TRIGGER_NAME, RDB$TRIGGER_INACTIVE, RDB$TRIGGER_SOURCE FROM RDB$TRIGGERS WHERE RDB$RELATION_NAME IN ('SHIPMENTS','SHIP_PIECES')` |
| Which carriers `patina-service-2` writes back, and which carriers hold the 1,309 `BILL_ON_SCAN=1` contracts | The carrier list is ADO variable group `gfs-patina-service.prod` (Library id 141), which the ADO MCP can't read. The contracts need one Billing query |
| Whether any n8n workflow calls a carrier API | A read-scoped n8n API key, or the Oz owners |
| Evri code-mapping coverage before the CID-315 cutover | The tracking config (TCDS bucket or mapper Mongo), via the CID-315 assignee |
| Live GCP state: cross-project grants, the warehouse subscription, `tracking-dump@` | SRE |
| Whether Client4's SOAP upload carries a file or shipment records | A look at the laptop clone `~/code/selector`: `uSoapUpload.pas` (upload mode 0) and the upload server's `UploadShips` |
| Which host runs the Scan Injector | Unresolved. Datadog logs show `MEDC-APP-01-P`. SRE-126 confirmed the service on `MEDC-APP-12-P` over WinRM |
| What the deployed mark-as-delivered code writes | Not observed. The default of 1003 is read from code, and legacy UPS loss reporting reads 1003 as lost. Nobody owns the write-back |
| "142M carrier calls" on the Polling Connectors and Ingress pages, against the 115M parcel polls the review measured | Nobody has reconciled them. They may be different measures |

## Next up
1. Finish pages 1 and 2: verify, fix, lint, show Harry the text, publish on his word.
2. Ask Harry which further pages he wants (see Waiting).

## How work is done here
- **Confluence pages:** use the `plainly` skill. British English, no em dashes, sentences of 25 words or fewer, tables for state, security findings at class level only. Publish only when asked.
- **Merak is unannounced.** Keep content in MPK, with no Slack. Don't anchor Merak pages on the Parcel Portal or its MKP gates (memory `feedback_merak_parcel_portal_irrelevant`).
- **Confluence mechanics:** `getConfluencePage` returns markdown, and `updateConfluencePage` takes a `versionMessage`. Confluence stores links by title, so swapping two linked titles needs a temporary one. MCP search results can be huge: they save to a file, so use `jq`.
- **Verification pattern:** Sonnet-high verifiers with a source lens and a runtime lens, an Opus-high judge and an Opus critic. Primary evidence only. The pages under test, the existing MPK Carrier Services pages and the vault explainers are not evidence. The earlier review result is a lead, not proof.
- **Explainers:** `node ~/.claude/skills/explain/lint-explainer.mjs <file> --mode event|overview|architecture`, then `python3 ~/.claude/waypoint/wp.py index`.
- **Read-only everywhere:** no Jira, Slack or GCP writes, and no edits to Tech Services repos.
- **Log:** this session's Tasks record is `Tasks/2026-11-06-pod-carrier-table.md`. Update it in place.
- **Memories that apply:** `project_merak_context`, `feedback_merak_parcel_portal_irrelevant`, `reference_firebird_ddl_dump`, `reference_ado_orgs`.

## On the target
Checked on `rc-hjf` (`uname -n`) at 2026-11-09T11:57Z:
- **Has:** `gh` signed in as `harry-fitzgerald_gfsdev`. `gcloud` account `harry.fitzgerald@gfsdeliver.com`, with no Pub/Sub access to `gfs-ecm-*`. The Atlassian, Datadog, Slack, Fuse, GitHub, ADO (`ado-local-mcp`) and orient MCP servers all answered this session. The Datadog server is on a deprecated endpoint and still works. `~/code` holds `fuse`, `merak`, `ilg-platform` and `remote-compute`.
- **Lacks:** ADO `git clone` (denied), so read source through `repo_file`, which needs a branch name or a full 40-character sha. `~/code/selector` does not exist, and `~/code/apiky-survey` holds only an empty `ado/` folder. The legacy ADO org `globalfreightsolutons-legacy` is unreachable. Central Firebird procedure source is readable in `gfs-data-services/gfs-pipelines` (a December 2025 dump).
- **Not part of the handover:** this session's scratchpad under `/tmp/claude-2001/`. The checked facts live in the two explainers and the MPK pages.

## Gotchas
- **Datadog logs keep about 15 days.** Use metrics for longer windows. `gcp.pubsub.*` isn't collected for ECM prod.
- **Don't use ADO `search_code` as evidence.** Its index lags both repos' heads and it missed matches. Read the file with `repo_file`.
- **The ECM catalogue's carrier values are swapped.** `carrier.id` holds the legacy name ("DPD") and `carrier.idV2` holds the almanac number ("10").
- **Don't write "GPS" about POD.** v2 returns GFS's own geocoded shipment address, v1 keeps the carrier's address, and the two share a cache key.
- **"Delivered" has at least six definitions.** Status 1003 is ECM's mark-as-delivered default, and legacy UPS reporting reads it as lost.
- **The Scan Injector runs 06:00 to 23:01 UK local time.**
- **zsh treats `echo ===` as an error.** Use `printf`.
- **`hostname` isn't installed on `rc-hjf`.** Use `uname -n`.
- **`TaskStop` on an already-killed workflow errors harmlessly.**

## Closed since handover
| When (UTC) | Work | Result |
| --- | --- | --- |
