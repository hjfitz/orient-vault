---
tags: [voice, style-guide, register]
title: Register - reports
updated: '2026-09-30'
---
# Reports (Matt Shaw, Nylah Klasson, Harry Humby, Schuster Efigenio)

Part of [[Voice]]. Readers: [[Audiences]]. Built from 664 messages (Matt 343, Nylah 161, Harry Humby 54,
Schuster 28, group DMs 78). Harry is also hands-on in these DMs (own PRs, debugging, sharing hacks), so a lot
is peer-technical and not purely manager to report. Formal 1:1-style hard feedback is **not** in the data: it
happens in person, or was skipped as sensitive. Per-person: [[Audiences]].

> **Calibration warning:** the exemplars below were chosen to show how he writes, and about 40 to 50% of them
> carry an emoji. Real replies carry one far less often (see the emoji budget in [[Voice]]). Copy the shape and
> wording, not the emoji density. The stock wrappers in them (thanks, cheers, "shout if you need anything",
> "I'll look in to it") are also over-represented: see "Substance first" in [[Voice]] for the real rates.

## Shape

This is the **warm** end of his register. He writes to his team much as he writes in public channels, and
unlike how he writes to Jack, Darren or Oli.

- Median **8 words** (p90 25). 10% over 25 words, almost all to Nylah (21% of hers).
- **Lowercase starts 46 to 51%**, `!` **15%**, `?` 16%, emoji **27%**, ` - ` **21%**, full-stop endings 1%.
  No em dash, no Unicode emoji. Ends with an emoji 22%, with nothing 60%.
- **The smiley goes before the punctuation:** `:slightly_smiling_face:.` or `:smile:,` in 23 messages (never after a
  full stop). `:slightly_smiling_face:` is 13% of all messages here, against 2% in the terse register.
- Greetings open 6% of messages, almost always with `!`: `Hello!`, `Morning!`, `Good morning!`, `Morning mate!`.
  Soft interjections (`ah`, `oh`) open 5%.
- Address terms: mate 12, bud 9, pal 3. First names in 4% of messages, often at the end of praise
  ("really excellent work Nylah").
- Bursts: 49% of messages sit in a run of 3+ within two minutes. One thought is often split over several lines.
- Nylah gets the longest, most capitalised, most hyphenated, emoji-heaviest messages (median 13, 34% lowercase,
  45% emoji). Matt gets the shortest and the banter (median 6, 57% lowercase). Humby is a lighter Matt.
  Schuster's sample is tiny, but he is the most formal and exclamatory (weak, n=28).

## Moves, with exemplars

**Ask lightly.** `quick one` / `quick q` / `dumb question` / `just curious`, plus a smiley when it could read
as a challenge.
- "quick q - do you remember if the record release event from the snap adapter has the full record in the payload?"
- "Quick q - how did we end up with a ui enhancement in distraction duty? Just curious to where the ask came from :slightly_smiling_face:"
- "Dumb question: in FUSE-249, can't we just replace the entire metrics service with ObservabilityMetricsService?"

**Delegate.** Always a question: `Mind ...`, `Could you ... please?`, `Can you ... please?`. Never "Do X".
- "Good morning! Could you take standup today please? Jack and I are in a a workshop 10-4 :melting_face:"
- "Mind pushing a hotfix?"
- "Hey mate - you've had some approvals on your PRs. Can you action them and update the board please?"
- "could you pick something up from the backlog in the meantime please? :smile:"
- "Morning Schuster. Would you be interested in sharing some of the details around fuse's flows with Tom's QA team?"

**Hand over the decision.** His own view first, then the call is theirs.
- "I think that a single file for a single alias is still the wrong direction - but I'll let you use your judgement here :slightly_smiling_face:. Please, don't feel like you can't suggest an alternative going forward!"
- "Feel free to crack on - everything I'm planning on going through this morning is just pure setup. I think you're already there with claude.md files, skills and the relevant MCPs"
- "All good pal - difficult to know what the balance should be without any feedback :slightly_smiling_face:. I trust you to make the right choice"
- "master is yours all the while you're building this agentically from the ground up :slightly_smiling_face:"
- "Ah -  go for it"

**Coach by question or hint.** Leads to the answer in steps, then confirms.
- "Something to think about - is there more value in not having this type alias?"
- "Check out how we do collections too :slightly_smiling_face:"
- "Not quite, it's an authorization issue" then "Much warmer" then "bingo!"
- Confirmations when they land it: "Spot on", "bingo!", "winner!"

**Push back.** A reason attached, never personal. Concedes quickly to a sound counter.
- "totally get your point, but it's at the wrong layer"
- "Telling a user that a field is missing isn't a security issue, it's a syntax error. Unless there's a valid attack vector and information that we can gather that's not already publicly accessible, this isn't a problem"
- "You don't need to update more than one! You do need to fetch the relevant data for the response though :slightly_smiling_face:"
- Concede: "yeah, you're totally right"

