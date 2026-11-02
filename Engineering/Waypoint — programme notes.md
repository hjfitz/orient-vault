---
tags: [waypoint, programme]
updated: '2026-09-02'
title: Waypoint — programme notes
---
# Waypoint — programme notes

Why the suite is shaped the way it is, and what was decided when. Mechanics live in the skills
(`~/.claude/skills/waypoint-*/`) and `~/.claude/waypoint/wp.py`; this page carries the *why*.

## What Waypoint is for

Replace Gemini's Conductor with something whose source of truth is this vault, not a `conductor/`
directory inside each repo. One folder per service under `Engineering/`, holding durable context
(overview / architecture / known-context), plans, a ledger and explainers. Source is implementation
truth; git is forensic truth; plans describe intended and current work; the ledger records completed
work; explainers describe the system as it is now.

## Conductor parity (reviewed 2026-09-02)

| Conductor | Waypoint | Verdict |
|---|---|---|
| `setup` → product / tech-stack / workflow / styleguides | `waypoint-onboard` → overview / architecture / known-context (+ CLAUDE.md for workflow rules) | Equivalent |
| `tracks.md` master index | `Engineering/index.md`, `wp list`, `wp doctor` | Equivalent (doctor is stronger) |
| `new-track` → spec.md + plan.md | `waypoint-plan` → one plan: intent, acceptance criteria, increments | Equivalent |
| `implement` — task checkboxes mapped to commits, phase checkpoints | `waypoint-work` — increments with `done: <sha>` stamps, PR-based shipping | Equivalent since 2026-09-02; no mid-plan checkpoint by design (the PR is the checkpoint) |
| `status` | `waypoint-status` (ticket / service / nothing) | Equivalent |
| `review` — appends a Review Fixes phase | `waypoint-test` — a failure becomes an unchecked increment | Equivalent |
| `revert` by track/phase/task | none | Deliberate: Waypoint never touches a repo; git owns revert |
| Context lives in the repo | Context lives here, with **staleness anchors** (`verified_sha`/`verified_paths`) | Waypoint is stronger |

Things Waypoint has that Conductor doesn't: staleness anchors, the ledger/explainer split by
audience, a sign-off gate that reads real PR/CI/review-thread facts, ideation with a dedup log.

## The 2026-09-02 review — what was wrong

26 services onboarded; 2 ledger entries, 1 explainer, 5 plans, 0 ideation logs. Onboarding was used;
the lifecycle wasn't. Three causes, all fixed in the hardening pass:

1. **The loop didn't close.** Nothing observed merges; unclosed-waypoint detection needed `pr:` in
   frontmatter and never looked at the branch; `pr:` was only written at two optional moments.
   FUSE-866 merged 09-01 and sat `active`/`pr: null` until found by hand. → `wp doctor` (with
   branch-based PR discovery, ignoring PRs created before the plan) + `wp sync`, run daily by the
   morning digest; `waypoint-work` Step 1 checks the branch for a merged PR and goes straight to
   sign-off.
2. **`wp.py` had data-loss and crash bugs, and `signoff` gated the wrong things** — a `: ` in a plan
   title wiped its frontmatter on the next `set-status`; a digit-only sha crashed `stale`; acceptance
   criteria counted as unchecked tasks; TS generics counted as template placeholders; config-only
   plans couldn't be gated; exit code always 0. → All fixed; `signoff` exits 2 on BLOCKED and
   reconciles `done: <sha>` stamps against the real diff.
3. **Three read-only skills for one job.** → `waypoint-list` and `waypoint-locate` folded into
   `waypoint-status`.

## Decisions

- **`sync` does not rewrite date types on disk.** Reads normalise them, so sorting is safe; rewriting
  ~80 files for cosmetics (which would also reflow `tags: [a, b]` into block lists) wasn't worth the
  churn. Sync writes only when something is actually wrong (`pr:` backfill, numeric sha).
- **STALE-DOC gates `doctor`'s exit code.** 33 docs were behind source the first time it ran; they
  were all cleared the same day (see the sweep below). The daily exit-2 is the signal to refresh a
  doc, not noise to suppress.
