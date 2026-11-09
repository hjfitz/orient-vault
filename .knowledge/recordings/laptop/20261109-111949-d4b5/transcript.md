**[00:00:00] Speaker 1:** Anyway, I've been team moved.

**[00:00:03] Speaker 2:** You've been T Mood?

**[00:00:03] Harry:** Even Timmy's.

**[00:00:04] Speaker 1:** Yeah, Harry's Harry's versions just team with me.

**[00:00:10] Harry:** Oh yeah yeah. B

**[00:00:10] Speaker 1:** You know, with that bitchy mood.

**[00:00:12] Harry:** Superior. I I did Matt a custom fucking Datadog Fairy claymation profile picture and he's not even using it.

**[00:00:20] Speaker 3:** Uh yeah. That will change.

**[00:00:23] Harry:** Room a week.

**[00:00:24] Speaker 3:** I'm worried about that.

**[00:00:26] Speaker 1:** He's got to be blue for the integration room, is the only thing. Mm-hmm.

**[00:00:35] Speaker 3:** Is that a uh Is that a dungeon dungeon crawler Carl t-shirt, Harry?

**[00:00:41] Speaker 3:** Nice.

**[00:00:43] Harry:** Why only one?

**[00:00:43] Speaker 3:** My my Instagram feed is non non-stop that at the moment as a result of your

**[00:00:46] Harry:** Good.

**[00:00:49] Harry:** Get on the books.

**[00:00:51] Speaker 3:** Yeah.

**[00:00:52] Speaker 2:** Well the audiobook's better.

**[00:00:52] Harry:** I've just thought Yes. I've just put Red Rising'cause I'm like I've already read the first four chapters of the next book of DCC and yeah, I just

**[00:00:57] Speaker 2:** Oh yeah.

**[00:01:02] Harry:** need to be entertained.

**[00:01:04] Speaker 2:** That's fair. There's someone walked past my house the other day with a Dungeon Cooler Card top on. And I was like, oh, nice top. And then um Yeah, he was like, oh, yeah, my wife and I are really into it. And then I saw a woman walking the same from the same direction past my house, also with a Donge Crawler car top. And I was like, are you related to the man who wears those tops? And she's like, yes, that's my husband he mentioned about you. And then about two weeks later, I saw them ring my doorbell and I was like, oh, that's weird.

**[00:01:28] Harry:** Mm-mm.

**[00:01:33] Speaker 2:** And then they kind of went away again. And then I found in my mailbox was a Dungeon Caller Car fridge magnet that someone had 3D printed. And I was like, oh my gosh, that must have been where they came around. They'd remembered and brought this round. I'm like, it's very sweet. And then we went to Cochrane.

**[00:01:47] Harry:** It's the fucking sweetest thing.

**[00:01:49] Speaker 2:** Yes, we went trickle-treating last week and knocking random houses and found out it was one of them was theirs. And they're like, oh my God, it's you guys. Like, did you get the magnet? I was like, yes. I'm like, it all came to a head. Beautiful. They're like, yeah, we made free to test out the print and we thought you'd like one. I'm like, I do. Thank you so much. I think it's going to be the same.

**[00:02:06] Harry:** That's so sweet.

**[00:02:08] Speaker 2:** Talking to talking to strangers went well.

**[00:02:12] Harry:** Yeah.

**[00:02:13] Speaker 2:** So proud of you. Thank you, thank you.

**[00:02:18] Speaker 2:** So that's my bit. Anyone else? That's it. There we go. Sorry.

**[00:02:25] Speaker 2:** Looks like orders over the weekend and we're still alive.

**[00:02:29] Harry:** Yeah, we dropped nothing, like literally nothing.

**[00:02:34] Speaker 2:** Bake wave. And So I saw like 500K orders. Was that just for Purdy and Fig? And that was just like us polling and pulling duplicates. Like, why numbers so high?

**[00:02:44] Harry:** Yeah. Um there's a lot of

**[00:02:45] Speaker 2:** When those are not real.

**[00:02:47] Harry:** There's a lot of overlap, so like they upload their orders at a certain time. and then they run some software to tag it. with like um a four ILG tag. There's like ninety minutes of lags, why our polling window needs to be ninety minutes. So given we poll every five minutes, that's like Every order gets duplicated a certain amount of times. Um so yeah it's like 500 create order request things and then the Djuper just carves it off.

**[00:03:18] Speaker 2:** Is it worth reassessing that? Like, we're not gonna nuka dupa, are we? Like, do we care?

**[00:03:18] Harry:** Slightly.

**[00:03:22] Harry:** though the Duper is like just profoundly good.

**[00:03:29] Harry:** Um I've I've been very impressed with it.

**[00:03:29] Speaker 2:** I mean, we could maybe ask.

**[00:03:32] Speaker 3:** We we can maybe ask the uh the client. Whether or not there's anything we could do around retrieval conditions. We don't have outbound tagging enabled for Purdy and Fig at the moment. So we're not filtering by ILG received at all. If we were adding those to the orders, we could drastically cut down the reap size. That's where we're seeing that volume because the first reap will be 500. First REAP will be 500 orders. Next REAP will be the first 500 orders plus the new orders and so on and so on, which is why you see that bell curve.

