---
tags: [explain]
date: '2026-09-01'
thesis: "waypoint-work drives one vault plan through six steps to sign-off and calls other skills only when a step needs them."
confidence: high
title: 'Actioning a Waypoint plan runs waypoint-work''s six-step lifecycle over one vault file, pulling in other skills only when a step needs them'
---
# Actioning a Waypoint plan runs waypoint-work's six-step lifecycle over one vault file

```orient-bluf
{ "v": 1, "bluf": "waypoint-work drives one vault plan through six steps to sign-off and calls other skills only when a step needs them.", "confidence": "high", "action": "none" }
```

## Situation

- **CONFIRMED** The 2026-09-01 page explained what "actioning a plan" involves. Skills and `wp.py` have changed since, so this version rechecks it on 2026-10-12. [1][5]
- **CONFIRMED** A plan is one file, `Engineering/<service>/plans/<stem>.md`. The stem is a ticket key or a slug. [1][6]
- **CONFIRMED** Each onboarded service holds `overview`, `architecture`, `interfaces`, `operations` and `known-context` docs. It also holds `waypoint.yaml`, `ledger.md`, and `explainers/`, `plans/` and `decisions/` folders. [6]

## Assessment

- **CONFIRMED** `waypoint-work` owns the lifecycle. Other skills feed it or run around it, and do not chain into it. [1][2][3][4]

| Skill | Role |
|---|---|
| `waypoint-onboard` | Offered when `wp context` reports `onboarded: NO`. Never forced. |
| `waypoint-plan` | Writes the plan file, in an earlier session. |
| `waypoint-test` | Runs on a risky increment (Step 2) and for extra evidence (Step 3). |
| `verify` | Deploys the branch to dev and drives the real flow (Step 3). |
| `action-ticket` | Not invoked. Step 3 reuses its Steps 3-6 mechanics. |
| `create-pr` | Opens the draft PR. |
| `explain --system` | Writes the service's system explainer at sign-off. |

```orient-flow
{
  "v": 1,
  "title": "waypoint-work lifecycle",
  "nodes": [
    { "id": "s0", "label": "Step 0: resolve ticket", "sub": "wp fleet if none given", "ev": [1] },
    { "id": "s1", "label": "Step 1: orient", "sub": "wp brief, wp doctor", "ev": [1] },
    { "id": "s2", "label": "Step 2: increments", "sub": "wp tick stamps sha", "ev": [1] },
    { "id": "s3", "label": "Step 3: ship", "sub": "verify, create-pr draft", "ev": [1] },
    { "id": "s4", "label": "Step 4: ship for real", "sub": "gh pr ready, Slack, Jira", "ev": [1] },
    { "id": "s5", "label": "Step 5: sign-off", "sub": "wp signoff", "tone": "accent", "ev": [1] },
    { "id": "blk", "label": "BLOCKED", "sub": "report, do not complete", "tone": "alert", "ev": [1] }
  ],
  "edges": [
    { "from": "s0", "to": "s1" },
    { "from": "s1", "to": "s2" },
    { "from": "s1", "to": "s5", "label": "PR already merged", "style": "dashed" },
    { "from": "s2", "to": "s3" },
    { "from": "s3", "to": "s2", "label": "red", "style": "dashed" },
    { "from": "s3", "to": "s4", "label": "user says ready" },
    { "from": "s4", "to": "s5", "label": "PR merges" },
    { "from": "s5", "to": "blk", "label": "exit 2" }
  ]
}
```

- **CONFIRMED** Step 0 resolves the ticket. A bare invocation runs `wp fleet` and offers up to four plans where the user holds the turn. [1]
- **CONFIRMED** Step 1 runs `wp brief`, which derives every fact live: increments, branch state, real PR state, whose turn it is. [1]
- **CONFIRMED** Step 1 also checks the `MODEL` line against model routing. An under-powered session halts before Step 2. [1]
- **CONFIRMED** Step 2 pushes guardrails with `wp context --paths`. It ticks each increment with `wp tick`, which stamps the commit sha. [1]
- **CONFIRMED** Two failed attempts on one increment stop the work. The agent writes `wp handback` and reports. [1]
- **CONFIRMED** Step 3 runs tests, lint and both build checks, then commits, pushes, deploys to dev and captures evidence. It opens a draft PR and stops. [1][7]
- **CONFIRMED** Step 4 runs only on the user's go-ahead: `gh pr ready`, the `#bifrost-forge` post, the Jira "Code Review" transition. [1]
- **CONFIRMED** Step 5 runs on request or on a successful merge. `wp signoff` exits 2 when BLOCKED. [1]
- **CONFIRMED** On PASS the agent reconciles the plan against the diff and sets status `complete`. It then appends a ledger entry and runs `explain --system`, updating before creating. [1]
- **CONFIRMED** It then promotes confirmed learnings into durable docs, re-anchors with `wp verify`, runs `wp index`, and flags Fuse MCP data files. [1]
- **ASSESSED** The design rule is to load only what a step names. `wp brief` and `wp context` give state and indexes, not whole docs. [1]
- **ASSESSED** The `wp` subcommands behave as the skill describes. This pass checked that they exist, not their output. [5]

### Corrections to the 2026-09-01 page

- **CONFIRMED** The lifecycle now has six steps (0-5), not five. Resolving the ticket became Step 0, and orient moved to Step 1. [1]
- **CONFIRMED** Orientation uses `wp brief`, not `wp context --plan`. `wp context` remains for reasoning and guardrails. [1]
- **CONFIRMED** Step 3 reuses `action-ticket` Steps 3-6, not 3-7. Its Step 7 matches Step 4 here. [1][7]
- **CONFIRMED** The CLI grew from 12 to 22 subcommands. They include `brief`, `tick`, `fleet`, `handback`, `decide`, `doctor`, `programme`, `system` and `sync`. [5]
- **CONFIRMED** New controls: `gate:` lines on increments, the model-routing check, and the two-attempt stop. `waypoint-programme` and `waypoint-refresh` exist, and `waypoint-work` does not call them. [1]

## Open items

| Item | Owner | By |
|---|---|---|
| Run `wp brief` and `wp signoff` on a live plan to confirm output matches the skill text | Harry | 2026-10-19 |

## Evidence

```orient-evidence
{
  "v": 1,
  "items": [
    { "id": 1, "kind": "doc", "ref": "~/.claude/skills/waypoint-work/SKILL.md", "note": "six-step lifecycle, read in full 2026-10-12" },
    { "id": 2, "kind": "doc", "ref": "~/.claude/skills/waypoint-plan/SKILL.md", "note": "writes the plan; --plan takes a stem" },
    { "id": 3, "kind": "doc", "ref": "~/.claude/skills/waypoint-test/SKILL.md", "note": "verification pass invoked from Steps 2 and 3" },
    { "id": 4, "kind": "doc", "ref": "~/.claude/skills/waypoint-onboard/SKILL.md", "note": "onboarding prerequisite and default doc set" },
    { "id": 5, "kind": "doc", "ref": "~/.claude/waypoint/wp.py", "note": "python3 wp.py --help lists 22 subcommands" },
    { "id": 6, "kind": "doc", "ref": "~/Documents/obsidian/Engineering/sftp-connector/", "note": "per-service vault layout, listed 2026-10-12" },
    { "id": 7, "kind": "doc", "ref": "~/code/.claude/skills/action-ticket/SKILL.md", "note": "Steps 3-7 numbering" }
  ]
}
```