- **A `repo:` override in `waypoint.yaml`** exists for a vault service whose code lives elsewhere
  (`snap-queue-polling-service` → `snap-adapter`). Without it the same-named archived checkout made
  every poller doc look unanchored.
- **The default branch is asked of the remote, not guessed.** When a checkout's `origin/HEAD` is
  unset, `wp` runs `git ls-remote --symref origin HEAD` rather than probing `main` then `master`.
  Found on `ilg-secure-notes` (2026-09-02): it carries both branches, its real default is `master`,
  and `origin/main` is a lone "Initial commit" on a disjoint history — so the main-first guess
  reported every doc as stale against a branch the work never lands on. Nine local checkouts have
  `origin/HEAD` unset, four of them carrying both names, so this was not a one-off. Offline
  fallback prefers the candidate with the newer tip instead of a fixed order.
- **`waypoint-plan` drafts with a fresh `Plan` agent and reviews with three parallel independent
  agents** (history/context, factual grounding, increment structure). The writer is deliberately
  denied `known-context.md`/ledger so the reviewers' cross-check catches real gaps rather than
  re-reading the same material. Not yet exercised on a real ticket (FUSE-1057 is the candidate).
- **Sign-off before merge is allowed** and noted, not blocked — a plan can be reconciled while the PR
  is in review; `doctor` catches the merged-but-unsigned case afterwards.
- **Writes to durable docs stay sign-off-only.** Planning/work/test add `## Learnings` candidates;
  only sign-off promotes them.

## The 2026-09-02 doc sweep

All 31 STALE-DOC findings cleared in one pass (15 services, six agents in parallel, one agent per
disjoint set of services). Two of the 31 turned out not to be drift at all, and both exposed a
class of bug in the anchoring itself rather than in the docs:

- **`ilg-secure-notes`** — the default-branch resolver picked `origin/main`, an abandoned
  one-commit stub on a disjoint history, when the real default is `master`. Every doc read as
  stale against a branch the work never lands on. Fixed by asking the remote (see Decisions).
- **`bifrost-pubsub`** — both docs were anchored to `331b811`, the *pre-squash* commit of a PR
  whose squashed form is the current tip. `git log <sha>..origin/master` still returns a plausible
  count for an off-branch anchor, so it read as one commit of drift against content-identical
  code. `wp doctor` now has an **ORPHAN-ANCHOR** section: any `verified_sha` that is not an
  ancestor of the default branch is reported as unmeasurable rather than counted as staleness.
  It caught a second instance in the same repo immediately on the next run.

The lesson for anchoring: **anchor after the merge, not from the branch**, in any repo that
squash-merges. And an anchor whose paths can't see the change that matters is worse than no
anchor — `fuse-mcp`'s `overview.md` was anchored to `README.md`/`AGENTS.md` while the fact it
asserted (mid-rewrite, traffic split in flux) lived in `iac/env/prod.tfvars`, so it went stale
invisibly and was only found by reading it. Several docs picked up widened paths in this pass for
that reason.

## Two gaps closed, 2026-09-02

A suite review after the sweep found the lifecycle complete but two things missing, both evidenced
rather than guessed:

- **Durable docs had no maintenance path.** Every write was gated behind sign-off, which only fires
  when a plan completes — and 21 of 26 onboarded services have never had a plan, so their docs could
  only rot. That is why 31 docs went stale and why the sweep had to be run by hand. Now
  **`waypoint-refresh`**: takes STALE-DOC / ORPHAN-ANCHOR / NO-ANCHOR from `wp doctor`, fans out one
  agent per service, re-anchors centrally. It is the only skill allowed to write durable docs
  outside sign-off, and it still may not write a ledger entry or touch `known-context.md`.
- **Programmes were invisible.** Five multi-repo programmes run from state docs under `Bifrost/`,
  each with its own hand-rolled skill, and `doctor` only ever looked at `Engineering/` — so one
  could stall for a month unnoticed. `doctor` now has a **STALE-PROGRAMME** section, finding state
  docs by their `migration-state` tag (folder names are prose, the tag is the discriminator),
  skipping terminal statuses, and flagging anything past the stale window. Non-gating, like
  STALE-PLAN.

