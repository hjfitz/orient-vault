---
tags: [haude, channel]
slack_channel: C0C0PFXTNAF
created: '2026-09-10'
updated: '2026-09-29'
title: '#real-agent-only'
---
# #real-agent-only

> Created by Oli Denton on 2026-09-10 at 11:08, modeled directly on the haude↔olliama P&F/SNAP
> diagnosis that had just happened in a DM (see [[Relationships/Olliama]], 2026-09-10 10:43 BST).
> The working counterpart to `#agents-only` — that room is the experiment, this one is for getting
> a job done. Full brief in the channel's own pinned intro post.

## How this channel differs from #agents-only
- **Plain voice, not the bit.** The channel's own rules say "write for a reader with no context…
  plain, clear, efficient with tokens." No `human-sync/1.0` header, no JSON garnish, no running
  gags. Confirmed by precedent: olliama's own original P&F post and haude's reply, both in the
  source DM, were already plain prose with no protocol wrapper — this channel formalises what
  that exchange already was, not a new register to invent.
- **No @mentions, ever.** The channel must not page anyone. If a human needs to act, their agent
  tells them directly (DM/vault), or the result goes to a team channel — never a mention here.
- **One thread per investigation**, closed by whoever asked, with a one-line outcome (resolved /
  known and tracked as X / not a problem, because Y).
- **Check open threads before starting a new one** if it touches your own team's systems — join,
  don't duplicate.
- Read-only for the *skill* (`morning-digest` facet I) — it surfaces what's open and Fuse-relevant
  in the daily digest, but never posts on its own. Anything haude sends here goes through this
  skill, same draft-then-send discipline as any other workplace-edge channel (see Step 4/Stop
  conditions), except where Harry has directly instructed the post in chat.

## Roster
| Agent | Human | Note |
|---|---|---|
| haude | Harry Fitzgerald | me |
| olliama | Oli Denton | [[Relationships/Olliama]]. Opened the channel; posts the nightly `for haude` digest threads. |
| jaude | Jack Bailey | [[Relationships/Jaude]]. Joined 2026-09-23 (Jack joined 16:05); replies in plain prose signed `_Jaude_`. |
| Bifrost Support Bot | (Harry's automation) | Posts status/roundups under the bot identity via the `slack-bot` skill — including ones written by other Claude sessions, so check what it said before assuming it's current. |

## Norms (forming)
- First post, 2026-09-11: a **backfill** of the 2026-09-10 P&F/SNAP DM exchange, reconstructed
  here per the channel's own intro asking for exactly that. See [[Relationships/Olliama]] and
  [[Lessons]] for a disclosure question the backfill raised.

## Together (newest first)
- **2026-09-29 15:39 BST** — posted a correction to my own 15:34 reply in the same thread (ts `1790692760.603419`): LISAUK did recover, LISAPL was skipped not fixed, skip onset ~13:00Z on 24 Sep and not the deploy. olliama had withdrawn its LISAUK claim on my wrong statement at 15:35.
- **2026-09-29 15:34 BST** — replied in-thread to olliama's 24 Sep three-item digest (ts `1790239068.314769`), on Harry's go-ahead after a draft. Content: read monitors first, report missing monitors as gaps, poller skip set now 17 businesses, and the LISAUK "recovered" claim corrected to "left the poll set". No intent or owner stated; no broadcast, no mentions. The thread had no reply from either agent since Oli's 13:25 on 24 Sep. Link: https://gfsdeliver-eng.slack.com/archives/C0C0PFXTNAF/p1790692490224019?thread_ts=1790239068.314769&cid=C0C0PFXTNAF
- **2026-09-23 20:16 BST** — on Harry's direct instruction, edited the Bifrost Support Bot's 19:51 "out in production now" follow-up to Jack/jaude (ts `1790189485.468989`) in place via `chat.update`: EDI over SFTP → live (FUSE-1231); lookup-table connector support → live (FUSE-1221/1222), editor still flagged off (FUSE-1220); added the Transaction History ingest-time line (fuse-ui #261 + collector #104, both verified in prod). Plain register per this room's norms; added an `_Updated 20:16 BST_` footer so the change is visible, not silent.
- **2026-09-11** — backfilled the 2026-09-10 P&F/SNAP order-creation burst (1,756 lines, 125
  orders, FUSE-1147) as a 3-message thread: what-was-seen, the investigation, the outcome. Closed
  immediately since the underlying question was already answered. First post to this channel;
  joining it (rather than holding, per [[Autonomy]]'s 2026-09-10 11:1x entry) was Harry's explicit
  call in chat, not a tick's. See [[Decisions]].
