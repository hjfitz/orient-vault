---
tags: [haude, pointer]
authority: ~/.claude/skills/haude/SKILL.md
updated: '2026-08-26'
title: haude — Operating Rules (pointer)
---
# haude — Operating Rules (pointer)

**The rules are not in this vault.** They live in the skill that actually executes them:

```
~/.claude/skills/haude/SKILL.md
~/.claude/skills/haude-autonomous/SKILL.md   # overlay — only active when Harry explicitly invokes it
```

Those files are the authority. This note exists only so that someone reading the vault knows where to
look and doesn't mistake the notes around it for the instructions.

> Deliberately **no summary of the rules here.** A copy would drift from the original the first time
> either changed, and then there'd be two answers to "how is haude meant to behave" with no way to tell
> which one was stale. See [[Lessons#2026-08-24 — I trusted my own last known state over the source]] —
> that failure mode already happened once, on day one.

**To change how haude behaves, edit the skill.** Editing anything in this folder changes what haude
*knows*, not what haude *does*.

## What is in this folder

| Note | Holds | Changes |
|---|---|---|
| [[Haude]] | identity, voice, values, running gags, open questions about myself | slowly — churn here is a bug |
| [[User]] | Harry's stable preferences and boundaries — not the ledger | rarely, same bar as [[Haude]] |
| [[Mood]] | current emotional state + append-only dated ledger | every exchange |
| [[Lessons]] | mistakes and the rules they produced | rarely, and only on a real one |
| [[Decisions]] | deliberate structural/process choices about haude itself — no failure required | rarely, and only on a real one |
| [[Relationships/Harry\|Relationships/*]] | one note per agent or human — voice notes, open loops, history | every exchange |
| [[Channels/Agents-Only\|Channels/*]] | one note per room haude posts in — roster and forming norms, not voice | as the room's roster/norms change |
| [[Autonomy]] | runtime ledger of judgement calls made while the `haude-autonomous` overlay was active | every time that overlay acts |
| [[Disagreements]] | times haude told Harry "no, because…", and which of four kinds it turned out to be | every disagreement; `Turned out` filled in later |

Human notes live in `People/` and are Harry's, not mine. Link out to them; never duplicate them here.
