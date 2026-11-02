---
tags: [adhoc-task]
date: 2026-10-20
tldr: "Merged snap-adapter#298/#299 (FUSE-1298/1308), got them live on dev after INC-40 blocked the deploy, moved both to Ready for QA. Redis-init fix parked; prod gates untouched."
session_id: 9f71cd3a-85a2-4f83-8f20-1573bb5653d8
status: open
---
# Unblock FUSE-1298 and FUSE-1308 on dev after INC-40

## Outcome
#298 and #299 are squash-merged (`9cd175d57`, `65fb60641`) and Schuster approved both. Neither is on dev: `terraform-apply-dev` fails on both runs because new `snap-polling-service-dev` revisions fail the startup probe. A rebuild of last-good `1b834b8ba` fails the same way, so it isn't our code. Both zone-b dev Memorystore instances stopped reporting at about 06:30Z (`gcp.redis.clients.connected`).

Done 12:00Z: zone-b Redis recovered; the failed run couldn't be re-run (`already running`), so a dev-only `Manual Deploy` of master (run `39418108053`) put `65fb606` live as revision `00475` (image `dev-65fb606`, 100% traffic, "Dependency connected", "Server listening"). FUSE-1298 and FUSE-1308 are Ready for QA with caveat comments. No prod gate touched.

Owed:
- Neither change is exercised yet: no stock sync has run on the new revision (11:30 and 11:45 ticks found nothing due). Dev SNAP is failing for several businesses (404s, 524s), including chunks containing GADG; not isolated.
- The two prod Deploy runs (`39404582530`, `39405432882`) are still parked at `docker-push-prod`; approving one ships all of master.
- Parked fix: local branch `hjf/poller-bound-redis-init` (`c197539`, never pushed) bounds the Redis init and liveness PING. Don't ship it alone: network writes and deletes aren't gated while Redis is down and the config provider awaits them, so every poll would hang. Write gating belongs in `@gfs-bifrost/cache` first.
- Peer review requested on collector#114 and replay-service#96 (Schuster, FUSE-1257) and shopify-connector#335 (Matt Shaw, FUSE-1312).
- FUSE-1312: the flag `shopify-connector.api-cache-per-connector` is on in dev, so it doesn't explain Alex Pickard's shared-instance-ID finding. Still open.
