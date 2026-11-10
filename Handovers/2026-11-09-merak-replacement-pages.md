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
updated: 2026-11-10T12:55Z
---
# Handover: Merak replacement pages (continues the carrier-integrations research)

Continues [[Handovers/2026-11-06-carrier-integrations]], which is closed. Read that record for the earlier waiting items.

## Where things stand
The ECM and Selector research is published to MPK and the vault. On 2026-11-09 a 31-agent review checked 36 claims on the first journey page: 19 confirmed, 17 partly right, none refuted. All 17 were corrected. Harry now frames Merak as a new despatch and shipping platform that replaces ECM and Selector. **The Parcel Portal is not part of that.**

Five design pages are **published as drafts, unverified**, under MPK "1. Architecture & Design" (page 351502339). Harry asked for them on 2026-11-09 at about 12:35Z and will send feedback afterwards. The verification run was killed at the session limit and returned nothing, so no claim on the pages has been through it. Apply Harry's feedback to the live pages first, then to the vault files, which are the source copies.

| Unit | What it delivered | Where | State |
| --- | --- | --- | --- |
| Journey page | One shipment from label to POD: what changes it, status codes, volumes | MPK "Shipment Journey Through ECM" 354975746, v2 | Live, corrected after the review |
| POD page | `gfs-pod-service`: GFS address on v2 only, v1 keeps the carrier's | MPK "Proof of Delivery Service" 353861642, v3 | Live |
| Carrier overview pages | Direction-neutral names. The ingress and egress model was dropped on 2026-11-09 | MPK: Carrier Tracking and Proof of Delivery 353206337 (was Carrier Ingress Services), Carrier Proxies and Labelling 353697822 (was Carrier Egress Services), Carrier Services 353468499 (now a flat index), Carrier Integration Uses 353206310 | Live, flattened |
| Explainers | Journey and diagnosis, rewritten with the checked facts | `Explainers/2026-11-06-life-of-a-shipment-through-ecm.md`, `Explainers/2026-11-06-ecm-event-world-where-its-a-mess.md` | Done, lint clean |
| POD docs and idea | Address and cache correction. POD-at-ingress idea kept as a draft plan | `Engineering/gfs-pod-service/` (`ideas-log.md`, `plans/`) | Done. The plan stub counts as open for `wp doctor`. To drop it: `wp plan set-status gfs-pod-service --plan capture-pods-at-ingress-and-serve-them-from-a-st --status abandoned` |
| Draft page 1 | **Selector and ECM Coupling**: six seams, what breaks if either goes first, duties nobody wrote down, three cut points | `Handovers/2026-11-09-merak-replacement-pages.page1-selector-ecm-coupling.md` | **Published 2026-11-09 12:37Z** as a draft: MPK 354418743. Unverified. 4 long-sentence lint warnings left in |
| Draft page 2 | **Tracking Events and Webhooks: What v1 Needs**: ten requirements from ECM's failures | `Handovers/2026-11-09-merak-replacement-pages.page2-tracking-events-webhooks.md` | **Published 2026-11-09 12:37Z** as a draft: MPK 355074077. Unverified. 1 long-sentence lint warning left in |
| Page 3 (old) | Dropped. It only answered MKP-9, a Parcel Portal gate | n/a | Hidden duties moved into page 1 |
| Draft page 3 (new) | **How Carriers Feed ECM**: polling, webhooks and files compared, plus the 12 mocked carriers by route (about 9% of events; Evri, DHL Parcel UK, DPD Local and DPD about 89%) | `Handovers/2026-11-09-merak-replacement-pages.page3-how-carriers-feed-ecm.md` | **Published 2026-11-09 12:38Z** as a draft: MPK 355074111. Unverified. No lint errors. The vault copy now says "Not confirmed" where the draft had `[??]`, and links page 2 |
| Page 4 | **From Label to Invoice: How a Selector Shipment Is Billed**: 15-step chain from CSS or Client4 to the NetSuite file, bill triggers, pricing inputs, timing, where shipments wait, what a replacement must write | `Handovers/2026-11-09-merak-replacement-pages.page4-label-to-invoice.md` | **Published 2026-11-09 13:09Z** as a draft: MPK 354353232. Unverified: built from the Billing space and the Selector docs by one Sonnet reader. CCDIS and `REG_WILKO_*` were not read |
| Page 5 | **How Each Carrier's POD Is Retrieved**: per-carrier calls, auth, image source, time handling and bugs for the 11 carriers plus the test carrier and DHL Express. Child of Proof of Delivery Service | `Handovers/2026-11-09-merak-replacement-pages.page5-pod-by-carrier.md` | **Published 2026-11-09 13:20Z** as a draft: MPK 354877489. Code read at `GFS POD` `origin/master` `d1f0ada` by three Sonnet readers. I checked 8 load-bearing claims against the code. No carrier was called |
| Diagrams (Lucid) | Nine C4 diagrams drawn in Lucidchart in the house style, from the text twins, and linked from the pages (a Lucid macro and a link under each heading; the ASCII blocks were removed on 2026-11-09). Lucid folder "Merak research diagrams" (id 454289417), scratch folder 454289424. Documents: carrier proxy `e1cffe19-99b0-45f9-bcc5-fb0f828c9b46`; tracking carrier to customer `bb2d2e80-97e3-4dd6-8987-fb476539082b`; polling connector `4081aae8-66c2-4184-b740-ca467d81ba87`; gfs-pod-service `22adc685-20d6-4e99-bed6-54a03bc4bc16`; tracking webhook service `a9a3115b-bce5-4257-b6e4-2f63ae886457`; customer data flow `0ebebd78-e550-4199-a8b6-37b48b6f4312`; Selector, Firebird and ECM `ea0a71eb-4fb1-4124-9fe5-e70720cb5e20`; shipment journey `2a2e0c77-b50f-4a8f-8389-63ad1cbf6a62` (2,585 px; the 4,460 px original `51ee5877-...` is in scratch); pre-advice by file `5c1c552d-27ef-430b-addd-6cc3cf894aea` | `Handovers/2026-11-09-merak-replacement-pages.diagram-*.md` (text twins) and the `c4-diagrams` skill (`~/projects/orient-writers/skills/c4-diagrams/`, uncommitted) | All nine linked on 2026-11-09, with view-only account-restricted share links (`...?invitationId=` URLs) swapped in. Audit of all MPK pages found no other ASCII blocks. Harry will build Confluence whiteboards by hand |