**[00:04:04] Speaker 2:** Yeah, yeah, yeah. Okay. If we don't care, doesn't matter. Like, if it's not gonna, if there's no cost, performance here, or confusion, doesn't matter. May maybe make it more clear in terms of like a high level observability that that's not really a relevant number. Unless it is. Um I mean I suppose it's only the Documents you're sharing inside the Bifrost channel, and Pete's the only person who doesn't understand what that means. It's not like it's being shared publicly. Um maybe the information he wants public we could make more obvious, but other than that if it doesn't matter, it doesn't matter.

**[00:04:37] Speaker 3:** In our ingress dashboard, we've got a total, a distinct orders count that perhaps we could surface that more clearly.

**[00:04:46] Harry:** Yeah, we're going to A better dashboard that's a bit of a here is what is happening that is relevant. because I've got This for the T V. Mm.

**[00:04:58] Speaker 2:** Do we need that?

**[00:05:00] Harry:** Um well in order to put something custom on there, yeah.

**[00:05:03] Speaker 1:** That's what we're going to run an EWMS on, and it will be faster. Yeah, that's got more compute than Snap. I think, just on that, though, I think the ideal outcome will be that we get outbound order tagging on Purdy and Fig. I mean, that's beneficial for the customer, it's beneficial for us. We need to, I was just speaking to Matt about this, we need to do some work to make sure that's available on the bulk. Half, which we'll look to do towards the end of the year. Because I know other clients have high volume and outbound tagging, so we'll need that as a parity requirement anyway. But to Harry's point, if the guys have no concern with its current way, then It's okay for now. We'll pick a battle another time.

**[00:05:51] Harry:** Yeah, like for us it's fine. Mm. genuinely fine. And it's quite good to see everything's dress tested, especially a TypeScript based Djuper that's doing like

**[00:06:03] Harry:** fifty concurrent requests a second. without breaking a sweat.

**[00:06:13] Speaker 2:** Um

**[00:06:16] Speaker 2:** Yeah, do we just want to go over stuff? Generically, anything else about peak? volumes that are worth mentioning. How how do we want to do this? I know there's not new customer onboardings. Um, for the next kind of couple of months over peak, right? So, do we replace that jump? Kind of. Okay, go on there, start there.

**[00:06:32] Speaker 1:** So there is one potentially this side of the year, which is a Jitabit customer called Indu. So those are one of the clients we're putting through Supply Lens because they use the onleash connector on the Jitibit world. Um they were originally meant to go live in January, but Supply Lens have been able to solve a problem with them in relation to TikTok Shop, which is a big market for them. Obviously, because TikTok shops are becoming more prevalent, we'll see this with other customers. So they are pressing very heavily. I've been read some of the emails, to say the least, to the CAMS and the project team about. Getting them live on view so they can take use of the supply lens capability. So I think prior to Black Friday is their aim, just so they can leverage Black Friday TikTok shop. Um it's an SFTP customer. They're testing at the moment. Um Tom's in the agreement that we'll still have seventy two hours' notice. So I'm still expecting it's not going to be a spin on a heel kind of situation, but they may go live in the next couple of weeks potentially. Apart from that, Flur is still waiting for their Polish fat number. So that, not Flur, sorry, Flur's already gone live. Joe Loves is waiting for their Polish fat number. Edom's packaging does need to be reworked, so that's going to be in the new year. We also have Empower, which is going to be in the new year, which is Mel B's beauty brand that she's launching. And we also apparently have a new verbal commitment, although no signed credit app yet for a customer called Wiggles, which Given that's the name of the strip club in Portsmouth, it is very amusing to me. But I draw Southampton.

**[00:08:16] Harry:** It's an Yeah, I was gonna say, isn't that a bike brand as well in Portsmouth?

**[00:08:20] Speaker 3:** It used to be a Um I interviewed there uh many years ago. I think I think they went bust. I'm not sure.

**[00:08:24] Harry:** I did it.

**[00:08:29] Speaker 3:** I don't want to Google.

**[00:08:31] Speaker 1:** To find out what the brand is. I'm just like, I'll wait till someone sends me a link to be honest, because I'm scared if Google wiggles what's going to come up.

**[00:08:36] Harry:** Okay.

**[00:08:39] Harry:** Man, can you imagine going through the fucking shelves of the warehouse and they just got like women packaged up?

**[00:08:39] Speaker 1:** Um

**[00:08:45] Speaker 2:** Ah yeah. I I I went bust at Wiggle in Portsmouth.

**[00:08:50] Speaker 2:** Ah, that could be broken down so many ways. Yeah. You're welcome.

**[00:08:51] Harry:** Interesting, I bust at Wiggle in Portsmouth.

**[00:08:57] Speaker 2:** Um not as bad as the best out of context. Comment from the office last week was, um Or was it I've only recently come to sweet potato. That was the best. context phrase from the office last week.

