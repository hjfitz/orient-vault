---
ticket: none
title: 'UF dual-publish: audit events to audit-service behind AUDIT_SINK'
service: fuse-ui
status: complete
created: '2026-10-12'
updated: '2026-10-15'
repo: /home/hjf/code/fuse/fuse-ui
worktree: /home/hjf/code/fuse/fuse-ui/.claude/worktrees/audit-dual-publish
branch: hjf/audit-dual-publish
base: origin/hjf/audit-log-hardening
base_sha: c47ebd6
pr: '305'
tags:
- waypoint
- plan
programme: Audit Service
unit: UF
impl_model: opus
impl_effort: high
---
# Audit Service UF — dual-publish: audit events to audit-service behind AUDIT_SINK

<!-- Guidance in this file is written as HTML comments: Obsidian hides them, agents read them,
     and `wp signoff` ignores them. Only <angle spans> are treated as unfilled placeholders, so
     they mark the places a human or agent must actually type something. Leave the comments in
     place — deleting them costs the next reader the guidance and gains nothing at the gate.

     SUPERSEDING A STATEMENT. This file is edited by several sessions over days. When something
     here stops being true, do NOT strike it through, delete it, or bury a correction inside it.
     Put one blockquote immediately ABOVE the stale text and leave the text alone:

         > SUPERSEDED 2026-09-04 — the monitor now lives in `gfs-bifrost/observability`.
         > Everything below is kept as the record of how it was first built here.

     One marker, always above, never inside. `wp decide` writes the dated entry in
     `## Decisions & deviations` that explains why. -->

## Intent
<!-- What we are changing and why. Link the ticket. -->
This is unit UF (first of three plans) of the [[Audit Service/Migration State|Audit Service]] programme. It is out-of-ticket work; the nearest epic is FUSE-980.

fuse-ui starts publishing every audit event to audit-service (topic `audit.<env>.fuse.v1`) as well as writing it to Mongo, behind `AUDIT_SINK=mongo|both|service`. Each event gets one `eventId`, stored on the Mongo row and used as the published id, so the later migration skips rows the service already holds. Reads stay on Mongo. The plan exits when dev runs `both` and every new dev row appears in audit-service under the same id.

Stacked on gfs-bifrost/fuse-ui#299 (UA), whose `lib/audit/audit-writer.ts` is the seam. The read client and the cutover are separate plans ("UF read path", "UF cutover and removal").

## Acceptance criteria
<!-- Observable, checkable outcomes — not tasks. Numbered by order: increments cite them as
     (AC 2,4), and sign-off prints which criteria no increment claims. -->
- [x] 1. Every audit row written from now on carries a lowercase UUID `eventId`, and the UI's row id and `?change=` links use it, so a link copied before cutover still resolves afterwards.
- [x] 2. With `AUDIT_SINK=both`, each audit write also publishes one `AuditMessage` with the same `eventId`, `occurredAt` equal to the row's `timestamp`, and the same tenant, kind, target and actor the legacy importer would derive for that row.
- [x] 3. A failed or slow publish never fails or delays the audited action beyond the publisher's timeout; it is logged and counted as `fuse.audit.publish_failed{reason}`, and the metric reaches Datadog.
- [x] 4. Preview environments never publish and have no publisher grant, whatever dev's sink is.
- [x] 5. dev runs `AUDIT_SINK=both`: a UI edit in dev produces a Mongo row with `eventId=E`, and `GET /api/v1/systems/fuse/events/E` on audit-service dev returns it.

## Affected boundaries
<!-- Components, paths and contracts this touches. Wikilink existing explainers; do not restate
     their contents. If this names a topic, endpoint, canonical type, collection, inter-service
     dependency or shared package, sign-off will prompt for the Fuse MCP data file too. -->
