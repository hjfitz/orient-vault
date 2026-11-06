---
tags:
- waypoint
- ups-proxy
title: ups-proxy — overview
thesis: 'ups-proxy is the UPS ''stepping stone'': Selector still builds UPS''s legacy
  XML, and the proxy forwards it unchanged to UPS under GFS''s own OAuth token. That
  kept old Selector sites working when UPS moved to OAuth. It also mounts JSON V2
  routes that get no traffic.'
confidence: high
verified: '2026-11-06'
verified_paths:
- src/startup.js
- src/auth.js
verified_sha: bacc881
---
# ups-proxy — overview

```orient-bluf
{ "v": 1, "bluf": "ups-proxy is the UPS 'stepping stone': Selector still builds UPS's legacy XML, and the proxy forwards it unchanged to UPS under GFS's own OAuth token. That kept old Selector sites working when UPS moved to OAuth. It also mounts JSON V2 routes that get no traffic.", "confidence": "high", "action": "Keep route matching case-insensitive: CSS and Client4 send PascalCase paths such as ShipConfirm." }
```

## Responsibility
- **Stepping stone** (`/api/stepping-stone/*`): ShipConfirm, ShipAccept, Void, Locator and LabelRecovery, passed through as XML [1].
- **V2 JSON routes** (`/api/v2`): create label, cancel, get label and access points, mapped to UPS's JSON APIs. Mounted in prod, but no traffic in 15 days [1].
- **One GFS OAuth client** for every customer, token cached for its lifetime minus 60 seconds [2].

## Why it exists separately
GFS can't upgrade about 1,000 Selector sites together. Moving UPS auth into one proxy meant no site needed changing.

## Neighbours

```orient-flow
{ "v": 1, "title": "ups-proxy in context",
  "nodes": [
    { "id": "css", "label": "CSS", "sub": "UPSProcedures.cs", "kind": "external" },
    { "id": "c4", "label": "Client4", "sub": "uUPSClient.pas", "kind": "external" },
    { "id": "p", "label": "ups-proxy", "sub": "ups.gfsdeliver.com", "kind": "service", "tone": "accent" },
    { "id": "ak", "label": "ApiKy", "sub": "validates the key only", "kind": "external" },
    { "id": "ups", "label": "UPS", "sub": "OAuth, XML and JSON APIs", "kind": "external" }
  ],
  "edges": [
    { "from": "css", "to": "p", "label": "legacy XML" },
    { "from": "c4", "to": "p", "label": "legacy XML" },
    { "from": "p", "to": "ak" },
    { "from": "p", "to": "ups", "label": "XML + bearer token" }
  ] }
```

## Where the reference lives
- [[architecture]] and [[known-context]] here; the repo's `api/swagger.yaml`.
- The dev rewrite on api-host-framework: [[carrier-proxies]] `apps/ups-proxy`.

## What deliberately isn't here
- **UPS tracking.** connectors-ups polls it.
- **Per-customer UPS accounts.** GFS assigns UPS accounts; the proxy uses one OAuth client.

## Evidence
```orient-evidence
{ "v": 1, "items": [
  { "id": 1, "kind": "code", "ref": "src/startup.js@bacc881:L34-L35" },
  { "id": 2, "kind": "code", "ref": "src/auth.js@bacc881" }
] }
```
