---
tags:
- waypoint
- ilg-secure-notes
verified: '2026-10-13'
verified_sha: 67115b4
verified_paths:
- CLAUDE.md
- README.md
- code/src
- iac/projects/ilg-secure-notes
title: ilg-secure-notes — overview
thesis: 'ilg-secure-notes is a public one-time-secret service: it encrypts a note
  into GCS and burns it at its view limit or expiry, and it stays apart from fuse-ui
  so an open reveal surface never joins an authenticated tool.'
confidence: high
---
# ilg-secure-notes — overview

```orient-bluf
{ "v": 1, "bluf": "ilg-secure-notes is a public one-time-secret service: it encrypts a note into GCS and burns it at its view limit or expiry, and it stays apart from fuse-ui so an open reveal surface never joins an authenticated tool.", "confidence": "high", "action": "Do not push to master unverified. A push deploys to prod and no staging exists, so run the local end-to-end check in CLAUDE.md first." }
```

## Responsibility

- The app serves `https://ots.ilg.software` (GitHub repo `gfs-bifrost/one-time-secrets`). A visitor creates a note with an optional file and gets a link. The note burns at its view limit or expiry [1].
- It owns one API contract, `POST /api/secrets`. The `x-api-key` header guards it and `/api/docs` describes it [2].
- fuse-ui calls that API to mint a 24-hour link carrying a new SFTP connector's host and credentials. This stack exports the key as the sensitive `api_key` output for fuse-ui to read [3].
- **ASSESSED** fuse-ui's dev environment mints against production, because no dev instance exists. Source: [[known-context]], which the repo cannot confirm.
- Harry owns it personally, not a team.

## Why it exists separately

The reveal side has no authentication. Possession of the link is the only credential [4]. Anyone on the internet can also create a note [5].

fuse-ui and the other Fuse services assume an authenticated operator. Bundling this surface into one of them would put an open, anonymous endpoint beside that assumption. The separate stack keeps the trust boundary visible.

## Neighbours

```orient-flow
{ "v": 1, "title": "ilg-secure-notes in context",
  "nodes": [
    { "id": "people", "label": "Senders and recipients", "sub": "browsers, no login", "kind": "external", "ev": [4, 5] },
    { "id": "ui", "label": "fuse-ui", "sub": "mints SFTP credential links", "kind": "service", "service": "fuse-ui", "ev": [3] },
    { "id": "ots", "label": "ilg-secure-notes", "sub": "ots.ilg.software", "kind": "service", "service": "ilg-secure-notes", "tone": "accent", "ev": [2] },
    { "id": "gcs", "label": "GCS notes bucket", "sub": "encrypted blobs, 30-day lifecycle", "kind": "store", "ev": [6] },
    { "id": "sm", "label": "Secret Manager", "sub": "crypto key, legacy IV, cleanup token", "kind": "store", "ev": [7] },
    { "id": "sched", "label": "Cloud Scheduler", "sub": "cleanup every 15 min", "kind": "external", "ev": [8] }
  ],
  "edges": [
    { "from": "people", "to": "ots", "label": "create form, reveal link" },
    { "from": "ui", "to": "ots", "label": "POST /api/secrets, x-api-key" },
    { "from": "ots", "to": "gcs", "label": "put, get, delete" },
    { "from": "ots", "to": "sm", "label": "key at start-up", "style": "dashed" },
    { "from": "sched", "to": "ots", "label": "POST /api/cleanup, Bearer" }
  ] }
```

The service stores and deletes only encrypted blobs in GCS. It publishes nothing to Pub/Sub and calls no other Fuse service.

## Where the reference lives

[[architecture]] holds the code layout, the create-store-burn path, the auth model and the deploy chain. [[operations]] holds the prescribed verification sequence. [[known-context]] holds ownership and the dev-points-at-prod coupling.

Do not trust three sources:

- `README.md` still says Node 20, ESLint and "Push to main". The code uses Node 22, Biome and a `master` deploy.
- `CLAUDE.md` says the prod env values are plain Cloud Run variables. Three are Secret Manager references.
- `waypoint.yaml` says `observability: none`. A Datadog sidecar runs, though the app writes no logs itself.

## What deliberately isn't here

- **Staging.** The org's prod-only exception removes it. Local verification replaces it.
- **Retention.** The reveal path deletes a note at its last view or at expiry. Nothing keeps it longer [9].
- **User accounts.** Only the create API has a credential. The web form and the reveal are open.
- **Rate limiting or abuse controls.** None exist in the app or the load balancer [5].
- **Other consumers.** **UNKNOWN** whether anything besides fuse-ui calls `POST /api/secrets`. This repo contains no caller.

## Evidence

```orient-evidence
{ "v": 1, "items": [
  { "id": 1, "kind": "code", "ref": "CLAUDE.md@67115b4" },
  { "id": 2, "kind": "code", "ref": "code/src/app/api/secrets/route.ts@67115b4" },
  { "id": 3, "kind": "code", "ref": "iac/projects/ilg-secure-notes/outputs.tf@67115b4" },
  { "id": 4, "kind": "code", "ref": "code/src/actions/fetch-secret.ts@67115b4" },
  { "id": 5, "kind": "code", "ref": "code/src/app/page.tsx@67115b4" },
  { "id": 6, "kind": "code", "ref": "iac/projects/ilg-secure-notes/gcs.tf@67115b4" },
  { "id": 7, "kind": "code", "ref": "iac/projects/ilg-secure-notes/secrets.tf@67115b4" },
  { "id": 8, "kind": "code", "ref": "iac/projects/ilg-secure-notes/scheduler.tf@67115b4" },
  { "id": 9, "kind": "code", "ref": "code/src/lib/secret.ts@67115b4" }
] }
```
