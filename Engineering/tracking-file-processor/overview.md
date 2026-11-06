---
tags:
- waypoint
- tracking-file-processor
title: tracking-file-processor — overview
thesis: tracking-file-processor turns carrier tracking files into tracking events.
  It reads file_tracking.v1, matches each row to a GFS shipment, and publishes to
  raw_tracking.v1. It carried about 54k events in 15 days, the third and smallest
  tracking path.
confidence: high
verified: '2026-11-06'
verified_paths:
- index.js
verified_sha: e6da4bf
---
# tracking-file-processor — overview

```orient-bluf
{ "v": 1, "bluf": "tracking-file-processor turns carrier tracking files into tracking events. It reads file_tracking.v1, matches each row to a GFS shipment, and publishes to raw_tracking.v1. It carried about 54k events in 15 days, the third and smallest tracking path.", "confidence": "high", "action": "none" }
```

## Responsibility
- Consumes `file_tracking.v1`, parses each carrier file, and matches rows against `shipments.v2.identified` [1].
- Publishes matched rows to `raw_tracking.v1`. A retry job re-processes rows that failed.

## In prod (snapshot 2026-11-06, 15 days)
- About 54k events published, by its own count. On `raw_tracking.v1` the file carriers total 61k: DX Freight 30.2k, BJS 15.7k, DPD NL 9.7k, Coll8 3.9k, OCS 1.4k. **ASSESSED:** the gap is retries and events also arriving another way.
- 12.4k processing errors logged, of which the retry job later published 7.0k.
- Exelot and DPD DE have feeds configured, but sent no files.

## Neighbours

```orient-flow
{ "v": 1, "title": "tracking-file-processor in context",
  "nodes": [
    { "id": "f", "label": "file-ingestion-ftp-proxy", "kind": "service" },
    { "id": "ft", "label": "file_tracking.v1", "kind": "topic" },
    { "id": "t", "label": "tracking-file-processor", "kind": "service", "tone": "accent" },
    { "id": "sid", "label": "shipments.v2.identified", "kind": "topic" },
    { "id": "rt", "label": "raw_tracking.v1", "kind": "topic" }
  ],
  "edges": [
    { "from": "f", "to": "ft" },
    { "from": "ft", "to": "t" },
    { "from": "sid", "to": "t", "label": "match rows" },
    { "from": "t", "to": "rt" }
  ] }
```

## Where the reference lives
- MPK *Carrier Egress Services* (353206337); the ECM workspace doc `backend/tracking-scan-pipeline.md` in `gfs-ecm/ecm-development`.

## What deliberately isn't here
- **Fetching files from carriers.** [[file-ingestion-ftp-proxy]] does that.

## Evidence
```orient-evidence
{ "v": 1, "items": [
  { "id": 1, "kind": "code", "ref": "index.js@e6da4bf" }
] }
```
