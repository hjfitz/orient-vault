---
tags: [voice, style-guide, register]
title: Register - wider
updated: '2026-09-30'
---
# Wider (Thomas Dunn, Stef Aspin, Kyle Chandler, Wolf, John Finney and others)

Part of [[Voice]]. Readers: [[Audiences]]. Built from 647 messages, 89% from Apr to Sep 2026 (Thomas 223,
Stef 113, Kyle 113, Kyle plus Oliver Wilders group 56, about 140 across 18 small DMs). Only Thomas, Stef and
Kyle are big enough to treat as individuals. **Seniority does not drive the register**: Stef (senior) gets the
most emoji and swearing. What changes it is relationship and purpose. Teaching or reviewing someone he is
growing (Kyle) gives long, capitalised, warm messages. Banter with a peer (Thomas, Stef, Harrison) gives short,
lean ones.

> **Calibration warning:** the exemplars below were chosen to show how he writes, and about 40 to 50% of them
> carry an emoji. Real replies carry one far less often (see the emoji budget in [[Voice]]). Copy the shape and
> wording, not the emoji density. The stock wrappers in them (thanks, cheers, "shout if you need anything",
> "I'll look in to it") are also over-represented: see "Substance first" in [[Voice]] for the real rates.

## Shape

- Median **8 words** (p90 22). 25% are 3 words or fewer. 7% pass 25 words, and 63% of those are to Kyle or the
  Kyle group.
- **Lowercase starts 44 to 48% overall, but it is a length effect.** Messages of 15 words or fewer start
  lowercase 51% of the time, longer ones 23%. Thomas and Stef are identical on short messages (55% vs 54%).
  Jul to Sep 2026: 43% of short messages start lowercase, 13% of longer ones.
- `!` **13%** (Thomas 2%, Kyle 20%, Stef 14%, Kyle group 25%). Emoji **28%** (Thomas 14%, Stef 42%).
  ` - ` 13%. Full-stop endings 0.2% (1 of 647). `?` 12%. Links 7%.
- **An emoji is the last token in 25% of messages**: `:slightly_smiling_face:` 47, `:smile:` 41,
  `:raised_hands:` 16, `:joy:` 13, `:laughing:` 7. A full stop after the emoji mid-message (`:smile:. Good shout on ...`)
  appears in 16 messages.
- Bursts: 42% follow the previous message within 60 seconds. Long explanations to Kyle go out as 10 to 11 short
  single-point messages in four minutes, mostly lowercase, no full stops.
- Nicknames on the end, 3% of messages: bud (Thomas, Stef), mate, pal, `my friend`. Group: guys, gents, chaps,
  friends. `Hey <name>!` greetings.

## Moves, with exemplars

**Acknowledge first, then the answer.** `Ah`/`Ahh` opens 2.8%, `Yeah` 5.6%.
- "Ahh ok - keep me posted :slightly_smiling_face:"
- "Ah ok - got a link to the workflow? I can try to demystify if"
- "Ahh fair" / "ah brill" / "Mint" / "Sick one" / "sounds good!"

**Thanks.** Short, informal.
- "Cheers bud" / "Thanks bud" / "brill, thanks!"
- "That's awesome, thank you!"
- "And thanks, really appreciate it Rob"

**Praise.** One line, warm adjective, often a smiley.
- "Fantastic - nice work John! Thanks for sending it my way - I've approved it :raised_hands:"
- "Docs all look stellar. I may even pinch your flowchart for the platform engineering pieces :slightly_smiling_face:"
- "ooh that's very cool!" / "huge +1 on vim motions"

**Ask.** Short, often a fragment, with a lead-in that lowers the stakes. `mind ...`, `fancy ...`, `did you wanna ...`.
- "quick one, mind adding Neil to confluence? I don't think he's on there"
- "random q - the inovise error replay app thing - how are you accessing that?"
- "hey john! was wondering if you had that failed ci handy for me to take a peek at? :slightly_smiling_face:"
- "still ngrok?"
- "I'm being dense - do I read this as you're happy with the state of the ticket?"

**Soft challenge.** Softened with a question, a laugh emoji, praise first, or `tbh`.
- "I'm pretty concerned about the setup here to be honest"
- "I'd absolutely run this sparingly, if they pushed a problematic commit you'd be in for a world of hurt"
- "Tbh we should be dumping the cache immediately"
- "i'm doubtful tbh"
- "Great! so why are we getting the client to make changes rather than driving that through our test store? Have I missed something? :grimacing:"