Deliberately **not** built: a generic programme skill to replace the five bespoke ones. They work,
they are heterogeneous, and rewriting them buys nothing visible. The moment to build the generic
thing is when a sixth programme starts. Also declined: a revert skill (git owns it), a separate
close skill (`waypoint-work` owns sign-off), and plan archival (five plans is not a problem).

## Asking for input — the modal convention (2026-09-02)

Every skill that stops for input now carries the same three-line rule, because "prefer the modal"
turned out to be the wrong instinct: **a modal is a blocking stop**, so the question is not which
widget to use but whether to stop at all.

1. A sensible default exists → take it and say so. Don't stop.
2. You'd stop anyway and the options are knowable → `AskUserQuestion`.
3. Only the user holds the fact → prose. **Having to invent an option to reach the two-option
   minimum is the mechanical test that you are here** — an invented option anchors the answer, and
   the automatic "Other" escape does not undo that.

Converted to modals (all were already hard stops): the `waypoint-refresh` scope confirmation, a
blocked increment and a BLOCKED sign-off in `waypoint-work`, plan activation in `waypoint-plan`,
the discard reason in `waypoint-ideate` (already written as options in prose), and the
`onboarded: NO` prompt in `waypoint-ideate` only.

## Giving dev back (2026-09-02)

**Correction to the parity table above.** It dismissed revert with "git owns it". True for code,
false for shared state: a branch deployed to dev, a flipped flag, a re-pointed prod mapping —
git undoes none of those.

The concrete asymmetry was in `verify`: it announced *taking* dev to `#bifrost-general` and never
announced giving it back. FUSE-1050 is what that costs — QA re-tested, saw the old result and
bounced the ticket to *Rework Required*; the log carried a colleague's branch sha from the day
before, and the fix had never once been running when they looked.

`verify` now has a **Step 3b — Give dev back**: redeploy master, announce it in the same channel
and format as the taking so the two read as a pair, and skip it *explicitly* (saying who owns dev)
when the deploy is meant to stay, when Step 2 didn't deploy, or when someone else's branch landed
on dev meanwhile — reverting then would overwrite *their* work, not yours.

`wp signoff` adds a matching **note** (never a blocker — deliberate, since a deploy is sometimes
meant to persist): it reads the real deploy history rather than a bookkeeping field, because a
field claiming "put back" can lie and `gh run list` cannot. A failed deploy of your branch doesn't
count, and someone else's branch on dev is not yours to flag. It found a live instance the first
time it ran — dev is still on FUSE-1056's branch.

Scope was deliberately held to **dev deploys only** (Harry, 2026-09-02) rather than all shared-state
mutations. Config sweeps and flag flips are still tracked only in a plan's prose.

Deliberately left as prose: reviewer-surfaced ambiguity (`waypoint-plan`), product/domain ambiguity
(`waypoint-work`), "what should I scrutinise" (`waypoint-test`), and ideate's blank-page-avoidant
"what's been on your mind" — the whole value of that last one is what you *didn't* think of, which
by definition cannot be offered as options. Two of those skills already said "don't invent an
answer"; a modal there would have manufactured a menu of them.

Also deliberately left alone: the `onboarded: NO` prompt in `waypoint-plan` and `waypoint-work`.
It reads "offer it, don't halt" — already non-blocking, so modalising it would have *added* an
interruption. Same condition, different treatment in different skills, and that asymmetry is the
point: it tracks whether the skill was going to stop.

## The refit, 2026-09-04 — waves 1 and 2

A full review (8 parallel surveys, 4 themed design sets, 3 adversarial critiques) against
Conductor's current source and the wider spec-driven field. Harry picked 11 of 23 proposals;
waves 3 and 4 are deliberately held. What the review actually concluded, and what shipped:

**The correction that reframed it.** Conductor generates **one** file per track (`plan.md`);
`spec.md` appears once in 1,251 lines, conditionally, and there is no `metadata.json`. The
richness is all *project-level*, from `conductor:setup`. So "more structure" and "missing tech
stack/constraints/design" are **the same ask** — not more per-plan sections, but a stable
*address* for stack, commands and constraints. The design pass had it backwards (six proposals
grew the plan template 8 → ~15 headings, and a seventh existed to defend against the weight).
The default plan template therefore stays at **8 `##` headings**.

