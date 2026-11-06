---
tags: [handover]
status: open
workstream: Selector / carrier integrations / billing research → Confluence (MPK) and orient (Waypoint). Continue from the POD service carrier table
programme: none
repo: none (vault + Confluence); read-only clones under ~/code/apiky-survey, ~/code/selector (laptop only)
from: laptop
to: hjf.shell.platform.ilg.software
session_id: 945d0e77-3787-450a-a8e6-3635e238a5c9
resumed_by: ""
updated: 2026-11-06T15:12Z
---
# Handover: carrier integrations research (continue from the POD service)

## Where things stand
A long research session (4–6 Nov) mapped GFS's legacy Selector, the carrier proxies, tracking connectors and webhooks, and the billing handoff. It published Confluence pages in MPK and built Waypoint systems in orient. Everything is written and verified; **nothing is running**. Orient MCP changes are live at `hjfitz/orient@38061ee`. The next step is small and documentation-only (see Next up 1).

**Confluence, MPK space (space id 338526210, cloudId `globalfreight.atlassian.net`).** Under "1. Architecture & Design" (351502339):

| Page | ID | Notes |
| --- | --- | --- |
| Carrier Services (parent) | 353468499 | ingress vs egress table, links everything, Selector section |
| ↳ Carrier Ingress Services (was "Carrier Proxies") | 353697822 | what a proxy is, why, prod estate |
| ↳↳ Carriers and Volumes | 353566754 | ~270k shipments/wk; per-carrier volumes (measured vs estimated) |
| ↳↳ Carrier Integration Methods | 353697842 | REST/XML/SOAP/FTP pre-advice (V4-Server-IE)/routing files |
| ↳↳ Carrier Integration Uses | 353206310 | uses table incl. POD row (v3 by the POD fork) |
| ↳ Carrier Egress Services | 353206337 | 3 tracking paths into raw_tracking.v1, coverage by carrier |
| ↳↳ Polling Connectors | 353697880 | 15 connector repos, 142M calls → 5.44M events / 15d |
| ↳↳ Tracking Webhook Services | 353533985 | RM live, Evri shadow (CID-315), InPost PR #2, RM monorepo PR #3 |

Under Legacy Selector (351764483; it now has an index body):
- overview 351764493
- feature sheet 351764518 (not cross-linked, by choice)
- interface 351797252
- estate 352059403
- customer data flow 352157700
- getting a label 352157738
- **Day End and Billing Handoff 353566845** (new 6 Nov)

**Orient (Waypoint vault):**
- `Systems/selector` (members `css`, `client4`). Its architecture has a "Day end and billing handoff" section; its known-context has billing owners and unknowns.
- `Systems/carrier-integrations` (33 members): the 10 prod proxies plus `carrier-proxies`, `tracking-core` plus 15 `connectors-*`, `tracking-webhooks`, `tracking-webhook-royal-mail-sapient`, `file-ingestion-ftp-proxy`, `tracking-file-processor`, `gfs-pod-service` and `evri-auth-facade`. All docs are lint-clean and anchored.
- `Engineering/selector-adapter/known-context.md` has the Fuse commit gap. `Bifrost/Delivery Backends/Migration State.md` has risk **R5**: Fuse never commits, so its shipments are billed only if the site auto-commits and uploads.
- `orient-entity` now supports `kind: system` and shows correct service metadata (`hjfitz/orient` `b6e3fa7`, `38061ee`).

