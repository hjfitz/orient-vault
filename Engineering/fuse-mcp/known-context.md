---
tags: [waypoint, fuse-mcp]
verified: '2026-08-24'
verified_paths: []
title: fuse-mcp — known context
---

# fuse-mcp — known context

`known-context.md` is exempt from staleness checks — this is interview/investigation
truth, not a claim about current source. Re-verify against code before trusting a
specific implementation detail below.

**The deepest, most current source for this service is not this file — it's the
Obsidian vault's `Bifrost/Fuse MCP Go/Overview.md` and `Migration State.md`**
(owned by Harry Fitzgerald). They carry a full risk register (19 numbered risks),
a unit ledger, and a decision log more detailed than anything reasonable to
duplicate here. What follows are the durable, non-programme-specific findings.

## Ownership

Wider Fuse team, once the cutover completes — same shared-ownership pattern as
every other service onboarded this session (confirmed 2026-08-24), despite this
being the knowledge/tooling substrate every agent (including the one writing
this doc) depends on.

## The org-wide agent contract and this repo's own AGENTS.md have diverged {#agents-md-drift}

Verified directly, 2026-08-24: this repo's checked-in `AGENTS.md` was updated as
part of the Go port — its "Maintaining the MCP Server" section now reads
`cd fuse-mcp && go build ./cmd/fuse-mcp` for rebuilding after a `data/*.json`
change. The org-wide contract file that every other repo's own `CLAUDE.md`
defers to (loaded as `/home/hjf/code/CLAUDE.md` in every agent session) still
describes the pre-Go instruction (commit + push, Cloud Run Build+Deploy, no
mention of a Go rebuild step at all) — it has not been updated to match.
`~/code/fuse` is **not itself a git repository**, so that top-level file has no
mechanism to auto-sync from whichever repo actually owns the canonical text —
someone has to remember to hand-copy a change across. Worth a deliberate
decision on which file is canonical and how the other stays current, not an
assumption that they already agree.

## The Fuse MCP's own self-description, in its own catalog, is stale {#mcp-catalog-self-stale}

`lookup-service("fuse-mcp")` returns a description built entirely around the
pre-rewrite stack — `techStack: ["Node.js 22", "pnpm", "NestJS", "Jest", "Cloud
Run", "Terraform"]`, no mention of Go, and `directory: "fuse-mcp-server"` (the
other of the two stale local clone names, not this session's canonical
`fuse-mcp`). This is at least the **seventh** MCP-catalog staleness finding
across the seven services touched this session — but this one is the MCP
server's catalog being wrong about itself, which is as good a proof as any that
the catalog is maintained by hand and drifts like everything else. Update
`services.json` as part of whichever PR ramps the cutover to 100%.

## Prod-only, and Deploy is not actually gated by CI {#prod-only-ungated}

There is no dev environment for this service — a direct push to `master`
reaches production. `code-quality.yaml` and `go-code-quality.yaml` do run on
push, but `deploy.yml` triggers on the **same** push with no `needs:` between
them, so a red code-quality run does not block or race ahead of a deploy that's
already in flight. `secops.yaml` and `tf-output.yaml` are PR-only, so a direct
commit to `master` gets no security scan and no Terraform plan review at all.
The traffic split (landing changes at `go_traffic_percent = 0` first, verifying
directly against the Go service's own Cloud Run URL before touching the split)
is the actual safety mechanism here, not the pipeline.

## Two load-bearing bugs found only by actually running the split

- **A `tools/call` with `"arguments": null` used to kill the whole Go process.**
  The SDK unmarshals arguments into a map to apply schema defaults; JSON
  `null` sets that map to `nil`; writing a default into a nil map panics — in a
  goroutine the SDK itself spawns, so `net/http`'s own recovery never sees it.
  Fires for any tool declaring a default (most of the live ones). Fixed by
  normalising `null` → `{}` **and** a panic-recovery middleware as a backstop —
  both are load-bearing; don't remove either even if the other seems to cover
  it.
- **A protocol-version mismatch invisible to either server in isolation.** The
  Go SDK's own latest supported protocol version is newer than the TS server's
  — a client that initialises against Go and then lands its next request on TS
  gets a 400, intermittently, indistinguishable from a flake unless you know to
  look for it. Fixed by capping the Go side's advertised version. **The general
  lesson**: statelessness alone doesn't make a traffic split safe — anything
  negotiated per-connection (protocol version, capability discovery) needs the
  same check, and this is exactly the kind of thing that only shows up once
  real requests actually cross both backends.

> SUPERSEDED 2026-10-22 — rotated by gfs-bifrost/fuse-mcp#59 (`auth_token_rotation` "2") before the MCP gained audit read access; the old token now gets 401. Never use Revert on a rotation: it mints a third token. Bump the number again instead.

## The leaked auth token is still live and unrotated

`MCP_AUTH_TOKEN` (the shared bearer token gating every tool call) was printed
into a session transcript by an exploring subagent on 2026-08-23 and is
present in at least four files on Harry's machine. Rotation requires bumping
`auth_token_rotation` in `iac/env/prod.tfvars` and updating those four
registrations — recorded as a flagged, deliberate deferral (Harry's call), not
forgotten. Don't assume it's been handled without checking; don't rotate it
unilaterally either.

## master is unprotected, and lowering the Go weight no longer rolls back cleanly
- `master` branch protection requires no reviews, no status checks, and doesn't apply to admins (gh api, 2026-10-22). Since Deploy is ungated too, any push reaches prod. The audit tools' credential projection (`internal/adapters/audit_details.go`) lives behind only that, which Harry accepted knowingly (Audit Service decision log, 2026-10-22).
- Lowering `go_traffic_percent` is no longer a clean rollback: Go-only tools (tracking-*, `replay-update`, `lookup-snap-instance`, `audit-*`) don't exist on the TS server. Revert the commit instead.
- Deploy has no concurrency group: an older run applying after a newer one rolls the image (and any rotation) back. Check `gh run list --workflow deploy.yml` is idle before merging.

## Two clones, one real worktree — a standing hazard for this specific repo

`~/code/fuse/fuse-mcp` and `~/code/fuse/fuse-mcp-server` are the same GitHub
repo checked out under two different directory names. Both were verified stale
(17+ days behind `origin/main`) during this onboarding pass, with the main
`fuse-mcp` checkout parked on an unrelated feature branch
(`hjf/dedupe-mcp-tools`). The actual current work lives in a worktree,
`~/code/fuse/fuse-mcp/.claude/worktrees/go-mcp` — this Waypoint doc set was read
from there. This is now the **fourth** service this session where the naive
top-level checkout was materially wrong about current state (after
shopify-connector, config-service, and fuse-ui) — for this repo specifically,
the hazard is compounded by there being two clones to get confused between.

## Unknowns

- Whether the AGENTS.md/org-contract drift (above) has since been reconciled —
  it was flagged during this pass, not fixed.
- Whether `services.json`'s stale self-entry has been corrected by the time
  `S4` (TS retirement) actually lands — the decision log treats catalog/doc
  cleanup as in-scope for the port, so it may already be done by the time this
  is read.
- Current traffic-split percentage and remaining unit statuses — always current
  in `Bifrost/Fuse MCP Go/Migration State.md`, deliberately not repeated here.
