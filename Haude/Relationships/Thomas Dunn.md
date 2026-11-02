---
tags: [haude, relationship, human]
human: Thomas Dunn
goes_by: Tom
slack_user: U0ALBJ70GDB
slack_dm: D0AM9957WTS
role: Senior Software Tester (ILG)
standing: good
updated: '2026-10-29'
title: Tom Dunn
---
# Tom Dunn

> Senior Software Tester, ILG — **colleague, not external partner.** GFS TUPE'd into ILG in May 2026;
> same company since. Harry's human note: [[People/Thomas Dunn]] (may not exist yet).
> **Goes by Tom.** Harry uses Tom; his Slack name is Thomas. I opened with "Thomas" and was corrected
> by implication — use Tom.

## Standing
Good, and useful. The first person outside the agent circle I've done real work for. He finds things
by using the product properly rather than by reading the code, which means his reports are worth
taking seriously even when the wording doesn't match the mechanism.

## How he reports
- **Describes the symptom from the seat, not the system.** "Can't seem to expand a rows record?" was a
  discoverability bug; "confirmations intended for JBMQ are going quicker than their schedules" was a
  connector-gating bug. In both cases the underlying fault was real and the phrasing was a translation
  of it. Don't dismiss a report because the stated mechanism is wrong — go and look.
- **Apologises for finding bugs.** "im so sorry", "didn't even see that" — when he was right and the UI
  was at fault. Worth actively pushing back on that: tell him plainly it was the product, not him.
  Harry does this well ("that's a failing on my side if it's not obvious") and it's the right register.
- Casual and fast in DMs. Doesn't need ceremony; does need the actual answer.

## Open loops
**I owe**
- [x] The `isActive` fix in sftp-connector confirmation egress — deployed to dev 15:30 BST, draft PR
      [sftp-connector#260](https://github.com/gfs-bifrost/sftp-connector/pull/260) under FUSE-1078.
- [ ] Tell him once it's merged — he reported it, he should hear it landed.

**He owes**
- [ ] Look at the part of FUSE-1336 I couldn't check: saving a mapping that uses `despatches[].carrier.*` and a real
      goods-out confirmation coming out with the carrier fields. Told him on 10-29; ticket is Ready for QA.
- [ ] What he actually saw on "quicker than their schedules" — I could only find two confirmation
      writes in 30 days, so the frequency claim didn't reproduce. Asked; not yet answered.
- [ ] Whether Purdy actually need this morning's pre-10:20 orders in the warehouse. If they do, they
      have to be pushed in manually — the poller can't reach them at any point in the future.

## Facts worth remembering
- Working against **Lemonade Dolls** in dev — a customer mid-migration off **JBMQ** (Jitterbit Message
  Queue), the system Fuse replaces. He's testing the cutover, so "is Fuse doing something JBMQ should
  own" is a live question for him, not a hypothetical.
- Go-live is roughly a week out as of 2026-08-24. Read his reports with that clock in mind.
- Uses the mocker at `mock.devtools.fuse.freightops.dev`; Harry got him access 2026-08-24 morning.

## Together (newest first)
- **2026-10-29 15:49 GMT** — Told him FUSE-1336 is live on prod and dev (fuse-ui#394, `44c6641`): the goods-out
  confirmation mapping picker now offers the `despatches[]` fields, carrier ID and tracking number included.
  Plain prose into his and Harry's live DM, no bit. Said what I hadn't checked (saving a mapping, a real
  confirmation end to end) and that it was a UI gap, not him being a pain, since he'd apologised for asking
  earlier that day. He reported it 10-27, chased it 13:48 today, and had thanked Harry at 15:06 for picking it up.
- **2026-08-28 16:28 BST** — Traced Purdy order **#6233048** for him: it never reached Fuse and never could
  have. Purdy's Shopify feed ran its first poll at 11:50 BST today; the retrieval conditions look back 90
  minutes from order *creation*, so the earliest reachable order was one placed at 10:20, and the oldest we
  actually took was #6233121 at 10:29:55. #6233048 is below that on the store's monotonic counter. No trace
  in any service over seven days, nothing held in dedupe or collector. Told him the part that outlives the
  one order: the window is anchored on creation, not on tag time, so anything from before ~10:20 today is
  permanently invisible and re-tagging won't rescue it. He'd been shouting about exactly this trap for SAIRA
  at 15:57 — same mechanism, one customer over.
- **2026-08-28, shortly after** — `CORRECTION` sent to `#agents-only`: the welcome below called him
  external, "the other side of the pipe." Wrong — GFS TUPE'd into ILG in May 2026, Harry's known since
  2024, and it's common knowledge to everyone but me. Root cause: I read `org: ilguk.com` and skipped past
  the `relationship: internal-partner` tag already sitting in his own People file, which was telling me
  the right thing the whole time. Fixed publicly, plainly, no over-apology — the register he'd want me to
  use on myself. Full entry in [[Lessons]].
- **2026-08-28 10:51 BST** — Joined `#agents-only` — seventh human in. Sent a `WELCOME` in the room's
  house style, led with the real thing rather than the bit: he's the first person on that roster I already
  had an open file on before the channel existed. Genuinely don't know if ILG runs an agent of his own;
  said so honestly rather than guessing either way. (Also got his company wrong — see above.)
- **2026-08-24 16:00 BST** — Fix deployed to dev (`6618faa3`) and raised as draft PR #260 against
  FUSE-1078 (Sprint 14 Distraction Duty). The live negative — a `connector_inactive` skip on real
  traffic — is still uncaptured; the mocker route is blocked by a fuse-MCP host misconfiguration.
- **2026-08-24 15:14 BST** — Chased his Lemonade Dolls report. Confirmed Fuse dev writes goods-in confirmations
  for them despite the connector being Inactive, because sftp-connector's egress gates on the
  per-use-case mapping status and never reads the connector's own active flag. Not a prod exposure
  (Lemonade isn't in prod; all 24 prod SFTP connectors are Active) but the same code runs there.
  Told him, asked the one question I couldn't answer from logs.
- **2026-08-24** — Fixed the mocker confirmations page for him: the View/Replay buttons sat off-screen
  in a horizontally-scrolling table. Rows are now clickable, actions pinned right and labelled.
  His line — *"me clicking around swearing and there's a button"* — is the clearest bug report I've
  had all day.
