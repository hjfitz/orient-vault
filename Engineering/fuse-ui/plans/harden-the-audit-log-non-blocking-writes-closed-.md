---
ticket: none
title: 'harden the audit log: non-blocking writes, closed client write surface, server-side
  guard and masking'
service: fuse-ui
status: complete
created: '2026-10-09'
updated: '2026-10-12'
repo: /home/hjf/code/fuse/fuse-ui
worktree: /home/hjf/code/fuse/fuse-ui/.claude/worktrees/audit-log-hardening
branch: hjf/audit-log-hardening
base: origin/main
base_sha: c17ce1485
pr: '299'
tags:
- waypoint
- plan
programme: Audit Service
unit: UA
impl_model: sonnet
impl_effort: medium
---
# none — harden the audit log: non-blocking writes, closed client write surface, server-side guard and masking

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
This is unit UA of the [[Audit Service/Migration State|Audit Service]] programme. It is out-of-ticket
work; the nearest epic is FUSE-980. It fixes five prod defects in fuse-ui's existing audit code before
any of the split lands:
- audit writes that block or corrupt the action being audited;
- fire-and-forget writes that are never awaited;
- a client-callable write surface that lets any session forge rows;
- read server functions with no admin guard;
- before/after snapshots that reach the browser unmasked inside the RSC payload.

The fixes also put every write behind one server-only seam, which is what UF later switches from Mongo
to Pub/Sub. Proof: a broken audit insert no longer stops a user create or a password reset; forged
writes and non-admin reads are rejected; no snapshot credential appears in the dev RSC payload.

## Acceptance criteria
<!-- Observable, checkable outcomes — not tasks. Numbered by order: increments cite them as
     (AC 2,4), and sign-off prints which criteria no increment claims. -->
- [x] 1. A failing audit write never fails or partly applies the audited action. User create still returns 201 and the one-time password; password reset still returns the new password; PATCH still applies its email change after a failed role audit.
- [x] 2. Every server-side audit write goes through a single server-only writer and is awaited inside the request. No `void logAuditEvent(...)` remains in server code.
- [x] 3. A client cannot write an arbitrary audit row. The only client-callable write is the allow-listed credential view/copy event on a connector; anything else is rejected and writes no row.
- [x] 4. `listAuditLogs` and `listAuditLogFilterOptions` reject a non-admin session server-side, whatever path they are invoked from.
- [x] 5. No secret value from an audit snapshot reaches the browser. The detail drawer still shows that a credential changed.

## Affected boundaries
<!-- Components, paths and contracts this touches. Wikilink existing explainers; do not restate
     their contents. If this names a topic, endpoint, canonical type, collection, inter-service
     dependency or shared package, sign-off will prompt for the Fuse MCP data file too. -->
- **Write seam:** `code/src/lib/db/audit-log.collection.ts` (`addAuditLog`).
- **Server functions:** `code/src/app/server-functions/audit/log-audit-event.func.ts` and `audit-config-change.func.ts` are both `'use server'` today, which is why they are client-callable.
- **Direct `addAuditLog` callers:**
  - `app/api/auth/users/route.ts:48`
  - `app/api/auth/users/[email]/route.ts:58,86,138`
  - `app/api/auth/users/[email]/reset-password/route.ts:38` (the hash is overwritten at :29 before auditing)
  - `server-functions/storefronts/storefronts.action.ts:353` and `connector-credential-link.func.ts:131` (both already try/catch)
- **`auditConfigChange` callers:**
  - `customer-ddp.action.ts:29,60,86`
  - `customer.action.ts:60,88,124,155`
  - `skus-to-ignore.action.ts:38,74,105`
  - `warehouse-routing.action.ts:30,64,95`
  - `backend.action.ts:48,89`
  - `shipping-methods.action.ts:36,72`
  - `storefronts.action.ts:52,115,163,218,269,313,420,461,496`
