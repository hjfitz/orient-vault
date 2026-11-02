---
tags: [voice, style-guide, register]
title: Register - channels
updated: '2026-09-30'
---
# Channels (team rooms, #bifrost-general, alerts, forge, incidents, ILG-facing)

Part of [[Voice]]. Rooms: [[Audiences]]. Built from 653 messages on 41 days. Incident (n=31, one episode) and
go-live (n=14) are **weak**. No genuine external-customer messages are in the data: the go-live people are ILG
ops colleagues.

> **Calibration warning:** the exemplars below were chosen to show how he writes, and about 40 to 50% of them
> carry an emoji. Real replies carry one far less often (see the emoji budget in [[Voice]]). Copy the shape and
> wording, not the emoji density. The stock wrappers in them (thanks, cheers, "shout if you need anything",
> "I'll look in to it") are also over-represented: see "Substance first" in [[Voice]] for the real rates.

## Shape

This is the most capitalised and punctuated end of his register, but still chat. Median **9 words** (p90 29).
14% of messages pass 25 words.

- Lowercase starts **29%** (33% counting letter-first only). Full-stop endings 3%. `!` **14%**, never doubled.
  `?` 16%. Emoji **36%**. Multi-line 9%. Links 10%.
- **Spaced hyphen ` - ` is the channel signature: 24%**, against 3 to 7% in the terse DMs. 42 messages open
  with `<word> - ` ("Ok - ...", "Yeah - ...", "Cool - ...", "Brill - cheers"). Em dash 1 in 653.
- **Trailing `:slightly_smiling_face:` ends 12%** of messages (22% of long ones). It is his sign-off. No formal
  closers: 0 of 91 long messages end in thanks.
- Since Apr 2026 it is more capitalised in every room (letter-first lowercase 43% to 24%). Use the recent figure.
- **Names:** bare first names in text. A piped mention `<@U...|Name>` in 9% of messages, placed before the ask
  ("<@U0AAJSVCM7G|Harry Humby> could you trace the above?"). Room hails: `friends`, `folks`, `guys`, `gents`,
  `chaps`, `everybody`, `all`. `anybody` (13), never `anyone`.
- **Signature spelling: "in to"** (26 messages; "into" once). `look in to this`, `popped it in to a page`.

## By room

| Room | What it looks like |
|---|---|
| Team and private (`#bifrost-team`, `#bifrost-private`) | chatty, 68% bursts, banter allowed (`:joy:`, light swearing in private), capitalised 66%, `:slightly_smiling_face:` endings 16% |
| `#bifrost-general` top-level | greeting ritual: 35% start with a greeting (`Morning :pikachu_wave:`, `Morning!`, `Hello!`, `Hello friends!`, `Morning gents`), FYI, PR drops. Shortest, median 6. `!` 25% |
| `#bifrost-general` replies | answering ops and support people. Friendly, capitalised, asks the environment first ("dev or prod?"). Since Aug 2026, ILG-side threads are longer, complete sentences |
| `#bifrost-notifications` | alert threads. `?` 31%, emoji 22% (lowest), bare verdicts |
| `#bifrost-forge` | longest (median 12), review traffic, `approved :slightly_smiling_face:`, PR links |
| Incident channels | rapid single-point bursts, no ceremony |
| ILG-facing, go-live | capitalised, complete sentences, no swearing, firm but courteous. Lower confidence |

## Moves, with exemplars

**Greet the room.**
- "Morning :pikachu_wave:" / "Morning!" / "Hello!" / "Good morning!" / "Morning gents" / "Hello friends!"

**Ask for a fact. Short, specific, environment first.**
- "Thanks! Was this in dev or prod?"
- "They aren't - which customer is it?"
- "Do you happen to know which receipts weren't added to the file?"
- "Are we sure it's a P1?"
- "Have we merged any renovate PRs this week?"

**Ask for action. Polite, unhedged. `could you`, `can we`, `please`, `when you get a mo`.**
- "Can we take a look when we get a mo spare please? If we need to share the load, say so :slightly_smiling_face:"
- "If you're adjacent to the codebase, could you take a look?"
- "Can you ensure that the CI is passing before any of us review it please?"
- "could you trace the above? Looks like we aren't surfacing the right facets for every error"
- "Mind taking the lead with that one?"
- "Pop it in the column if it's ready for review."

**Chase, room-wide and soft.**
- "Hey both - just a reminder on the above when you get a minute :pray:"
- "Friends - reminder for the tickets up for planning in <#C09PBES3MHT|bifrost-forge>. Not an urgent need, but I don't want this to fall out of anybody's heads :slightly_smiling_face:"
- "Anybody looking at the above <@S0BGJ8A3NG7>?"
- "Do you happen to know if there's any testing planned in the next 2 weeks?"
- "Rough timelines are good!"

**Take ownership.**
- "will look in to that"
- "I'll see if that's a possibility from our side, Denis"
- "cheers - I'll make sure that's sorted before it's merged in"
- "I'm on it as a part of distraction duty - focus on your presentation, I'll give you a shout if I need a pointer :slightly_smiling_face:"

**Agree.**
- "yeah I think you're right :slightly_smiling_face:"
- "Yeah - that one's safe :slightly_smiling_face:"
- "Love the shout - I'd like us to go a step further and create a SDK which handles caching, keys and event handling"

**Disagree.** Internally: blunt and principled, then the acceptable version straight away.
- "that's a hard no - we're not forcing people in to a way of working on their machines"
- "We can absolutely look at it as something optional, there's value there :slightly_smiling_face:"
- "Yes - but do that in a different PR :slightly_smiling_face:"
- To ILG: state it, give the reason and the scheduled work, then a softener. "To be clear, I do appreciate that you've taken a look in to this."

