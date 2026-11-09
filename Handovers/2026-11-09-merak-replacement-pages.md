---
tags: [handover]
status: resumed
workstream: ECM and Selector research, now feeding Merak (Harry frames it as a new despatch and shipping platform that replaces both). Finish and publish two MPK design pages
programme: none
repo: none (vault + Confluence MPK; read-only GitHub and Azure DevOps)
from: rc-hjf
to: next session, any machine
session_id: 9ef32451-f6a6-429e-88df-add8e5d83ddf
resumed_by: 4ff6c302-4da3-4b14-bf3c-fc976c0ec75b   # laptop (freightops), 2026-11-09T12:14Z
updated: 2026-11-09T12:40Z
---
# Handover: Merak replacement pages (continues the carrier-integrations research)

Continues [[Handovers/2026-11-06-carrier-integrations]], which is closed. Read that record for the earlier waiting items.

## Where things stand
The ECM and Selector research is published to MPK and the vault. On 2026-11-09 a 31-agent review checked 36 claims on the first journey page: 19 confirmed, 17 partly right, none refuted. All 17 were corrected. Harry now frames Merak as a new despatch and shipping platform that replaces ECM and Selector. **The Parcel Portal is not part of that.**

Three design pages are **published as drafts, unverified**, under MPK "1. Architecture & Design" (page 351502339). Harry asked for them on 2026-11-09 at about 12:35Z and will send feedback afterwards. The verification run was killed at the session limit and returned nothing, so no claim on the pages has been through it. Apply Harry's feedback to the live pages first, then to the vault files, which are the source copies.

| Unit | What it delivered | Where | State |
| --- | --- | --- | --- |
| Journey page | One shipment from label to POD: what changes it, status codes, volumes | MPK "Shipment Journey Through ECM" 354975746, v2 | Live, corrected after the review |
| POD page | `gfs-pod-service`: GFS address on v2 only, v1 keeps the carrier's | MPK "Proof of Delivery Service" 353861642, v3 | Live |
| Ingress and Egress pages | Names from GFS's side: ingress = carrier to GFS, egress = GFS to carrier | MPK Carrier Ingress Services 353206337 (v5), Carrier Egress Services 353697822 (v6), Carrier Services 353468499 (v5), Carrier Integration Uses 353206310 (v6) | Live |
| Explainers | Journey and diagnosis, rewritten with the checked facts | `Explainers/2026-11-06-life-of-a-shipment-through-ecm.md`, `Explainers/2026-11-06-ecm-event-world-where-its-a-mess.md` | Done, lint clean |
| POD docs and idea | Address and cache correction. POD-at-ingress idea kept as a draft plan | `Engineering/gfs-pod-service/` (`ideas-log.md`, `plans/`) | Done. The plan stub counts as open for `wp doctor`. To drop it: `wp plan set-status gfs-pod-service --plan capture-pods-at-ingress-and-serve-them-from-a-st --status abandoned` |
| Draft page 1 | **Selector and ECM Coupling**: six seams, what breaks if either goes first, duties nobody wrote down, three cut points | `Handovers/2026-11-09-merak-replacement-pages.page1-selector-ecm-coupling.md` | **Published 2026-11-09 12:37Z** as a draft: MPK 354418743. Unverified. 4 long-sentence lint warnings left in |
| Draft page 2 | **Tracking Events and Webhooks: What v1 Needs**: ten requirements from ECM's failures | `Handovers/2026-11-09-merak-replacement-pages.page2-tracking-events-webhooks.md` | **Published 2026-11-09 12:37Z** as a draft: MPK 355074077. Unverified. 1 long-sentence lint warning left in |
| Page 3 (old) | Dropped. It only answered MKP-9, a Parcel Portal gate | n/a | Hidden duties moved into page 1 |
| Draft page 3 (new) | **How Carriers Feed ECM**: polling, webhooks and files compared, plus the 12 mocked carriers by route (about 9% of events; Evri, DHL Parcel UK, DPD Local and DPD about 89%) | `Handovers/2026-11-09-merak-replacement-pages.page3-how-carriers-feed-ecm.md` | **Published 2026-11-09 12:38Z** as a draft: MPK 355074111. Unverified. No lint errors. The vault copy now says "Not confirmed" where the draft had `[??]`, and links page 2 |

## In flight
None of this session's workflows or agents is running (checked 2026-11-09 11:53Z). The sessions `ListAgents` shows are Harry's other sessions: leave them alone.

| Work | Where | State | To close it |
| --- | --- | --- | --- |
| Verify drafts 1 and 2 | `Handovers/2026-11-09-merak-replacement-pages.verify-workflow.js.txt` | Killed, no results | Optional now the pages are live as drafts: ask Harry whether to run it before or after his feedback. Needs his go-ahead for multi-agent work. Add page 3 to its scope. Copy the script to a `.js` file and run it with `Workflow({scriptPath})`. It uses two Sonnet-high verifiers per page (source and runtime lenses), an Opus-high judge and a cross-page critic. Its CONTEXT points at this session's scratchpad (clones, `review-result.json`), which a new session won't have. Apply the corrections to the two draft files |
| Fix lint warnings | Pages 1 (4 long sentences) and 2 (1) | Open. Fix in the vault, then `updateConfluencePage` with a `versionMessage` | `python3 ~/.claude/skills/plainly/lint.py <file>` |
| Link the three pages from [Carrier Services](https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/353468499/Carrier+Services) | MPK 353468499 | Not started. Harry asked only for the pages. The pages already sit under "1. Architecture & Design", which lists them as children | Add one line per page on Carrier Services, with a `versionMessage`. Ask Harry first: it edits a live page |

## Waiting on Harry
- **Feedback on the three published drafts.** Harry will send it. Page 3's title, "How Carriers Feed ECM", is mine: the other two titles were agreed.
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
| Carrier layer for the five carriers | Which carriers Merak can lean on | **Reshaped 2026-11-09.** "Five" was never defined. `ilg-merak/carrier-playground` mocks 12 proxies. Proxies serve Selector for labels and are not in the event flow, so this became draft page 3 (event routes). Existing MPK pages already hold the proxy estate and volumes |
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
1. Finish pages 1, 2 and 3: verify, fix, lint, show Harry the text, publish on his word. The verify script covers pages 1 and 2 only: add page 3.
2. Ask Harry which further pages he wants (see Waiting). Harry asked for the carrier page and the connectors page on 2026-11-09; both are now draft page 3.

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
- **Carrier proxies are not in the event flow.** Selector calls them for labels, cancels and manifests. Events arrive by polling connectors, webhooks or SFTP files. The one link is `connectors-amazon`, which polls through the Amazon proxy.
- **The laptop clone of `carrier-playground` was stale** (3 apps, branch gone upstream). Read `origin/main` with `git show`. It has 12 proxies plus `mock-upstreams`.
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