**Landed:**

- **R5** — `atomic_write()` (tmp + `os.replace`) behind all 8 write sites, plus an mtime
  compare-and-swap in `write_fm`/`_prepend_entry`. `cmd_sync` now **re-reads the file after its
  `gh` call** and re-applies only the keys it changed: it was reading a plan body, spending
  ~0.4s on the network, then writing the pre-network body back — vault-wide, daily, from the
  morning digest, targeting plans with no `pr:` yet (i.e. the ones being actively edited),
  reverting an edit with exit 0 in a store with no git history.
- **S0** — template guidance moved into HTML comments, and `find_placeholders`/`strip_placeholders`
  strip comments before scanning. Previously *every* `<angle span>` of guidance was a sign-off
  blocker, so each new section was a mandatory fill and the cheapest way to clear the gate was to
  **delete the guidance**. Measured: template placeholders 11 → 8, all genuine per-plan fills; a
  plan that fills the spans but keeps the comments now scores 0. The `## Verification` length gate
  still blocks on a section holding only its comment.
- **R6** — `dev_deploy_state` moved from sign-off-only into `wp context --plan`, and now into
  `plan_facts`. It is the suite's best cross-instance check and it was reachable only *after* the
  work was finished.
- **S7a** — `--reason` required for `--status blocked|abandoned`, stamped as `reason:` plus a
  `blocked_since:` that survives a re-block.
- **R1** — `cmd_signoff` split into `plan_facts()` + `gate()` + a printer (verified byte-identical
  on all 8 plans), then **`wp brief`** on top: zero-arg from a worktree, ≤30 lines, every fact
  derived and none stored, counts labelled with direction, and a whose-turn line. A persisted
  `## State` block was rejected — a cached copy of derived facts can be *stale*, a computed brief
  can only be *buggy*.
- **R0** — `waypoint-work` now runs `wp brief` at Step 1 (re-entry), after each increment, after
  the PR is recorded, and at sign-off, leaving it as the last thing in the terminal. The ask was
  for a push; every design proposal had delivered a pull.
- **M1** — `action-ticket` Step 0 checks `wp find <ticket>` before scoping (`grep -ci waypoint`
  over `action-ticket` and `create-pr` returned 0 and 0, against 8 plans for 40 merged PRs), and
  its shared-checkout `cd` instruction — which contradicted CLAUDE.md's worktree rule outright —
  is now a worktree.
- **M5** — `wp tick`, which stamps the sha from HEAD so the format cannot be mistyped; `TICKED_RE`
  widened to non-numeric ids; `NO-SHA` added to `doctor` (note-level), finding 5 real cases.
- **C6** — `doctor` prints the actual commit subjects with each STALE-DOC row, and STALE-DOC now
  gates **only for a service with an open plan**. Immediately legible: config-service's three
  findings all trace to one commit, and several rows are Renovate/secops noise.
- **C5** — a pointer line at the top of `MEMORY.md` (memory = inbox, vault = filed copy) — the
  only change here that alters what an agent knows without anyone running a command. Plus the one
  genuinely dangling wikilink, which pointed into the memory directory Obsidian cannot see.