## In flight
None of this session's workflows or agents is running (checked 2026-11-09 11:53Z). The sessions `ListAgents` shows are Harry's other sessions: leave them alone.

| Work | Where | State | To close it |
| --- | --- | --- | --- |
| Verify the drafts | `Handovers/2026-11-09-merak-replacement-pages.verify-workflow.js.txt` | **Declined by Harry 2026-11-09.** Drafts stay unverified | None. Don't run it unless he asks |
| Fix lint warnings | Pages 1 (4 long sentences) and 2 (1) | Open. Fix in the vault, then `updateConfluencePage` with a `versionMessage` | `python3 ~/.claude/skills/plainly/lint.py <file>` |
| Link the five pages from Carrier Services | MPK 353468499 | Done 2026-11-09 as part of the flatten: Carrier Services now lists every page | None |

## Waiting on Harry
- **Flatten MPK "1. Architecture & Design": done 2026-11-09 13:35Z.** The root is now "1. Research into Existing Services" (351502339) with an index body. All carrier, tracking, POD, billing and Selector-coupling pages are direct children of it (checked with `getConfluencePageDescendants`). Services (Legacy Selector, Parcel Portal) is unchanged, and the Journey page keeps its whiteboard. Ten pages moved up, 15 bodies written (13 with wording or link changes), and the old two-family table on Carrier Services is gone. Version messages on older versions still say ingress and egress.
- **Security items from the POD code read, class level only, not yet in the ticket draft below:** hard-coded credentials in the unloaded DHL Express module; credential-like sample values in comments in the Yodel and Panther modules; a Panther API key sent in a URL query string; the UK Mail token that never expires; the test carrier loaded in the prod config. The repo is `GFS POD` in Azure DevOps.
- **Page corrections applied 2026-11-09 (Harry approved).** Journey (stages 10, 11, In short, CCIS/ICIS direct, Slipway masked copy, shipment ID as lookup on consignment plus carrier with a counter for new shipments, repo only, not confirmed against the deployed service). Polling Connectors (status-deriver sidecar; counts now about 5.97M polling events, 24 calls per event, 96%; the page never stated a namespace, so no namespace change). Carrier Tracking and How Carriers Feed ECM (`connect-hooks` on its own `raw_tracking.v1` subscription; per-carrier counts sum to 6,246,802: polling 5.97M, webhooks 215k, files 61k; 5.44M and 54k kept as lower counts, difference not confirmed). Tracking Webhook Services (map then match; Royal Mail older, synchronous, no interim topic; 90 days is a read cutoff, TTL indexes not confirmed). Customer Data Flow (per-customer invoice schedule, live timetable not confirmed). Pre-advice link added on Selector and ECM Coupling and Customer Data Flow.
- **Open:** "Evri keeps them up to 90 days" on Tracking Events and Webhooks and on Selector and ECM Coupling could read as deletion. Recommended rewording to "reads them for up to 90 days"; waiting on Harry. The pre-advice link request did not name a page; applied to the two pages that mention pre-advice.
- **Cleanup pass 2026-11-09 (Harry: "get all of this sorted").** Lucid macro embedded on all nine diagram pages (ADF only; markdown edits drop it). Page reviews: 24 pages are needed, 2 can go. Selector suite: Legacy Selector is the single index with a reading order; Overview and Feature Sheet corrected (invoice schedule per customer, Monday default weekly, live timetable not confirmed; Firebird Transfer Service publishes `fb.shipments.v1`; 278 is a VM count, about 306 not reconciled); ApiKy moved from Interface to Estate; Getting a Label trimmed about 150 words; Day End folded into From Label to Invoice (353566845 kept as a pointer). Numbers: canonical window is the 15 days to the end of 6 Nov 2026 UTC (23 Oct to 7 Nov): raw_tracking.v1 about 6.29M (polling 6.01M, Royal Mail webhook 218k, files 62k), Royal Mail received 343k, Evri received 563k, customer webhooks 406k, unmapped codes 11.6k; applied across 14 pages. Table in `numbers-canonical.md` (session scratchpad, not in the vault). Settled from code: `dhl-pod-images` is UK Mail SOAP only (prod uses the eCommerce module, which does not call it); DPD Local posts the parcel number it is given; DHL Express is both direct API and template (waybill and routing codes, label drawn from a template); TNT has no carrier call and is disabled in seed data; Nightline and Nightfreight are two carriers; Royal Mail column is `GFS_RM_URL`. Evri 90 days is a read cutoff (TTL indexes not confirmed). Links to Carrier Services repointed to the root on 14 pages; links to Day End repointed to From Label to Invoice; re-scan found none left.
- **ASCII blocks removed 2026-11-09 (Harry asked).** Taken out of eight MPK pages, each already carrying its Lucid macro: 352157700, 353206337, 353533985, 353697822, 353697842, 353697880, 353861642, 354975746. Carriers and Volumes (353566754) keeps its SQL block. On the Journey page, "Two paths are not drawn above" became "Two paths in the diagram need a note" (the Lucid draws both) and one sentence was added for claims and reporting, which the diagram leaves out. Customer Data Flow gained one sentence naming `TRANSFER_QUEUE` and `rm_replica`.
- **Owed by hand (no delete tool):** delete Carrier Services (353468499) and Day End and Billing Handoff (353566845, now a pointer), and the scratch draft 355565572.
- **Still open:** Not confirmed: 142M poll calls vs about 114M polls, 306 vs 278 VMs, DPD Europe proxy dormant, Royal Mail "about a third never matches" vs 21k of 343k unmatched and 146k held, which parcel callers ask for on the v2 POD route, the live billing timetable, whether the shipment-identity repo matches the deployed service. Stale numbers elsewhere: How Carriers Feed ECM still says "12 mocked carriers" over a table with Amazon SFP and Veho unresolved. The per-carrier POD traffic figures were not re-run on the canonical window.
- **Lucid on Confluence, decided 2026-11-09.** Harry chose to link the diagrams and draw whiteboards himself, not embed. The Lucid macro showed "error loading the extension" and the existing macro on the DST page failed too, so the Lucid app is not working on the site (Harry asked the admin to install it). Smart links (inline, block, embed) do render. Retest the macro after the install. Embeds must be written in ADF only: a markdown edit drops the macro. See the skill's Lucid workflow section.
- **Lucid share links not made.** The links use each document's normal `/view` URL, so colleagues need access to the Lucid document. If Harry wants the team to open them: `lucid_create_document_share_link`, role `view`, `restrict_to_account` true, then swap the links.
- **Shipment journey redraw and link.** An agent is redrawing it at about 2,600 px wide with the same 20 boxes and 30 arrows. When it returns, check the render, then add the link under "The journey" on Shipment Journey Through ECM (354975746). The coupling twin differs from its drawing: Selector's IE service added, gfs-modernizer and shipment-identity-service folded into one box, a dashed masked-copy arrow from Slipway.
- **Cleanup by hand.** Discard the scratch Confluence draft (355565572). The Atlassian and Lucid tools cannot delete. Lucid scratch documents are in folder 454289424.
- **Page corrections (applied 2026-11-09, see the cleanup pass line below; kept for the record):**
  - Shipment Journey Through ECM: "In short" says a Dataflow job and the Scan Injector set shipment status (the Dataflow job sets none; Firebird derives it from raw scans). Stage 11 says the write-back sets a delivered status. Raw events also reach CCIS and ICIS directly. The ASCII omits Slipway's masked billing copy. The shipment ID rule (counter, or consignment plus carrier) is unresolved.
  - Polling Connectors: the response-publisher pod also runs a `shipment-tracking-status-deriver` sidecar that the page omits. The manifests say namespace `default`, not `fenghuang`.
  - Carrier Tracking and Proof of Delivery: `connect-hooks` subscribes to `raw_tracking.v1` directly, not after CCIS and ICIS. The three path counts sum to about 5.71M, not the 6.25M total. The same 5.44M appears on How Carriers Feed ECM.
  - Tracking Webhook Services: code maps first, then matches, dedupes and publishes. The Royal Mail handler is older and synchronous, with no interim topic. The 90-day limit is a read cutoff, and the TTL indexes are unconfirmed.
  - Customer Data Flow: it says a Sunday invoice run, but each customer has its own schedule.