- **Unawaited writes:** `server-functions/templates/templates.action.ts:97,189,292,347,401,428,462,497,524` (`void logAuditEvent`).
- **Client-side writers:** `modules/connector/components/sftp-connector-display.tsx:60` and `rest-connector-display.tsx:65`.
- **Reads:** `server-functions/user/audit-log.func.ts`, called from `app/user-management/audit-log/page.tsx`, `app/customer/[customerId]/changes/page.tsx` and `modules/connector/components/connector-change-history.tsx`.
- **Auth gate:** `src/proxy.ts`. A session is required everywhere except `/login` and `/api/auth`; the role check covers only the `/user-management` prefix.
- **Masking:**
  - `modules/audit-trail/components/audit-detail-drawer.tsx` (`maskSnapshot`; `diffConfig(before, after)` at :235).
  - `modules/audit-trail/logic/audit-summary.logic.ts` (`SECRET_PATH_ENDINGS`/`isSecretPath`). It has no directive and is only bundled into client code.
  - `AuditLogTable` and `ChangeTimeline` are `'use client'` and receive full `AuditLogView` objects.
- See [[../architecture#bff-not-data-plane]] and its audit guardrails (`PATH_LABEL`, `pending-changes`, the total `ENTITY_LABEL`).

## Assumptions & uncertainty
<!-- One line each, with how it was established. A genuine product or domain question goes here
     as UNRESOLVED: and is raised with the user, never invented. -->
- **Server actions are callable by anyone with a session.** A `'use server'` export can be invoked by any session that obtains its action id. That id is in the client bundle whenever a client component imports the export, which is the case for `logAuditEvent`. Established by the factual-grounding review reading `proxy.ts` and the imports.
- **Cloud Run CPU is throttled outside requests.** `iac/projects/fuse-ui/cloud-run.tf` has no `cpu_idle` override, so an unawaited write can be lost. Established from source.
- **Full snapshots stay in the store; masking moves server-side at read.** This keeps the recorded fuse-ui decision (full snapshot, masked at render), whose diffs and planned restore UX depend on raw values. Programme gate G3 confirmed this on 2026-10-12 (Harry): full snapshots plus server-side masking, with no write-time redaction. Source: fuse-ui `known-context.md`.
- **Masked values keep the diff signal.** A changed secret becomes distinct tokens on each side; an unchanged one becomes the same token on both. The drawer's `diffConfig` still flags the change without any secret reaching the client. This is a design choice, not something established from source.
- **PROPOSED: a new directory `code/src/lib/audit/`** for the server-only writer and the read-side masker. It can't live in `server-functions/` (those files are `'use server'`, which is the exposure being closed) or in `lib/db/` (UF moves the sink off Mongo). A new directory is an agents.md stop condition, so it needs confirmation at plan review.
- **Fix only the reset-password and PATCH ordering at the audit call.** Making the writer non-throwing is the fix; the route logic is otherwise left alone.

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

- [x] 1. **Server-only writer that never throws.** Add `lib/audit/` with a `server-only` writer that wraps `addAuditLog`, catches, and logs without the payload. Route every direct `addAuditLog` caller and `auditConfigChange` through it, and replace each `void logAuditEvent` in `templates.action.ts` with an awaited writer call. (AC 1,2) — verify: — jest: create/reset/PATCH survive a throwing insert (3 fail if the writer rethrows); writer swallows, logs no details; full suite 912/912 — done: ec17f85
      - Jest: a user create with a throwing insert still returns 201 and the password; a reset with a throwing insert still returns the password; a PATCH with a throwing role audit still applies the email.
      - `grep -rn "addAuditLog\|void logAuditEvent" code/src` matches only `lib/audit`.
      - dev: a config edit and a template edit each still write a row.
- [x] 2. **Close the client-callable write surface.** `audit-config-change.func.ts` loses `'use server'` and becomes server-only. The `'use server'` `logAuditEvent` entrypoint accepts only `viewed`/`copied` on `connector`, with a fixed `details` shape, and rejects anything else. (AC 3) — verify: — jest: copy recorded against connector; forged action/target/field/extra details write nothing; auditConfigChange server-only; 917/917 — done: 5e48828
      - Jest: a non-allow-listed action or target writes no row.
      - dev: a server-action POST using `logAuditEvent`'s action id with a forged `action: 'deleted'` writes no row, while a credential copy in the UI still writes one.
- [x] 3. **Admin guard inside the read functions.** `listAuditLogs` and `listAuditLogFilterOptions` check the session role themselves rather than relying on the pages. (AC 4) — verify: — jest: editor and no-session rejected by both readers; admin served; all 3 callers already admin-gated — done: 089b73f
      - Jest: an editor session is rejected.
      - dev: as an editor, a server-action POST to `listAuditLogs` from a non-`/user-management` path is rejected, and admin pages still load.
- [x] 4. **Mask snapshots on the server before the client boundary.** Move `SECRET_PATH_ENDINGS`/`isSecretPath` to a server-importable module. The read functions map `details.before`/`after` to masked copies (changed → distinct tokens, unchanged → equal tokens) before returning. Client components never get raw values. (AC 5) — verify: — jest: no secret survives (snapshots, arrays, top-level); diffConfig flags changed credential, not unchanged; next build green — done: b1bc9d0
      - Jest: no secret path survives in the mapped view, and `diffConfig` over the masked pair still flags a changed credential.
      - dev: after rotating a dev connector credential, grepping the `/user-management/audit-log` RSC payload for the old and new values finds nothing, and the drawer shows the credential as changed. Take a screenshot.

## Verification
<!-- The single authority for evidence. Increment lines carry `— done: <sha>` and nothing else.
     Check-selection order lives in verification-menu.md — do not restate it here. -->

### Evidence
<!-- Newest first, dated. One bullet per check actually run, opening with what it discharges.
     "Suite green" alone is not evidence. Sign-off requires at least one dated bullet here. -->
- 2026-10-12 [shipped] **gfs-bifrost/fuse-ui#299 merged** as `40255e4` (squash). That included the logger-safety fix `d2516d2` and the comment trims `c47ebd6`. It runs in **dev and prod at `9aa6174`** (Deploy run 38270870197; prod apply `1 added, 1 changed, 0 destroyed`). `https://fuse.ilg.software/login` returns 200, and no ERROR logs appeared in the 15 minutes after the apply.
- 2026-10-12 [local run, all incs] **Why local, not dev:** the branch ran with `next dev` against a throwaway Mongo (`mongo:7`, port 27031) and the env-defined admin login, not a dev deploy. Two reasons: a manual deploy would replace the shared dev image, and the masking check would have meant rotating a real dev connector's credentials. Afterwards the container, the env file and the generated `AGENTS.md`/`CLAUDE.md` were removed, and `next-env.d.ts` was reset.
- 2026-10-12 [inc 1, AC 1] **Failed audit inserts (live run):** with a validator on `audit_log` rejecting every insert:
  - `POST /api/auth/users` returned **201** with the password;
  - `…/reset-password` returned **200** with the password;
  - `PATCH {role, email}` returned **200**, and Mongo shows the user renamed to `ua-editor2@example.com`;
  - 0 audit rows were written, and 4 `Failed to write audit log` lines were logged, carrying action, target and error but no details.
  - **The first attempt returned 500 on all three.** The shared redacting logger throws on a `MongoServerError` (it reassigns the error's read-only `name`), so the writer's own catch block threw. Fixed in `d2516d2`; the unit tests had mocked the logger.
- 2026-10-12 [inc 1, AC 2] **Awaited server-side writes:** a template collection created via its server action id wrote a `created template_collection` row. Of `grep addAuditLog|void logAuditEvent`, only `lib/audit/audit-writer.ts` and the two client credential displays (`void logAuditEvent({...})`, the allow-listed client path) remain.
- 2026-10-12 [inc 2, AC 3] **Forged writes:** server-action POSTs with `logAuditEvent`'s id wrote **0 rows** for each of these as admin:
  - `{action:"deleted", targetEntity:"user"}`;
  - the old positional form `["deleted","user","victim@x.com",{…}]`;
  - a copy carrying `before.apiKey`.

  A real credential copy wrote one `copied connector conn-1 {field:"apiKey"}` row. The production `server-reference-manifest.json` has no `auditConfigChange` entry, so it is no longer an action.
- 2026-10-12 [inc 3, AC 4] **Editor reads:** an editor session's server-action POST to `listAuditLogs` and `listAuditLogFilterOptions` from `/templates` returned `"Only admins can read the audit log"` and no logs. The admin got `total: 3`, and `/user-management/audit-log` still loads (200).
- 2026-10-12 [inc 4, AC 5] **Masked payloads:** seeded a connector row whose snapshots held `OLD-PW-…`/`NEW-PW-…` (changed password) and `KEEP-KEY-…` (unchanged `apiKey`).
  - The HTML/RSC payloads of `/user-management/audit-log` and `/customer/HJF/changes` contain **0** of the three secrets, while still carrying the row, `new.example.com` and one `•••••• (previous)`/`•••••• (new)` pair.
  - **Control:** swapping in `origin/main`'s `audit-log.func.ts` put all three secrets back in the payload.
  - The drawer lists "SFTP password" as changed and does not list the unchanged API key. Screenshot: `ua-audit-drawer-masked.png`.
- 2026-10-12 [all] Jest 928/928, biome clean, `tsc` clean (after `next typegen`), `next build` green.

### Not verified
<!-- Stated, not papered over. "(none)" is a deliberate claim, and a fine one. -->
- Config edits (`auditConfigChange`) writing a row live: not exercised, because every config action writes to the real dev config-service. They share `writeSessionAuditLog` with the template path that was exercised.
- A deployed Cloud Run revision: proven locally only. A dev deploy or preview env would prove it in place.

## Decisions & deviations
<!-- Date-stamped, newest first — written by `wp decide`, and by hand when that is easier.
     Where implementation departed from this plan, and why. Source wins over the plan: correct
     the plan in the same increment and record the correction here. Legitimately empty at plan
     time. A decision worth defending in a review six months out belongs in a durable record
     instead — `wp decide --record`. -->

- **2026-10-12** — Marked complete after #299 merged (40255e4) and shipped to prod (9aa6174). The final signoff run reported one blocker: uncommitted changes in /home/hjf/code/fuse/fuse-ui. That is an artifact. The UA worktree had already been removed, so signoff fell back to the shared main checkout, which is on someone else's branch (hjf/fuse-1000-secops-02-migrate-fuse-ui) with its own uncommitted work. The increment shas being absent from HEAD is expected after a squash merge.

- **2026-10-12** — isSecretPath stays in modules/audit-trail/logic/audit-summary.logic.ts rather than moving: it has no directive and no client-only imports, so lib/audit/mask-audit-details.ts imports it on the server as is; moving it would only churn imports. auditConfigChange stays at server-functions/audit/audit-config-change.func.ts, now 'server-only' instead of 'use server', to avoid touching its 7 importers. logAuditEvent keeps its name but takes one CredentialAccessEvent object validated by a strict zod schema.

## Learnings
<!-- Durable facts about the service surfaced while planning, working or testing that are not
     already written anywhere in the vault — a gotcha, a constraint, a fragile edge, a confirmed
     or refuted hypothesis. Not restated doc content. Sign-off promotes each confirmed one into
     the matching durable doc, then clears it from here; a refuted one moves to ## Handback
     rather than being deleted. Legitimately empty. -->
(none)
