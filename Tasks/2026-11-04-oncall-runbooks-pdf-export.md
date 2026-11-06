---
tags: [adhoc-task]
date: 2026-11-04
tldr: "Exported the out-of-hours on-call page and support runbooks to PDFs for Ryan Ellis (added FXS board link); published a Legacy Selector overview page in Confluence Merak space."
session_id: 945d0e77-3787-450a-a8e6-3635e238a5c9
status: open
---
# Export on-call/support runbook PDFs; publish Legacy Selector overview

## Outcome
6 PDFs in ~/Documents/fuse-oncall-pdfs-2026-11-04 (rendered locally from the live Confluence pages 351567873, 334757891, 334856194, 335020034, 334856221, 334725130). On-call rota (351600641, has phone numbers) deliberately not exported. Owed: Harry to send to Ryan; decide whether to add the 3 FAQs.

Later, same session: on-call PDF re-exported with a link to the Fuse Support board (FXS, project URL only, board ID not verified); Confluence source page not changed.
Published "Legacy Selector: overview (current state, 4 Nov 2026)" (page 351764493, child of 351764483 in Merak Project / MPK) from the "Selector Deep Dives" artifact. Not checked against code; unverified items listed on the page. Owed: someone who owns Selector to sanity-check the figures.

Later still: feature sheet (351764518) drafted, then both Selector pages (351764493, 351764518) rewritten for readability and corrected from Oliver Wilders's 4 Nov DM clarifications (CSS = ClientShipService; on VMs CSS labels and Client4 only does auto commit/upload; upload server URL hard-coded in Client4.exe; Pub/Sub published from main Firebird). V4 source (ADO org globalfreightsolutons-legacy) NOT reachable from the ado MCP (different org): pages say "not yet checked against code". Owed: Wilders review; read access to V4 repo then spot-check gazetteer pull, upload, GET_SHIP_SERVICE.

Then: Harry cloned all 15 Selector repos (~/code/selector). Verified claims in code and rewrote both Selector pages (v3 overview, v4 feature sheet). Corrections: GET_SHIP_SERVICE resolves contract/service (not gazetteers); postcode routing is inline SQL duplicated in Client4 + CSS (+ GET_*_DEPOT procs); upload server list is per-site CUST_UPL_SERVERS (not hard-coded); SAVE_UPDATES silent failure is real but guarded since 27 Jul (4.50.6.6); no Pub/Sub code in any repo; 4.50.7.x only on release branches, CSS master reverted 4.50.7.0 on 16 Oct. Added server-side services (IE, Notify, WR, route updaters). Owed: Wilders review; locate repos for tracking/billing/proxies/Slipway/Channel Connector; confirm which build is deployed.