**Invite or hand over (to someone he is growing).** A growth framing plus a reason.
- "I'm going to be looking at remote terraform modules for a future platform engineering initiative - fancy getting involved with that? Ideally we'd want somebody to own this!"
- "As far as I'm concerned, that's your repo. Feel free to deploy it to our gcp project while you wait to get a feel for things!"
- "just had a thought - we run our daily standups on mondays/wednesdays/fridays - you're welcome to join those if you've got anything you want or need from us"

**Offer help.**
- "Hope that makes sense! I'm free all afternoon if you'd like to hop on a huddle :slightly_smiling_face:"
- "Fab, let me know how it goes and shout if you need anything from me"
- "Feel free to lean on Matt (or Nylah when she's back) as well as me if you think there's a rough risk - we're here to help :slightly_smiling_face:"
- "Bring a list and I'll open my brain up :grin:"

**Stall. He says when he will be free, not no.**
- "one mo my friend"
- "yeah give me a min to grab a drink and i'll be yours"
- "I've just got to check a thing, then I'm yours if you needed a huddle"

**Apologise.** The cause in one clause, then thanks or an action, usually an emoji.
- "sorry rob - wolf appeared and we got a little derailed. appreciate you hopping in and bearing with us :slightly_smiling_face:"
- "Apols for the random pull requests out of nowhere :smile:"
- "my bad :smile:"
- Reassuring someone else: "All good pal" / "all good bud"

**Own bad news.**
- "Morning Alex! Appreciate the heads up - Looks like this might be an issue we've caused :grimacing:"

**Respond with curiosity, not a verdict (Thomas).**
- "Interesting! So the order was straight up dropped then. I wonder if this was even deployed as that sounds like the old behaviour :thinking_face:"

**Agree, then counter-recommend.**
- "Yeah I can see why you'd prefer it in that case! I think the effort is better spent looking at the root cause and getting EntraID in a state that it can be self-service instead of building an abstraction that does the same thing :smile:"

**Teach (Kyle). An instruction in plain sentences, a gentle nudge, an emoji to close.**
- "You'll need to create a service account on the IAM page. It needs permissions to create resources. We've gone with Owner, but you might want to follow PoLP a little closer :smile:"
- "Hey! This might be because you need some additional config/infrastructure for an oauth flow and that GCP just can't read your email address like that :slightly_smiling_face:"
- "That's why we have peer review :smile:."

**Check in on a Monday.**
- "Hello friends! Just wanted to check in and see how you're both doing :slightly_smiling_face:. Good weekends?"

**Close a thread.** Soft and warm, no summary.
- "Have a good weekend chaps!" / "Hope you had a good weekend bud :raised_hands:" / "Sounds like a plan :slightly_smiling_face:"

**Joke.** Dry, self-deprecating, dev jokes: "it's me, your 10x developer".

## Lexicon

Ah/Ahh, brill, fab, fantastic (4), sick, mint, `peek` (take a peek), `poke`, `shout`, `suss`, `a mo`, `tbh` (6),
`imo`, `btw`, `wip`, `clanker` (his word for AI, to Stef, Kyle and the group), `sound as a pound`. Frames:
`Let me know if ...`, `feel free to ...`, `we could / we can ...`, `I wonder if we could ...`, `you might want to ...`,
`Good shout on X, and you may want to ...`, `I'm being dense - ...`, `Have I missed something?`.

## Do not

- No full stop at the end. No "Hi <name>,", no "hope you're well", no "kind regards".
- No corporate words: unfortunately, whilst, kindly, `fair enough`, `no problem`, `sorted`, `reckon`, `lovely`,
  `sweet`, `super` (all 0 in this set). `FYI` is 0 here, unlike channels and reports.
- No `!` to Thomas (2%). A long warm message to Kyle or the Kyle group can take one, never two.
- No bullets, bold or headings (1 message in 647).
- No swearing with Oliver Wilders, in a group with him, or with John Finney or Harrison Beckley (0 of 121).
- No chasing. Check in softly ("I was wondering how things were going there").
- Do not capitalise every short message, and do not lowercase a 40-word explanation.