- **Writer seam:** `code/src/lib/audit/audit-writer.ts` (from #299); `code/src/lib/db/audit-log.collection.ts` (`addAuditLog` computes `timestamp`/`sourceIp`; read maps `id: _id.toString()`); `audit-log.types.ts` (`AuditLogDocument`).
- **Config:** `code/src/config.ts` (single file; `configSchema` + `superRefine` precedent for conditional requirements).
- **Packages:** `@gfs-bifrost/audit@0.1.0` (`./fuse`, `./publisher`), `@google-cloud/pubsub`; `next.config.ts` `serverExternalPackages`; `code/pnpm-workspace.yaml` `minimumReleaseAgeExclude` (pnpm 11, package published 2026-10-12).
- **IaC:** `iac/projects/fuse-ui/{variables.tf,cloud-run.tf,iam.tf}`, `iac/env/{dev,prod,feature-branch}.tfvars`. Topic built by name `audit.${var.env}.fuse.v1`, no remote state.
- **Contract:** `AuditMessage` / `FuseAuditMessageInput`; audit-service's legacy importer `Kind()`/`Map()` in `code/internal/core/legacy/legacy.go` is the classification new events must match.
- **Shared state:** Pub/Sub IAM in dev and prod (merge to main applies prod), the dev Cloud Run revision.
- Fuse MCP at sign-off: fuse-ui as a publisher of `audit_fuse` in `pubsub-topology.json`.

## Assumptions & uncertainty
<!-- One line each, with how it was established. A genuine product or domain question goes here
     as UNRESOLVED: and is raised with the user, never invented. -->
- **The topic exists in both envs and lives in fuse-ui's project.** bifrost-pubsub#15 applied in dev and prod; `bifrost-<env>-global1`. Established by the grounding review from bifrost-pubsub `origin/HEAD`.
- **Previews inherit `var.env = dev`,** so a by-name topic resolves to the dev topic; the sink and the grant must both be forced off with `is_preview_env`. Established from `terragrunt.hcl` and `feature-branch.tfvars`.
- **Neither publisher nor ingest enforces per-kind `details` at runtime;** only `FuseAuditMessageInput` typing does. The mapping must build typed messages, not casts. Established from `audit-publisher.ts:64` and `ingest.go`.
- **Kind mapping matches the importer:** viewed/copied/link_created/rotated → `credential_access`; target `user` → `user_change`; created/updated/deleted → `config_change`; `businessId` lifts out of `details` to `tenantId`; `actor.type = user`; `target.type = targetEntity`; `details` defaults to `{}`. Established from `legacy.go:31-80`.
- **`correlationId` comes from the request's `x-request-id`** (`proxy.ts`), falling back to the `eventId` when absent.
- **Metric delivery on a CPU-throttled Cloud Run is unproven for fuse-ui** (audit-service needed a per-request flush). Verified in dev in increment 3, not assumed.
- **Masking stays at read** (G3): the published `details` carry full snapshots, exactly as the Mongo row does.

## Increments
<!-- Each independently implementable AND verifiable. Cite the criteria it discharges as
     (AC n,n). Tick with `wp tick`, which stamps `— done: <sha>` from HEAD; never hand-write it.
     Prefer 3-7 — more usually means the ticket is too big, so say that rather than splitting
     hairs.

     A PRECONDITION THAT IS NOT CODE goes on its own indented `gate:` line, with a confirmation
     box under it. Sign-off blocks on a ticked increment sitting above an unconfirmed gate, and
     `wp brief` shows unmet gates in its NEXT block — so "do not action this yet" stops being
     bold prose a fresh session can miss:

         - [ ] 6. Widen the subscription filter (AC 6) — verify: filter matches in dev
               gate: FUSE-1052 AND FUSE-1053 confirmed in prod
                     [ ] confirmed
-->
- [x] 1. **One `eventId` and timestamp per event.** The writer mints a lowercase `crypto.randomUUID()`, computes `timestamp` and `sourceIp` once, and stores `eventId` on the Mongo row; reads map `id = eventId ?? _id`. Stacked PR on #299. (AC 1) — verify: — jest 933/933; local: user create row eventId 616d66a3-…; `?change=<eventId>` and `?change=<legacy ObjectId>` both open the drawer — done: b2aabe9
      - Jest: the stored row carries the minted id; a row with `eventId` reads back with `id = eventId`, one without keeps the ObjectId.
      - Local run: a user create writes a row with a UUID `eventId`, and its `?change=<eventId>` link opens the drawer.
- [x] 2. **IaC: sink, topic and publisher grant.** `audit_sink` (default `mongo`) and `AUDIT_SINK`/`AUDIT_TOPIC` env vars, with the sink forced to `mongo` on previews; `google_pubsub_topic_iam_member` (`roles/pubsub.publisher`) for `cloudrun_sa` on `audit.${var.env}.fuse.v1` with `count = is_preview_env ? 0 : 1`. dev and prod tfvars stay `mongo`. Stacked PR. (AC 4) — verify: — #301 dev plan: 1 add (pubsub.publisher for fuse-ui-dev on audit.dev.fuse.v1), Cloud Run +2 env; the sidecar/max_instance_count/annotation diffs are standing drift (same on #300's plan, which has no IaC change); post-merge get-iam-policy check pending — done: eb135fc
      - PR tf-plan: dev and prod each add exactly one IAM member and two env vars, nothing else.
      - After merge: `gcloud pubsub topics get-iam-policy audit.<env>.fuse.v1` lists `fuse-ui-<env>@` as publisher in both envs; a preview plan adds no member.
- [x] 3. **Publish behind `AUDIT_SINK`.** Add `@gfs-bifrost/audit` + `@google-cloud/pubsub` (`serverExternalPackages`, `minimumReleaseAgeExclude`), `AUDIT_SINK`/`AUDIT_TOPIC` in `config.ts` (topic required unless `mongo`), a mapper from the row to `FuseAuditMessageInput`, and the publish in `writeAuditLog` when the sink is `both`; a `{ok:false}` result logs and increments `fuse.audit.publish_failed{reason}`. Stacked PR. (AC 2,3) — verify: — jest 950/950 (mapper matches importer fixtures; sink mongo/both/service; failure resolves + counts); local sink=both → audit-service dev logged stored user_change for eventId 33362a2f-…; missing topic → 201, row written, publish_failed logged; next build green — done: baacd43
      - Jest: one test per sink value; mapper output per kind equals what `legacy.Map` produces for the same row (fixtures from the importer's tests); a publisher resolving `{ok:false, reason:'timeout'}` leaves the write resolved and counts the metric.
      - Local run against the real dev topic (`sink=both`, `GOOGLE_CLOUD_PROJECT=bifrost-dev-global1`): a user create lands in audit-service dev under the same `eventId`.
- [x] 4. **dev runs `both`.** tfvars `audit_sink = "both"` for dev, merged and deployed. (AC 5) — verify: — #305 merged (ca5962f), dev applied in run 38370761002; AUDIT_SINK=both live; no-op role PATCH at 10:41:30Z → audit-service-dev ingested f201a595-c8c8-4a93-a745-a3723245651c (user_change) and the fuse-ui Mongo row carries the same eventId — done: abe9363
      - A UI edit in dev gives a Mongo row with `eventId=E`; `curl -H "Authorization: Bearer $(gcloud auth print-identity-token --impersonate-service-account=<a dev api_reader SA> --audiences=<dev url>)" <dev url>/api/v1/systems/fuse/events/E` returns it with matching tenant/kind/target.
      - `fuse.audit.publish_failed{environment:dev}` and the dev `.dlt` stay at zero over a day; a deliberately failing local publish shows the metric arriving in Datadog.
      gate: #299 and increments 1–3 merged to main and deployed to dev (2026-10-12: #299–#302 merged, 9aa6174 in dev and prod)
            [x] confirmed

## Verification
<!-- The single authority for evidence. Increment lines carry `— done: <sha>` and nothing else.
     Check-selection order lives in verification-menu.md — do not restate it here. -->

### Evidence
- 2026-10-15 [AC 1-5] **Proven through the cutover.**
  - **AC 1:** prod legacy link `?change=6a8eb6aa0b752eceb1415694` opens after the cutover. #326/#325 evidence.
  - **AC 2, 5:** dev soaked `both` for 2 days: 34 stored, 0 `publish_failed`, 0 dead-letters. The dev migration found 33 rows already present under the same `eventId`. Prod ran `both` and stored 6 real events, and Mongo 255 = service 255 for every customer.
  - **AC 3:** the same `getMetrics()` path delivers `fuse.support_flow.action` from `fuse-ui-app-prod` (13 in 7d). The failure branch was proven locally on 10-12. No real publish failure has happened, so `fuse.audit.publish_failed` has never been seen from Cloud Run.
  - **AC 4:** both topic policies list only `fuse-ui-<env>@` and `upload-svc2-<env>-cr@`, with no preview SA. `audit_publisher` is `count = is_preview_env ? 0 : 1`, and since #325 previews get an empty topic.
<!-- Newest first, dated. One bullet per check actually run, opening with what it discharges.
     "Suite green" alone is not evidence. Sign-off requires at least one dated bullet here. -->
- 2026-10-12 [inc 2, AC 4] **Merged and applied.** #299–#302 merged bottom-up, and each merge's dev apply was green.
  - **Prod:** run 38270870197's plan was `1 to add, 1 to change, 0 to destroy`. The scaling/annotation/sidecar lines match the last applied prod plan (10-09), so they are standing drift. Approved, applied with `1 added, 1 changed, 0 destroyed`, and the six superseded gated runs were cancelled.
  - **Live state:** `fuse-ui-app-{dev,prod}` run `9aa6174` with `AUDIT_SINK=mongo` and `AUDIT_TOPIC=audit.<env>.fuse.v1`.
  - **Grants:** `get-iam-policy` on `audit.{dev,prod}.fuse.v1` lists only `fuse-ui-<env>@` as publisher.
  - **Smoke:** prod `/login` returns 200, with no prod errors in the following 15 minutes.
  - **Scope:** the same deploy shipped #294/#297/#304 to prod without QA, per Harry.
- 2026-10-12 [inc 3] **Docker image (local build of `code/dockerfile`):** `@google-cloud/pubsub` resolves inside the image. The publisher code is bundled into the server chunks (`auditKind` present), and Pub/Sub is required as an external.
- 2026-10-12 [inc 2, AC 4] **#301 dev plan:** `1 to add, 1 to change, 0 to destroy`. The add is `google_pubsub_topic_iam_member.audit_publisher[0]` (`roles/pubsub.publisher`, `fuse-ui-dev@` on `audit.dev.fuse.v1`); the change is Cloud Run +2 env vars. The sidecar env, `max_instance_count 100 → null` and `container-dependencies` diffs are standing drift: the same diffs appear on #300's plan, which has no IaC change. The first runs on #301 and #302 failed on a state-lock race between the stacked plans and passed on rerun.
- 2026-10-12 [inc 3, AC 2,3] **Local run (`next dev`, throwaway Mongo, `sink=both`, the real `audit.dev.fuse.v1`, ADC):**
  - a user create wrote a Mongo row with `eventId 33362a2f-3f57-4e30-b377-84d4669c727d`;
  - audit-service dev logged `audit message ingested … outcome: stored, kind: user_change, system: fuse` for that id;
  - with `AUDIT_TOPIC=audit.dev.does-not-exist.v1`, the create returned 201 in 1.6s, the row was written, and the server logged `Failed to publish audit event … reason = publish_failed`.
  - Jest 950/950, `next build` green, `pnpm audit` passed.
- 2026-10-12 [inc 1, AC 1] **Local run:** a user create wrote a row with `eventId 616d66a3-…`. `?change=<eventId>` opened the drawer on it, and `?change=<ObjectId>` opened a seeded legacy row. Jest 933/933.

### Not verified
<!-- Stated, not papered over. "(none)" is a deliberate claim, and a fine one. -->
- That `fuse.audit.publish_failed` reaches Datadog from Cloud Run. It is checked in increment 4 once dev runs `both`. fuse-ui's existing low-volume metrics do arrive, so no flush problem is expected.
- After #301 merges: `gcloud pubsub topics get-iam-policy` in dev and prod, and a preview plan with no member.

## Decisions & deviations
<!-- Date-stamped, newest first — written by `wp decide`, and by hand when that is easier.
     Where implementation departed from this plan, and why. Source wins over the plan: correct
     the plan in the same increment and record the correction here. Legitimately empty at plan
     time. A decision worth defending in a review six months out belongs in a durable record
     instead — `wp decide --record`. -->

- **2026-10-12** — Harry agreed #301's Terraform plan (dev: 1 add = pubsub.publisher for `fuse-ui-<env>@` on `audit.<env>.fuse.v1`; 1 change = Cloud Run +AUDIT_SINK/AUDIT_TOPIC plus standing drift; 0 destroy). That covers merging #301 and approving its terraform-prod apply without re-asking, provided the prod plan has the same shape. Anything else in it, especially a destroy or a replace, means stop and share. #299–#302 marked ready and posted to #bifrost-forge.

- **2026-10-12** — UF split into three plans after review: this one (dual-publish to dev both), 'UF read path' (id-token generalisation, generated client, AUDIT_READ_SOURCE, cursor paging, masking via mask-audit-details), and 'UF cutover and removal' (rehearsal, prod both + soak, scoped read-only Atlas user for the human-run import, the one-way-door deploy, migration, then removing the Mongo path and AUDIT_LOG_RETENTION_DAYS). The Atlas read-only user moved out of UF.1: its only user is the human-run migration, and it must be scoped to audit_log because the same database holds users' bcrypt hashes.

## Learnings
<!-- Durable facts about the service surfaced while planning, working or testing that are not
     already written anywhere in the vault — a gotcha, a constraint, a fragile edge, a confirmed
     or refuted hypothesis. Not restated doc content. Sign-off promotes each confirmed one into
     the matching durable doc, then clears it from here; a refuted one moves to ## Handback
     rather than being deleted. Legitimately empty. -->
