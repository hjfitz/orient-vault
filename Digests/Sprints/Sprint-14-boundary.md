---
tags: [sprint-digest]
sprint_closed: Sprint 13
sprint_closed_window: 2026-07-06 → 2026-07-20
sprint_started: Sprint 14
sprint_started_window: 2026-07-27 → 2026-08-10
posted: '2026-07-27'
channel: bifrost-general (C098LD5PS95)
title: Sprint 13 → Sprint 14 boundary digest
---

# Sprint 13 → Sprint 14 boundary digest

First run of the `sprint-digest` skill.

- Retro post: https://gfsdeliver-eng.slack.com/archives/C098LD5PS95/p1785150247693109
- Look-ahead post: https://gfsdeliver-eng.slack.com/archives/C098LD5PS95/p1785150266848859

---

## Post 1 — Sprint 13 retro (4,725 chars)

**Sprint 13 wrapped** (6 → 20 Jul). What went out, how prod held up, and some of the engineering behind it.

### 📊 At a glance
- **120 PRs merged** — plus 69 automated dependency updates
- **20 tickets completed**, 6 more reached QA
- **2 epics reached QA-ready** — Returns (RGA) and Confirmation Mapping
- **Pick/Pack confirmations built end to end** — 12 tickets across 9 repos
- **Zero incidents, zero platform failures in prod**
- **11 repos** moved onto the new security-scanning workflows

### 📈 Reliability in production
- API gateway served 5,033 requests with no platform failures (dev counterpart recorded 6, so the metric was live)
- Snap polling made 1.01M successful warehouse calls, no failures recorded (dev counterpart recorded 18)
- Record creates into Snap at 95.4% call success — 30,238 succeeded, 1,456 failed
- No incidents

### 🚀 What went out
Pick/Pack confirmations end to end · failed confirmations recoverable via failure topic + Retry Queue + replay · duplicate confirmations fixed at the root (queue-id claim + idempotent creates) · Returns and Confirmation Mapping both reached QA · Shopify token revalidation · channel/connector on every log line + ingest capture preserved onto ack/failure · recent/pinned customers + Test Mapping dry-run.

### ⚙️ Engineering nuggets
`source` named the service not the channel · the dedupe claim deliberately never retries · 4xx were counted as platform errors · confirmation-made traffic diluted create success rate · outbound-queue parser crash diagnosed by logging raw items · Snap circuit breaker never self-closed · fuse-ui per-PR preview environments.

---

## Post 2 — Sprint 14 look-ahead (4,635 chars)

**Sprint 14 is underway** (27 Jul → 10 Aug).

### 🚀 What Fuse gains
Smart Routing of Confirmations (11 tickets) — confirmations return only via the originating channel, with a broadcast opt-in for manual-origin orders · Work Orders become a Fuse capability (22 tickets) — WO/WOC/FGR across SFTP + API · Mapping Template Library (4 tickets) — ILG-managed, copy-on-apply, retires the code-managed templates · raw customer payload stored and surfaced for support · every record gets a real accepted/rejected status · weight and dimensions return to goods-out confirmations.

### ⚙️ Engineering nuggets
Collector has never recorded success (`lifecycle.status` always null; publishers already emitting) · status transitions need rank-guarding against out-of-order delivery · dual-publish → migrate → decommission for PO/SO onto the cross-entity vein · routing via Terraform subscription filters, never app code · broadcast flag needed no new plumbing on `BACKEND_CONFIG` · copy-on-apply means templates have no consumers · the hardcoded templates already are the data · the weight/dimensions ticket inherits a root cause already disproved.

---

## Evidence

- **Sprint 14 board**: 76 issues — 42 To Do (41 Ready for Development + 1 Ready for Refinement), 13 in-flight, 5 Done, 16 Won't do. Every To Do item was in a sprint for the first time except FUSE-995.
- **Look-ahead scope**: To Do column only. Epics — FUSE-927 Smart Routing (11), FUSE-655 Work Order Flow (22), FUSE-1004 Template Library (4), FUSE-1047 raw payload, FUSE-1024 lifecycle status, FUSE-1009 weight/dims, FUSE-995 logging spec (refinement), FUSE-1078 distraction duty.
- **Sprint 13 delivery**: 26 tickets advanced (20 Done, 6 reached QA). Pick/Pack epic FUSE-707 = 12 of them.
- **PRs**: 189 merged in window, 120 non-bot / 69 bot. By author — harry-fitzgerald 73, schuster-efigenio 18, matt-shaw 18, harry-humby 10, kyle-chandler 1.
- **Incidents**: INC-31 (P4, 7 Jul) was collections-service, another team. Zero Fuse incidents.
- **Datadog** (`environment:prod`, 6–20 Jul): `fuse.request` 5,033 · `fuse.request.success` 5,035 · `fuse.request.failure` no prod data (dev 6) · `snap_adapter.snap.request` 30,238 ok / 1,456 fail · `snap_polling_service.snap.request` 1,011,142 ok / no prod failures (dev 18).

## Withheld figures — reported to Harry, deliberately not published

1. **Throughput / records processed.** `dedupe_service.event.handled` = 11,792 (S13) vs 66,457 (S12), but the series steps down ~75% on **30 June ~18:00 UTC** and stays flat at the new level since. The two sprints sit either side of it, so no valid comparison and no trustworthy absolute. Cause unattributed — candidates: dual-publish removal, OMS decommission, Snap poller ack-deadline/idempotency fixes. **Open action: attribute this properly.**
2. **4xx rejection volume.** Prod logged 7,996 client rejections against 5,033 accepted requests — more rejections than successful traffic. But `fuse.request.rejected` only began emitting ~**10 July** (the mid-sprint 4xx reclassification), so there is no sprint-long rate. The underlying signal still looks worth understanding — misconfigured customer, auth failures, or probe noise. **Open action: investigate.**
3. **Env tagging gap.** `dedupe_service.*` reports only `env:serverless` with no `environment` tag, so even its absolute figures mix prod and dev. Blocks using dedupe throughput in future at-a-glance sections until fixed.