- **Feedback on the published drafts.** Harry will send it. Page 3's title, "How Carriers Feed ECM", is mine: the other two titles were agreed.
- **Merak replacing ECM and Selector is an unconfirmed hunch (Harry, 2026-11-09).** It can't be confirmed with Jack and Stef yet. The published pages say "a replacement" hypothetically and leave the choice to the Merak team. Keep any new wording that way.
- **Keep or drop one link.** Page 2 links the "Idea: Developer promise" page (349110455) in its opening paragraph. Recommendation: keep it. That page asks for the same v1 webhook features, and the decisions on it stay with Stef.
- **Further pages: none wanted (Harry, 2026-11-09).** The four proposed pages stay unwritten. Keep any future pages research level, comprehensive and simple.
- **Security ticket: declined (Harry, 2026-11-09: "not my domain").** Don't draft or offer it. The class-level items below stay here as notes only. They come from the research agents and I have not re-checked them:
  - a committed credentials file in `patina-service-2`'s rollback tool;
  - plaintext secrets in several prod and dev manifests;
  - TLS verification off on the Shipment Update Service API and collections-service;
  - carrier credentials in cleartext on Pub/Sub feeds;
  - a Datadog key in a push URL and in Terraform state;
  - committed Terraform state in `gfs-pipelines`;
  - project-wide Pub/Sub editor for two identities, one unclaimed (`tracking-dump@`);
  - a personal Gmail address with `pubsub.admin` on `gfs-ecm`, being revoked under SRE-305.