**[00:09:12] Speaker 1:** I I see. Okay. But anyway, apart from that, on the rest of the gay lies, I think, yeah, we're good till the end of the year. We may see one or two customers pick up one or two interfaces that they're already live, but like, for example, they might turn on stock adjustments, but Nothing been heard of yet. And then in the new year, we're looking at migration, migration, migration. So I'm just waiting for the plan to be formalized for that and agreed on the actual dates for the customers. And then obviously we'll share that with the group, but that's mostly Darren's project. in terms of the planning and stuff. And we're just focused on enabling Shopify as best as we can. by the year end really. So Me and Tom Dunn have been going through the parity requirements, making sure everything's there, it's looking fairly all right, to be honest. I think Shopify's in a pretty solid space. Um but yeah, otherwise that's it for Go Lives at least.

**[00:10:12] Harry:** Do we have any info around CT?'Cause they've kind of gone dark.

**[00:10:17] Speaker 1:** Yes. Um Well, kind of. So obviously there was the issue about their splitting. I'm just catching up on the emails because they all came in Thursday, Friday. Basically They pressed us to get an SFTP set up because they were like, we want to send files, we want to send files, we want to send files. So we did that. And then guess what? They weren't ready to send files. God forbid. Basically, the one thing they come back with now, it sounds like to set up their EDICOM connection, they need the folders there already. So the thing I was just speaking to Matt about, and I was going to chat to you later, Harry, was just for those folders that are missing, can we just get them created on those two SFTPs? Appreciate it.

**[00:11:00] Harry:** Yes and no.

**[00:11:00] Speaker 1:** Um Yes or no. Okay.

**[00:11:03] Harry:** Yeah, it's it's a bit more nuanced with the new approach uh to

**[00:11:04] Speaker 1:** Uh

**[00:11:07] Harry:** The VM, which isn't a VM anymore.

**[00:11:09] Speaker 1:** Right. Yeah, that's what Matt said. He was like, I the change might have messed with that. Um Because I understand why we keep it like that, because those customers, some customers won't have that use case and therefore don't need to see those folders. So I think the approach makes sense. But yeah, it sounds like they just need those folders there for the two SFTPs. Since CT has taken so long, they have provided a de facto example. So the suggestion was to set up a secondary SFTP. on the dev customer. That is specific to ILG. So separate credentials, separate mapping essentially. And then just land those example files, but that's with Lee's team and they haven't done anything with that yet. But that's really just to keep the segregation between the two SFTPs'cause we don't want to muddy the customers' creds and whatnot.

**[00:12:03] Speaker 1:** Um but that's it. We've meant to enter formal sit on the 16th, but to be honest, like if I think they're going to be ready for that, I'd be lying. Um they've been pretty naff, I'm going to be truth. Um

**[00:12:16] Harry:** Yeah.

**[00:12:16] Speaker 1:** I uh Obviously I'll keep you guys in the loop as we go, but at the moment it's really just waiting for them to send files. We do have reserved capacity till the end of the year to deal with any functional feedback. Um but we don't know that until we know that unfortunately. Um

**[00:12:33] Harry:** We we can we can always look to do some like end to end stuff ourselves outside of like

**[00:12:38] Speaker 1:** Okay.

**[00:12:40] Harry:** the integration that Lee's team will presumably set up.

**[00:12:44] Speaker 1:** Yeah, I I'm hesitant on it at the moment just'cause I don't want to set that precedent. I want to try and pressure test them first to get them to do it and then yeah.

**[00:12:51] Harry:** Site.

**[00:12:55] Harry:** just to get ahead of it internally, we don't have to say to the integrations team, and I'd rather not, because... like you I think they need to pull their fucking thumb out their ass and do something. Um Because looks like Tom is now doing what James was meant to be doing, which means we've got even less QA capacity.

**[00:13:14] Harry:** Um but at the same time I'd rather not get blindsided by a ah suddenly everything's a priority. So if we can do like some Silent fixes. I think that's where I'd rather push us towards.

**[00:13:26] Speaker 1:** Yeah, yeah, I mean, all all the files are attached to the epic. I'll double check that and make sure the latest are on there. But we have a plethora of examples. So if someone wants to take them and stress test, then absolutely please do.

**[00:13:40] Harry:** Yeah, I I think that'd be an important step.

**[00:13:45] Harry:** 'Cause we we've just gone off like the fucking Edicon standard sample files, which is great. But you know. the devs of us in the room know how good people are at um sticking to standards.

**[00:14:00] Speaker 1:** Monsecum Ride so it's written on a stone tablet.

**[00:14:03] Harry:** Yeah. Wow. Might as well have been.

**[00:14:08] Speaker 1:** on old parchment paper.

**[00:14:08] Harry:** damage that came out.

**[00:14:13] Speaker 1:** But but yeah, they're they're all on there, so feel feel free to give it a stress test or whatnot. I just know it's been a busy few weeks, so um but if we've got capacity now, then yeah, absolutely.

**[00:14:23] Harry:** That sounds good.