- **D1** — the two dead rules deleted: the ~400-word plan cap (violated by 8 of 8 plans, 3.6x to
  14.7x) and the ~25-line `waypoint.yaml` cap (22 of 26). Both replaced by rules that bind
  ("every paragraph is something only this plan can say"; "every value is a fact, a path, or a
  command").

**The budget, from here on.** The plan template may not exceed **8 default `##` headings**; `wp`
may not exceed **22 top-level verbs** (17 now); `wp doctor` may not exceed **13 finding types**
(11 now). Every future proposal that adds must name what it replaces. And a standing rule adopted
from the review: **a `doctor` section that cannot reach zero on day one never ships** — which is
why MCP-DRIFT and a checkout-drift section were both refused.

**Deviation from D1 as picked.** D1 said delete the 22 free-prose `note:` blocks. Reading them
first showed 19 are durable orientation and among the best content in `waypoint.yaml` — deleting
them would have been data loss. The real bug is narrower and was proven live: **three carried
mutable machine state in the one file no staleness check can see.** `secops-reporting`'s read
"ACTIVE GO REWRITE IN PROGRESS RIGHT NOW... hours, not weeks" while its own programme doc says the
rewrite shipped 2026-08-27 and Node is decommissioned — 11 days stale and actively misleading. So:
those three rewritten to durable form, the field **declared** in the template with a rule against
machine state and dated snapshots, and the other 19 left alone.

**Two claims from the review that did not survive verification** (recorded because the review is
otherwise well-evidenced and this is where it wasn't): the widened `DONE_RE` was said to rescue
FUSE-1057's `(commit 32a08cd)` — no plan in the vault contains such a token, and the widening
currently rescues **zero** shas on real data. It is kept because it handles the
`— done 2026-09-02: <sha>` form authors plausibly write, and candidates are now resolved against
the repo before they count, so a hex-looking English word cannot become a phantom blocker. The
real fix is `wp tick`. Separately, a claimed worktree collision between two snap-adapter plans is
the documented `repo:` override, not a collision.

## Decisions taken 2026-09-04

- **The tmux tab keeps its no-auto-hook rule.** A turn-glyph in the tab would answer "which of my
  six windows needs me" before switching, but only Harry sets the tab. Declined; `wp brief`'s
  terminal push covers the need once you are in the window.
- **`known-context.md`'s staleness exemption is to gain a `(snapshot <date>)` marker** so `doctor`
  can age the expiring claims inside it without breaking the exemption for interview truth. A doc
  exempt *by policy* while full of dated snapshots is worse than an unchecked one, because the
  exemption reads as a guarantee. **Decided, not yet built** — it was not one of the 11 picked and
  needs a convention, a `doctor` check and a line in onboard/refresh.
- **Shared-state scope is reopened** beyond dev deploys to all five classes git does not own:
  dev deploys, prod config writes, Datadog monitors, CI vars/secrets, cross-repo IaC. This
  supersedes the 2026-09-02 "dev deploys only" decision, on new evidence (the four non-dev classes
  are now visible in real plans rather than hypothetical). **Its vehicle is S2's
  `Shared state touched:` bullet, which is in a held wave — so nothing records them yet.** Either
  pull that bullet forward on its own, or accept the gap until S2 lands.

**Also noticed, not fixed:** `Bifrost/SecOps API Go/Migration State.md` carries frontmatter
`status: in-progress` while its own body says "✅ Done. S4 shipped 2026-08-27." `wp doctor`'s
STALE-PROGRAMME reads the frontmatter, so it will keep flagging a finished programme.

## The refit, waves 3 and 4 — 2026-09-04

The remaining twelve proposals, plus the two decisions logged that morning. Three latent bugs
surfaced while building, all of which had been producing standing `doctor` findings for weeks.

**Bugs found and fixed (none of these were on the list):**

- **`locate()` ignored a `repo:` override whenever cwd contained a same-named directory** — which
  is always, from `~/code/fuse`. It treated a bare service name as a path *before* consulting the
  vault's own declaration, so `snap-queue-polling-service` resolved to the archived standalone
  checkout instead of the snap-adapter monorepo it actually lives in. That is the entire cause of
  the three NO-ANCHOR findings that had stood since the vault was created: the anchors were fine,
  the resolver was wrong. **NO-ANCHOR 3 → 0.** `repo_override` had the same cwd-relative hazard
  and was returning a *relative* path, which every later `git -C` then read from wherever it
  happened to run.
- **`PROGRAMME_TAG` was a string literal**, so `Tech Services IaC Review/Remediation State.md`
  (tagged `remediation-state`) was invisible to STALE-PROGRAMME. Any `*-state` tag or a
  `programme:` key now counts. **STALE-PROGRAMME 2 → 3** — the sixth programme, found by fixing a
  comparison rather than by looking.
- **`wp fleet` first put an APPROVED, green, open PR in WAITING ON A REVIEWER.** Approved and
  green is not the reviewer's turn any more, it is yours to merge. Caught by checking the buckets
  against real `gh` state rather than trusting them — #227 and #211 were both approved and both
  mis-bucketed.

**Landed:** `wp fleet` (grouped by whose turn, parallel gh calls, ~2.7s for eight plans, printing
its own bucketing rules so a miscall is visibly wrong) · `wp handback` (append-only, holds only
what cannot be derived; `wp brief` falls back to a derived `SINCE LAST LOOK` from git when there
isn't one) · `wp decide` in two modes, which also stamps `updated:` — previously set in exactly
one place in the CLI, so a plan worked hard all day never moved · `wp plan add-section` for
rollout/options, keeping the default template at 8 headings · the `gate:` marker, which blocks
sign-off on a ticked increment above an unconfirmed precondition · `## Verification` as the single
authority with `### Evidence` / `### Not verified` · one supersession marker replacing the six that
had grown in one plan in ten days · decision records under `decisions/` · guardrails · the
runtime/commands block · snapshot markers · programme linkage · the stall-and-abandon path.

**Deliberate tolerances, so none of this flipped existing work red:**

- The Verification gate is **strict for new plans, tolerant of old ones**: a dated bullet under
  `### Evidence` is required only when that section exists. Measured first — only 2 of 8 plans
  had dated bullets, so a hard gate would have flipped six to BLOCKED, two of them carrying
  thousands of characters of real evidence.
- AC coverage is reported **only when some increments already cite `(AC n)`**, so a plan that
  cites none is not nagged about all of them.
- `section()` became level-aware so `### Evidence` cannot end its own parent. Verified zero plans
  used `###` first, making it a no-risk change.
- Guardrails live at the top of **`architecture.md`**, not `known-context.md`. Refresh already
  maintains architecture.md; known-context.md is exempt from anchors by design, so a path-tagged
  checkable list there would have had no writer able to fix a dead path. (This was option (b) of
  the two offered; Harry didn't pick between them, so the argued-for one was taken.)

**C1 backfill: 24 of 26 services.** Derived from each repo's real manifests read at
`origin/<default>`, never the working tree — several checkouts are weeks behind and one was parked
on a merged branch, exactly the class of fact this block must not inherit. Two are **deliberately
left empty and need a human**: `fuse-mocker` (apps/api Go + apps/ui Next) and `secops-reporting`
(api/ Go + ui/ Next) have two apps on different stacks, and picking one root would be a coin toss
that then reads as fact. A wrong command is worse than no command. `fuse-mcp` is derived as Go
(root `go.mod` + `Makefile` beats a leftover `package.json` awaiting the S4 teardown).

**Q2 built.** Seven expiring claims across six `known-context.md` files now carry
`(snapshot <date>)` — dated with the date the claim already asserted, never today, which would
have reset a clock nobody had actually re-checked. `STALE-SNAPSHOT` ages them at 60 days and is
**0 on day one**, per the standing rule.

**Q3's vehicle now exists.** `Shared state touched:` shipped inside `wp plan add-section rollout`,
so the five classes git does not own finally have a home. The reopening decision from this morning
is no longer stranded. **Kill criterion, to be honoured literally:** if that bullet is empty on
every plan a month from now, delete it.

**Budgets after both waves:** `wp` 20 verbs / 22 · `doctor` 12 finding types / 13 · plan template
8 default `##` headings / 8. The template is at its cap: anything further must replace a heading,
not add one.

## Open

- `FUSE-866` stays `active` until QA confirms the live SFTP file (increment 6); it is the one
  expected `UNCLOSED` finding.
- `collector/pubsub.tf` claims every subscription has a `retry_policy`; six don't (WOC/FGR
  `confirmation_ready`, `confirmation_made` ×2, `confirmation_data_failure` ×2). Candidate fix PR.
- `secops-reporting`: `api/diffcheck` is a committed 8.7 MB binary; `ui/CLAUDE.md` still points at
  `api/src/*` paths that no longer exist. Repo-side cleanups, not vault work.