- **DHL Parcel UK (CID-317, blocked): dropped (Harry, 2026-11-09: "not an us issue for now").** Nothing was sent and nothing is owed. If it comes back: the 11-06 record never listed this hand-off, the 92% and monitor claims are unverified, and the ticket's ~19 accounts, our ~15 contracts and the 368k wasted calls in 15 days don't agree.
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
0. (Done 2026-11-09) The POD per-carrier page is published as MPK 354877489.
1. Apply Harry's feedback on the published pages when it arrives: live page first, then the vault copy. No verification run was wanted.
2. Nothing else is queued. Wait for Harry's feedback on the five published pages.

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
- **Selector and ECM Coupling was corrected live on 2026-11-09 (v2)** after three read-only agents challenged it. Firebird is the seam, not a tight coupling. The findings are in `Handovers/2026-11-09-merak-replacement-pages.page1-challenge-findings.md`. The Amazon SFP sentence on Carrier Tracking and Proof of Delivery was corrected too (v7).
- **Confluence updates link targets when a page is renamed, but not the visible link text.** After a rename, search for the old title and fix the labels. Moves by `parentId` keep ids and links.
- **Don't rewrite a Selector page that uses smart-link cards through markdown.** `Legacy Selector: overview` (351764493) shows live titles in cards, and a markdown write would turn them into plain links. It needed no change, so it was left alone.
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