**[00:14:26] Harry:** Yeah, happy to Happy to ask my cronies to do that.

**[00:14:31] Speaker 1:** I knew you were just gonna throw your agent at it, so yeah.

**[00:14:34] Harry:** Ah, I was talking about that.

**[00:14:42] Harry:** Okay, now that that's

**[00:14:45] Harry:** Good but concerning Uh The momentum that

**[00:14:48] Speaker 1:** Yeah, we'll keep an eye on it.

**[00:14:50] Harry:** probably pretty another just peak to be fair.

**[00:14:50] Speaker 1:** Excellent.

**[00:14:55] Speaker 1:** I think that, and I think, to be honest, I don't even think it's CT. I think it's Pugh that are being the pain in the ass, to be honest. So.

**[00:15:05] Speaker 1:** Well, and Eddie Pom because they have technology from the 1900s. So, um but anyway.

**[00:15:13] Harry:** Yeah.

**[00:15:14] Speaker 1:** Do we have a teletype integration? Yeah. Facts facts my orders in.

**[00:15:23] Harry:** Yeah, we we we'll be working on our um R S catalogue integration next night.

**[00:15:28] Speaker 1:** Yeah.

**[00:15:32] Speaker 1:** Xerox printer integration.

**[00:15:35] Harry:** No, it sounds overall sounds good. Um

**[00:15:40] Harry:** I think Nothing nothing that's

**[00:15:44] Harry:** Unknown, shall we say.

**[00:15:48] Speaker 1:** Yeah, we'll wait to see what they say about the split in. That's probably the biggest risk at the moment. And if that happens, there needs to be a conversation of how to solve that problem because I think Harry, as we discussed, Fuse is definitely not the right place to solve that problem. So somewhere upstream. But if SAP or EDICOM can't do it, then there may need to be a different approach that we need to look at collectively.

**[00:16:10] Harry:** Yeah, I I expect it might be The only way to do that would be a bespoke connector.

**[00:16:16] Speaker 1:** Uh Yeah.

**[00:16:19] Harry:** maintenance overhead and that.

**[00:16:22] Speaker 1:** Yeah.

**[00:16:22] Harry:** Mm. Things to things to consider.

**[00:16:29] Speaker 1:** But if we get to that situation we'll pull everyone together and we can Talk and work it out. Like, we want to take whatever's most maintainable for us forward that just solves the problem, right? So

**[00:16:41] Harry:** Yeah.

**[00:16:43] Harry:** Be fine.

**[00:16:45] Speaker 1:** Yeah, that'll sort any tongue can fall a thing, right? It'd be fine.

**[00:16:46] Harry:** Mm-mm.

**[00:16:51] Speaker 1:** I hope. That is.

**[00:16:55] Speaker 2:** Um Ryan's team and the support model and kind of the handover of our document, is that going well? How Are they liking it? Have we had any incidents? Blah blah blah.

**[00:17:03] Harry:** Nothing on on call started as of Saturday, nothing over the weekend. Um Brian was all happy with the docks and the approach and everything, which is nice. Um

**[00:17:13] Speaker 2:** If they've been using them, can you see that anything's been triaged? Do we have visibility of issues raised to them? I don't think so, right?

**[00:17:19] Harry:** We we have no kind of visibility. Uh we we just have the wall.

**[00:17:26] Harry:** Um but I mean Since handing it over, we've we've had a grand total of nothing. Which is less than something, so my suspicion is that the documentation's actually been helpful. You know, it's it's like if if you hear nothing from your sock, that's good news. If your sock starts talking, that's really, like, not very good.

**[00:17:47] Speaker 2:** What you been doing to yourself?

**[00:17:51] Speaker 2:** and was sweet potato involved? Only recently. Cool. Okay. And have we noticed a decrease in messages in like the Bifrost General channel since handing over those workbooks? Like, do you think they are becoming more self-sufficient or do you think it just? Hot talk.

**[00:18:07] Harry:** Yeah. I I'd say

**[00:18:11] Harry:** It it's been quieter since we handed over the order tracker.

**[00:18:17] Harry:** I I'd say the the appearances of the support team is kind of just yeah. been less since then. Um as of handing the docks over to Ryan, like we've we've seen absolutely nothing.

**[00:18:31] Harry:** So yeah, it it's uh no news is good news.

**[00:18:37] Speaker 2:** Mm-hmm. Um what else did I have on my list? I think that's pretty much it. Um That blow testing and Stability, like it's not really in our control, but it's been blippy the last few few. Days or weeks? How how are we feeling? Well there's much we can do, but

**[00:18:57] Harry:** I mean

**[00:18:59] Harry:** Wa we've like limited it to fifteen requests a second. Uh that that's all we can do. Um Snap's been extra blippy especially recently. I don't know if you've seen any of the Snap channels but like those monitors have been going wild.

**[00:19:13] Speaker 2:** No.

**[00:19:15] Harry:** Uh somebody did something on Saturday morning because it was like fine fine fine find Jesus fucking Christ Mm Yeah. Don't really understand.

