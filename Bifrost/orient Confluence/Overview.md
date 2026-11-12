---
title: "orient Confluence — Overview"
status: active
verdict: go
owner: "hjf"
services: ["orient"]
created: "2026-11-12"
updated: "2026-11-12"
tags: [bifrost]
---
# orient Confluence — Overview

## Deliverables
- [[orient Confluence/Migration State|Migration State]] — the live source of truth for progress
- **The minimum Harry set (2026-11-12): tabs for Confluence spaces, "ideally fuse + merak at a minimum".** In the Notes workspace's space switcher, next to Notes, Incidents and Soaks, a **Fuse** tab and a **Merak** tab: browse the space's page tree, read pages rendered inside orient in the same shell as Notes, search the space, and jump to the page in Confluence. That is units C0 to C3. Links to Confluence pages found in notes and tickets then open the in-orient page (C4).
- Read-only first. Creating and editing Confluence pages from orient is a separate decision (C5, gated).

## Verdict
**Go, read-only.** It stands on the Notes workspace (the space switcher, tree, breadcrumbs, page view: N4b, N13, NV2) and on the Sync programme's cache and job runner (S0 live).

## Verified facts (2026-11-12)
- **Which spaces.** "Fuse" is the **Bifrost** space (key `Bifrost`, id `4587524`, a knowledge-base space): the `create-pr` skill writes the Fuse service changelog pages under spaceId 4587524. A space literally named "Fuse (Bifrost)" (key `Fuse`, id `4751364`) exists but is **archived**; it is not offered by default. **Merak** is "Merak Project" (key `MP`, web alias `MPK`, id `338526210`, global). Other candidates for later tabs: Product Management (`PM`, `219414577`), Data Solutions Team (`DST`), Site Reliability Engineering (`SRE`), Billing, Carrier Integrations Development (`CID1`). Space types differ (`global`, `knowledge_base`, `collaboration`), so a space list must not filter on type; personal spaces (`~…`) are in the list and are skipped.
- **The credential reaches Confluence.** orient already holds Jira REST credentials (`jiraCredentials()` and `jiraApiBase()` in `src/config.ts`: `JIRA_API_EMAIL` and `JIRA_API_TOKEN` from the environment or `~/.secrets`, and the site from the vault config `external.jiraBase`). A read-only probe through those functions against the same site returned HTTP 200 for `GET /wiki/api/v2/spaces`, `GET /wiki/api/v2/spaces/{Bifrost id}/pages`, `GET /wiki/api/v2/spaces/{Merak id}/pages` and the v1 CQL search `GET /wiki/rest/api/search`. No new token or scope is needed. The probe printed only status codes and counts.
- **orient has no Confluence client today.** The only references are tool names in the headless runs' allowlists (`src/domain/{ticket,epic,slack}-run.ts`, the Atlassian MCP).
- **Content format.** Confluence pages are stored as ADF (Atlassian Document Format) and as storage-format XML. The v2 API returns either (`body-format=atlas_doc_format`). Macros are ADF `extension` nodes; the Lucid diagram macro is `extensionKey: lucidchart` with the document URL in its parameters (from the `c4-diagrams` skill). The Atlassian MCP **drops macros when a page is edited through markdown**, which is why writing back is a separate, careful decision (C5).

## Strategy
- **One more kind of page in the same shell.** The Notes workspace already has a tree, breadcrumbs, a page view and a scoped search. A Confluence tab provides the same shape from a Confluence adapter instead of the vault: a lazily loaded page tree, a page view rendered from ADF, and CQL search.
- **Read-only by construction.** The client can only `GET`, to one allowlisted host, with no redirects off the site, and size and time caps.
- **Our own ADF renderer, with an allowlist.** Unknown nodes and macros become a visible labelled placeholder with an "Open in Confluence" link, never raw HTML, never dropped silently.
- **Spaces are configuration.** `confluence.spaces` in the vault config: a tab label, a key and an id for each, with Fuse and Merak as the defaults, so PM, DST or SRE are one line each.
- **Series, main checkout, one builder at a time across all programmes** (`CLAUDE.md:22`). Order proposed: after the writer core and NV2 (the shared sidebar and tree), before the whiteboard canvas.

## Scar tissue
See the State doc. The short form: no real Confluence content in the repo, its tests, its logs or a disk snapshot (the repo is on a personal GitHub account and the pages are company documents); everything Confluence returns is untrusted; read-only.

## Next
C0, driven by `waypoint-programme`.
