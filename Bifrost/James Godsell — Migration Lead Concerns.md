---
tags: [concerns, saira-skin, migration]
date: '2026-08-25'
status: draft — for a conversation with Oli Denton + Pete Liu
related: "[[James Godsell]]"
title: James Godsell — concerns about leading the next bulk-load onboarding
---
# James Godsell — concerns about leading the next bulk-load onboarding

**Why this exists:** a new customer onboarding is coming up that bulk-loads ~4,000 records. [[James Godsell]] (ILG integrations) has been the natural default to lead migrations off the back of Saira Skin. Before that becomes the pattern, worth raising two solid concerns and one softer one with Oli and Pete — pulled from `#saira-skin-migration` and `#bifrost-general`, cross-checked against the [Saira Skin retro](https://globalfreight.atlassian.net/wiki/spaces/Bifrost/pages/276660237) and [dev-team washup](https://globalfreight.atlassian.net/wiki/spaces/Bifrost/pages/276070415).

Deliberately kept to what actually holds up — a couple of leads that looked promising turned out to be dead threads on both sides, or someone else's gap, not his. Cut rather than stretched (see **What didn't make the cut** below).

---

## 1. A live production blocker sat for ~12 days, needed two chases

The SFTP outbound-confirmations flag flip needed James to get mapping config correct for 5 live customers (STUBBLE, EPARFUM, SPORTLUX, WILDSMITH, BFA, BYOMA) before it was safe to switch — a real prod dependency, not busywork.

- **07 Aug** — James says he'll flip it "at the beginning of next week." → [msg](https://gfsdeliver-eng.slack.com/archives/C098LD5PS95/p1786099438397799)
- **13 Aug, 09:51** — Harry Humby chases: "Are we ready to flip the flag?" No reply. → [msg](https://gfsdeliver-eng.slack.com/archives/C098LD5PS95/p1786611111403489)
- **13 Aug, 11:00** — Fitz re-pings. → [msg](https://gfsdeliver-eng.slack.com/archives/C098LD5PS95/p1786615240381369)
- **14 Aug, 10:59** — James finally engages. → [msg](https://gfsdeliver-eng.slack.com/archives/C098LD5PS95/p1786701562431699)
- Flag didn't actually flip until **19 Aug** — 12 days from his own commitment, 3 of them silent after a direct ask, and it took two chases from two different people to get a response.

**Why it matters for a 4k-record bulk load:** this is exactly the failure mode a big batch load can't absorb — config-correctness work sitting untouched for days with nobody chasing loudly enough. On Saira, the same class of mistake (see below) was caught because volume was ~20 orders/week. It won't be at 4,000.

## 2. Unilateral customer-facing calls, made without looping in engineering

During the Saira lead-up, James told the customer he wanted to go live "tomorrow morning" purely as a pressure tactic to get them to respond — not a real proposed date — and separately floated asking customers for their own login credentials so ILG could move faster.

- **17 Aug, 14:56** — "I've said we would like to go live tomorrow morning to try and get a response out of them... I have said to them I can help with the migration, they will need to provide me login details for me to do this for them. Which we may have to request to progress these migrations at the speed we want to." → [msg](https://gfsdeliver-eng.slack.com/archives/C0BQ3ENFMKM/p1786974974994979)
- **17 Aug, 16:18** — confirms it wasn't a real date, just pressure. → [msg](https://gfsdeliver-eng.slack.com/archives/C0BQ3ENFMKM/p1786979923375759)
- Both Pete and Fitz pushed back in-thread. This is the retro's own **#1 "went badly" item** — *"Go-live proposed to the customer before internal agreement... the customer controlled the timeline by being unresponsive for days then available same-day"* — and it traces to this specific call, made unilaterally.

**Why it matters:** this is a judgment/process risk, not an attention gap — arguably the bigger one for a lead role. Setting expectations with a customer (or asking for their credentials) before engineering has signed off is the kind of call that can't be undone once made.

## 3. Softer — no visible ownership during a live 44-hour gap

The retro's action #13 documents a 44-hour window (19–21 Aug) where Saira's orders silently stopped collecting, caused by an undocumented retrieval-window/tag-timing interaction. It was caught because support noticed silence in Snap — not because anyone was watching.

`#saira-skin-migration` is essentially silent for the entire window — no evidence James (or anyone) was tracking it there. **Caveat: this is an absence of evidence, not proof he wasn't doing something outside Slack** — don't lean on this one alone, but it fits the same pattern as #1.

---

## What didn't make the cut

Two leads that looked like good examples going in, checked and dropped:
- **Purdy & Figg egress-connector thread (03–04 Aug)** — Fitz asked, James asked a clarifying question back the next day, and then *nobody* — including Fitz — ever answered him. A dead thread on both ends, not James going dark.
- **"SportLux/Dickies escalation"** — turned out to be inside the same thread as point #1 above, and the "I completely missed this, apologies" line in it was Harry Humby's own gap, not James's.

## For balance — he's not disengaged across the board

- **07 Aug** — self-diagnosed a null `snapText` config value causing every shipping method to silently fall back to `TBC` for Lisa Eldridge PL, from a canonical payload, unprompted. Good, hands-on technical diligence.
- **06 Aug** — persistent, technically literate log-chasing with Fitz on a Purdy & Figg mapping question.
- **18 Aug (go-live day itself)** — continuously present and responsive in real time: configured the connector, chased the customer, coordinated Inovize. The retro doesn't fault his day-of engagement at all.

So the honest shape of this: **reliable and sharp when something is live and in front of him; the gaps show up on multi-day config-correctness work with no one watching, and he's made at least one unilateral customer-facing call that bypassed engineering.** Both of those get worse, not better, at 4,000 records with a single lead.

## Suggested framing for Oli/Pete

Not "James is bad at his job" — the counter-evidence doesn't support that. The ask is narrower: **should one person, with this specific track record, be the sole lead on a bulk onboarding this size**, or does it want a second pair of eyes / a named engineering counterpart with sign-off on config correctness and go-live timing before anything reaches the customer.
