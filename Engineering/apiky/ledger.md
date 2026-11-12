---
tags: [waypoint, ledger]
---
# apiky — work ledger

Agent-facing. Newest first. What meaningful work happened here, and the
context a future agent needs. Not a diary, not release notes, not a diff.

## 2026-11-12 — Unblock the deploy: API lockfile registry and a valid Cloud SQL sslmode

Unblock the deploy: API lockfile registry and a valid Cloud SQL sslmode

Merged the 8-PR ApiKy UI rewrite stack (#5-#10, #12, #13) on 2026-11-12; the stack is on main but not in prod. Deploy has failed on every main push since the June dependency upgrade: the API lockfile pins 241 packages to the private JFrog proxy (npm ci E401), so the API image never builds. Second find: the Cloud SQL connection string says sslmode=disbale, which Prisma 5 ignored but the Prisma 7 pg adapter turns into TLS with CA verification (self-signed certificate, every query 500s). Fix is lockfile resolved URLs to registry.npmjs.org plus sslmode=no-verify; both verified against the built API image and a TLS Postgres. Prod still runs the 20 May build (ce1b407); the API upgrade (Prisma 7, Express 5) has never run in any environment. Dev plan job is separately broken (missing TF vars).

PR: gfs-hybrid-services/apiky#14

## 2026-10-09 — Rewrite the ApiKy UI on Next.js 16 and the ILG UI toolkit

Rewrite the ApiKy UI on Next.js 16 and the ILG UI toolkit

Draft 6-PR stack replacing the Pages Router app: App Router + TypeScript + @ilg-platform/ui-toolkit, marketing site removed, structured profile editor instead of raw JSON, client key rotation, member invite/remove, project settings and danger zone, profile page. Fixes a cross-project client write (any member could edit/delete any project's clients) and moves committed SMTP credentials to env. CI blocked: GH_ORG_TOKEN gets 403 on @ilg-platform packages. Separate PR clears the pre-existing red nightly (proxy-addr critical) and removes the never-working tf-output workflow.

PR: gfs-hybrid-services/apiky#5
PR: gfs-hybrid-services/apiky#6
PR: gfs-hybrid-services/apiky#7
PR: gfs-hybrid-services/apiky#8
PR: gfs-hybrid-services/apiky#9
PR: gfs-hybrid-services/apiky#10
PR: gfs-hybrid-services/apiky#12