Then: published "Legacy Selector - Carrier and Proxy Interface" (351797252, MPK, child of 351764483) from three parallel read-only code investigations (CSS, V4 client, carrier-proxies + selector-rest-proxy), with spot-checks of the riskiest claims. Restored ~/code/fuse/carrier-proxies working tree (169 zero-byte files since 8 Oct; git restore . on Harry's go-ahead). Owed: raise ups-proxy route-casing risk (PascalCase ShipConfirm vs camelCase shipConfirm) with carrier-proxies owners before cutover; cross-link new page from overview and feature sheet.

ApiKy check (code only, no live data read): Client.profile is free-form JSON (Postgres via Prisma); keys are plaintext UUIDs looked up by equality, passed as ?token=; any project read-only key reads every client profile in that project. Consumers: selector-rest-proxy reads profile.upstream/username/password (Selector CSS creds in plaintext); exelot-proxy reads exelotPartnerId; api-host-framework calls ApiKy on every request, no cache, whole profile exposed via getApiKyProfile. Owed: field-name inventory of prod profiles (needs Harry's access); ApiKy section on the carrier interface page.

ApiKy survey done: cloned 31 consumer repos to ~/code/apiky-survey (gh + ado, shallow). Profile fields found: bjsSecret (credential), username/password/upstream (selector-rest-proxy), royalmailCustomerId, exelotPartnerId, fedexCustomerId, CustomerId, accountCode, company, allowedReferrers, customerId, name. Added "ApiKy: what it holds and serves" to page 351797252 (v2), risks at class level only. Verified on apiky origin/main: client PUT/DELETE scoped by clientId only (cross-project write/delete; fix in open PR #7), PUT logs profile body, hard-coded SMTP creds in invite route; DB conn string public IP + sslmode typo. Owed (Harry): land/hotfix PR #7; rotate SMTP creds + plaintext cluster ApiKy values (droppoints, connect-gateway); move bjsSecret out of profiles; stop key logging; live profile field-name inventory.

## 5 Nov: full carrier-proxy survey
69 repos (GH + ADO) plus Datadog (~15 days of retention) plus cluster/Cloud Run manifests. Selector label creation is the main use, but not the only one. Live non-Selector uses:
- ECM tracking via amazon-logistics-proxy-internal (unauthenticated) and evri-auth-facade
- selector-rest-proxy serving external REST customers (2 logins, ~9k ProcessShipments)
- checkout droppoints, plus a nightly import
- collections-service for the portal/CCP, going to legacy SOAP and Firebird
- RM cron and config UI
Prod is mostly the ADO originals on GKE. The GH/monorepo copies are dev-only or idle (Exelot 0, new Amazon 0 prod, OCS test only, DPD-EU all failing).
New security items (chat only):
- amazon internal IS_SECURED=false
- new amazon tracking route takes company from the URL
- collections-service plaintext LEGACY_COLLECTION_PASSWORD in the prod-uk1 repo
- UPS stepping-stone/DPD-EU/InPost payload+PII logging
Published: MPK page 352059403 "Legacy Selector - Carrier Proxies: Estate and Use Cases" (v2). Owed: fold items into the security ticket draft (awaiting Harry).

## 5 Nov: customer data flow page
Published MPK 352157700 "Legacy Selector - Customer Data Flow". Covers:
- per-site tables
- RegisterCustSite registration pull
- tools-ui SQL pasted into site DBs
- route codes vs postcode routing
- Client4 vs CSS: CSS UploadShipments only fires SHIP_COMMITED, and Client4 on UPLOAD_STATION does the upload
Open:
- CUST_SCRIPTS registration table list (needs central DB read)
- whether Manager pushes changes to registered sites

## 5 Nov: Selector onboarded into Waypoint/orient
System `Systems/selector/` (overview, architecture, known-context, design) with members `Engineering/css` (repo selector/CSS @414569b) and `Engineering/client4` (repo selector/V4 @73cfd69). Owner Jez Poppleton; GFS-hosted box per customer; being replaced by part of Merak's output (no programme yet). Release path, CUST_SCRIPTS table list, SITE_REG=2 left as Unknowns. No `commands` anchor: wp's manifest allowlist has no .NET/Delphi entries.

## 5 Nov: getting a label
Added "Getting a label" to Systems/selector/architecture.md (lint clean). Published MPK page 352157738 "Legacy Selector - Getting a Label". Finding: CSS draws labels from PDF_LABEL_TEMPLATES by default; a hard-coded carrier list (ProcessShipProcedures.cs:108-130) goes to proxies/direct APIs instead. Client4's split unverified.

## 5 Nov: Selector gap investigation
4 read-only agents (carrier split, registration/updates, release/logging, estate/Datadog), key claims spot-checked. Orient: system architecture rewritten (hosting models, packages-not-push, SITE_REG table, CSS users = gfs_users role 3, carrier path table incl. Client4 FEDEX/INPOST direct, releases, telemetry); known-context and css/client4 docs updated. Confluence: 352059403 v3 (Royal Mail ~29.6k labels, log lines mislabelled), 352157738 v2, 352157700 v2. Owed: central-DB reads (REG_STATUSES, CUST_SCRIPTS rows, AUTO_UPDATE), vault corrections (CSS vs CSS-Enterprise; "CSS writes main DB"), security ticket additions (UPS/Coll8 PII logs).

## 5 Nov: carrier-playground mock proxies, handed over to the VM
Built ilg-merak/carrier-playground PR #1: mock Royal Mail, UPS and Coll8 proxies with mock-upstreams, dev Cloud Run IaC (mock-*-cp-dev), golden image, observability SDK and dd-trace; 374 tests, docker smoke passed. Handed over to hjf.shell (tmux main:carrier-playground) to watch CI and summarise plans. Record: [[Handovers/2026-11-05-carrier-playground]]. Owed: Harry's merge/deploy call after the plans; Amazon and DPD Europe decision.

## 6 Nov: Carrier Proxies pages (MPK)
Researched volumes, integration methods and uses (3 read-only agents, spot-checked), then wrote MPK 353697822 Carrier Proxies (what a proxy is, why, estate) with children 353566754 Carriers and Volumes, 353697842 Carrier Integration Methods, 353206310 Carrier Integration Uses. Corrections: Client4 has no outbound FTP (the "FTP" hits were ZeroLeftPad); pre-advice is V4-Server-IE over plain FTP. Owed: central-DB reads (per-carrier volumes, live IE jobs); connectors deep dive is next.

## 6 Nov: tracking egress deep dive (connectors + webhooks)
3 read-only agents, spot-checked in Datadog and gh. 15d: ~6.25M raw_tracking.v1 events; ~5.44M from 11 polling connectors (~142M carrier calls), ~215k from the Royal Mail webhook (only live publisher), ~54k from SFTP files. Evri webhook in monorepo since 15 Oct but shadow (CID-315 In Progress); RM and InPost monorepo PRs #3/#2 open. No pages written yet; proposal sent to Harry.
Published: MPK 353468499 Carrier Services (parent) → 353697822 Carrier Ingress Services (renamed from Carrier Proxies; children Volumes, Methods, Uses) and 353206337 Carrier Egress Services (children 353697880 Polling Connectors, 353533985 Tracking Webhook Services).
