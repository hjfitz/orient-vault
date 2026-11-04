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
