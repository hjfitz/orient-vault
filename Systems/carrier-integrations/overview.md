---
tags:
- system
- carrier-integrations
verified: '2026-11-06'
title: carrier-integrations — overview
thesis: "Carrier integrations move data between GFS and carriers, named from GFS's side. Egress is a proxy per carrier that Selector calls to make labels. Ingress is what comes back: tracking by polling, webhook or file into raw_tracking.v1 (about 6.25M events in 15 days), and proofs of delivery fetched on request."
confidence: high
---
# carrier-integrations — overview

```orient-bluf
{ "v": 1, "bluf": "Carrier integrations move data between GFS and carriers, named from GFS's side. Egress is a proxy per carrier that Selector calls to make labels. Ingress is what comes back: tracking by polling, webhook or file into raw_tracking.v1 (about 6.25M events in 15 days), and proofs of delivery fetched on request.", "confidence": "high", "action": "Before switching a carrier from polling to webhook, plan the connector switch-off: both feeds reach raw_tracking.v1 while both run." }
```

**Egress (GFS to carrier).** Selector sends a request with the customer's ApiKy key. The proxy finds that customer's carrier credentials, calls the carrier, and returns a label. Most carriers don't use a proxy at all: Selector draws their labels and pre-advises them by file (system [[selector]]).

**Ingress (carrier to GFS).** Three paths publish to one topic, `raw_tracking.v1`. Polling connectors on [[tracking-core]] carry about 5.44M events in 15 days. Webhooks carry about 215k (Royal Mail only). SFTP files carry about 54k (snapshot 2026-11-06).

**Ingress on request (proof of delivery).** [[gfs-pod-service]] calls the carrier live when the portal, Connect API or Nexus asks for a POD: about 21k requests in 15 days.

## Members

| Family | Services | Where they run |
| --- | --- | --- |
| Egress proxies | [[royal-mail-proxy]], [[ups-proxy]], [[coll8-proxy]], [[bjs-proxy]], [[ocs-proxy]], [[exelot-proxy]], [[dpd-europe-proxy]], [[amazon-proxy]] | GKE prod-uk1, from Azure DevOps |
| Egress proxies on Cloud Run | [[fedex-proxy]], [[inpost-proxy]] | Cloud Run, from GitHub |
| Egress rewrite (dev only) | [[carrier-proxies]] | Cloud Run dev |
| Polling engine | [[tracking-core]] | GKE, namespace fenghuang |
| Polling connectors | `connectors-*`: amazon, dhlparcel, dpd (also DPD Local), hermes, hermesps, international, ups, dhlexpress, inpost, fedex, plus idle collectplus, panther, yodel, and switched-off hdnl, tuffnells | GKE, namespace fenghuang |
| Connector support | [[evri-auth-facade]]: one cached Evri token for connectors-hermes and connectors-hermesps | GKE prod-uk1, from Azure DevOps |
| Webhooks | [[tracking-webhooks]], [[tracking-webhook-royal-mail-sapient]] | Cloud Run |
| Files | [[file-ingestion-ftp-proxy]], [[tracking-file-processor]] | GKE |
| On-request POD | [[gfs-pod-service]]: API and subscriber, one module per carrier | GKE prod-uk1, from Azure DevOps project GFS POD |

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
- Confluence MPK *Carrier Services* (353468499) and its children [2]. Egress is 353697822 and Ingress is 353206337, with *Proof of Delivery Service* (353861642) under Ingress.
- How a shipment moves through ECM's events, label to POD: [[2026-11-06-life-of-a-shipment-through-ecm]]. Why that event world is hard to change: [[2026-11-06-ecm-event-world-where-its-a-mess]].

## What deliberately isn't here
- **Selector and pre-advice files.** System [[selector]].
- **The ECM pipeline after `raw_tracking.v1`.** Status derivation, consignment stores, portals.
- **selector-rest-proxy.** It fronts CSS, not a carrier.
- **gfs-smart-pod-service.** Azure DevOps marks its repo disabled, and prod config comments it out.
- **Mock copies.** `ilg-merak/carrier-playground`.

## Evidence
```orient-evidence
{ "v": 1, "items": [
  { "id": 1, "kind": "doc", "ref": "Systems/selector/architecture.md" },
  { "id": 2, "kind": "doc", "ref": "Confluence MPK 353468499 Carrier Services" }
] }
```
