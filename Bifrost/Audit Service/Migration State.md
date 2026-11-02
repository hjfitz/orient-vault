---
title: Audit Service — Migration State
programme: audit-service
status: active
owner: hjf
services:
- fuse-ui
- pkg-node
- bifrost-pubsub
- sftp-connector
- audit-service
created: '2026-10-09'
updated: '2026-10-15'
tags:
- bifrost
- migration-state
---
# Audit Service — Migration State

<!-- The single source of truth for PROGRESS. The Overview carries the narrative and the verdict;
     this doc is the live ledger a session reads to know what is done and what is next.
     `wp programme status/next/tick` read and write the `## Unit status` tables below, so keep the
     table shape intact. Guidance lives in HTML comments (Obsidian hides them); <angle spans> mark
     what a human or agent must fill in. -->

## Unit status
Legend: ⬜ not started · 🟨 in progress · ✅ merged · ⛔ blocked · ⏸ deferred · ❌ dropped · 🔄 rescoped

### Core: split and cutover
| Unit | St | Summary | Deps | Risk | Tier | PR | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **UA** | ✅ | fuse-ui audit hardening | | low | sonnet/medium | #299 | Runs alongside the service build; must land before UF.1 (its writer is the dual-publish seam). Promoted to a fuse-ui plan. Fixes prod bugs independent of the split: audit writes that never throw and are awaited; the client-callable write surface closed; an admin guard on reads; snapshots masked server-side. |
| **UB** | ✅ | Bootstrap the audit-service repo | | low | sonnet/low | github-config#18 | Plan-less, in github-config. Adds the repo with `terraform-dev`/`terraform-prod` envs, package grants and Atlas key secrets. |
| **UC** | ✅ | `@gfs-bifrost/audit` 0.1.0 | | med | opus/medium | pkg-node#268 | pkg-node. Generic `AuditMessage` envelope (usable outside Bifrost) plus per-kind `details` in Zod, and a publisher that never throws. 3 increments (Overview). |
| **UD** | ✅ | `audit.<env>.fuse.v1` topic | | low | sonnet/low | bifrost-pubsub#15 | Plan-less, single PR in bifrost-pubsub. One topic per system; the module `.dlt` is the dead-letter topic. Applied in dev and prod before UE.3 merges. |
| **UE** | ✅ | audit-service (Go) | UB, UC, UD | high | opus/high | | New repo. UE.1–UE.5 done: dev and prod ingest live, read API, import tool (dev dry run 702/702). UE.6: metrics live; monitors in observability#64 are held on a human call (the plan also carries #61's parked changes and a threshold revert). No TTL; data kept forever. |
| **UF** | ✅ | fuse-ui cutover | UA, UC, UE | high | opus/high | #300-#302, #305-#308, #310, #323, #324, #326, #328, #325 | Dual-publish, then the read client (off), then Mongo path removal. Dev cut over 2026-10-14 (#323; 751 verified). Prod: `sink=both` 2026-10-14 19:38Z (#324), the import (249/249), reads from the service (#326). **2026-10-15:** `sink=service` live 10:00Z (#328, revision 00075) once 6 real prod events had been stored. The catch-up import inserted 0, verify read 255 / missing 0, and every customer matches. Mongo `audit_log` is frozen at 255 rows. UF.3 (#325) removed the Mongo path. |
| **UG** | ✅ | sftp-connector user-lifecycle events | UC, UE | med | sonnet/medium | #309 (sftp-connector) | First non-UI producer. Deterministic `eventId`. No VM change. |