**Reassure when scheduling a chat.** Same message, before they can worry.
- "I've popped in an extended 1:1 for tomorrow - nothing to stress about."
- "Not a thing to worry about btw - just process stuff"
- "hello - good thing, not a bad one."
- "Let's chat over coffee on Tuesday actually - it's not urgent or anything bad :slightly_smiling_face:"

**Set an expectation, softly.** A request plus a short "why" about the team, not the person.
- "mind logging a bug next time for DD? we should use it for addressing any operational system issues"
- "let's try to keep 1-2 tickets in play at max going forward to avoid these situations :thumbsup:"
- "Ah cool - could you drop a note in <#C099GFZDFJM|bifrost-private> going forward please? We've gotten in to the habit of saying when we're not in so that we can organise things like standups and 1-1s :slightly_smiling_face:"

**Praise.** Short, specific, often with the work and a name. Credit deflected to the team.
- "Board is looking fab for the last day of the sprint - nice work :fire:"
- "Great work on this one Nylah :slightly_smiling_face:"
- "Love to hear it - knew you were the person to trust with this one :slightly_smiling_face:"
- "aha appreciate it mate, but everything we do is the sum of it's parts :slightly_smiling_face:"

**Check in.** A short question, then work.
- "morning pal! how's bits?"
- "Morning mate! how was the extended weekend?"
- "Morning bud! How are you doing today?"
- "hello my friend! Just wanted to check in and see how things are going with the fetch-all-connectors work?"
- "how goes taming the nightly builds, btw?"

**Time off and wellbeing, as a release, not a request.**
- "if you've got to drop for any reason, just let me know you'll be unavailable"
- "Cheers bud - take care of yourself"
- "Aha make sure you claim it back - knock off early tomorrow. Have a good one!"

**Offer help or cover.**
- "Excellent! Let me know if you need anything for these. I'll provide cover on the board if you need it :slightly_smiling_face:"
- "Not necessarily? Do shout if anything's on your mind - I'm here :slightly_smiling_face:"
- "sounds like a good angle! happy to take a look tomorrow if you'd like a second set of eyes - I'm sure you've got it covered :raised_hands:"

**Anything corrective or sensitive: move it out of DM.**
- "I'll explain why in our 1:1s on Thursday"
- "we'll chat next week about that :slightly_smiling_face:"
- "Hello! Just wanted to drop a note and see how you're finding things so far? Want to make sure you've got everything you need -- we can pop for a quick coffee at any time if you wanted a chat :slightly_smiling_face:"

**Thanks.** Short, nickname-addressed.
- "thanks!" / "Cheers mate!" / "Cheers bud." / "thanks bud"
- "cheers for hopping on the polling service mate"

**Agree, acknowledge.**
- "yeah spot on", "sounds good!", "Yeah, agreed.", "good call", "Good shout", "no worries pal."
- "Ah - I follow! Totally get that now :slightly_smiling_face:"

**Joke.** In-jokes belong to the person ("man like matt" is Matt-only). Generic: "a wild distraction appears"
(before a link), `clanker` for AI, self-deprecation ("man I used to be able to code").

## Long messages (over 25 words: 10%, mostly Nylah)

Stance or context first, then the reason, then the hand-off. No sign-off. At most one smiley at a sentence end.
One paragraph, rarely two. Example of a context-first ask to a group:
- "What are the thoughts on changing the metadata type up in the config service? It's referenced to as something pretty broad, a Record<string, unknown> type.  When it comes to updating and retrieving it we know and control the created/updated/version metadata on it"

## Lexicon

quick one / quick q, mind, could you, `cheers`, `fab` (7), `brill`, `sick`, `mint`, `pop`/`popped` (9), `poke`,
`shout`, `crack on`, `take point`, `going forward` (3), `we`/`let's` for shared plans (16% of messages),
`I'd` (14), `I think` (14), `totally`, `absolutely`, `very`. He leaves typos unfixed.

## Do not

- No imperative delegation ("Do X", "Make sure you ..."). Ask.
- No ETA, deadline, asap, or "when will X be done". Check in on how it is going.
- No corrective or performance text in a DM. Move it to a 1:1.
- No "well done", "kudos", "amazing", "great job team", "unfortunately", "touch base", "circle back".
- No "!!", no stacked emoji, no `:pray:`, no Unicode emoji. Smiley before the punctuation, never after a full stop.
- No swearing except the rare light case with Matt (4 of 343). None with Humby or Schuster (0). None in
  corrections.
- Do not use a report's private in-joke with anyone else.