**[00:19:26] Speaker 2:** Recovered?

**[00:19:27] Harry:** what's happened. No. No, it's it's The latency graph looks like a sine wave.

**[00:19:33] Speaker 2:** Our vibes.

**[00:19:35] Harry:** Um but like Map requests take up to

**[00:19:43] Harry:** They they can hang on to a request for about thirty seconds and then commit it, so given we're only like at 10% of that, I don't have any concerns.

**[00:19:54] Speaker 2:** at ten percent of that. Oh, I think like that's that's happening.

**[00:19:56] Harry:** Yeah, so two two seconds for a request to go through.

**[00:20:00] Harry:** Uh whip.

**[00:20:01] Speaker 2:** And are we not getting to the point with 15 being processed a second, we're not building like an insurmountable backlog yet?

**[00:20:06] Harry:** uh the the cue's about like and minute lasso checks.

**[00:20:14] Speaker 2:** As long as it's not growing by more than a second a second, we're fine.

**[00:20:18] Harry:** No. Yeah, that like that when they get the troughs the the queue tends to drain. Um I think the the worst we ever saw the queue was when we performance tested dev. Mm-hmm. you know, a few million records and that. had a queue where the oldest item was about an hour, that traded in about 10 minutes.

**[00:20:39] Speaker 2:** Oh, okay.

**[00:20:41] Speaker 2:** Right.

**[00:20:45] Speaker 2:** Um That's most of the stuff from my list apart from with Matt. Candidates, interviews. Ethel

**[00:20:52] Speaker 3:** How are we to We've got uh we've got three this week that we're quite interested in seeing. Um our favourite at the moment. Favorite without actually having spoken to him is second Matt Shaw. Um yeah, uh speaking to him on Wednesday, the only thing with with that is he is at uh second slash final interview process uh with um another firm. So That could go either way at the moment. We could get to Wednesday and find out that he's already accepted an offer somewhere. But we do have Edward Savage and second Darren. Um Also on Wednesday and Thursday. Edward Savage is an interesting one.

**[00:21:44] Speaker 2:** Second stage of Matt Shaw. Is that?

**[00:21:48] Speaker 3:** Uh Matt Short is at a second stage with a another another company. And what about And Wednesday will be his first first round interview and a live check. And that's true for all the candidates that we're seeing this week. We haven't had a first round with anyone we like yet. Uh no, not yet. Uh hopefully that will change change this week. Um Edward Savage has come back last week and said, Oh, by the way, I want an extra 5K. Yeah. Which is a bit for your first interview, but there we have it. It is certainly bold, but I mean, he could turn out to be an absolute, absolute dude. We'll see, but it does.

**[00:22:36] Speaker 3:** put some some extra onus on him really really demonstrating a strong fit there. But we'll see. Very interesting considering his background. Um he's at Kinetic on Hill at the moment. Very different. It is it is it is very, very different and um I kind of get the feeling that on what he's been working on is kind of like data center on a warship kind of stuff, reading between the lines. I mean, it could be interesting. I mean, he's not a completely weak fit. It'd be interesting to speak to him, but also, you know, there's not a huge amount of experience there to back up the salary expectation.

**[00:23:21] Harry:** probably worth mentioning that's it that his um background is like quite relevant though. Uh so

**[00:23:27] Speaker 3:** Yes, yeah,'cause he was at Lin

**[00:23:30] Harry:** Legworks.

**[00:23:32] Speaker 3:** Linworks, yeah, which is kind of supply chain inventory management, if I remember correctly. So, yeah.

**[00:23:32] Harry:** uh

**[00:23:39] Speaker 3:** Oh, ab absolutely. So if he can if he can demonstrate all the other the other qualities, then that doesn't put him out of contention at all. And you know, salary is a discussion rather than a demand. So.

**[00:23:53] Speaker 1:** Yeah. You're a son of your co-operative already, man. I love it.

**[00:23:58] Speaker 1:** Learning from the best.

**[00:24:01] Speaker 3:** Gosh, who's that? They're not in the room with us at the moment. I'm trying to find them. Soon you can start saying not to be that product, guy. We do have one more referral from Ruby who came in on late Thursday slash slash Friday. I've taken a brief look at that CV need to go and then and Detailed a bit more, but didn't strike me as being particularly strong. But you know, it could be a

**[00:24:29] Harry:** Okay.

**[00:24:30] Speaker 3:** Yeah, that's we have the Mm-hmm.

**[00:24:34] Speaker 2:** It's worth being kind of strict on our CV filter, and that will probably change even more so because we are going to be talking to. Another um consultancy as well. For several reasons. So they will be sending us candidates as well. And obviously we have to inform we have to inform Spectrum that we're now non-exclusive. And that means Spectrum will also start fucking flinging us candidates. So I will not be shocked if our volume goes up by three to four. I get that means like let's just be stricter on our filter. Sure. I think it is half a week. Gone. Yeah.

