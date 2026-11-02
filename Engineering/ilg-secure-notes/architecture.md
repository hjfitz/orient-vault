---
tags:
- waypoint
- ilg-secure-notes
verified: '2026-10-13'
verified_sha: 67115b4
verified_paths:
- code/src
- iac/projects/ilg-secure-notes
- code/dockerfile
- code/package.json
- .github/workflows
- code/src/app/globals.css
title: ilg-secure-notes — architecture
thesis: A Next.js 15 app on public Cloud Run encrypts each note with AES-256-GCM into
  one GCS object, deletes it inside the reveal request at its last view or expiry,
  and relies on the unguessable id as the only reveal credential.
confidence: high
---
# ilg-secure-notes — architecture

```orient-bluf
{ "v": 1, "bluf": "A Next.js 15 app on public Cloud Run encrypts each note with AES-256-GCM into one GCS object, deletes it inside the reveal request at its last view or expiry, and relies on the unguessable id as the only reveal credential.", "confidence": "high", "action": "Keep the burn inside secretManager.get and keep reveal a POST behind a click, so a link previewer never consumes a note." }
```

## Guardrails

- [contract:G1] `POST /api/secrets` keeps its request and response shape. fuse-ui mints SFTP credential links through it, and the OpenAPI document is generated from the same Zod schema.
  — paths: code/src/app/api/secrets/route.ts, code/src/lib/openapi.ts
- [technical:G2] The burn happens inside `secretManager.get`, before the payload returns. Reveal stays a POST server action behind a button, so a GET on `/view` or a link preview never consumes a view.
  — paths: code/src/lib/secret.ts, code/src/actions/fetch-secret.ts, code/src/components/view-secret.tsx
- [technical:G3] New notes always use the `v2:` random-IV AES-256-GCM format. `CRYPTO_IV` only decrypts legacy blobs and never encrypts.
  — paths: code/src/lib/crypto.ts, code/src/lib/config.ts
- [technical:G4] Every `put` of an existing note passes the `expires-at` metadata again. A rewrite replaces custom metadata, and a note without it is treated as legacy and swept 30 days after creation.
  — paths: code/src/lib/secret.ts, code/src/lib/storage.ts
- [technical:G5] The note id is the only reveal credential. Never log an id, payload or decrypted text, and never put the Dockerfile's `GITHUB_TOKEN` outside the deps stage.
  — paths: code/src, code/dockerfile
- [technical:G6] `.brand-gradient` stays one combined `background-image` declaration. Splitting it into two classes silently blanks the backdrop, which ran white-on-white in prod for months.
  — paths: code/src/app/globals.css

## Where the app sits

The app is one Next.js 15 standalone container on Cloud Run. Browsers reach it through a global HTTPS load balancer, and fuse-ui calls the same host. [1][2]

```orient-flow
{ "v": 1, "title": "Routes and what guards them",
  "nodes": [
    { "id": "b", "label": "Browser", "sub": "no login", "kind": "external", "ev": [3] },
    { "id": "ui", "label": "fuse-ui", "sub": "x-api-key", "kind": "service", "service": "fuse-ui", "ev": [4] },
    { "id": "sch", "label": "Cloud Scheduler", "sub": "Bearer token", "kind": "external", "ev": [10] },
    { "id": "app", "label": "ilg-secure-notes", "sub": "Next.js 15, Cloud Run", "kind": "service", "service": "ilg-secure-notes", "tone": "accent", "ev": [1] },
    { "id": "sm", "label": "secretManager", "sub": "encrypt, burn, sweep", "kind": "step", "ev": [5] },
    { "id": "gcs", "label": "GCS notes bucket", "sub": "<id>.json per note", "kind": "store", "ev": [6, 9] }
  ],
  "edges": [
    { "from": "b", "to": "app", "label": "/, /view, /success, /api/docs" },
    { "from": "ui", "to": "app", "label": "POST /api/secrets" },
    { "from": "sch", "to": "app", "label": "POST /api/cleanup" },
    { "from": "app", "to": "sm" },
    { "from": "sm", "to": "gcs", "label": "put, get, delete, list" }
  ] }
```

Source layout:

```
code/src/
  actions/fetch-secret.ts      reveal server action
  app/
    page.tsx                   create form and its createSecret server action
    view/page.tsx              reveal page (noindex)
    success/page.tsx           link page (noindex)
    error/, not-found.tsx
    api/secrets/route.ts       POST, x-api-key
    api/cleanup/route.ts       POST, Bearer token
    api/docs/route.ts          GET, OpenAPI document, no auth
  components/                  create success view, reveal view, submit button
  lib/
    secret.ts                  SecretManager: add, get, sweepExpired
    crypto.ts                  AES-256-GCM
    storage.ts                 GCS read, write, delete, list
    config.ts                  lazy Zod env access, DOMAIN_BASE
    expiry.ts, limits.ts       presets and size caps
    openapi.ts                 request schema and OpenAPI document
iac/projects/ilg-secure-notes/ Cloud Run, GCS, load balancer, DNS, IAM, Secret Manager, Scheduler
```

