---
tags:
- waypoint
- file-ingestion-ftp-proxy
title: file-ingestion-ftp-proxy — overview
thesis: file-ingestion-ftp-proxy is a CronJob that, every 20 minutes, collects carriers'
  tracking files from their SFTP servers into Cloud Storage and announces each on
  file_tracking.v1. It runs the fenghuang-ftp-proxy image, whose README still says
  the project is being archived.
confidence: moderate
verified: '2026-11-06'
verified_paths:
- index.js
verified_sha: 6c5e9fa
---
# file-ingestion-ftp-proxy — overview

```orient-bluf
{ "v": 1, "bluf": "file-ingestion-ftp-proxy is a CronJob that, every 20 minutes, collects carriers' tracking files from their SFTP servers into Cloud Storage and announces each on file_tracking.v1. It runs the fenghuang-ftp-proxy image, whose README still says the project is being archived.", "confidence": "moderate", "action": "Don't trust the README's archived status: the CronJob runs in prod." }
```

## Responsibility
- Polls carrier SFTP servers on a 20-minute schedule and copies tracking files to Cloud Storage [1].
- Feeds [[tracking-file-processor]] through `file_tracking.v1`.
- **ASSESSED:** carriers include DX Freight, DPD NL, DPD DE, Coll8, Exelot, OCS and BJS, from the file-tracking volumes. The feed list lives in config, not checked.

## In prod (snapshot 2026-11-06)
- CronJob `file-ingestion-ftp-proxy` in `prod-uk1-primary-cluster` (`deploy/k8s/fenghuang/tracking/`), schedule `*/20 * * * *`, image `fenghuang-ftp-proxy:prod-48483` [2].
- Repo `fenghuang/fenghuang-ftp-proxy`, last commit May 2025.

## Neighbours

```orient-flow
{ "v": 1, "title": "file-ingestion-ftp-proxy in context",
  "nodes": [
    { "id": "sftp", "label": "Carrier SFTP servers", "kind": "external" },
    { "id": "f", "label": "file-ingestion-ftp-proxy", "sub": "every 20 minutes", "kind": "service", "tone": "accent" },
    { "id": "gcs", "label": "Cloud Storage", "kind": "store" },
    { "id": "ft", "label": "file_tracking.v1", "kind": "topic" },
    { "id": "tfp", "label": "tracking-file-processor", "kind": "service" }
  ],
  "edges": [
    { "from": "f", "to": "sftp", "label": "poll" },
    { "from": "f", "to": "gcs" },
    { "from": "f", "to": "ft" },
    { "from": "ft", "to": "tfp" }
  ] }
```

## Where the reference lives
- The tracking-path view: `Systems/carrier-integrations/architecture.md`; MPK *Carrier Egress Services* (353206337).

## What deliberately isn't here
- **Parsing the files.** [[tracking-file-processor]] does that.

## Evidence
```orient-evidence
{ "v": 1, "items": [
  { "id": 1, "kind": "code", "ref": "index.js@6c5e9fa" },
  { "id": 2, "kind": "doc", "ref": "prod-uk1-primary-cluster deploy/k8s/fenghuang/tracking/file-ingestion-ftp-proxy.yaml" }
] }
```