**[00:25:07] Speaker 3:** We at this stage we've also ruled out Projector, which is the referral that came in via Jay. Yeah. She looks interesting and she her background is kind of varied, but kind of not as strong as some of the other candidates and perhaps not as strong in some of the areas that we're looking for. That doesn't mean that she wouldn't be a fit somewhere in the team at another period, but I'd think for the senior role, probably not.

**[00:25:33] Speaker 2:** Okay, cool. I just didn't feel strong enough for a senior. Yeah, correct. There so worth mentioning there will be a There is not a single team that doesn't isn't going to have a vacancy on it in the next week or so. Across the spectrum of junior to mid. So if they are like We're not going to necessarily fully reject them. As a whole, for the company. Obviously, there's a balance of As much as I think people could be fit for roles. There also could just be like a pool of candidates for everyone, and we'll see where people fit. So I don't want to just give one person to one company, I'll take all managers into. Like I remember like, here's the pool of candidates. Tell me what you're all looking for individually, and we'll kind of find them out. Like, just because, yeah, someone's not a good fit somewhere, doesn't mean not somewhere else. Okay. So that's good to know. Okay. Um all right, happy that's flowing through. Um How are we feeling in terms of capacity and like roadmap? Do we still feel like bringing in two people at the senior-ish level is the right call? How are we feeling about that?

**[00:26:37] Speaker 3:** That's an interesting question. Maybe, Harry, you can kind of help me out with that at the moment as well. My feeling is that eventually we probably want to look at bringing two. On but at this stage, I think probably the primary concern is just backfilling, backfilling neither. Um

**[00:27:01] Speaker 2:** Rome w won't rush the second then, okay.

**[00:27:04] Harry:** Yeah, I th I think the team will be fine with Um four. Given what next year looks like. Um, if it was everything like a month ago then I'd be pushing for the other head, but yeah. given things are calming down and Well, perform the left and shift it sort of is what is.

**[00:27:32] Speaker 2:** We'll okay, we'll stick to one with maybe one penciled in the background for later, but it's not like we're not going to have other roles, so Okay. seems good so we've got a few people we kind of like but still at very much the first round stage going from there

**[00:27:44] Speaker 3:** Yeah, I'm hoping that this week will generate one slash two candidates to take forward into our next round.

**[00:27:54] Speaker 2:** It doesn't need to, of course. Like, I would much rather. Pass on. Oh, yeah. I don't want to talk. Yeah, yeah. Not to put words in your mouth, but obviously just worth reiterating the. The opinion that Yeah, I want you to be like excited about someone, not someone. No, no fine people allowed.

**[00:28:11] Speaker 1:** You can't hire them because they've got the same name as you is basically what you're saying. has foiled my dastardly plan to uh

**[00:28:22] Speaker 3:** Now that that that that's cool. I mean it would it would be nice to see the process Progressing. But also at the same time, I do want to protect the quality and the standards and the qualities that we look for in the Fuse team and the Certainly for me, I think Harry, you probably feel the same. The the the Intangibles, the culture and the personality fit and the ability to integrate into the team is as important as the technical skill at this point. And especially given what the kind of asks around the kind of reimbursement and salary reward are, it's, you know, let's make sure we get someone who is absolutely as. Far as possible right for the team.

**[00:29:07] Harry:** Yeah. Yeah, salaries be high. My my rule is like if you can work side by side with them. five years and you don't dread looking on to them, then Actually man or woman?

**[00:29:17] Speaker 3:** Yeah.

**[00:29:19] Harry:** Or thing.

**[00:29:19] Speaker 3:** I'm I'm also looking I'm also My concern, and this was my concern with the last interview, is that I want someone who feels like they they would be interested in being with us for five years. There are lot lots of interesting things happening across ILG and Fuse specifically. The last 12 months has been an absolute blur. don't want to do is bring someone on who's with a ging get feels like they're going to get bored in two years and go and look for something else.

**[00:29:53] Speaker 2:** Alright.

**[00:29:55] Speaker 2:** Happy with that. Um

**[00:29:58] Speaker 2:** I think it's it from my list. Um yeah, covered peak, we covered Um

**[00:30:05] Speaker 1:** New customer onboardings, we've covered that. Is there anything about roadmap we want to talk about? still still chugging. Yeah, so roadmap till the end of the year, um C T and JBIP parity. The hope is that we can get legit bit parity by the end of the year. I think CT is on a case. Well, almost parity. Let me click caveat. Parity on Shopify, parity on SFTP. API in January with Ian Mark to build the extensions to the API that some customers have today because API customers are going to have a longer tail anyway. Some of it's around getting status back when you ingest an order via a webhook and whatnot. And I know Harry, when we spoke about it, there was some rework to do on the webhooks themselves anyway as part of that. So that's earmarked for early in the year. Same with some MLOR configuration, which is needed for one or two clients. But then the hope is after that point, unless anything substantially flags, it should be net new green grass stuff at that point. So started to have early discovery conversations around Kind of role-based where people work. So, how those views fit in versus CCP and the customer portal. So, I've been speaking to Um Tom and Then about their roadmaps and when they're looking at those kinds of things and stuff. Okay, interesting. Obviously, we'll need it for Merak as well. So it depends what happens with Merak. But I imagine a lot of the stuff we'll look at post is about either making the experience better within the portal itself or enabling new parties in new facets essentially. But it's all under discovery at this stage. And I think there too many unknowns. But It's so fatal.