### Follow-ups
| Unit | St | Summary | Deps | Risk | Tier | PR | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **UH** | ⏸ | Drop fuse-ui `audit_log` | UF | high | sonnet/low | | Irreversible. Gated by G6. Atlas point-in-time and backups keep credential-bearing copies until they expire. |
| **UI** | 🔄 | SFTP session events from the logind lines | UE | low | sonnet/medium | | Log sink on systemd-logind `Started session-N.scope … of User <u>` lines, which already reach Cloud Logging. No VM change. No source IP. |
| **UJ** | ⛔ | SFTP sshd IP and failed logins via Ops Agent | UI | high | opus/high | | Ops Agent by OS Config policy (no reboot), then a sink on trusted sshd fields, then sftp-connector (username → connector), then an `sftp_login` event with a 1-year TTL. Plan: sftp-connector `uj-sftp-login-audit-events-from-the-vm-via-ops-a`; siblings P1 (audit 0.3.0), A1 (audit-service retention), F1 (fuse-ui labels). G7 waived for agent-only. UI folded in. **Halted 2026-10-20 after inc 1 (Harry):** login audit moves to the Go SFTP host, which emits `sftp_login` itself (sftp-connector `sftp-host-b-provisioning-login-audit-and-dev-cut` inc 2). A1, F1 and the `sftp_login` kind (P1) still apply to it. |
| **UK** | ⏸ | More producers (fuse-mcp mutations, others) | UE | med | opus/medium | | Needs a real user identity at the producer. dedupe-service and config-service only see a shared key or `"admin"`. Changes made through fuse-ui are already audited. |

## Gates
- [x] **G1 — Audit envelope is a documented exception to the canonical-only bus** — blocks UC, UD. Cleared 2026-10-12: a standard `AuditMessage` envelope, distinct from `BifrostMessage` and usable outside the Bifrost suite. It rides its own topic with a single unfiltered subscriber. Record it in fuse-mcp `event-contracts.json` at UD sign-off.
- [x] **G2 — Package location: standalone `@gfs-bifrost/audit` vs inside `@gfs-bifrost/types`** — blocks UC. Cleared 2026-10-12: standalone, because the envelope is meant to be usable outside Bifrost. The org rule says types shared by several services go in `types` first, so a standalone package needs explicit sign-off.
- [x] **G3 — Secrets in snapshots: keep full snapshots, or redact at write time** — blocks UC, UE, UF. Cleared 2026-10-12: keep full snapshots and mask server-side at read (UA increment 4). No write-time redaction. Reverses or keeps a recorded fuse-ui decision (full snapshot, masked at render; restore UX planned).
- [x] **G4 — Datastore cost and region** — blocks UE. Cleared 2026-10-12: a dedicated Atlas cluster per env (prod M10, dev Flex in `WESTERN_EUROPE`) is accepted. Decides between a dedicated Atlas cluster per env (prod M10) and a database on an existing cluster, and whether dev Flex in `WESTERN_EUROPE` (Belgium) is acceptable for credential-bearing data.
- [x] **G5 — Retention window** — blocks UE. Cleared 2026-10-12: keep forever, with no TTL. This deliberately departs from FUSE-980's 30-day criterion.
- [ ] **G6 — Hold before dropping `audit_log`** — blocks UH. How long the old collection stays after prod sink=service.
- [x] **G7 — SFTP VM owner and recovery runbook exist** — waived 2026-10-15 for an agent-only change (decision log); still applies to any sshd_config, mount or reboot change. Formerly blocked UJ. From 2026-10-20 the VM's only remaining change of that class, the S4-rollback `sync_users.sh`, is covered by the sftp-host plans: owner Harry, runbook `cut.sh` rollback, drilled in dev (Harry). The VM's guardrail G5 (single point of failure, recovery untested) still stands.