## Inbound routes

| Route | Guard | Behaviour |
| --- | --- | --- |
| `/` (server action `createSecret`) | none | Creates a note from the form. Enforces the text cap, an expiry preset and the file cap [3] |
| `/view?id=` (server action `fetchSecret`) | none; the id is the credential | Shows a warning card. A click runs the reveal [7][8] |
| `/success?id=` | none | Shows the share link built from the browser origin |
| `POST /api/secrets` | `x-api-key` | Creates a note and returns `{ id, url }`, status 201 [4] |
| `POST /api/cleanup` | `Authorization: Bearer` | Deletes expired notes and returns `{ deleted }` [10] |
| `GET /api/docs` | none | Serves the OpenAPI 3.0 document |

Both `/view` and `/success` carry `noindex`. No route has a health endpoint. Cloud Run grants `run.invoker` to `allUsers` and sets ingress to all traffic, so the load balancer is a front, not a gate [1][2].

## Create, store, burn

```orient-flow
{ "v": 1, "title": "Life of a note",
  "nodes": [
    { "id": "c", "label": "Create", "sub": "form or API", "kind": "step", "ev": [3, 4] },
    { "id": "e", "label": "Encrypt", "sub": "AES-256-GCM, random IV", "kind": "step", "ev": [5, 11] },
    { "id": "s", "label": "Store", "sub": "<id>.json + expires-at", "kind": "store", "ev": [5, 6] },
    { "id": "r", "label": "Reveal click", "sub": "POST server action", "kind": "step", "ev": [7, 8] },
    { "id": "d", "label": "Delete", "sub": "last view or expiry", "kind": "step", "tone": "accent", "ev": [5] },
    { "id": "k", "label": "Sweep", "sub": "every 15 min", "kind": "step", "ev": [10, 12] }
  ],
  "edges": [
    { "from": "c", "to": "e" },
    { "from": "e", "to": "s" },
    { "from": "s", "to": "r" },
    { "from": "r", "to": "d", "label": "views hit 0, or expired" },
    { "from": "r", "to": "s", "label": "views left: rewrite", "style": "dashed" },
    { "from": "s", "to": "k" },
    { "from": "k", "to": "d", "label": "past expires-at" }
  ] }
```

1. **Create.** The id is a UUID without dashes. The payload is `{ text, file? }` as JSON, encrypted, and stored as `{ encrypted, viewsRemaining, createdAt, expiresAt }` in `<id>.json` with `expires-at` as custom metadata [5].
2. **Limits.** Text is at most 100,000 characters and a file at most 10 MB. Expiry is one of 1 hour, 24 hours, 7 days or 30 days, with 24 hours the default [13]. The API also caps `viewLimit` at 1 to 10 and checks `Content-Length` before buffering. The web form checks the expiry preset but not `viewLimit` [3][4].
3. **Reveal.** `fetchSecret` reads the object. A bad shape or an expired note deletes it and returns not-found. Otherwise it decrypts, then deletes at the last view or rewrites the object with one fewer view, then returns the payload [5][7].
4. **Cleanup.** The Scheduler job posts every 15 minutes with one retry and a 320 s deadline. `sweepExpired` lists the whole bucket and deletes each object past `expires-at`. A blob without that metadata expires 30 days after its GCS creation time [5][6][10].
5. **Backstop.** The bucket also deletes any object 30 days after its last write through a lifecycle rule. Versioning is off and public access prevention is enforced [9].

**ASSESSED** The reveal is a read-then-write with no lock or generation precondition. Two simultaneous reveals of a multi-view note can both read the same count, so the limit can be exceeded. Nothing in [5] or [6] serialises them.

## Encryption

New notes use AES-256-GCM with a random 12-byte IV. The stored string is `v2:` plus base64 of IV, ciphertext and 16-byte tag. A blob with no prefix is a legacy note encrypted under the fixed `CRYPTO_IV` and is decrypted with it. Legacy blobs carry no `expires-at`, so the sweep and the bucket lifecycle rule expire them 30 days after their last write [11][6][9]. `CRYPTO_KEY` must be 32 bytes of hex and `CRYPTO_IV` 16 bytes of hex, or `Crypto` throws on first use [11].

## Auth