**[00:31:54] Speaker 2:** CCP quite likely. Yeah. Like CCP plans for IOG expansion is, yeah, this is hand in hand and very probable. marriage so we may more utilize Mm-hmm. underlying technology than the actual product and the fulfilment process for America, I expect.

**[00:32:10] Speaker 1:** Yeah, I think the better way to summarise it is North Star. It'll be North Star essentially and how we work forwards for North Star. Cause I think. I don't foresee the need for a new connector coming in because TikTok shop is actually mostly done through Shopify, so actually less of a worry. Same with Instagram stores, and those seem to be the two that are big at the moment. So I have less concern about that. It's more around, I think, the big one for us that will be a good win is how do we get customer support working with the capabilities that Fuse has, which comes to the CCP conversation. That serves us well because that stops Ryan's team from bronching that. Okay, fuck you. I'm all right, but then um But that would mean that there's less burden on Ryan's team, which inherently less burden on us because Ryan's team won't be able to us. I think also Ben was talking about they want to try and get off Fresh Desk eventually, which I imagine CCP would be part of that plan as well. Um apart from that, we're obviously going to have a lot of migrations. So just the usual keeping tabs on things. I I'm confident that all the requirements have been captured. I'm asking Tom to go through them again to make sure. Um But obviously, we'll see how that goes. It should hopefully be an ironed-out process by that point. But if history has taught us anything, let's go with an error of caution, right? So, um,

**[00:33:38] Speaker 2:** But in terms of Fuse capabilities, like we feel like we're getting there for Jitterbit on time, we're not going to be the blocker. It's going to be by frost time of migration of existing customers from Jitterbit to Fuse, right?

**[00:33:46] Harry:** Mm.

**[00:33:48] Speaker 1:** Yeah, I think Shopify and SFTP, I think API is an interesting one. API is going to be very much a client by client basis because some of them have basic API integrations and that's less concerning that we can integrate. Some of them have the most bespoke, complex shit that's going on that's like. It's either gonna have to move to the client or they're gonna have to find a new way of doing it. So, yeah, the good news is one of those was CT, which we're doing as part of Edifax. So that's good. And another one I just forwarded you guys an email, just read it five minutes ago, is that BAT, another of our three big customers, on the list. They're moving to SAP next year. So they want to rebuild their integration anyway. So that is a very good opportunity for us. For some of the other ones, like this works, for example, I've heard are pretty tragic in their integration setup. It's probably going to be a longer tail and we won't be looking at a go live before March. Obviously, we'll see with the assessment of those integrations. But I think the big thing that the API customer is missing at the moment is a status webhook that they use to feed back to their system in terms of did the order make it in or not. And I think a couple of them expressed the need to want to be able to query for a shipment. But then that comes as part of the customer portal conversation. And that's where the tie-in comes in with Tom and his plans there. And because it's like, well, you may already get it through that facet, essentially. Um

**[00:35:17] Speaker 1:** So, yeah, we'll see how it goes. But we're planned as much as we can at this stage, to be honest. Yeah. I'm happy with that. Nice views additions we want to add in the future, like change revision history. So like we track changes in the UI, but easy rollback for said things, promoting config from dev to prod, other things like that. But Really, only there if we need to keep busy, but then the argument could be made: well, just put investment in the areas that do need the time and focus. But I think this year has been getting fused to a product, a stable product and well fleshed out, which I think has been achieved. So

**[00:35:55] Speaker 2:** Yeah, yeah. Okay. Oh, it sounded really good. Honest Smith.

**[00:36:07] Speaker 2:** That's it really.

**[00:36:08] Speaker 1:** Didn't anyone got any other things that haven't been covered they want to talk about?

**[00:36:16] Harry:** Mm.

**[00:36:16] Speaker 1:** I don't think so. Anything I've lagged is I still haven't heard my JD is written, but it hasn't been posted. So I'll check with Steph on that. Um Obviously it doesn't change anything, not going anywhere for a while, but just a FYI.

**[00:36:35] Speaker 3:** Just on the recruitment side of things, I did reach out to a couple of people that I know who A, either expressed some interest or could have been in. interested and they've decided that it's not for them at the moment.

**[00:36:49] Speaker 2:** Fair. Was that for Fuse specifically? Or kind of? Yes.

**[00:36:54] Speaker 3:** Yeah, yeah, that was specifically for for Nyla's backfill. Um, one of those, uh, my very good friend Dimple, who's currently at Oracle, uh, I thought she might be interested because her daughters are now sort of moving to university in Southampton, and you know, she's not really doing a lot of development at Oracle, it tends to be more kind of like OS and uh stuff like that, but she's a very strong developer. I thought maybe it would be. of interest to her and she's decided she wants to stay where she is for now. The other person I spoke out, reached out to was a good friend of mine who I've worked with a long time ago. He's now a program manager. would like to get back into development, but um Yeah, the lot the last time you deployed any code, it was to an IIS server. Say not quite up there with modern modern cloud stuff, and I think he would find it. Uh more frustrating than rewarding. So, yeah. Um but I'm you know, if anything comes up in the DM kind of space, then that might be something he's interested in. So

