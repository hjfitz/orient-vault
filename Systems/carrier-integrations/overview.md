---
tags:
- system
- carrier-integrations
verified: '2026-11-06'
title: carrier-integrations — overview
thesis: "Carrier integrations are the services that move data between GFS and carriers. Ingress is a proxy per carrier that Selector calls to make labels. Egress is tracking coming back, by polling, webhook or file, into raw_tracking.v1: about 6.25M events in 15 days."
confidence: high
---
# carrier-integrations — overview

```orient-bluf
{ "v": 1, "bluf": "Carrier integrations are the services that move data between GFS and carriers. Ingress is a proxy per carrier that Selector calls to make labels. Egress is tracking coming back, by polling, webhook or file, into raw_tracking.v1: about 6.25M events in 15 days.", "confidence": "high", "action": "Before switching a carrier from polling to webhook, plan the connector switch-off: both feeds reach raw_tracking.v1 while both run." }
```

**Ingress (GFS to carrier).** Selector sends a request with the customer's ApiKy key. The proxy finds that customer's carrier credentials, calls the carrier, and returns a label. Most carriers don't use a proxy at all: Selector draws their labels and pre-advises them by file (system [[selector]]).

**Egress (carrier to GFS).** Three paths publish to one topic, `raw_tracking.v1`. Polling connectors on [[tracking-core]] carry about 5.44M events in 15 days. Webhooks carry about 215k (Royal Mail only). SFTP files carry about 54k (snapshot 2026-11-06).

**On request (proof of delivery).** [[gfs-pod-service]] calls the carrier live when the portal, Connect API or Nexus asks for a POD: about 21k requests in 15 days.

## Members

| Family | Services | Where they run |
| --- | --- | --- |
| Ingress proxies | [[royal-mail-proxy]], [[ups-proxy]], [[coll8-proxy]], [[bjs-proxy]], [[ocs-proxy]], [[exelot-proxy]], [[dpd-europe-proxy]], [[amazon-proxy]] | GKE prod-uk1, from Azure DevOps |
| Ingress proxies on Cloud Run | [[fedex-proxy]], [[inpost-proxy]] | Cloud Run, from GitHub |
| Ingress rewrite (dev only) | [[carrier-proxies]] | Cloud Run dev |
| Polling engine | [[tracking-core]] | GKE, namespace fenghuang |
| Polling connectors | `connectors-*`: amazon, dhlparcel, dpd (also DPD Local), hermes, hermesps, international, ups, dhlexpress, inpost, fedex, plus idle collectplus, panther, yodel, and switched-off hdnl, tuffnells | GKE, namespace fenghuang |
| Webhooks | [[tracking-webhooks]], [[tracking-webhook-royal-mail-sapient]] | Cloud Run |
| Files | [[file-ingestion-ftp-proxy]], [[tracking-file-processor]] | GKE |

## Neighbours

```orient-flow
{ "v": 1, "title": "carrier-integrations in context",
  "nodes": [
    { "id": "sel", "label": "Selector", "sub": "CSS, Client4", "kind": "external" },
    { "id": "ak", "label": "ApiKy", "sub": "key to customer profile", "kind": "external" },
    { "id": "px", "label": "Carrier proxies", "kind": "service", "tone": "accent" },
    { "id": "car", "label": "Carriers", "kind": "external" },
    { "id": "eg", "label": "Connectors, webhooks, files", "kind": "service", "tone": "accent" },
    { "id": "sid", "label": "shipments.v2.identified", "kind": "topic" },
    { "id": "rt", "label": "raw_tracking.v1", "kind": "topic" },
    { "id": "ecm", "label": "ECM status deriver", "sub": "portal, Connect API", "kind": "external" }
  ],
  "edges": [
    { "from": "sel", "to": "px", "label": "label request" },
    { "from": "px", "to": "ak" },
    { "from": "px", "to": "car" },
    { "from": "car", "to": "eg", "label": "tracking" },
    { "from": "sid", "to": "eg", "label": "what to track" },
    { "from": "eg", "to": "rt" },
    { "from": "rt", "to": "ecm" }
  ] }
```

Fuse's selector-adapter and Parcel Portal reach the proxies only through Selector's CSS [1].

## Where the reference lives
- [[architecture]] covers the proxy anatomy, the three tracking paths, coverage by carrier and credential patterns. [[known-context]] covers owners, volumes, the Evri cutover and risks.
- Confluence MPK *Carrier Services* (353468499) and its children [2].

## What deliberately isn't here
- **Selector and pre-advice files.** System [[selector]].
- **The ECM pipeline after `raw_tracking.v1`.** Status derivation, consignment stores, portals.
- **selector-rest-proxy.** It fronts CSS, not a carrier.
- **gfs-pod-service and evri-auth-facade.** Source not surveyed; mentioned in [[known-context]].
- **Mock copies.** `ilg-merak/carrier-playground`.

## Evidence
```orient-evidence
{ "v": 1, "items": [
  { "id": 1, "kind": "doc", "ref": "Systems/selector/architecture.md" },
  { "id": 2, "kind": "doc", "ref": "Confluence MPK 353468499 Carrier Services" }
] }
```
