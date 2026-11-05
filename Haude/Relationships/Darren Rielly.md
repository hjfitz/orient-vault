---
tags: [haude, relationship, human]
human: Darren Rielly
slack_dm: D09GTBH3WNQ
standing: Principal Engineer, ilg-platform
updated: '2026-11-05'
title: Darren Rielly
---
# Darren Rielly

> Principal engineer on ilg-platform. Human note: [[People/Darren Rielly]] is Harry's view. This file is mine.

## Standing
First contact on 2026-10-27, in Harry's DM with him. Harry framed it as "i'll have my guy talk to your guy", so Darren knows there's an agent on this end and has one of his own (unnamed so far) flipping his PRs to the in-container Datadog pattern.

## Voice
He writes in short, lowercase, plain-English bursts ("legend", "got a link?"). There's no protocol bit with him yet, so match that register.

## Open loops
- **Owed to him (drafted, not sent yet):** the "mocker sends joined-up traffic" note. Harry promised it at 11:24 GMT on 11-05 ("i'll have the clanker update the mocker"). It sits as a Slack draft in Harry's DM with him for Harry to send. Next: whether his customer ref + biz id join pairs the mocked orders with their confirmations, and whether broadcast reaches his subscription.
- **Owed to him:** answers if his agent hits anything the golden-images README doesn't cover. I offered this in the handoff.
- **Unclear:** after Harry said no auth is needed for the stock image, Darren said "we're actually going to have to set that up". The handoff noted that registry writes are WIF-scoped to `ilg-platform/images` only. It didn't guess what he meant.

## Together (newest first)
- 2026-11-05 16:00 GMT — drafted, held for Harry to send: the mocker confirms its own sales orders now. It mirrors customerRef, bizId and lines, and every line ships in full; for a short-ship, Fill from order and edit `quantities.shipped`. It's broadcast with source `mock-<channel>`. `confirmAfterSeconds` works on schedules and load runs. This answers his 11:23 "not seeing any actual sales orders created… on the topics in dev". What he's building: matching confirmations to orders on customer ref + biz id, and comparing lines to spot short-shipped versus fully fulfilled.
- 2026-10-27 19:29 GMT — sent a correction to my own handoff. I had said "pin by digest"; Harry then decided consumers use the rolling tag on its own, so I told Darren that and linked images#9. [message](https://gfsdeliver-eng.slack.com/archives/D09GTBH3WNQ/p1793129384761719)
- 2026-10-27 19:26 GMT — sent the golden images handoff: the repo, the public AR registry, `go-runtime`/`node24-runtime` `0.1-affogato` digest pins, the CMD-only / USER nonroot / stdout / sidecar-removal recipe, and audit-service#16 as the worked example. [message](https://gfsdeliver-eng.slack.com/archives/D09GTBH3WNQ/p1793129188181929)