## Tracking research (2026-11-10)
**Asked.** How ECM orchestrates tracking, whether the polling interval shrinks as a parcel ages, what a tracking event and a status look like at each stage, and which topics carry them. Harry asked for orient first, before any Confluence page. No Confluence page has been written or edited.

**Answers, in three lines.**
- `tracking-core` stores active parcels and leases due ones to connectors over gRPC. It has no scheduler, and the chain after `raw_tracking.v1` is choreography through Pub/Sub topics.
- The polling interval does not shrink with age. Code holds one `TargetPollingMinutes` per carrier and state, and the prod values in etcd are unread.
- A tracking update has three shapes (scan, mapped event, shipment status). `groupId` is a free string, and no topic or enum exists for delivered, out for delivery, POD ready or customer notification.

**Where it lives.**
- [[Systems/ecm/tracking]] is the explainer, with the topic spine, a topic table and what a replacement must keep.
- [[Systems/ecm/architecture]] gained guardrails G9 to G14 and a corrected G6. [[Systems/ecm/known-context]] has the settled facts, the new unconfirmed items and the owed corrections.
- Research copies: [[Handovers/2026-11-09-merak-replacement-pages.tracking-core-findings]], [[Handovers/2026-11-09-merak-replacement-pages.tracking-topic-catalogue]] and [[Handovers/2026-11-09-merak-replacement-pages.tracking-model-findings]].

**Owed corrections (Confluence not edited, Harry to decide).** Polling Connectors (353697880) gives the `FindOneAndUpdate` to the connector, and it runs in batch-creator. How Carriers Feed ECM, Selector and ECM Coupling and Shipment Identity state the 90-day expiry too firmly. Tracking Events and Webhooks says every event carries the raw code beside the derived status. The full list, and the contradictions in the `tracking-core` Waypoint docs, are in `known-context` under Owed.

## Topic usage (2026-11-10)
**Asked.** Harry asked for a page on the ECM Pub/Sub topics: what each carries, who writes it and who reads it. Harry reviewed the draft and authorised publishing.

**Published.** MPK 356155424, "ECM Pub/Sub Topics: Shapes, Producers and Consumers", under 351502339. It is an unverified draft. It covers all 70 topics the prod Terraform creates (145 subscriptions), with a verdict for each: LIVE 42, CONSUME-ONLY 9, PUBLISH-ONLY 8, UNKNOWN 5, ORPHAN 3, UNDEPLOYED 3. Datadog counters cover 41 topics. The published page was fetched back and checked against the source: all 70 topic names, the six verdict counts, the five linked pages and every table row were present.

**Correction.** [[Systems/ecm/tracking]] said 10 of the 15 `raw_tracking.v1` subscriptions had a running consumer, and listed 41 topics. The map found 8 running consumers, one that runs but drops every event, a Dataflow job in an unknown state and 4 with no running workload. Both are corrected there.

**Where it lives.**
- [[Handovers/2026-11-09-merak-replacement-pages.page7-ecm-topics]]: the page source copy.
- [[Handovers/2026-11-09-merak-replacement-pages.topic-usage-map]] and [[Handovers/2026-11-09-merak-replacement-pages.topic-datadog-usage]]: the research copies.
- [[Systems/ecm/known-context]] has the settled facts, the new unconfirmed items and the owed GCP read. [[Systems/ecm/overview]] indexes the page.

## Where this now lives
The durable, indexed copy of these findings is the system [[Systems/ecm/overview|ecm]]. This record stays the transient handover.
- [[Systems/ecm/overview]]: the MPK page index and states, the nine Lucid document ids and their text twins.
- [[Systems/ecm/architecture]]: the Firebird contract, six seams, three cut points (hypothetical) and the carrier facts settled from code.
- [[Systems/ecm/known-context]]: standing decisions, the canonical figures and window, and every unconfirmed item.
- [[Systems/selector/known-context]] points to it, and the follow-ups are in the 9 Nov digest Todo.
