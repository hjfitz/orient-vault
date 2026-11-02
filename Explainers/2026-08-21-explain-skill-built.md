---
tags: [explain]
date: '2026-08-21'
title: 'Built the explain skill, then rebuilt it BLUF and orient-native'
thesis: "The explain skill was built on 2026-08-21 as a mermaid-diagrammed Obsidian write-up, then rebuilt on 2026-10-12 as a BLUF, orient-native explainer. Only the rebuilt design is current."
confidence: high
---
# Built the explain skill, then rebuilt it BLUF and orient-native

```orient-bluf
{ "v": 1, "bluf": "The explain skill was built on 2026-08-21 as a mermaid-diagrammed Obsidian write-up, then rebuilt on 2026-10-12 as a BLUF, orient-native explainer. Only the rebuilt design is current.", "confidence": "high", "action": "none" }
```

## Situation
- **CONFIRMED** Harry asked for an `explain` skill for high-signal write-ups. It had to differ from the digest skills (periodic rollups) and `incident-postmortem` (Confluence, blameless). [1]
- **CONFIRMED** The first version took one decision flow. With no target it explained the conversation in context. With a named target (PR, ticket, incident, service, code path) it researched fresh first. [1]
- **CONFIRMED** The first version wrote plain Obsidian pages. It added a mermaid diagram only when a diagram carried information prose could not. [1]
- **CONFIRMED** The 2026-08-21 page described that design as live. This page replaces it. The design below is current, and the mermaid design is not. [2]

## Assessment
- **CONFIRMED** The 2026-10-12 rewrite changed the skill's format. The current skill writes for orient, not Obsidian. [2]
- **CONFIRMED** Each page opens with one `orient-bluf` block: conclusion, confidence, action. Every claim leads with a basis tag (`CONFIRMED`, `ASSESSED`, `UNKNOWN`) and cites numbered evidence. [2]
- **CONFIRMED** The skill no longer writes mermaid. It uses `orient-flow` for structure, `orient-sequence` for ordered calls, and tables or lists otherwise. [2]
- **CONFIRMED** Event pages use Situation, Assessment, Open items and Evidence. They stay under about 600 words. [2]
- **CONFIRMED** The rewrite added a system mode (`--system <service>`) and a drift check (`--check`). Both are absent from the first version. [2][3]
- **CONFIRMED** The rewrite shipped a lint (`lint-explainer.mjs`) and a drift tool (`explain-drift.py`). Both carry a 2026-10-12 modified date. [3]
- **CONFIRMED** The 2026-08-21 session also tripped a memory-index size hook. It ran a compaction pass: 21,559 to 17,508 bytes. 16 entries moved to `ARCHIVE.md`, 3 deleted, the rest trimmed. [1][4]
- **UNKNOWN** Whether the skill ever ran on a real PR, ticket or incident target before the rewrite. The original page left that untested and recorded no later run.
- **CONFIRMED** Harry ordered the rewrite on 2026-10-12. Explainers no longer need to be Obsidian-readable markdown. The skill now targets a high-signal, military-style page with a BLUF.

## Open items
| Item | Owner | By |
|---|---|---|

## Evidence
```orient-evidence
{
  "v": 1,
  "items": [
    { "id": 1, "kind": "doc", "ref": "Explainers/2026-08-21-explain-skill-built.md (original page, 2026-08-21)", "note": "first design, mermaid, memory compaction figures" },
    { "id": 2, "kind": "doc", "ref": "~/.claude/skills/explain/SKILL.md", "note": "current skill, read 2026-10-12" },
    { "id": 3, "kind": "doc", "ref": "~/.claude/skills/explain/lint-explainer.mjs and explain-drift.py", "note": "files dated 2026-10-12" },
    { "id": 4, "kind": "doc", "ref": "~/.claude/projects/-home-hjf-code-fuse/memory/reference_explain_skill.md", "note": "memory pointer written 2026-08-21" }
  ]
}
```
