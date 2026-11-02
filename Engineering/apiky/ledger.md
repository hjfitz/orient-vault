---
tags: [waypoint, ledger]
---
# apiky — work ledger

Agent-facing. Newest first. What meaningful work happened here, and the
context a future agent needs. Not a diary, not release notes, not a diff.

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
