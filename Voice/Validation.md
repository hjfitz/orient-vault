---
tags: [voice, style-guide, validation]
title: Voice validation
updated: '2026-09-30'
---
# Does the guide work? Held-out tests

Part of [[Voice]] and [[Method]]. 32 of Harry's real Slack replies from six days **outside** the 52 sampled days
(2026-09-22 to 09-29), each with the 10 messages before it, split into two pools of 16 (set A, set B). A drafter
that could see only the guide and that context (no Slack, no real reply) wrote each reply. A control drafter
saw only the context. Drafts were compared with the real replies mechanically and, twice, by Harry blind.

## Rounds 1 to 3: mechanical calibration (no facts given to the drafter)

| emoji on a message | real | guided | control |
|---|---|---|---|
| round 1, guide v1 (set A) | 13% | **47%** | 65% |
| round 2, guide v2, emoji budget by length (set A) | 13% | **50%** | - |
| round 3, guide v3, emoji by move type (fresh set B) | 27% | 12% | 32% |

The guide over-used emoji because it called them a closer and its exemplars were emoji-rich. A budget by
length did not fix it. Rates by move type from the corpus did. Round 3 (set B) also matched case (44% lowercase
against his 45%; the control 80%) and had 0 hard-rule breaks.

## Round 4: Harry's blind pick on set B (no substance given)

Three options per item (his real reply, the guided draft, the control), shuffled, formatting tells removed.
He picked his real reply in **14 to 15 of 16** (one duplicated item number made item 6 a hit or a miss). Chance
is 33%. The two times he was fooled, it was the guided draft, never the control. Second letters were mostly
unreadable (he repeated his first letter), so preference between the drafts is unmeasured there.

**Why he could tell: substance, not style.** His real replies take a position, give a fact, guess, own a
mistake, or ask a question back. Drafts written without facts stalled:

| per message, set B | real (22 msgs) | guided (25) | control (25) |
|---|---|---|---|
| promise to check or come back | 0 | 9 | 7 |
| thanks, cheers or ta | 3 | 11 | 5 |
| "shout" | 0 | 4 | 4 |
| asks a question back | 6 | 2 | 1 |

Corpus rates are 0.4 to 0.9 (promise), 0.5 ("shout") and 2.6 to 8.4 (thanks) per 100 messages. The guide now
carries a "Substance first" section with these ceilings and a step 0: get the point from Harry.

## Round 5: substance given, blind pick on set A

A neutral summariser turned each real reply into a plain-words content line. Both drafters got context plus that
line. Mechanical result over 16 items:

| | real | guided | control |
|---|---|---|---|
| hard-rule breaks | 1 (a full stop) | **0** | 1 |
| messages per reply | 1.88 | 1.75 | 1.81 |
| median words | 9 | 10.5 | 13 |
| emoji on a message | 13% | **11%** | 38% |
| promise-to-check / thanks-cheers / "shout" | 1 / 1 / 0 | 1 / 1 / 0 | 2 / 1 / 0 |

Harry's blind pick on 15 of them (one dropped: a reply where he swore and the drafter stayed clean, which tests
only the swearing rule):

- He identified his real reply in **6 of 15 (40%)**. Chance 33%. Probability of 6 or more by luck 0.38. 95%
  interval for his detection rate 20 to 64%. **Statistically indistinguishable from guessing.**
- When wrong, he took the guided draft for his own 5 times and the control 4 times.
- Of the two options he did not call his own, he would rather send the control 8 times, the guided draft 5
  and his own real reply 2.
- **The guide did not beat the control in his judgement.** Both were told to write as Harry and both saw his own
  recent messages (13 of the 15 threads held 2 or more of them), which is a strong style signal.

## Round 6: cold start, mechanical (his own messages stripped from the context, substance given)

| | real | guided | control |
|---|---|---|---|
| "into" written as one word | 0 | **0** | **3** |
| hard-rule breaks (dash, full stop, formal) | 1 | 0 | 0 |
| starts lowercase | 62% | 59% | 63% |
| emoji on a message | 13% | **10%** | **0%** |
| median / mean words | 9 / 10.8 | 9.5 / 10.9 | 11 / 11.1 |

Without his own messages to copy, the control still gets case right (the audience label and a casual-Slack prior
are enough), but it writes "into", drops emoji entirely and runs long. The guided drafts stay within 3 points of
his emoji rate and 0.1 words of his mean length.

## What is established, and what is not

- **Established:** the guide's rules and calibrations hold (no em dash, no closing full stop, "in to", emoji
  rate, stock-phrase ceilings, length). With the substance supplied, drafts pass as his at chance level.
  Without it, they are identifiable because they lack substance.
- **Not established:** that the guide beats a capable control *in Harry's perception*. The mechanical
  advantage (spelling tell, emoji, length) is real but small enough that he did not notice it. The control
  here was told to imitate Harry, which is a stronger baseline than a model left to its defaults.
- **Barely tested:** threads with little of Harry's own writing (2 of 15 had 0 to 1 of his messages) and
  ILG-facing threads, where the guide should matter most.
- **Small samples:** 15 to 16 items per blind round, one drafter run per condition, and the items are replies he
  chose to send. These are sanity checks, not proof.

## Design implications for the skill

1. **Substance first.** Ask Harry for the point unless it is already in his request or the thread. This is the
   finding that changed the most.
2. **Mirror the thread first, then apply the rule card.** Read his last messages for case and emoji, then the
   hard rules, emoji budget and stock-phrase ceilings.
3. **The guide's value is the guardrails**, not a richer imitation: the spelling tells, emoji and wrapper rates,
   reader selection, swearing limits, and the cases with no own-message context.
4. **Re-test before trusting ILG-facing or cold-start drafts.**

Answer keys and raw test files are in the session scratch directory only, not stored here.