**[00:38:03] Harry:** Mm-mm.

**[00:38:03] Speaker 3:** I mean it seems it's like

**[00:38:05] Speaker 1:** There is a hosted project program role at the moment, so feel free to spend on that.

**[00:38:11] Speaker 3:** Yeah. Yeah, well, he he work he works for Molex at the moment and uh not particularly on board with the whole big American kind of corporate world these days. Pretty much preached a lot.

**[00:38:27] Speaker 3:** Why why is Ro Molex ringing it? Oh, it's the cable, Molex plug, isn't it? Isn't that a power cable? Yeah, they they they they do all kinds of things. They do, uh various kinds of connectors, but they anything associated with that, he works on connection.

**[00:38:45] Speaker 3:** No, he works for their premise networks division at the moment in Lakeside. So you think structured cabling, massive runs of, you know. Cat sick table influenced. um, offices and data centers and stuff like that. It's kind of his jam at the moment, so All right. Not fair, no worries. Um Alright. Anything else from anyone else?

**[00:39:09] Speaker 1:** live in La Vida Loca.

**[00:39:11] Harry:** That's in here. I've got

**[00:39:12] Speaker 1:** Oh yeah.

**[00:39:13] Harry:** Got a hated m uh mouse mat and the cats are loving it, but

**[00:39:18] Harry:** Business related stuff, nothing.

**[00:39:18] Speaker 1:** I'm gonna start thinking you're working for their sales team or someone.

**[00:39:22] Harry:** Like, honestly, like...

**[00:39:24] Speaker 1:** No.

**[00:39:24] Harry:** live in the dream.

**[00:39:26] Speaker 1:** Ah, that's cute. Why do you have a heated mouse map?

**[00:39:29] Harry:** I've got the circulation of uh an eighty year old woman. I've broken so many fingers that like blood just doesn't flow anymore.

**[00:39:33] Speaker 2:** Yeah.

**[00:39:36] Speaker 2:** Maybe you know. Yeah. It is a bit sad when you gotta put like I considered putting gloves on in my own house the other day, because your fingers do get cold, especially when you're typing.

**[00:39:43] Harry:** Yeah.

**[00:39:46] Harry:** Yeah. Yeah, my my hands like routinely go blue in the winter.

**[00:39:47] Speaker 1:** Chickens have your pants, isn't it? You say sticking down your pants, Jack?

**[00:39:53] Speaker 3:** I thought you were all text to speech these days, Ollie. I am it depends if there's people like if I'm near people.

**[00:39:59] Speaker 2:** Like on a laptop. I do. I do love a bit of text of speech. He's really good. And I feel like I think better as well. I do sound a bit wacky.

**[00:40:07] Speaker 1:** Lie on the floor if you want to think better. It's scientifically proven. It works. Oh, Steph was talking to me about this. Yeah. I thought it was stupid, and then I did it. And I was like, I've only come up with an idea in my first 12 months of working here. Like, it's like it.

**[00:40:24] Speaker 2:** My um For me, it's pacing. Like, I walk, if I walk around, I do better. Like, marching up and down my path in the garden during COVID was where I like solved all my problems.

**[00:40:35] Speaker 1:** Makers like, oh, he's out again.

**[00:40:39] Speaker 2:** Actually fucking mental, but it worked.

**[00:40:44] Speaker 2:** Right. Mm-hmm. Right, lunchtime everybody. Absolutely.

**[00:40:50] Speaker 3:** Something like that. Certainly next coffee time.

**[00:40:50] Harry:** Yeah.

**[00:40:53] Speaker 2:** Hell yeah. And for me. Well At one o'clock I've got the AM boarding workflow planning with Dan Enoch. And then I've got the Snap UI automation project with Schuster and Moises. And then I've got the C X weekly for another hour, so

**[00:41:07] Harry:** A meeting run by Heuthrid Moises, I just

**[00:41:10] Speaker 2:** Oh yeah. I don't know what can go on there, but

**[00:41:14] Harry:** Man, what a dynamic.

**[00:41:14] Speaker 2:** gonna be something. Hmm.

**[00:41:20] Speaker 2:** Oh no.

**[00:41:22] Speaker 2:** Yeah. There might be some conversations out the back of that of what actually he's doing.

**[00:41:31] Speaker 2:** Um

**[00:41:33] Speaker 2:** Alright. Seems good. Does anyone need anything from me?

**[00:41:40] Harry:** Yeah.

**[00:41:40] Speaker 2:** No, I don't think so. I like them. Easy. Alright then, well. Nice to meet you, lads. See you two thirty tomorrow. As always, boys, in a bit. Just take care. Bye bye.

