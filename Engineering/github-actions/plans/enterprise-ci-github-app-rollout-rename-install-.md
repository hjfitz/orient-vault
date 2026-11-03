---
ticket: none
title: 'Enterprise CI GitHub App rollout: rename, install, docs'
service: github-actions
status: draft
created: '2026-11-03'
updated: '2026-11-03'
repo: ilg-platform/github-actions
worktree: none
branch: none
base: origin/main
base_sha: none
pr: null
tags:
- waypoint
- plan
impl_model: sonnet
impl_effort: low
---
# none — Enterprise CI GitHub App rollout: rename, install, docs

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
Make the platform CI GitHub App (app 4035291, `ilg-platform-ci`, owned by the `gfs-dev` account)
the enterprise-standard credential for cross-org Go/Terraform module fetches: rename it, install
it on every enterprise org, distribute its id/key consistently (cleaning up repo-level shadows and
the old terraform-framework app 3896251), and publish the pattern in Confluence. Config/admin
work only — the code it relies on is [[cross-org-go-terraform-module-auth-via-the-ci-gi]].

## Acceptance criteria
<!-- Observable, checkable outcomes — not tasks. Numbered by order: increments cite them as
     (AC 2,4), and sign-off prints which criteria no increment claims. -->
- [ ] 1. The app has its new name, and pr-sitrep (dev + prod) still authenticates and posts after the rename.
- [ ] 2. `gh api orgs/<org>/installations` shows the app installed on **every** org in the enterprise (list sourced from an enterprise admin view, not from Harry's memberships).
- [ ] 3. Each org has org-level `PLATFORM_CI_APP_ID` var + `PLATFORM_CI_APP_PRIVATE_KEY` secret pointing at 4035291; no repo-level shadow of either remains, and no live workflow still reads app 3896251 / `TERRAFORM_FRAMEWORK_GITHUB_APP_*`.
- [ ] 4. A Confluence page exists covering what the app is and may do, per-org setup, caller snippets per reusable, Dockerfile + Go/TF patterns, the 5-owner cap, why npm stays PAT, the shared-key risk, and rename/bot-login impact; linked from the repo README.
- [ ] 5. The rollout is announced in `#platform-engineering` / `#ilg-platform`, noting that turning the key on can surface new findings (private modules now scanned; custom Rego policies now enforced).

## Affected boundaries
<!-- Components, paths and contracts this touches. Wikilink existing explainers; do not restate
     their contents. If this names a topic, endpoint, canonical type, collection, inter-service
     dependency or shared package, sign-off will prompt for the Fuse MCP data file too. -->
- GitHub App 4035291 settings (owner account `gfs-dev`) — name/slug, bot login `ilg-platform-ci[bot]`, permissions.
- pr-sitrep in `gfs-bifrost/fuse-devtools` (`iac/projects/pr-sitrep/variables.tf:66` client id; Secret Manager `pr-sitrep-github-app-key` dev+prod) — the one prod service that authenticates as this app.
- Private-key homes: ilg-merak org secret, gfs-ecm org/repo secrets, gcp-config + ilg-tech-services-iac repo secrets/vars, pr-sitrep Secret Manager.
- Org installations: installed gfs-bifrost, gfs-ecm, gfs-hybrid-services, ilg-platform, ilg-tech-services, ilg-merak; missing gfs-sink, gfs-docs, gfs-selector, gfs-johnc-scrapyard; unknown gfs-cold-fusion, gfs-sre, gfs-customer-care, ilg-cx (ilg-cx is a known private-Go-module consumer, README:52-61).
- App 3896251 (terraform-framework) — still documented as `PLATFORM_CI_APP_ID` for ilg-tech-services-iac.

## Assumptions & uncertainty
<!-- One line each, with how it was established. A genuine product or domain question goes here
     as UNRESOLVED: and is raised with the user, never invented. -->
- App owner is the `gfs-dev` account — fuse-devtools known-context + ledger 2026-10-28.
- Live perms 2026-11-03: checks:read, contents:read, metadata:read, packages:write, pull_requests:write — `gh api orgs/*/installations`.
- Rename keeps app id, client id and key — GitHub behaviour; no repo code references the slug or bot login (grep + `git log -S`). Consumer repos (branch protection bypass, pr-sitrep filters) not yet swept.
- Installing into an org needs that org's owner via the UI (no user-token REST path) — Harry is owner of the four "missing" orgs.
- Shared key in every org + `repository_selection: all` ⇒ anyone who can edit a workflow with the secret can mint a token reading every private repo in the enterprise. Mitigations: org secret visibility = selected repos; split purpose-scoped apps; longer-term OIDC token broker.
- UNRESOLVED: new app name.
- UNRESOLVED: keep one app (contents:read + pr-sitrep's pull_requests:write + unused packages:write) or split a contents-read-only module-fetch app from pr-sitrep's app — precedent: secops issue-writer got its own purpose-scoped app. Split changes `PLATFORM_CI_APP_ID` for every caller, so decide before inc 3.
- UNRESOLVED: Confluence home — PLTE space, or the ECS-space "GFS Platform" hub that repo CLAUDE.md names as canonical?
- UNRESOLVED: full enterprise org list — needs an enterprise owner (or `read:enterprise` token).

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
- [ ] 1. Inventory: full enterprise org list; per org, install state + org-level var/secret; repo-level `PLATFORM_CI_APP_*` / `TERRAFORM_FRAMEWORK_GITHUB_APP_*` shadows; code-search `ilg-platform-ci[bot]` / `ilg-platform-ci` across every org. Written into this plan. (AC 2,3) — verify: table in this plan covers every enterprise org with no "unknown".
      gate: enterprise owner (or a `read:enterprise` + `admin:org` token) available
            [ ] confirmed
- [ ] 2. Rename the app (and, if split chosen, create the read-only module app with contents+metadata read only); drop unused `packages:write`. (AC 1) — verify: pr-sitrep dev then prod posts a sitrep after the change; `gh api orgs/ilg-platform/installations` shows new slug; any bot-login references from inc 1 updated.
      gate: new name + one-app-vs-split decided
            [ ] confirmed
- [ ] 3. Install on every missing org (UI, `repository_selection: all`), set org var + secret (visibility: selected repos where an org wants it tighter), delete repo-level shadows, retire 3896251 references. (AC 2,3) — verify: `gh api orgs/<org>/installations` per org; `gh api orgs/<org>/actions/variables` shows `PLATFORM_CI_APP_ID=4035291`; repo-level search returns none; one terragrunt caller per org green on next run.
- [ ] 4. Confluence page + README link. (AC 4) — verify: every snippet on the page copied into `ilg-platform/github-actions-canary` runs green; README links resolve.
      gate: code plan inc 1-6 force-moved onto `0.2-bonbon`
            [ ] confirmed
- [ ] 5. Announce via `platform-announcement` (Slack draft + Confluence blog). (AC 5) — verify: post sent by Harry, link recorded here.

## Verification
<!-- The single authority for evidence. Increment lines carry `— done: <sha>` and nothing else.
     Check-selection order lives in verification-menu.md — do not restate it here. -->

### Evidence
<!-- Newest first, dated. One bullet per check actually run, opening with what it discharges.
     "Suite green" alone is not evidence. Sign-off requires at least one dated bullet here. -->

### Not verified
<!-- Stated, not papered over. "(none)" is a deliberate claim, and a fine one. -->
- Everything — plan stage.

## Rollout & rollback
<!-- Added on demand. Written at plan time; amend in place as it changes.
     `Shared state touched:` is the single home for the five classes git does not own — a dev
     deploy, a prod config write, a Datadog monitor, a CI var or secret, cross-repo IaC. Reverting
     the branch undoes none of them, so if they are not written here they are not written down. -->

- **Order:** inventory → decide name/split → rename (pr-sitrep check) → installs + secrets → Confluence (after code plan on tag) → announce.
- **Flags/config:** org var `PLATFORM_CI_APP_ID` (=4035291, or new app id if split) and org secret `PLATFORM_CI_APP_PRIVATE_KEY` in every org; repo-level shadows deleted.
- **One-way doors:** the rename frees the old slug (another app can take it) — anything matching on `ilg-platform-ci[bot]` must be updated first. Deleting repo-level shadows can break callers whose repo value differed (e.g. pointed at 3896251) — verify each before deleting.
- **Rollback:** rename back (if slug still free); re-add repo-level var/secret from the inventory record; uninstall per org.
- **Shared state touched:** GitHub App settings (gfs-dev); org installations in every org; org + repo Actions vars/secrets in every org; pr-sitrep dev+prod (Secret Manager key unchanged unless rotated).

## Decisions & deviations
<!-- Date-stamped, newest first — written by `wp decide`, and by hand when that is easier.
     Where implementation departed from this plan, and why. Source wins over the plan: correct
     the plan in the same increment and record the correction here. Legitimately empty at plan
     time. A decision worth defending in a review six months out belongs in a durable record
     instead — `wp decide --record`. -->
- 2026-11-03 — npm/Node is out of scope: GitHub Packages' npm registry rejects App installation tokens (G5; github/docs#9547). Node cross-org stays PAT-backed.

## Learnings
<!-- Durable facts about the service surfaced while planning, working or testing that are not
     already written anywhere in the vault — a gotcha, a constraint, a fragile edge, a confirmed
     or refuted hypothesis. Not restated doc content. Sign-off promotes each confirmed one into
     the matching durable doc, then clears it from here; a refuted one moves to ## Handback
     rather than being deleted. Legitimately empty. -->
- App 4035291's private key has at least four homes (ilg-merak org secret, gfs-ecm org/repo, gcp-config repo, pr-sitrep Secret Manager dev+prod) — a rotation must touch all.
- Install dates: gfs-bifrost/gfs-hybrid-services/ilg-platform/gfs-ecm 2026-06-12; ilg-merak/ilg-tech-services 2026-10-24 — `gh api` installation `created_at`.
- `secops-reporting/plans/vulnerability-report-issue-writer.md:55` says the app is contents:read-only — stale since 2026-10-28.
