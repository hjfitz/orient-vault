---
tags:
- system
- selector
verified: '2026-11-05'
title: selector — known context
---
# selector — known context

Interview truth (Harry, 2026-11-05), the Tech Services vault, Datadog, and facts source can't give. Claims marked `(snapshot …)` describe mutable state and age out.

## People and ownership
- **Jez Poppleton owns Selector** and writes nearly every commit to CSS and Client4 (SMXI). Andy Palmer contributes now and then.
- Work runs on **SMXI** Jira tickets: one branch per ticket, merged into a `Release-4.50.x` branch, then into master/main.
- **Chris Cumings** builds, tests and announces each GFS Enterprise (CSS) release, and is the contact for manifest semantics.
- **Tech Services** (Kyle) supports it day to day and keeps the team vault (`ilg-tech-services/knowledge-system`).
- **Billing is Finance's, not Selector's.** It's a separate Delphi billing app that reads central `SHIPMENTS`.
  - George Vavoulogiannis develops it.
  - George Renshaw-Fox answers operational questions; William Valentine sets customers up.
  - Ben Turvey is the BA, and Neil Janman owns the Billing Confluence space.
  - Billing 2.0 / carrier invoice tracking is Jira FID. It plans a unique source ID per shipment (FID-196), which may change the handoff.
- Oliver Wilders is due to review the MPK *Legacy Selector* pages (snapshot 2026-11-05).

## Direction
- **Selector is being replaced.** Part of what Merak delivers will replace it.
- No programme folder or Jira epic tracks the replacement yet (snapshot 2026-11-05). The MPK *Legacy Selector* pages are the survey feeding it.
- The ECM side of the same research, and the Firebird contract Selector and ECM share, are in system [[ecm]]. The MPK pages are *Selector and ECM Coupling* (354418743) and *From Label to Invoice* (354353232).
- Until then, Fuse's [[selector-adapter]], [[parcel-portal]] and [[selector-rest-proxy]] all book through CSS. A replacement has to reproduce the CSS contract they rely on.

## Estate (snapshot 2026-08-06, Tech Services vault)

| Measure | Number |
| --- | --- |
| Live customers | 739 |
| Registered sites (`SITE_REG = 1`) | 1,019 |
| Sites that despatched in one week | 377 |
| Hosted GCP VMs (`gfs-cloud-selector-prod-uk1`) | 278, backing 259 sites |
| Sites marked `GCP` / `Standalone` / `Rackspace` in `CUST_URL` | 266 / 172 / 1 (free text, 2,043 blank) |

- **CSS use is measurable only for UPS** (snapshot 2026-11-05, 21 Oct–5 Nov). The UPS proxy logs the request XML, and its header shows the builder. CSS sent about 6,100 ShipConfirms for about 35 companies (Omlet, LISAUK, Zippo, ETI the largest). Client4 sent 228 for 8.
- **Royal Mail is the busiest proxy** (same window): about 29.6k label creations for 19 accounts. The proxy's log messages are mislabelled (see the MPK *Carrier Proxies* page).

## Fragility and surprises
- **CSS-only customers still depend on Client4.** If the upload station is down, labels print but nothing reaches GFS or billing. Nothing alerts on this.
- **No duplicate guard.** Selector books a repeated `ProcessShipment` again (proved by the [[selector-adapter]] spike).
- **Carrier logic lives twice, and it drifts.** `FEDEX` and `INPOST` mean a GFS proxy in CSS but the carrier's old direct API in Client4. `label_id = 0` means something different in each app.
- **Manager edits don't flow on their own.** Someone has to press "Site update". Deletions never propagate. tools-ui fixes land on the site only, and re-registration wipes them.
- **The vault and the code disagree on two points:**
  - The vault says CSS writes to the main DB directly. The code says it only fires `SHIP_COMMITED`, and Client4 uploads.
  - The vault names `CSS-Enterprise` as the CSS source. The 4.50.7.0 work is in the `CSS` repo (see [[css]] known-context).
- **No CI and no automated tests** in any Selector repo. A release merge into CSS master was reverted on 2026-10-16 (`Release-4.50.7.0`).
- **CSS refuses every call during a database update.** When `clientdb.UPD_START = 1` it returns `0066 Database updating`.
- **No central telemetry.** CSS and Client4 logs stay on the box, or go to the old LoggingServer. Datadog sees only the carrier proxies (about 15 days' retention).
- **Security, class-level only.** The specifics belong on the security ticket:
  - committed database admin credentials in CSS config
  - plaintext API user passwords
  - request and response dumps under `C:\temp`
  - a public, unauthenticated log sink
  - full recipient PII at info level in the UPS and Coll8 proxy logs

## Unknowns
- **Billing:**
  - Which billing run program and timetable are live, and whether split runs are on.
  - How `BILL_ON_SCAN = 2` (GFS International) works.
  - What the `REG_WILKO_*` procedures de-duplicate on.
  - Whether the October double billing came from Manager's recycle-replace, Slipway or DataBridge. FID-211 is related.
- **The label for `SITE_REG = 2` and which sites have it.** Needs a read of the central DB: `REG_STATUSES`, and `CUST_SITES WHERE SITE_REG = 2`.
- **Which `CUST_SCRIPTS` rows are live** for registration (type 0) and site update (types 1 and 5), and whether a non-tuned type-0 row exists. Needs a central read.
- **Which sites auto-update.** Needs `CUST_SITES.AUTO_UPDATE`, `CUST_SITE_UPDATES` and the live `UploadServer.ini`.
- **Whether `CUST_VER_INFO` is current.** It is the only central record of site versions.
- **Pipelines in the `globalfreightsolutons-legacy` ADO org.** The ADO MCP is bound to `globalfreightsolutions`, so they couldn't be listed. None exist in the repos.
- **Who creates site `web_users` rows.** No repo does it.
- **How many hosted VMs take CSS calls** beyond UPS customers, and which GFS customer is behind each Royal Mail, BJS or FedEx proxy client ID.
- **Production `Web.config` values per VM**, the logging keys among them.
