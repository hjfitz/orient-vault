---
tags: [person]
role: Migration Lead
org: ILG (external to Bifrost team)
relationship: internal-partner
reports_to: "[[Lee Simmons]]"
team: Migration
title: James Godsell
comms: "Plain-language, reassurance-first; short, one idea at a time; no jargon or fault-admission; point to one self-serve place."
---
# James Godsell
> ILG-side contact, surfaces on Saira Skin Shopify migration and the Fuse-Bifrost Weekly Sync distribution.

## Coordinates
- Slack: <@U0BJVEJ4BGT>
- Email: james@ilguk.com

## Open loops
**I owe**
- [ ] Reply to him and raise the ticket: he wants `identifiers.solLineId` selectable in the pick and pack confirmation line mappings, as on the dispatch confirmation (10 Nov 10:55 UTC, answering my 5 Nov question, with [[Matt Shaw]], [[Tom Dunn]] and Liam Andrews on the thread) — [email](https://outlook.office365.com/owa/?ItemID=AAMkADVhYjUxODIyLWM5NTktNGJmOC1hN2FjLWFjMjllNWUzYmY4MwBGAAAAAAAEXHdKGOMeRLfpaU7ff8ChBwABLsgQpFdPTayXOZTVrraLAAAAAAEMAAABLsgQpFdPTayXOZTVrraLAAHc35JzAAA%3D&exvsurl=1&viewmodel=ReadMessageItem)
- [ ] Confirm the multi-stores change is in prod — [thread](https://gfsdeliver-eng.slack.com/archives/C0C8Q398DC4/p1793099765390759)
- [ ] Follow up on the Engraving meta-fields once the ticket exists; I told him I'd update him — [RE: Engraving email](https://outlook.office365.com/owa/?ItemID=AAMkADVhYjUxODIyLWM5NTktNGJmOC1hN2FjLWFjMjllNWUzYmY4MwBGAAAAAAAEXHdKGOMeRLfpaU7ff8ChBwABLsgQpFdPTayXOZTVrraLAAAAAAEMAAABLsgQpFdPTayXOZTVrraLAAHHiU5sAAA%3D&exvsurl=1&viewmodel=ReadMessageItem)
- [ ] Tell him whether it is ok to replay the fixed Byoma mapping records (carried since 2026-09-22) — [digest](../Digests/2026-10/2026-10-09.md)
- [ ] Send Byoma TRF04208, TRF04257 and TRF04280 through to Snap, or tell him why not — [Slack](https://gfsdeliver-eng.slack.com/archives/C098LD5PS95/p1790693695351559?thread_ts=1789999974.819089&cid=C098LD5PS95)
- [ ] Confirm whether line-level VAS is viable in FUSE today for the Escentric Molecules ECOM → Shopify connector — the "RE: Engraving" thread now ends on my side (09-07)
- [ ] Send the Fuse↔Snap field document he asked for in DM (09-02 09:49) — agreed same-thread ("I'll get a one-pager together") but not yet sent — [Slack](https://gfsdeliver-eng.slack.com/archives/D0BKW2XEM2L/p1788338995986199)
- [ ] Send him the PDF export he asked for on the Fuse↔SNAP fields thread (2026-08-28 direct email ask)
- [ ] Answer his question on the field name for retrieval-condition (fulfilment order location ID) filtering in the Fuse/Shopify dev app install guide UI — emailed 07-29, still unanswered (same topic as [[Jack Bailey]]'s filtering-conditions clarification)
- [ ] Answer what use case the ~16 hanging Purdy & Figg confirmations are for — asked in #bifrost-general, unanswered since 08-04 — [Slack](https://gfsdeliver-eng.slack.com/archives/C098LD5PS95/p1785845516459279)
- [ ] Follow up on the SPORTLUX/Dickies OC-confirmation escalation (w/ Joseph Mashiloane) — his 12:30 comment flagged as related after I got confused mid-thread, unanswered since 08-05 — [Slack](https://gfsdeliver-eng.slack.com/archives/C098LD5PS95/p1785936417045209)
- [x] Advise on the Shopify dev-app review blocker — closed 07-16/17: confirmed two ways to create a dev store via the link; James advising Saira Skin (P&F will need the dev app later)

**Owed to me**
- [ ] Answer my Purdy & Figg missing-egress-connector question — still unanswered — [Slack](https://gfsdeliver-eng.slack.com/archives/C098LD5PS95/p1785768353172359)

## Standing context
- Holds that both header-level and line-level custom properties must be catered for on the Escentric engraving flow
- ILG; regular attendee on the Fuse-Bifrost Weekly Sync and Bifrost Operational Readiness meetings
- ✍️ 

## Comms persona
- **Works:** short sentences, one idea at a time; lead with reassurance ("nothing's lost, nothing you need to do differently"); plain language; steer him to one concrete self-serve place (e.g. the Retry Queue) rather than a list of steps; leave next steps with him to drive.
- **Avoid:** admitting fault or calling something "broken" — frame in-progress features as "still building out / improving"; long or multi-part messages; jargon, service/ticket names, mechanism detail; technical self-serve queries he'd have to run and interpret.
- **Evidence:**
  - 2026-09-29 — Byoma held-transfers thread: Harry approved a short, plain draft unchanged, one that stated a duplicate-receipt side effect plainly (no service or ticket names) and ended with one concrete ask plus one scoping question.
  - 2026-09-24 — Lisa Eldridge drained-confirmations update (DRSAMS thread): Harry cut the "if it helps, I can pull the references" offer — support should drive next steps (resends/exports); give him the facts and counts, don't volunteer to do the follow-up legwork.
  - 2026-09-16 — Purdy & Figg carrier-name (GFS_EVRI) thread: root cause was a genuine platform gap (a config mapping the code silently ignored), reported as "handled separately from the usual mapping settings — needs a fix on our side, not a config change" with no service/PR/ticket names, framed around priority ("we appreciate Purdy & Figg are high profile") rather than internal process detail.
  - 2026-09-15 — goods-out Transaction History thread: Harry directed a gentler, no-fault, simpler rewrite. Keep replies short and reassuring, and take extra care with clarity.

## Together (newest first)
- 2026-11-11 — Answered my 5 Nov question on 10 Nov: he wants `identifiers.solLineId` in the pick and pack line mappings
- 2026-11-11 — I have not replied yet, and it is on today's 13:00 sync → [[Meetings/Fuse-Bifrost Weekly Sync]]
- 2026-11-02 — Asked for a ticket or mapping expression to drop Sistaco's 0-fulfillable virtual-SKU lines; Jack suggested the SKU blacklist on 30 Oct
- 2026-10-29 — Asked on 27 Oct whether the multi-stores change is deployed to prod; the thread has no reply
- 2026-10-16 — I answered him on Escentric: one connector per store, now tracked as FUSE-1312
- 2026-10-09 — "RE: Engraving": I replied 10-08 that Fuse needs a couple of changes; my follow-up once the ticket exists is still owed. His "worth testing it" answer on one Shopify store serving UK and PL customers likely covers [[Tom Dunn]]'s Escentric question
- 2026-09-30 — asked in #bifrost-general (09-29 17:29) for Byoma TRF04208, TRF04257 and TRF04280 to be sent through to Snap. No receipt yet, and nothing from me since 16:40. He also supplied Dock & Bay's prod credentials; in today's 13:00 sync → [[Meetings/Fuse-Bifrost Weekly Sync]]
- 2026-09-07 — the "RE: Engraving" thread came back to me: after [[Tom Dunn]] asked whether line-level VAS is viable in FUSE today for the Escentric Molecules ECOM → Shopify connector, James confirmed both header- and line-level custom properties must be catered for
- 2026-09-01 — live all morning in the Purdy & Figg go-live war room: switched the Shopify connector live at 09:34, replayed 3 orders after tightening retrieval conditions, worked through "City too long"/missing-SKU field failures and an `ILG_OTHER` tag mapping gap; PDF-export ask (08-28) still not sent
- 2026-08-28 — direct email: "can you please send the PDF export for this through to me" on the Fuse↔SNAP fields thread — new, unanswered
- 2026-08-05 — raised the SPORTLUX/Dickies OC-confirmation escalation with Joseph Mashiloane in #bifrost-general; separately still owed an answer on the ~16 hanging Purdy & Figg confirmations he asked about 08-04
- 2026-07-29 — emailed me directly asking what field name to enter in the UI for retrieval-condition (fulfilment order location ID) filtering on the Fuse/Shopify dev app install guide — unanswered
- 2026-07-17 — [[Saira Skin]] dev-app blocker closed after my confirmation (two dev-store creation routes); he's going back to Saira Skin — nothing on me unless it resurfaces
- 2026-07-16 — re-surfaced the [[Saira Skin]] Shopify dev-app review blocker ("please advise" — Purdy & Figg can't install it for testing); still owed advice
- 2026-07-15 — attendee on [[Meetings/Bifrost - Operational Readiness]] (10:00) + [[Meetings/Fuse-Bifrost Weekly Sync]] (12:00)
- 2026-07-14 — forwarded the Saira Skin Shopify migration app-review blocker, direct ask for advice

## Links
- (external — no Fuse Jira / GitHub)
