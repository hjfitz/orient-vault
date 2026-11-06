---
tags:
- system
- carrier-integrations
verified: '2026-11-06'
title: carrier-integrations — known context
---
# carrier-integrations — known context

From the 5–6 Nov 2026 carrier surveys (code, prod manifests, Cloud Run, Datadog, Jira). No interview: claims not confirmed by a person are marked inferred. Claims marked `(snapshot …)` age out.

## Owners
- **Proxies and webhooks:** changed on CID tickets by Carrier Integrations: Daniel Grzenia, Chris Mulder, John Finney. John Finney owns the Evri webhook work (CID-315). The `owner: carrier-integrations` in each `waypoint.yaml` is inferred.
- **Connectors, tracking-core and the file path:** the fenghuang / ECM side. Owner unconfirmed; `owner: ecm` is inferred.
- **gfs-pod-service:** team "carriers" in ECM's `repos.json`, in its own Azure DevOps project, GFS POD. John Finney makes most commits.
- **evri-auth-facade:** one commit, by Harry Fitzgerald (2025-05). `owner: ecm` is inferred.

## Volumes (snapshot 2026-11-06, 15 days)
- **Ingress:** Royal Mail about 29.6k labels; UPS about 6.1k. Most GFS volume never touches a proxy: Selector draws the label and pre-advises by file.
- **Egress:** about 6.25M events into `raw_tracking.v1`: polling 5.44M, webhook 215k, files 54k.
- **Polling cost:** about 142M carrier calls for 5.44M new events, roughly 26 calls per event. About 7M calls failed:
  - DHL Parcel UK's invalid-credentials error never pauses (368k wasted calls);
  - Evri returned 598k 403s;
  - DHL Express is rate-limited on about 10% of calls.
- **POD:** 20,978 requests, 17,607 of them DHL Parcel UK; 25,878 request errors. The POD subscriber read about 7.8M messages.
- **Evri token:** the facade served 1,347 token requests and refreshed from Evri 15 times.

## Polling to webhooks
- Royal Mail has always been webhook-only.
- **Evri (CID-315, In Progress):**
  - The webhook runs in shadow from the `tracking-webhooks` monorepo.
  - Go-live needs four things: Evri sending all customers (about 25% today), account-ID reconciliation, a mapping review, and publish on.
  - Then about 2 hours alongside the connectors before connectors-hermes and connectors-hermesps are switched off.
- **InPost:** PR #2, not deployed.
- **No webhook plan was found** for the biggest polled carriers: DHL Parcel UK, DPD Local, DPD, Amazon, UPS.

## Risks (class-level; specifics belong on the security ticket)
- Several proxies log full carrier payloads with personal data, and one logs a carrier token.
- One internal proxy route has no authentication.
- One new route takes the customer from the request, not the caller's key.
- Coll8 echoes upstream error detail back to the caller.
- Two proxies ignore their configured ApiKy URL through a typo.
- One connector reaches its service over plain HTTP.
- gfs-pod-service's v2 API checks no token. It's safe only while no ingress routes to it.
- The POD ingress path rule isn't bound to its host.
- evri-auth-facade's caller auth is off by flag, with a placeholder key. It has no ingress.

## Duplicates and dev copies
- **Seven carriers have two codebases.** The Azure DevOps copy serves prod; GitHub copies are dev only, behind, or idle.
- **Royal Mail and BJS:** the Azure DevOps copy is the newer one.
- **Mock copies** of the Royal Mail, UPS, Coll8 and FedEx proxies live in `ilg-merak/carrier-playground`, at `<carrier>.mocks.merak.freightops.dev`.

## Unknowns
- Where the prod Amazon proxy's source lives (image `gfs-amazon-logistics-proxy`).
- The prod etcd polling values and the `untracked` list.
- Who owns the connectors and tracking-core.
- The feed list for `file-ingestion-ftp-proxy`.
- Why POD request errors (25.9k) exceed requests (21.0k); not-found PODs are a likely part.
- Whether anything still calls the public POD v1 API.
- When gfs-pod-service moves from the legacy `gfs-carrier-credentials` to `carrier-credentials-manager`.
- Whether evri-auth-facade retires with the Evri connectors at CID-315 go-live.
- Which GFS customer is behind each Royal Mail, BJS and FedEx account ID.