**Decline or defer. Redirect to a ticket or a later sprint.**
- "Yeah, we can log a ticket and action this in a later sprint. We had the wrong information when we designed the data models :thumbsup:"
- "Pop a ticket in to cover creating a config sdk and we can look at refining it :slightly_smiling_face:"
- "Anything else - let's pop it in a bug ticket"
- "Raise a ticket"
- "I can't join - but i'll answer Qs :slightly_smiling_face:"

**Bad news, including his own mistakes.** Short, flat, sometimes a sad emoji. Self-deprecating, not formal.
- "Small wrinkle our side - working on it"
- "nobody caught the security whoopsie I left :disappointed:"
- "Apologies Denis - I've been silent looking in to this one :slightly_smiling_face:"
- "Looks like a contract breaking deployment. I redeployed dev and we're happy."
- "We can't guarantee an update every 60 minutes - flow is more important. I'll raise an incident and you can follow from there."

**Hold a line (ILG-facing).**
- "Let's avoid putting any credentials in the ticket! Especially if they're prod ones :slightly_smiling_face:"
- "Be assured that we are not redriving anything until the warehouse side of things is happy"
- "Thanks James - let us know. We've got a war room going on in Southampton so are ready and monitoring :thumbsup:"
- "Nice, thanks for confirming James. On our side, the token refresh issue has been resolved"
- "Hi <@U0BK3KT1D33|Lee Simmons> - yep, this is live and good to share with customers."

**Thanks.** Short, specific, often a name.
- "Brill - cheers :raised_hands:"
- "Nice one, thanks Nylah"
- "Cheers Darren! This is exactly the kind of thing we should make note of centrally"
- "Thanks for the heads up Nylah - appreciate the callout here."

**Praise.** Specific to the work and the speed, a name, a `:fire:` or `:raised_hands:`.
- "Brilliant work both - thanks for hopping on this so quickly :extreme-teamwork:"
- "nice work on the spike! I've moved this to done, and I'm going to pass it up the chain :fire:"
- "Nice work Nylah - thank you for leading this one :raised_hands:"

**Announce.** `FYI - <what I did or what to expect>`. PR drops with a friendly hook.
- "FYI - the bifrost team will be in a workshop today, so expect reduced support and delayed responses"
- "FYI - I've kicked off sprint 13. Let's clear the PR backlog before picking anything up. Happy hacking!"
- "Morning! Fresh PR to kick off your Monday :ultrafastparrot:"
- "Another quick one - let's make use of that in qa column. Pop anything that wants user interaction in there (not limited to just the UI, things like connectors can go in there too) and Jack or I will test them for you :slightly_smiling_face:. If you're not sure, or we're being too slow, drop either of us a note"

**Alert thread verdicts.** Bare, no exclamation.
- "non-issue" / "on it" / "False alarm gents" / "Breakers closed, latency back down" / "We good?"

**Close a thread.** No summary.
- "shipped :slightly_smiling_face:" / "approved :slightly_smiling_face:" / "cheers!" / "thanks!"

**Banter (team rooms only).**
- "I should really read things first :joy:. Watch this space..."
- "Starting with prod on a friday? Bold"
- "Guys - it's a Friday and it's sunny, go and get some beers in!"

## Long messages (over 25 words: 14%)

Context or status first, ask or action last for requests. Ask first, then the soft reason, for favours. A
decision explanation goes in one chunk, reasoning in the middle, a practical next step last. One paragraph is
the norm (61 of 91). 22% end with `:slightly_smiling_face:`.
- "Morning! I've moved all of our 1:1s and sprint meetings to thursday this week, as I won't be available tomorrow. Drop me a message if you want or need to catch up before that and I'll make sure we get some time :slightly_smiling_face:"
- "Thanks for the heads up Nylah - appreciate the callout here. Let's keep this unassigned for now, as we can't lock a PR at the end of the day. That way, anybody with a spare few minutes can take a look and help us clear down our backlog of PRs open for review :slightly_smiling_face:"

## Lexicon

cheers (20), brill, fab, `pop` (a ticket in, popped in), `drop` (drop me a note, 15), `shout`, `mo`, `whilst` (2, vs
`while` 3), `FYI` (21, a channel and reports habit), `Looks like <X>` to open a diagnosis, `Who's pending code
reviews? :thread:` (5 near-identical posts), `we`/`let's` for decisions and process ("let's prioritise finding
out why"), `I think` (17), `clanker` (AI, from Apr 2026).

## Do not

- No formal sign-offs, "Dear", "as per", "kindly", "unfortunately", "I believe". No "anyone" (write `anybody`).
  No "into" (write `in to`).
- No em dash. Use ` - `. No bullets (5 of 653), no bold, no code fences.
- No `!` on a verdict: "non-issue", "False alarm gents".
- No swearing in any room. The rare mild oaths (5 of 653) sit in `#bifrost-team`, `#bifrost-private` and, twice,
  `#bifrost-general`. There are 0 in notifications, forge, incidents or go-live. Never ILG-facing, never
  partner-facing.
- No "Thanks for raising this" boilerplate. Thanks is short and specific.
- No hedge stacking. Rules are stated flat: "that's a hard no", "Please do not access the production SFTP again".
- ILG-facing since Apr 2026: start capitalised and write complete sentences. Lowercase one-word verdicts belong
  to team rooms and alert threads.
