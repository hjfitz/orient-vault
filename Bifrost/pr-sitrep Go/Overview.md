---
title: "pr-sitrep Go — Overview"
status: planning
verdict: go
owner: "Harry Fitzgerald"
services: ["fuse-devtools"]
created: "2026-10-29"
updated: "2026-10-29"
tags: [bifrost, pr-sitrep, golang, migration]
---
# pr-sitrep Go — Overview

## Deliverables
- [[pr-sitrep Go/Migration State|Migration State]]: the live source of truth for progress.
- [[pr-sitrep Go/Port Design|Port Design]]: the file map, Go layout table and byte-parity hazard list.
- `apps/pr-sitrep` in `gfs-bifrost/fuse-devtools`, rewritten in Go and serving `pr-sitrep-prod` (`bifrost-prod-global1`). It posts the weekday 09:00 sitrep to #bifrost-forge.

## Verdict
**Go.** This rides on three things:
- byte-identical `GET /api/v1/sitrep` output in all three formats, on two separate days (G1);
- a cutover window after that day's TS post (G2);
- the G3 merge refusal ported exactly.

## Why this needs a programme
It's about 6k lines of Go and tests against a 600-line PR target, so it ships as eight stacked PRs. pr-sitrep posts to a shared channel on a schedule, and nobody can invoke it by hand, so the only proof in prod is the next morning's run. A parity miss shows up in public as a wrong or doubled post. The work also spans several sessions with a calendar gate, which needs a ledger rather than one plan.

## Strategy
- Build Go at `apps/pr-sitrep-go/` behind the on-push path filter. Prod can't change until the move.
- Port the code bottom-up: skeleton, classifier, renderers, adapters, services, HTTP. Each unit carries its TS spec cases as characterisation tests with identical names.
- Prove parity locally against live PRs, bracketed TS/Go/TS.
- Cut over in one revertable PR (X1) that `git mv`s Go into `apps/pr-sitrep`. The image is a Terraform variable, so the existing on-push workflow builds and deploys it with no Terraform change.
- **Rollback:** `gcloud run services update-traffic` back to the last TS revision, revert X1, then `update-traffic --to-latest`.

## Scar tissue
- Behaviour is ported as-is, including the double-post-on-retry hazard. Same-day idempotency is F1, after cutover.
- Declared non-parity: Express ETag/304, `X-Powered-By`, case-insensitive routing, the HTML 404 page, and `stack` in non-prod error bodies.
- fuse-devtools stays polyglot. Go is the convention for this app, not a repo-wide rule.

## Next
`S1`, the Go skeleton, driven with `waypoint-programme`.
