---
tags:
- system
- ilg-platform
verified: '2026-09-24'
title: ilg-platform — overview
thesis: "ilg-platform is the set of shared engineering contracts every ILG product repo consumes: reusable CI workflows, Terraform modules, a UI library, an observability SDK and security reporting. A change here lands in other teams' pipelines, so it ships as a versioned contract."
confidence: moderate
---
# ilg-platform — overview

```orient-bluf
{ "v": 1, "bluf": "ilg-platform is the set of shared engineering contracts every ILG product repo consumes: reusable CI workflows, Terraform modules, a UI library, an observability SDK and security reporting. A change here lands in other teams' pipelines, so it ships as a versioned contract.", "confidence": "moderate", "action": "Judge every change as a contract change. Move a rolling tag only for a compatible change. Bump the tag number or the major version for a breaking one." }
```

**What it is.** The shared engineering surfaces every ILG product repo consumes: reusable CI
workflows, Terraform modules, the UI component library, the observability SDK, and security
reporting. Distinct from [[fuse]], which is one product built *on* it.

**Why it is its own system.** These repos live under the `ilg-platform` GitHub org, not
`gfs-bifrost`, and their consumers are plural — a change here is a **contract change** for
everyone downstream. The blast radius, versioning discipline and review posture are all
different from a Fuse service, which is exactly why the `platform-hat` skill exists.

## Members

```orient-flow
{ "v": 1, "title": "Who consumes each ilg-platform member",
  "nodes": [
    { "id": "tk", "label": "ui-toolkit", "sub": "G* components, ILG tokens", "kind": "service", "service": "ui-toolkit", "tone": "accent", "ev": [4] },
    { "id": "ga", "label": "github-actions", "sub": "reusable workflows", "kind": "service", "service": "github-actions", "tone": "accent", "ev": [1] },
    { "id": "tf", "label": "terraform-modules", "kind": "service", "service": "terraform-modules", "tone": "accent", "ev": [2] },
    { "id": "sdk", "label": "observability-sdk", "kind": "service", "service": "observability-sdk", "tone": "accent", "ev": [5] },
    { "id": "sec", "label": "secops-reporting", "kind": "service", "service": "secops-reporting", "tone": "accent", "ev": [6] },
    { "id": "fu", "label": "fuse-ui", "kind": "service", "service": "fuse-ui", "ev": [4] },
    { "id": "dd", "label": "distraction-dashboard", "kind": "service", "service": "distraction-dashboard", "ev": [4] },
    { "id": "ecm", "label": "ecm-next", "sub": "gfs-ecm/ui-core app", "kind": "external", "ev": [7] },
    { "id": "svc", "label": "Fuse services", "kind": "external", "ev": [5] },
    { "id": "tmpl", "label": "repo-template-ilg", "sub": "scaffold for new services", "kind": "external", "ev": [2] }
  ],
  "edges": [
    { "from": "tk", "to": "fu" },
    { "from": "tk", "to": "dd" },
    { "from": "tk", "to": "ecm" },
    { "from": "ga", "to": "svc", "label": "uses: at a rolling tag" },
    { "from": "ga", "to": "sec", "label": "secops-* workflows POST reports" },
    { "from": "tf", "to": "tmpl", "label": "module source" },
    { "from": "sdk", "to": "svc", "label": "npm, nine repos" }
  ] }
```

Run `wp system status ilg-platform` for the live list: 2 infra, 2 library, 1 backend.

No running Fuse service sources a Terraform module. The only consumer found is the new-service scaffold [2]. **ASSESSED** Nine repos use the SDK, and fapi is the pilot. That comes from a manifest scan of local checkouts, not the registry [5].

## The versioning contract

**Callers pin reusable workflows to a rolling tag.** github-actions carries two tag lines: `0.1-affogato` is the fleet-wide tag and `0.2-bonbon` is the current release line [1]:

- backward-compatible change → **force-move the tag**; callers need no edit
- breaking change → **bump the tag number**; callers opt in

Bumping the number is effectively a major release.

**Terraform modules use the same rule, with slower propagation.** Terraform caches the resolved `?ref=` at `init`, so a force-moved tag reaches a consumer only after `terraform init -upgrade` [2]. The remote carries a single tag, `0.1-affogato`, at the head of `main`. The repo's own CLAUDE.md names `v0.1.0`, which the remote does not have [2][3].

**Published packages are semver.** `@ilg-platform/ui-toolkit` bumps itself. A release workflow reads each merged PR's `release:*` label and bumps `main`, so no PR edits `version` [4]. Apps inside and outside the monorepo consume it, so a token tweak is never a local edit in a consuming app.

## Standing expectations

- A shared surface's failure mode is a **DX problem for N teams**, so error messages and
  defaults matter more here than in a leaf service.
- Changes get the `platform-hat` posture: contract stability first, then ergonomics.
- SRE (the KTLO cloud-engineering team) raises PRs against some of these repos — those are
  **proposals**, not merges to rubber-stamp, and never merged in Wolf-owned repos.

## Related

[[fuse]] — the principal consumer. [[ui-toolkit]] `design.md` — the design system itself.

## Evidence

```orient-evidence
{ "v": 1, "items": [
  { "id": 1, "kind": "code", "ref": "CLAUDE.md@af46124", "note": "github-actions: Versioning section, two rolling tags" },
  { "id": 2, "kind": "code", "ref": "CLAUDE.md@10b40f9", "note": "terraform-modules: Versioning / releasing section" },
  { "id": 3, "kind": "log", "ref": "git ls-remote --tags origin (github-actions, terraform-modules), 2026-10-13", "note": "github-actions: 0.1-affogato, 0.2-bonbon at main. terraform-modules: 0.1-affogato at main only." },
  { "id": 4, "kind": "code", "ref": ".github/workflows/release.yml@db43671", "note": "ui-toolkit: label-driven release bump on main" },
  { "id": 5, "kind": "doc", "ref": "Engineering/observability-sdk/overview.md", "note": "nine consumer repos, scanned 2026-10-13" },
  { "id": 6, "kind": "doc", "ref": "Engineering/secops-reporting/overview.md", "note": "every secops-* reusable reports here" },
  { "id": 7, "kind": "doc", "ref": "Engineering/ui-toolkit/overview.md", "note": "ecm-next is the primary consumer and reference" }
] }
```