- **Create API.** `x-api-key` compared with `timingSafeEqual` against `SECRETS_API_KEY`. An empty configured key fails config validation [4][14].
- **Cleanup.** `Bearer <token>` compared the same way. Terraform generates the token and puts it in the Scheduler header and in Secret Manager [10][9].
- **Reveal and web create.** No authentication. Possession of the id is the entire access control for reveal, and anyone can create a note.

## Secrets and configuration

| Variable | Source in prod |
| --- | --- |
| `GCS_BUCKET_NAME` | the Terraform bucket name |
| `CRYPTO_KEY`, `CRYPTO_IV`, `CLEANUP_TOKEN` | Secret Manager references. The Cloud Run service account holds `secretAccessor` on each [1][15] |
| `SECRETS_API_KEY` | a plain Cloud Run env value from a Terraform `random_bytes`, also a sensitive stack output |
| `ENVIRONMENT` | `var.env`, optional in the schema |

Config validates lazily, so a build needs no env. The Terraform-generated key, IV, token and API key all pass through Terraform state. **ASSESSED** Anyone who can read this stack's state or the Cloud Run revision can read `SECRETS_API_KEY`, and anyone who can read state can derive the encryption key. The state bucket's access list is outside this repo.

## UI toolkit

The app uses `@ilg-platform/ui-toolkit` for two `Select` controls (view limit, expiry) and for toasts (`sonner`, with the toolkit's `Toaster`). Neither `Select` renders an icon in its options, so the `SelectTrigger` icon-stacking bug in ui-toolkit does not affect it. A Radix-bridged hidden native `<select>` is what lets a toolkit `Select` submit a named value through a server-action form. If the create form changes, create a 2-view note, reveal it twice, and confirm the third view burns.

## Build and deploy

- Node 22, pnpm 9.15.9, Next 15.2.4, Biome 2.4.7. The server-action body limit is 12 MB [16].
- The Dockerfile has three stages and runs as a non-root user. The `GITHUB_TOKEN` build argument lives in the deps stage only, so it never reaches the runtime image [17].
- `code-quality.yaml` runs lint and build on pull requests and nightly. `tf-plan.yaml` posts a plan on pull requests [18].
- `deploy.yaml` runs on a push to `main` or `master`, and only `master` carries the workflow. It plans, builds and pushes the image, then applies with `-auto-approve` against prod. **ASSESSED** The `terraform-prod` environment gate sits on the image-push job, and the apply waits on it. The reusable workflow in `ilg-platform/github-actions` sets that gate [19].
- Cloud Run runs at least one instance. A Datadog `serverless-init` sidecar ships logs to both the GFS and ILG accounts. The app writes no logs of its own [1].

## Evidence

```orient-evidence
{ "v": 1, "items": [
  { "id": 1, "kind": "code", "ref": "iac/projects/ilg-secure-notes/cloud-run.tf@67115b4" },
  { "id": 2, "kind": "code", "ref": "iac/projects/ilg-secure-notes/iam.tf@67115b4" },
  { "id": 3, "kind": "code", "ref": "code/src/app/page.tsx@67115b4" },
  { "id": 4, "kind": "code", "ref": "code/src/app/api/secrets/route.ts@67115b4" },
  { "id": 5, "kind": "code", "ref": "code/src/lib/secret.ts@67115b4" },
  { "id": 6, "kind": "code", "ref": "code/src/lib/storage.ts@67115b4" },
  { "id": 7, "kind": "code", "ref": "code/src/actions/fetch-secret.ts@67115b4" },
  { "id": 8, "kind": "code", "ref": "code/src/components/view-secret.tsx@67115b4" },
  { "id": 9, "kind": "code", "ref": "iac/projects/ilg-secure-notes/gcs.tf@67115b4" },
  { "id": 10, "kind": "code", "ref": "code/src/app/api/cleanup/route.ts@67115b4" },
  { "id": 11, "kind": "code", "ref": "code/src/lib/crypto.ts@67115b4" },
  { "id": 12, "kind": "code", "ref": "iac/projects/ilg-secure-notes/scheduler.tf@67115b4" },
  { "id": 13, "kind": "code", "ref": "code/src/lib/expiry.ts@67115b4" },
  { "id": 14, "kind": "code", "ref": "code/src/lib/config.ts@67115b4" },
  { "id": 15, "kind": "code", "ref": "iac/projects/ilg-secure-notes/secrets.tf@67115b4" },
  { "id": 16, "kind": "code", "ref": "code/package.json@67115b4" },
  { "id": 17, "kind": "code", "ref": "code/dockerfile@67115b4" },
  { "id": 18, "kind": "code", "ref": ".github/workflows/code-quality.yaml@67115b4" },
  { "id": 19, "kind": "code", "ref": ".github/workflows/deploy.yaml@67115b4" }
] }
```
