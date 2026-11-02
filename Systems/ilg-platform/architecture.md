---
tags:
- system
- ilg-platform
verified: '2026-09-24'
title: ilg-platform — architecture
thesis: "ilg-platform has no runtime. It ships contracts that consumers pin: a workflow tag, a module tag or a package version. The posture follows from that: judge each change as compatible or breaking, because someone else's pipeline finds out first."
confidence: moderate
---
# ilg-platform — architecture

```orient-bluf
{ "v": 1, "bluf": "ilg-platform has no runtime. It ships contracts that consumers pin: a workflow tag, a module tag or a package version. The posture follows from that: judge each change as compatible or breaking, because someone else's pipeline finds out first.", "confidence": "moderate", "action": "Before moving a tag or publishing, search the orgs for consumers. An additive change that alters a default is breaking." }
```

Five repos with one thing in common: **their consumers are plural**. There is no runtime here
— nothing in this system serves traffic as a system. What it ships is *contracts*: a workflow
you pin, a module you instantiate, a component you import.

That is the whole architecture, and it dictates the posture.

## What each contract looks like

```orient-flow
{ "v": 1, "title": "What each consumer pins",
  "nodes": [
    { "id": "ci", "label": "Caller CI", "sub": "uses: workflow@tag", "kind": "external", "ev": [1] },
    { "id": "ga", "label": "github-actions", "sub": "rolling tag, resolved every run", "kind": "service", "service": "github-actions", "tone": "accent", "ev": [1] },
    { "id": "iac", "label": "Service iac/", "sub": "module source ?ref=tag", "kind": "external", "ev": [2] },
    { "id": "tf", "label": "terraform-modules", "sub": "rolling tag, cached at init", "kind": "service", "service": "terraform-modules", "tone": "accent", "ev": [2] },
    { "id": "app", "label": "App package.json", "sub": "semver range", "kind": "external", "ev": [3] },
    { "id": "tk", "label": "ui-toolkit", "sub": "label-driven semver", "kind": "service", "service": "ui-toolkit", "tone": "accent", "ev": [3] },
    { "id": "sdk", "label": "observability-sdk", "sub": "semver, five packages", "kind": "service", "service": "observability-sdk", "tone": "accent", "ev": [4] }
  ],
  "edges": [
    { "from": "ci", "to": "ga", "label": "pins tag" },
    { "from": "iac", "to": "tf", "label": "pins tag" },
    { "from": "app", "to": "tk", "label": "installs" },
    { "from": "app", "to": "sdk", "label": "installs" }
  ] }
```

| Contract | What a consumer pins | Compatible change | Breaking change |
| --- | --- | --- | --- |
| Reusable workflow | Rolling tag (`0.1-affogato`, `0.2-bonbon`) | Force-move the tag | Bump the tag number |
| Terraform module | Rolling tag, `?ref=` | Force-move the tag; consumers run `init -upgrade` | Cut the next tag |
| Published package | Semver range | Minor or patch publish | Major publish |

secops-reporting is the fifth member. It ships no pinned contract: it is a deployed API that the `secops-*` workflows call [5].

**Rolling tags and semver behave differently and that is deliberate.** A workflow fix should
reach every caller without a PR in each one, so the tag force-moves. A package's consumers pin
explicitly, so a fix needs a bump and a republish — and will not reach a consumer that reads
it *through* another package until that one is bumped too.

A force-moved Terraform module tag is slower: it sits inert until the consumer runs `terraform init -upgrade`, and the reviewed plan is the safeguard [2]. Two tag lines can coexist. github-actions keeps `0.1-affogato` for the fleet and `0.2-bonbon` for the current line, so a compatible fix needs both tags moved [1].

## Change lifecycle

```orient-flow
{ "v": 1, "title": "Change lifecycle",
  "nodes": [
    { "id": "prop", "label": "Proposed change", "kind": "step" },
    { "id": "comp", "label": "Compatible", "sub": "additive, no default changes", "kind": "step", "ev": [1] },
    { "id": "brk", "label": "Breaking", "sub": "renamed, removed, default changed", "kind": "step", "tone": "alert", "ev": [1] },
    { "id": "moved", "label": "Tag force-moved", "kind": "step", "ev": [1, 2] },
    { "id": "pub", "label": "Minor or patch published", "kind": "step" },
    { "id": "bumped", "label": "Tag number bumped", "sub": "0.1 to 0.2", "kind": "step", "ev": [1] },
    { "id": "major", "label": "Major published", "sub": "check every consumer", "kind": "step" },
    { "id": "mig", "label": "Consumers migrate", "kind": "step", "tone": "accent" }
  ],
  "edges": [
    { "from": "prop", "to": "comp" },
    { "from": "prop", "to": "brk" },
    { "from": "comp", "to": "moved" },
    { "from": "comp", "to": "pub" },
    { "from": "brk", "to": "bumped" },
    { "from": "brk", "to": "major" },
    { "from": "bumped", "to": "mig" },
    { "from": "major", "to": "mig" }
  ] }
```

The expensive path is the breaking one. Most of the judgement in this system is deciding
honestly which side a change is on — an "additive" change that silently alters a default is
breaking, and will be discovered by someone else's red pipeline.

## Posture

- **Failure here is a DX problem for N teams.** Error messages, defaults and docs carry more
  weight than in a leaf service.
- SecOps scanning gates on high/critical in production dependencies; triage before bumping —
  allowlist with an expiry is the default response, an override needs a demonstrated exploit
  route [6].
- SRE raises PRs against some of these repos. They are **proposals**.

## Related

[[fuse]] — the principal consumer. [[ui-toolkit]] — the design system.

## Evidence

```orient-evidence
{ "v": 1, "items": [
  { "id": 1, "kind": "code", "ref": "CLAUDE.md@af46124", "note": "github-actions: rolling tags, two lines, force-move rule" },
  { "id": 2, "kind": "code", "ref": "CLAUDE.md@10b40f9", "note": "terraform-modules: ?ref= pin, init -upgrade caching" },
  { "id": 3, "kind": "code", "ref": ".github/workflows/release.yml@db43671", "note": "ui-toolkit: bump derived from release:* labels" },
  { "id": 4, "kind": "doc", "ref": "Engineering/observability-sdk/overview.md" },
  { "id": 5, "kind": "doc", "ref": "Engineering/secops-reporting/overview.md" },
  { "id": 6, "kind": "doc", "ref": "~/code/CLAUDE.md", "note": "Security Scanning section" }
] }
```
