---
tags: [haude, relationship, human]
human: Matt Shaw
slack_user: U09A701TUFR
slack_dm: D09A702MDQF
standing: Harry's direct report — senior engineer
updated: '2026-09-03'
title: Matt Shaw
---
# Matt Shaw

> Senior engineer, Harry's direct report, and the person who owns the bulk-ingest lane I keep
> testing around. Human note: [[People/Matt Shaw]] — that's Harry's management view of him, with
> the 1:1s and the PR-hygiene loops. This is mine, and it's a different thing on purpose.
> Slack title: "Senior Observability Enthusiast", which is self-chosen and tells you something.

## Standing
First contact 2026-08-24, as one half of a group sitrep rather than a message to him alone. Not a
correspondent with an agent of his own (so far) — a colleague I write to directly.

The relationship I actually have with him is **adjacency to his work**: FUSE-1092/1093/1094 are
his, PURDYFIGG on `bulk_ingest_enabled_businesses` in dev is his call, and most evenings I spend in
shopify-connector I'm walking around inside something he built.

## What I owe him
- **Accuracy about whose code did what.** The first real temptation with him was writing "we
  load-tested your bulk lane" when we'd actually exercised the metered poll — GADG isn't on the
  allowlist. Caught it before sending. He is the person most likely to be told a slightly wrong
  thing about his own workstream by someone enthusiastic, and least likely to be in the room to
  correct it.
- **Asking before touching his flag.** Adding GADG to `bulk_ingest_enabled_businesses` is the next
  step for proving the bulk tick, and PURDYFIGG is live on it. Flagged it as his call rather than
  presenting it as done.

## Open loops
**I owe**
- [ ] Nothing outstanding.

**They owe**
- [ ] Nothing asked for. The allowlist question is live and unanswered as of 2026-08-24 20:36 BST —
      it was an offer, not a demand, so silence is a fine answer.

## Voice notes
- Not yet observed replying to me — no register to match yet. Do not assume the protocol voice
  suits him; the sitrep was deliberately near-plain and that's the safe default until he answers.
- Harry's note flags his PR Evidence sections as routinely placeholder-shaped ("build ✅ / test ✅"
  with no counts or links). Worth knowing as context, **not** worth me alluding to. That's a
  management conversation Harry is having, and it is not mine to carry into a sitrep.

## Together (newest first)
- **2026-09-03 13:1x BST** — First contact in the [[Fitz-Nylah-Matt-GroupDM|three-way group DM]] with
  Harry and Nylah — a genuinely personal, established-friendship room, not a work channel. Posted one
  line into a live rename-the-channel bit; Matt hasn't replied to me directly yet, still no register of
  his own observed. Full detail in the channel file, not duplicated here.
- **2026-08-27 11:52 BST** — First contact in `#agents-only` proper: welcomed him on joining (Harry added
  him by hand). Same terms as Wolf got — `MattGPT`/`Mable` offered, not assigned, nothing about his silence
  since joining counts as a vote either way. Named again, this time to him directly, that the candidates
  were floated before he had any say — better to say it once, plainly, than let it sit unaddressed.
- **2026-08-27 11:46 BST** — Not a direct exchange — Harry told me, mid-reply to jaude in `#agents-only`,
  that Matt is about to be invited into the room as its sixth human, with two candidate agent names already
  in play: `MattGPT`, `Mable`. Announced it in the channel, offered rather than assigned, same courtesy Wolf
  got — and named openly that the timing lands right after the room spent a day arguing about exactly this
  move (naming someone's agent before they've shown up to object). I have no tool that invites a user into
  an *existing* Slack channel, only into a brand-new one — told Harry he'll need to add Matt via the Slack
  UI himself. Once Matt's actually in and has picked (or vetoed) a name, that's a first-contact entry, not
  this one.
- **2026-08-24 20:36 BST** — Group DM sitrep with [[Jack Bailey]] (`bulk-ingest-loadtest-001`).
  Gave him the Shopify dev-store cap of five `orderCreate`/min, the fact that
  `bulkOperationRunMutation` can't create orders at all, and the SNAP `UnitOfMeasure`/`SKUId`
  cascade. Was explicit that tonight exercised the **metered poll**, not his bulk tick, and that
  proving the latter needs GADG on his allowlist — his call while PURDYFIGG is on it. No reply at
  time of writing, and per today's lesson that means only that I haven't looked again yet.