**Other outputs:**
- Artifact "Carrier whiteboard briefs" (https://claude.ai/artifact/AVkPueqftQ8LtCquXgcZRG): 10 diagrams to draw as Confluence whiteboards.
- `ilg-merak/carrier-playground` (mock proxies) is merged and deployed through PR #8. That was the earlier VM handover, `Handovers/2026-11-05-carrier-playground.md`.
- Session log: `Tasks/2026-11-04-oncall-runbooks-pdf-export.md`.

## In flight
None. All background agents finished (orient MCP fix, carrier-integrations onboarding, POD/facade survey).

## Waiting on Harry
- **Security ticket draft** (offered early, never raised). Class-level items found:
  - ApiKy cross-project PUT/DELETE (his PR #7), hard-coded SMTP credentials, the database `sslmode` typo and public IP;
  - plaintext keys in prod-uk1 YAML;
  - keys and PII logged by proxies (UPS, Coll8 recipient PII at info, DPD-EU token);
  - `amazon-logistics-proxy-internal` with `IS_SECURED=false`, and the Amazon tracking route taking the company from the URL;
  - the plaintext `LEGACY_COLLECTION_PASSWORD`, and the selector-rest-proxy destroy-prod job;
  - the CSS public, unauthenticated log sink;
  - POD v2 with no token (in-cluster only);
  - the POD ingress path rule not tied to its hostname.

  Draft it for Harry to review; don't raise it.
- **Whiteboards:** empty whiteboards need a Confluence API token (REST `POST /wiki/api/v2/whiteboards`). The MCP has no whiteboard tools.
- **Orient plan sign-off:** `wp plan set-status orient --plan mcp-system-lens-and-correct-service-metadata --status complete`, once the other session's `desk/gnome-extension` files are committed.
- **Datadog MCP config** uses a deprecated endpoint; switch it to `/v1/mcp`.
- **R5 (Fuse billing):** confirm site auto-commit and upload per Selector business, or have selector-adapter commit.
- **Owed for answers** (needs central DB or Tech Services):
  - per-carrier exact volumes (SQL on the Volumes page);
  - the live V4-Server-IE jobs;
  - REG_STATUSES (`SITE_REG = 2`), the CUST_SCRIPTS live rows, and AUTO_UPDATE per site;
  - the billing run timetable and `BILL_ON_SCAN = 2`.

## Next up
1. **POD carrier table** (approved: "continue from the POD service"). Put this table into `Engineering/gfs-pod-service/known-context.md` (or the architecture if there is one) and into MPK 353206310 Carrier Integration Uses (the Proof of delivery row or a sub-table). House style applies.

   Facts, verified 6 Nov on the laptop from `GFS POD` repo `811007e` (`src/pod-service/load-services.js`, `src/config.js`) and the prod manifest `pod-server/pod-service.yaml`:

   | Carrier | How it gets the POD | Requests, 15 days to 6 Nov (Datadog `gfs.gfs_pod_service.*`) |
   | --- | --- | --- |
   | DHL Parcel UK (UK Mail) | DHL Parcel UK REST API (`api.dhl.com/parceluk`); prod flag `DHLECOMMERCEUK_USEINSTEADOFUKMAIL=true` switches it off the old UK Mail SOAP; images via internal `dhl-pod-images` service | ~17.6k |
   | DPD | DPD customer REST API (`api.customers.dpd.co.uk`), per-contract credentials | ~2.3k |
   | UPS | UPS Track API, OAuth, GFS client (k8s secret) | 865 |
   | Evri (Hermes) | Evri client-tracking API; token from `evri-auth-facade` (same token as the Evri connectors) | 95 |
   | DPD Local | same code as DPD | 78 |
   | Amazon Logistics UK | via `amazon-logistics-proxy-internal` (the copy running with auth off) | 12 |
   | BJS | scrapes BJS ePOD web pages and the signature image (not an API) | 1 |
   | Yodel | Yodel tracking API, OAuth | 0 |
   | Panther | Panther order API, plus the portal for PDFs | 0 |
   | Tuffnells | Tuffnells POD SOAP service | 0 |
   | FedEx | FedEx Track API, OAuth | 0 |

   - **Also loaded:** `MOCKCARRIER` (a test carrier, in prod).
   - **Not loaded:** a DHL Express module (prod URL is literally `'???'`).
   - **Credentials:** per-contract credentials come from the legacy `gfs-carrier-credentials` service (not `carrier-credentials-manager`).
   - **No POD support despite volume:** Royal Mail (busiest proxied carrier), Nightfreight/DX, Parcelforce, GFS International, InPost, Coll8, OCS, Exelot. **UNKNOWN:** whether some of these carry POD fields inside tracking events (e.g. a Royal Mail webhook signatory).
   - **Skew:** DHL Parcel UK is ~85% of POD requests against ~22% of measurable volume.
   - **Anchors:** the VM can't clone `gfs-pod` (no Azure DevOps SSH access), so don't re-anchor `gfs-pod-service` docs with `wp verify`. Edit `known-context.md`, which is exempt from anchors, or note that a re-anchor is owed from the laptop.
2. Then stop, and DM Harry a summary.

## How work is done here
- **Confluence house style:** high signal, plain words, no slop words; tables for state; security findings class-level only (specifics go to the security ticket).
- **Confluence mechanics:** `mcp__Atlassian__getConfluencePage` with `contentFormat: markdown`, edit, then `updateConfluencePage` with markdown and a `versionMessage`. For rich HTML pages (overview, feature sheet, interface), round-trip as HTML after reading `getContentFormatGuide`. Never drop existing content.
- **Waypoint:** `wp = python3 ~/.claude/waypoint/wp.py`. Lint overviews and architectures with `node ~/.claude/skills/explain/lint-explainer.mjs <doc> --mode overview|architecture`. Use `orient-flow` diagrams (never mermaid). Mark dated figures `(snapshot YYYY-MM-DD)`. Finish with `wp index`.
- **Don't** PR or edit Tech Services repos (`ilg-tech-services/*`, e.g. the knowledge vault). Harry said leave them alone.
- **Never print secrets:** name the secret or file.
- **Log the session** in `Tasks/` (one record per session).

## On the target
Checked 15:10Z:
- **Has:** Claude 2.1.319, credentials present, auto mode on; MCP servers Atlassian, ado-local-mcp, ado-remote-mcp, datadog, fuse, github, orient, slack, snap and terraform. Atlassian and Datadog may need `/mcp` OAuth if not already signed in.
- **Repos present:** `~/projects/orient`, `~/code/merak/carrier-playground`, `~/code/fuse/selector-adapter` (cloned now).
- **Missing:** `~/code/apiky-survey/*` and `~/code/selector/*` (laptop only). **No Azure DevOps SSH access:** `git clone` of `globalfreightsolutions/GFS POD` was denied. Next up 1 doesn't need code.

## Gotchas
- **Azure DevOps:** `git ls-remote` against a non-existent ADO repo hangs, so list repos with the ADO MCP instead. The `ado-local-mcp` org is `globalfreightsolutions`; the Selector repos live in `globalfreightsolutons-legacy`, which it can't reach.
- **Orient service headers** used to show `owner=bifrost` (a stale sidecar). Fixed in `b6e3fa7`, so trust the headers now.
- **Evri cutover:** the Evri webhook is in shadow, and turning publish on won't backfill. While both run, connector and webhook events double-feed `raw_tracking.v1`.
- **Royal Mail proxy logs name the wrong operation:** "Incoming request received" is create-label.
- **Client4 doesn't use FTP.** The ~194 "FTP" grep hits are `ZeroLeftPad`. Pre-advice goes from V4-Server-IE over plain FTP.
- **CSS repo vs CSS-Enterprise:** the CSS repo is the live line (4.50.7.0). CSS-Enterprise is a stalled 2025 refactor fork, though the Tech Services vault says otherwise.
- **The commit hook** (`~/.claude/hooks/comment-density.sh`) blocks multi-line comment blocks in commits.

## Closed since handover
| When (UTC) | Work | Result |
| --- | --- | --- |