## Risks
- **R1 ★ The cutover deploy is a one-way door** — After the single deploy that flips sink and read to the service, rolling back to Mongo reads hides post-cutover events, so the fix is forward-only. Mitigations: a full dev rehearsal; a prod dry-run migration before cutover; dual-publish soak exit criteria (`publish_failed` = 0, dead-letter = 0); verify shows 0 missing after the migration. Old history is missing from the UI for the few minutes the migration runs; announce it — open.
> SUPERSEDED 2026-10-12: R1 above replaces the original wording below (catch-up import dropped).
- **R1 ★ The sink=service flip is a one-way door** — Once it flips, a failed publish is a permanently lost event. Mitigations: a catch-up import before the flip; exit criteria `publish_failed` = 0, dead-letter = 0, verify shows 0 missing; a publish timeout of 3 s or less so a failure never blocks the action — open.
- **R2 ★ The split widens credential exposure** — Snapshots will sit in Pub/Sub retention, the dead-letter hold, a second store and backups. The size of the increase depends on G3. Never log payloads; reads limited to fuse-ui (masked server-side) and the Fuse MCP (`fuse-mcp-prod-sa`, prod only, per-kind allow-list projection that never returns snapshots); the MCP's shared bearer token is rotated before its grant goes live — open.
> SUPERSEDED 2026-10-22: R2 above replaces the original wording below (Fuse MCP added as a second reader, see decision log).
- **R2 ★ The split widens credential exposure** — Snapshots will sit in Pub/Sub retention, the dead-letter hold, a second store and backups. The size of the increase depends on G3. Never log payloads; reads limited to fuse-ui — open.
- **R3 A prod apply fails on missing cross-stack state** — Every merge goes to prod. Mitigated by gating UE.3 on UD's prod apply and UF.2 on UE.4's prod apply, and by having fuse-ui use tfvars rather than remote state — open.
- **R4 Preview envs lose audit after cutover** — This is the tracker precedent. Previews share the dev cluster and their client IP can be spoofed. Accepted by default; needs a revisit if previews are used for audit-sensitive QA — standing.
- **R6 Unbounded growth of credential-bearing history** — With retention forever (G5), the store, its backups and point-in-time copies grow without limit, including high-volume SFTP events once UI/UJ land. Watch storage and plan Atlas tier scaling; revisit retention per kind if SFTP volume dominates — standing.
- **R5 Go gotchas on the read path** — A nil slice encodes as `null` and crashes the JS client; `bson.D` encodes as `[{Key,Value}]`. Mitigated by a real-Mongo round-trip test in UE.3 — open.

## Decision log
- **2026-10-22** — Harry: the Fuse MCP becomes a second audit-service reader (`fuse-mcp-prod-sa` in prod `api_readers`), for staff access audits after the Mongo `audit_log` froze. Accepted knowingly: (1) the grant lets that identity read raw snapshots; the MCP's `audit-search`/`audit-get-event` return only an allow-list projection of `details`, never `before`/`after`; (2) `READ_CALLERS` spans every system, so the grant also covers `secrets` (key names, no values), while the MCP code is fixed to `fuse`; (3) fuse-mcp `master` has no required review or checks, so the projection lives in an ungated repo; (4) the MCP's only gate is its shared bearer token, which is rotated before the grant goes live. Ship order: fuse-mcp first (tools answer 403 until granted), the audit-service grant last, so approving its prod plan is the go-live. Prod only. Run SHIP-1022-audit-mcp-tools.
- **2026-10-20** — Harry: UJ halted after inc 1 (PR #312, dev `prep`, no agent installed). The SFTP VM is being replaced by a multi-zone Go SFTP host (sftp-connector plans `sftp-host-a/b/c`), and SFTP login audit comes from that host only. VM-served logins before the cut aren't audited. A1, A2 and F1 still gate storing `sftp_login` in prod.
- **2026-10-15 (later)** — The UJ plan (`Engineering/sftp-connector/plans/uj-sftp-login-audit-events-from-the-vm-via-ops-a.md`) changes the earlier entry after three reviews:
  - **No `startup.sh.tpl` install.** apt at boot would race OS Config for the dpkg lock and break the reboot recovery path.
  - **Rollback is two steps.** Deleting the assignment leaves the agent installed, so the stage `removing` comes first.
  - **The sink filters on trusted journald fields** (`_COMM`, `_UID`), so `logger` forgery is blocked.
  - **The sink has a per-env cutoff timestamp.** The agent reads the whole journal on its first start.
  - **App retry budget instead of a DLT.**
  - **Prod is verified on real traffic only.**
- **2026-10-15** — Harry: start SFTP login auditing (UI and UJ merged into UJ). The minimum is IP, time, business ID and connector. G7 is waived for an **agent-only** VM change: Ops Agent via a Google-managed agent policy (no SSH, no reboot), dev first, rolled back by removing the policy, and also added to `startup.sh.tpl` for rebuilds. Path: sshd journal → Ops Agent → a log sink filtered to sshd → Pub/Sub → sftp-connector (username → connector/business through its existing lookup) → `sftp_login` AuditMessage. Volume policy (8,072 sessions on 2026-10-14, 10 users, one polling every ~15s): store every accepted login and every failed attempt on a real Fuse username; count, but do not store, attempts on unknown usernames. `sftp_login` gets a retention limit (about 1 year) in audit-service, the first exception to keeping data forever, because of R6. The logind-only route (old UI) is dropped: it has no IP and no failures.
- **2026-10-15** — Prod `sink=service` was flipped at 10:00Z, about 14h into the planned ≥24h soak. Harry agreed to flip early once real prod traffic was proven: 6 real events stored (config_change 4, credential_access 2), `publish_failed` 0, DLT 0, Mongo 255 = service 255 for every customer. The catch-up import afterwards inserted 0. UF.3 (#325, approved by Harry in chat) merged straight after. The `audit_log` collection and the `audit_migration` user stay until G6 (UH).
- **2026-10-14** — Harry: take the programme to completion autonomously (prod DB scripts included), provided no data is lost and prod stays healthy. UH (drop `audit_log`) stays behind G6, so it is out of scope. Prod order changed from "one deploy flips sink+read, then migrate": (1) `sink=both`, soak; (2) run the migration under `both`; (3) `read=service` with `sink=both`, which is reversible because Mongo still gets every event; (4) `sink=service` (the one-way door) once there are ≥24h of `both` with real events and 0 failures, then an idempotent catch-up import and `-verify` showing 0 missing. Why: there is no history gap, prod reads are proven with the real SA before the door (no Token Creator grant needed), and the catch-up covers any publish that failed during `both`. Dev keeps the single-flip rehearsal (#323). Prod volume is a handful of events a day (249 rows total; dry run 249/0 failed), so the soak needs real events stored, not just elapsed time.
- **2026-10-13** — UF dual-publish live in dev (fuse-ui#305, ca5962f): a dev edit landed in Mongo and audit-service under the same eventId. Read path #307/#308/#310 out for review. UG built as sftp-connector#309 and verified in dev with a throwaway HJF connector (event ad426d58-… ingested); connector deletion doesn't deprovision, so its dev login stays, keyless in practice. Dropped the planned audit-service `{system, target.id, occurredAt}` index: the existing target index serves connector history (explain: 13 keys, 4 ms on 200k events). observability#65's monitors watch fuse-ui only; widen them for sftp-connector before UG ships to prod.
- **2026-10-12** — Scaling review (Harry agreed):
  - **Topics:** one per system (`audit.<env>.<system>.v1`), so publisher IAM enforces `system` and each system gets its own blast radius.
  - **Store:** one `events` collection, with every index leading on `system`.
  - **Read API:** cursor paging on `(occurredAt, _id)` with a capped total, so forever-retention stays fast.
  - **Dead-letter topic:** the topic module's `.dlt`, so there's only one dead-letter convention.
  - **`FuseAuditMessage`:** a discriminated union for producers only; the envelope stays open.
- **2026-10-12** — Harry: proceed autonomously through UD and UE; stop before fuse-ui (UA/UF).
- **2026-10-12** — Audit events are stored **by system** (Harry), for extensibility; Fuse (`system: fuse`) is the first. Design defaults, refined at UC/UE planning:
  - `system` is required on the `AuditMessage` envelope.
  - The tenant field is scoped within a system.
  - Every index leads with `system`.
  - Reads are always system-scoped.
  - Kind registries are per system.
  - Repo naming stays system-agnostic (`audit-service`).
- **2026-10-12** — Rollout order (Harry):
  1. Build the service first, in its own repo, landed in prod.
  2. fuse-ui dual-publishes.
  3. Cut over, then migrate the existing records to the new service and the `AuditMessage` format.
  - **Cutover mechanics:** one deploy flips sink and read; one human-run migration follows. Because Mongo is frozen, a single run is complete, so the catch-up import is dropped.
  - **UA:** runs in parallel with the service build and gates UF.1.
- **2026-10-12** — Gates G1–G5 cleared (Harry):
  - **G1:** a standard `AuditMessage` envelope, different from `BifrostMessage`, because it may be used outside the Bifrost suite. The envelope therefore carries no Bifrost-specific fields; `businessId` becomes a generic tenant/scope field.
  - **G2:** a standalone `@gfs-bifrost/audit` package, for the same reason.
  - **G3:** full snapshots plus server-side masking. The recorded fuse-ui decision stands, and the restore UX stays possible.
  - **G4:** a dedicated Atlas cluster per env.
  - **G5:** keep data forever, with no TTL. This overrides FUSE-980's 30-day criterion. `AUDIT_LOG_RETENTION_DAYS=24855` was a placeholder and now matches intent until UF removes it.
- **2026-10-09** — Intent (Harry):
  - Other services report into one Go audit-service.
  - It owns its own datastore and fuse-ui's `audit_log` is migrated into it.
  - fuse-ui keeps writing and browsing, through the service.
  - Out-of-ticket work.
- **2026-10-09** — Design defaults, taken by the planning session after three adversarial reviews:
  - **Write path:** Pub/Sub only.
  - **Store:** MongoDB Atlas.
  - **Contract:** Zod is the source; the Go envelope is generated canonschema-style, from the package's Zod rather than shipped JSON Schema.
  - **Dead-letter topic:** owned by the subscriber, consciously overriding the manual-retry-budget preference because audit has no failure topic.
  - **Publisher:** emits no telemetry.
  - **Envelope fields:** `producer`, not `source`; `correlationId` required.
  - **fuse-ui → service wiring:** tfvars URL and static invoker list, not remote state.
  - **Previews:** no audit.
  - **SFTP:** logins from the logind lines first; the VM is left untouched until G7.
  - **config-service:** dropped as a producer; it would contradict the recorded "no second, competing audit trail".
- **2026-10-09** — Hardening split out as UA, ahead of everything else. The reviews found prod bugs in today's audit code; they need no new service and ship regardless of G1–G7.

## Scar tissue
- **Merge stacked PRs with `merge-async`** (`gh pr merge` refuses). Don't PATCH a stack member's base; GitHub retargets it after the parent merges.
- **Never store a synthetic smoke event in prod**, because data is kept forever. Prove the prod ingest path with a system-mismatched message, which is acked and not stored.
- **Every merge to main applies to prod** in all five repos. Gate on the prod apply, never on "in dev".
- **Prod imports are human-run, dry-run first**, never by an agent.
- **Grant the Pub/Sub service agent on the dead-letter topic explicitly.** Otherwise dead-lettering fails silently.
- **The `AuditMessage` envelope must not be a root union.** canonschema/go-jsonschema emits an empty file for one, and `gen-check` then passes vacuously.
- **Every stored event carries `system`.** Never add a query or index that isn't scoped by it. Legacy fuse-ui rows import as `system: fuse`.
- **Keep the old ObjectId hex as `_id` for imported rows.** `?change=<id>` deep links depend on it.
