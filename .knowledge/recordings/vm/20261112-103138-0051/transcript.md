**[00:00:00] Speaker 1:** there's a chat with Bill Chris Cummings and Peter that I got dragged into. Because they're talking about Um it was all about the FedEx accounts but specifically. But it's it's sort of diverted because every time we go on this call, Basically, they've got MVP one, which is where they're using a CSV to upload. by a dispatch class.

**[00:00:21] Room 1:** Okay.

**[00:00:23] Speaker 1:** you've built a system that we can basically, I think, just literally do a swap out type thing.

**[00:00:29] Speaker 1:** So at least we can test that today. We can sort of do a run through and check where we're at.

**[00:00:32] Room 2:** Yeah. Absolutely.

**[00:00:35] Speaker 1:** From that.

**[00:00:37] Speaker 1:** They then started going, oh, what about MVB two? Because they quoted me four weeks to get an SFTP setup working on their end.

**[00:00:45] Room 1:** Could help.

**[00:00:45] Speaker 1:** And I was like, that's insane. Like, doesn't it, it takes like. 40 minutes, not four weeks.

**[00:00:51] Room 1:** Yeah, I don't

**[00:00:51] Speaker 1:** We'll provide you with the implement details. And basically, they're saying the guy. The guy was just like using tech words that had no meaning. For what? But he was just like, oh, we'll have to like check all of the bugs of where the CSVs and make sure that it's like hard coded to drop into the right location so that it doesn't like create the wrong formatting. And I was like, you just waffling. Like, it's.

**[00:01:15] Room 3:** I yeah. Is he an enterprise architect by any chance?

**[00:01:16] Speaker 1:** Nonsense basically. Yeah, I think he might be. Yeah.'Cause basically that They they're getting stuff out of s of Manhattan scale. Um But I was like, if you're already getting the CSV, I need no changes to the CSV. Just send the CSV to the SFTP setup that we're going to provide you.

**[00:01:36] Room 2:** Oh yeah, because it the the thing that we've built, you you can just like doesn't fucking matter about the CSV, like what the columns look like, because we can just change that.

**[00:01:44] Room 3:** mapping.

**[00:01:46] Speaker 1:** Um and also so Let's forget the SFTP for now because clearly that's out of their remit. We could, you said there's a drag and drop feature, right? So they can literally just drag CSV in and

**[00:01:53] Room 3:** Yeah.

**[00:01:55] Room 3:** Yeah.

**[00:01:59] Speaker 1:** Order by order, I guess. They could just drop it in.

**[00:02:00] Room 3:** F full on yeah, full on retard mode.

**[00:02:04] Speaker 1:** Cool. If we test that this morning and we prove that works.

**[00:02:07] Room 3:** Yes.

**[00:02:09] Speaker 1:** Um I think people will be okay with us going forward because now the Americans have moved fully onto, oh, well, let's look at MDP2, which is their API system.

**[00:02:18] Room 2:** Yeah, uh okay.

**[00:02:19] Speaker 1:** But Pete, I think there's some confusion there because Pete was like, we don't want to talk about MVP2 because that's mirror.

**[00:02:26] Room 3:** Yeah, okay.

**[00:02:28] Speaker 1:** So that's where we're getting into the realm of like, but is it Merrick or is this just They need to get their API call, which is actually completely separate from because whatever we build. Their API call still has to fucking work.

**[00:02:38] Room 2:** Yeah. Yeah, and and like we we can just swap out whatever the API backs onto. So it's

**[00:02:42] Speaker 1:** Mm-hmm.

**[00:02:45] Speaker 1:** Yeah, exactly. So I was like, maybe, maybe this isn't Eric, and we do get the API working because.

**[00:02:47] Room 2:** Oh,

**[00:02:51] Speaker 1:** Also, that's a completely separate team. from the guys that did the CSV team. Okay. If we if we can prove the CSV works today.

**[00:03:02] Speaker 1:** I will um if we can go through it now basically, and then we go to Pete at 11.

**[00:03:04] Room 2:** Yeah, yeah, so have a look.

**[00:03:07] Speaker 1:** And say We've got the CSV working. Here's like the evidence of a call to the, because what we can do is test against the live endpoint, the TCA one.

**[00:03:15] Room 3:** Yeah.

**[00:03:15] Speaker 1:** So we can switch that out and then I'll just delete the order immediately because it's bill on scan. So we can kind of hammer it and it doesn't actually matter.

**[00:03:21] Room 3:** Okay cool.

**[00:03:22] Speaker 1:** Um So we can we can pick let me get the T C A info so that you can Yeah. Um And then

**[00:03:33] Speaker 1:** Once we've done that.

**[00:03:36] Speaker 1:** We we need to I get we need to have a discussion with Pete and figure out Do we do they want me to guide the conversation with the Americans to the API or like massively push against it and say? we are not doing API for this at all. That is going to be future solution Because the Americans fully think they're getting an API system.

**[00:03:57] Room 2:** Yeah. Well we we could always

**[00:03:57] Speaker 1:** Now Like right now.

**[00:04:00] Room 2:** Yeah, we we could always position it as like a

**[00:04:00] Speaker 1:** I mean, we your like you said, your system works, right?

**[00:04:03] Room 2:** Yeah, we we can always like position it as a like stepping stone AP

**[00:04:06] Room 3:** They feel like this is what you've got in the interim, but be warned, you'll have to change.

**[00:04:09] Speaker 1:** I think we just need to get Pete on board with that. That's the The conversation side because Pete immediately was like, No, it's Merrick, don't touch it. And I was like, It's not, I promise this is not Merrick.

**[00:04:14] Room 3:** Yeah.

**[00:04:19] Room 3:** Yeah. Yeah, we we need to keep these people fucking happy as well. That that's part of the battle. Um shall we shall we have a look? Should we have a look, see?

**[00:04:28] Speaker 2:** Yes. Yes, I'm just getting that.

**[00:04:29] Room 3:** Um

**[00:04:32] Speaker 2:** Yeah, you do chip it now.

**[00:04:33] Room 3:** Here you go. So if I ball up a screen share.

**[00:04:39] Room 3:** There you go.

**[00:04:43] Room 3:** I've got like it it's even got a I I don't know how actually poked about but I've got a spec test customer you should

**[00:04:45] Speaker 1:** Yeah.

**[00:04:49] Speaker 1:** Yeah, I did yeah, I did go through. I did have a look at ESA. I haven't done any like upload tests or anything yet, though. Didn't have time.

**[00:04:54] Room 2:** Let's uh Let's have a peek. So

**[00:04:58] Speaker 1:** I had a really fun moment yesterday where they tested Talos in the fucking BM two.

**[00:05:02] Room 2:** Hey fucking hell.

**[00:05:02] Speaker 1:** And just added like an they added like an entire process.

**[00:05:07] Room 2:** Yeah.

**[00:05:07] Speaker 1:** And they were like, where's this? And we were like, they said, where's the mezzanine scan point? And I was like,

**[00:05:11] Room 2:** Yeah.

**[00:05:11] Speaker 1:** At no point in the entire discovery or testing or anything has anyone said the word mezzanine ever.

**[00:05:17] Room 2:** Oh, I swear they've only just built the fucking mezz at BM2. Um

**[00:05:23] Speaker 1:** May I and I was like, So you want this to work? And they were like, Yeah, we need it to work by Friday. And I was like, That's a complicated.

**[00:05:25] Room 1:** Here you go.

**[00:05:27] Room 1:** The the fucking mes is empty.

**[00:05:29] Speaker 1:** Yeah, and they were like They were like, yeah, this needs to work now. We were like.

**[00:05:33] Room 1:** See, look at the colours.

**[00:05:34] Speaker 1:** Watch. We literally like we've had it running like.

**[00:05:36] Room 1:** Yeah, look.

**[00:05:38] Speaker 1:** Since they told us yesterday, and I think we've got a like first draft build coming out like this morning, it finished at like 9th A.

**[00:05:43] Room 1:** Yeah.

**[00:05:45] Speaker 1:** It's a complete rebuild because they were like, Oh, we want the scans to work offline.

**[00:05:49] Room 1:** It's fucking empty though. Like what what are they doing?

**[00:05:50] Speaker 1:** Originally, in the original spec. Man, it's not fucking ready, is it? Just yeeting pallets off the top.

**[00:05:54] Room 1:** Yeah, true.

**[00:05:56] Room 2:** Yeah. They've got a man on the mezzanine and like clearly he needs this.

**[00:05:58] Speaker 1:** Well, yeah.

**[00:06:01] Speaker 1:** Yeah, I I don't know what's gonna be going on with that, but Yeah. And they were like, oh, we needed it to work. And also the whole concept of, because we had it so the PDA stored the local data. And if like the Wi-Fi went down, they could still work. So, and then they double load later. But now they're like, well, we need the mezzanine PDA to speak to the. Endpoint a PDA. And we're like, but what the network goes down. And like, they were like,

**[00:06:24] Room 1:** Oh my son.

**[00:06:27] Speaker 1:** Yeah, no, but we still needed to talk. So we were like, so you don't want offline capability.

**[00:06:31] Room 1:** Yeah, but the network goes down as well, like I don't understand why they they aren't, um uh

**[00:06:31] Speaker 1:** Because

**[00:06:36] Speaker 1:** It's messy, man. Yeah, well, I might have to get you to look at it next week or something and be like, what the fuck are we doing? Because it's crazy. But yes, back to back to the back to this.

**[00:06:36] Room 3:** Talking about that bow.

**[00:06:44] Room 3:** Oh my god. Yeah, yeah, yeah, yeah. So, um here we go. So I've got a sample CSV. You can um you can grab the sample from that link.

**[00:06:52] Room 2:** Uh

**[00:06:53] Speaker 1:** Is that sample the dispatch cloud format that we had before? Okay, cool, sok.

**[00:06:55] Room 2:** Yes.

**[00:06:58] Room 2:** Yeah, and when you when you create yeah, so it's got like some uh like fake errors as well and you can go in and

**[00:07:03] Speaker 1:** But yeah, like Faux problems.

**[00:07:04] Room 2:** modify it like

**[00:07:06] Room 3:** So city. Um

**[00:07:07] Speaker 1:** Okay.

**[00:07:11] Room 1:** Is that fine?

**[00:07:12] Speaker 1:** So the thing they were harping on about was. Um the the dims, which is the thing on the top right of the label.

**[00:07:19] Room 2:** Yes.

**[00:07:20] Speaker 1:** Um for that they wanted because of the rounding issues they were having.

**[00:07:23] Room 2:** Uh

**[00:07:25] Speaker 1:** Um And Because I think they're having to do like, and the weights, they're having to do the conversions, because I don't think Dispatch Cloud offers. American weights.

**[00:07:35] Room 1:** Okay.

**[00:07:37] Speaker 1:** So they were like having to do the conversion and then enter it. Converted and it was coming out a little bit iffy sometimes. But if you offer everything.

**[00:07:42] Room 1:** Boy.

**[00:07:44] Speaker 1:** even easier. And then we can do the conversion into our system.

**[00:07:45] Room 3:** Yeah.

**[00:07:48] Room 3:** And they they can they can set up packaging presets as well.

**[00:07:51] Speaker 1:** Yes, that's what they had. Yeah, so I can actually get the presets from

**[00:07:52] Room 3:** Um

**[00:07:57] Speaker 2:** Dispatch cloud so we can have it ready to go as well.

**[00:08:01] Room 1:** Yeah, and I think

**[00:08:01] Room 3:** think for this customer as well so this is the smote test customer you should Card layout? Yeah. This is, yeah, like it defaults to dispatch card because we

**[00:08:15] Speaker 2:** So it should. reasonably just pick up their files that they're using. Like

**[00:08:19] Room 3:** Yeah. Like they might they might have to change this and like these will be their columns in their CSV. Um

**[00:08:28] Room 3:** And yeah, like they they could just change that as an as an one. But like really you can just fucking

**[00:08:36] Room 3:** Dispatching four. Okay, the carry. course because it's I've set it up on the B check Devo customer.

**[00:08:42] Speaker 1:** Yeah.

**[00:08:43] Room 3:** Um

**[00:08:45] Room 2:** But yeah, so like you basically just select it or hit dispatch, um and you can either go like into the order, preview the label.

**[00:08:53] Speaker 1:** And then that sends the commit call to the s to the VM. Which then

**[00:08:56] Room 2:** Yeah.

**[00:08:57] Speaker 1:** Who's back the the the string for this? Okay, cool.

**[00:09:00] Room 3:** Yeah, and this this saves the um label locally so you can print it as and when.

**[00:09:01] Speaker 2:** Uh

**[00:09:06] Room 3:** Um but you can also go into like the shipments tab. Um And you can do like Bob Print as well, which is fucking sick.

**[00:09:13] Speaker 1:** Oh shit. Okay, yeah. So this is a bro and We haven't tested m I don't think anyone's tested multi packs yet.

**[00:09:20] Room 3:** Yeah.

**[00:09:20] Speaker 1:** So that is something we need to do as well. But what I don't know is with FedEx, do you have to have like, say you do two packs, do you have to have like a commodity block for each one? Or can it use? That's what I'd need to figure out. But I don't think anyone knows yet. Like, Carrier team haven't tested this either.

**[00:09:34] Room 1:** Yeah.

**[00:09:39] Room 1:** Mm-hmm.

**[00:09:39] Speaker 1:** Um the problem I've got at the moment with the the accounts is there is no FedEx test account. Anyway.

**[00:09:44] Room 2:** Right.

**[00:09:45] Speaker 1:** It was a USIN Live account that they used for testing, which I don't want to hammer anymore because that's now with a customer somewhere, like being used.

**[00:09:52] Room 2:** Mm. Oh.

**[00:09:53] Speaker 1:** And the Usen FedEx one we have now. It is their TCA live account.

**[00:10:00] Room 2:** We we have a thing that we could extend. So some of the stuff we

**[00:10:02] Room 3:** been doing in the background. Mate, I maxed out two claud accounts yesterday.

**[00:10:09] Speaker 1:** Wait, I the my problem at the moment is max out my PC, uh, my laptop. Look, my si literally half of my fucking demos shut because my 16 giga RAM, like, shit the bed.

**[00:10:17] Room 2:** Oh dude, we've got we've got um oh here you go. We have

**[00:10:23] Room 3:** from my computer.

**[00:10:25] Speaker 2:** Oh yes, Ollie was saying that you were you were looking into this, yeah.

**[00:10:25] Room 3:** And you can just SSH in.

**[00:10:28] Room 3:** Um so

**[00:10:30] Room 2:** I can send you a link and you can set up a pull request but like do this hacker as fuck like this is so cool.

**[00:10:36] Speaker 2:** Yeah.

**[00:10:36] Room 3:** Um but yeah, these come off like

**[00:10:37] Speaker 2:** sick.

**[00:10:39] Room 3:** 32 gigamemory on the small tip.

**[00:10:42] Speaker 2:** Yeah. Okay, cool.

**[00:10:44] Room 3:** Um So yeah, that that is an option.

**[00:10:47] Speaker 1:** Yeah. Well, I might take up on that we're hitting limits on on building

**[00:10:48] Room 2:** But

**[00:10:52] Room 2:** The I was like mirrored every carrier proxy.

**[00:10:57] Speaker 1:** Oh sick, okay, cool.

**[00:10:58] Room 3:** Um So we've got mocks for everything. What we could do is like

**[00:11:05] Room 2:** Oh, they should.

**[00:11:05] Speaker 1:** Is this similar to what Jake did on that VM that you would test that I gave you? Where it sent where it doesn't actually go anywhere, it just like pseudo creates the label and sends it back.

**[00:11:15] Room 1:** think so, yeah.

**[00:11:15] Speaker 1:** It's similar concept.

**[00:11:18] Room 2:** Yeah, so th this like the actually might be really pertinent for the stuff that you work on actually.

**[00:11:23] Room 3:** should have like you know sooner um but this just mocks every single um carrier proxy that we've got in the business.

**[00:11:32] Speaker 1:** Yeah.

**[00:11:33] Room 3:** Well, not every single I think there's a couple of gaps, like, um

**[00:11:36] Speaker 1:** The bulk.

**[00:11:37] Room 3:** Yeah, I s I know we got A C S. Um but yeah, it it should

**[00:11:40] Speaker 1:** I would guess it's

**[00:11:41] Room 3:** It should mark the contracts. Um And it should return.

**[00:11:49] Room 3:** return the same thing. So the contracts are the same. So the return time should be the same.

**[00:11:53] Speaker 1:** Okay.

**[00:11:55] Room 3:** So this is like might be useful to plug into. I'll try and get some odd docs together. Uh but yeah, this is like

**[00:12:04] Speaker 1:** Well I'm imagining with Merrick we're going to build like a a test playground. Which is going to be like we we a hundred percent should roll that out because we don't have any like beyond what Jake's built. So if yeah, whatever we I imagine there'll be things from this that we can rip out and and use on the daily elsewhere. straight away, especially in terms of like the testing process.

**[00:12:25] Room 3:** Yeah. Because this like

**[00:12:26] Speaker 1:** Mm-hmm.

**[00:12:28] Room 3:** handles all of the upstreams. I think it handles yeah, hap handles a AP key, handles like everything else so. Um

**[00:12:35] Speaker 2:** Yeah, that would work.

**[00:12:36] Speaker 1:** That'll help a lot.

**[00:12:37] Room 3:** Could could be pertinent, but yeah, so that that's like the very quick demo. Like, obviously, you can go into settings, you'll have a GFS account like this one as well, so you can.

**[00:12:38] Speaker 1:** Cool.

**[00:12:47] Room 2:** ActAds, various things, the beachhead demo.

**[00:12:49] Speaker 2:** Oh shit, let me send you let me send you this.

**[00:12:52] Speaker 1:** This is like their actual live

**[00:12:52] Room 2:** Yeah.

**[00:12:55] Speaker 1:** Um

**[00:12:57] Room 2:** Okay.

**[00:12:57] Speaker 1:** No, that's that's an error I just got sent. Give me two seconds, delete that.

**[00:13:00] Room 2:** Oh,

**[00:13:01] Speaker 1:** Uh

**[00:13:02] Room 2:** Um

**[00:13:02] Speaker 1:** I tried to copy paste too quick. My print screen wasn't happening.

**[00:13:03] Room 2:** The yay.

**[00:13:06] Room 1:** Yeah.

**[00:13:09] Speaker 1:** Ping.

**[00:13:11] Room 1:** Um

**[00:13:12] Speaker 1:** There we go. So that's the actual templates they're running on live.

**[00:13:18] Room 3:** Okay. Yes, we can we can set all of that up under the Beachhead demo customer then. So you should be able to go and um Yeah, supple Luki packaging here is various presets which Yeah, I can I can mirror, um we can do that in inches or centimetres and I I think it does all the conversion. Um Yeah, you can act as a customer. The Beachhead demo is one with um uh the selector instance that Jake set up and configured for it.

**[00:13:48] Room 3:** Um there is um an MCP for this, so if you wanna go configure stuff and you don't wanna do it through the UI you can just point your fucking clanker at it.

**[00:14:00] Room 3:** Um, ignore the password box being empty. Uh just yeah. doesn't service it because it's, yeah, for safety reasons.

**[00:14:09] Room 2:** Um Yeah, you can set up printers.

**[00:14:12] Speaker 2:** Thank you. This is one.

**[00:14:19] Speaker 1:** This is like a lump of unformatized or unformatted shit data.

**[00:14:26] Room 3:** Mm-hmm.

**[00:14:27] Speaker 1:** That is that's their contract numbers, and that's their actual config that they have set up to be able to use at the moment.

**[00:14:31] Room 3:** Okay.

**[00:14:33] Room 3:** Cool. I will have my body take a look at that.

**[00:14:38] Room 3:** Um set up.

**[00:14:41] Room 2:** SFTP is just a case of setting up like a username Um and you'll get like a private key.

**[00:14:46] Speaker 1:** Yeah, I'm like, it was mad to me what they were saying. Like, I was like, this is, this is a 20 minute job to set up. Like, this is not a, this is not some crazy.

**[00:14:56] Speaker 2:** discovery process that you need to do. Just dump files you're getting into here.

**[00:15:00] Room 2:** Yeah, and like you can bring your in key as well, so it's not not exactly rocket science, but Here you go, so if we

**[00:15:06] Speaker 2:** Yeah, I think yeah I think the standards Bad to hear off.

**[00:15:11] Room 3:** Yeah. Okay, that's it to do for me.

**[00:15:12] Speaker 2:** wildly different expectations.

**[00:15:14] Room 3:** That's a d do for me then, automatically generate the key.

**[00:15:15] Speaker 2:** Yeah.

**[00:15:18] Room 3:** Um

**[00:15:21] Room 2:** Then, yeah, the like the API exists. You can just

**[00:15:25] Speaker 1:** Yeah, so this is They'cause they c they got the swagger dot uh that they they basically said it was too complicated. Currently, I think feels getting like a new open API spec.

**[00:15:37] Room 2:** Yeah.

**[00:15:38] Speaker 1:** Um But I've not heard what time frames on that. I think maybe today.

**[00:15:44] Room 2:** Yeah, we should probably

**[00:15:44] Speaker 1:** Mike David. Provide that.

**[00:15:46] Room 2:** probably send our own APIs back instead of like

**[00:15:47] Speaker 1:** Yeah.

**[00:15:51] Room 3:** Did you say Phil was gonna design the fucking API?'Cause I'd

**[00:15:54] Speaker 1:** No, so Chris Cummings is giving it to

**[00:15:55] Room 3:** Okay.

**[00:15:57] Speaker 1:** Someone in the carriers' team. I think there's a lot of like.

**[00:15:59] Room 2:** Oh okay.

**[00:16:00] Speaker 1:** I'm not, I know about it happening. I don't know the specifics, unfortunately.

**[00:16:04] Room 2:** Oh.

**[00:16:06] Speaker 1:** It's all out of my purview at the moment.

**[00:16:08] Room 2:** Yeah.

**[00:16:08] Speaker 1:** Which is why I think I I'm hoping Pete comes back and says he's free yet. Oh wait. Actually, I've been missing that. 11:30. So Pete's free at 11:30. It might be good if we just both jump in and call with him and just try and like see.

**[00:16:17] Room 2:** Yes.

**[00:16:21] Speaker 1:** That was good.

**[00:16:22] Room 2:** Yeah, I think um

**[00:16:23] Speaker 1:** we'll call yeah i'll call pete and you at 1130. Um Let's try and do a quick um Test order against

**[00:16:35] Speaker 1:** Fuck sake so she was just pushing updates during the day is wild.

**[00:16:38] Room 1:** Yeah

**[00:16:40] Speaker 1:** remaining updates one. I haven't had any other pop t pop-ups today. This is so stupid.

**[00:16:44] Room 1:** Yeah, we we got a category on Linux or something.

**[00:16:47] Speaker 1:** Yeah. Well, I've got a Mac coming. I asked for one of them. Um So just to just a dabble with. So hopefully I can move off with this. But and then I'm gonna, Carl's actually helping me at the weekend do a Linux setup on my personal computer.

**[00:16:54] Room 2:** Excellent.

**[00:17:02] Room 1:** Love to hear it.

**[00:17:02] Speaker 1:** Um so that I can like start start dabbling about with it. So I never Never really. Taking a die, yeah. Um

**[00:17:10] Speaker 2:** So the Okay, so if I get you the Endpoint implementation. All this.

**[00:17:19] Room 3:** Yeah, shoot it over. I th I think like to be completely blunt, we need to

**[00:17:25] Room 3:** This is kind of ballooning in terms of people that are involved so we should keep the carriers team out. Um

**[00:17:31] Speaker 1:** Yeah, it's it's h the problem is it's they are all like

**[00:17:32] Room 3:** I might start with A.

**[00:17:34] Speaker 1:** Phil and Chris, not Chris, Phil is all over this in terms of Yeah. My opinions of how that's been handled are probably known to you. What I'm trying to do at the moment is get some like

**[00:17:51] Speaker 1:** trying to bring back a bit of reality to the conversation with them because they they're expecting

**[00:17:58] Speaker 1:** We're going to have like a fully fledged product today, which granted it probably does exactly what Dispatch Cloud does already. But they're expecting this to be like, cool, this works now. Let's go on to API system in two weeks.

**[00:18:09] Room 2:** Yeah.

**[00:18:10] Speaker 1:** is what they're expecting. I speaking to the API team from America, they haven't got a fucking clue. I don't think they've done a single test.

**[00:18:11] Room 2:** Yeah.

**[00:18:17] Room 2:** As standard, yeah, they'll push for it because they want to get ahead of it, and then because we're really prompted, we'll be waiting for six weeks with our thumbs up our asses.

**[00:18:25] Speaker 1:** Yeah, so Either. I d I don't think I think our conversation with Pete today will probably be more enlightening.

**[00:18:31] Speaker 2:** Um

**[00:18:33] Room 2:** Yeah.

**[00:18:34] Speaker 2:** Let me go to a secret manager for

**[00:18:39] Speaker 2:** Peace today. Get you better.

**[00:18:50] Speaker 2:** You need the users. Actually, I can generate a user so that we can tell where the tests are coming from us instead of. coming into fargo from them.

**[00:19:01] Speaker 2:** Great cheese, I call it.

**[00:19:03] Room 2:** You're good.

**[00:19:19] Speaker 2:** Yeah.

**[00:19:25] Speaker 2:** Right actually we can use this. So

**[00:19:29] Speaker 2:** Yes, I

**[00:19:32] Speaker 2:** Or uh

**[00:19:39] Speaker 2:** I'm just gonna put them. Fucking cleans drinks, I'm gonna wipe it after. Um That's our biggest.

**[00:20:00] Speaker 1:** No.

**[00:20:16] Speaker 1:** I see um Carl was talking to you about the the IRS set up that we're we're planning or building.

**[00:20:20] Room 2:** Yes.

**[00:20:21] Speaker 1:** Um at the moment, try and get some ideas about how we can

**[00:20:28] Speaker 1:** Um I think yeah, I think that's going to be some bigger conversations. I mean, there's some some stuff we could probably take into Merrick conceptually. Um with how we build it, but there's we're trying to make the best of what we can at the moment.

**[00:20:43] Room 2:** Yeah, I've I've given them a bit of stare.

**[00:20:43] Speaker 1:** Um yeah, it's a bit messy.

**[00:20:46] Speaker 2:** Yeah. I think he's going to speak to um Other people in your team as well.

**[00:20:51] Room 2:** Yeah.

**[00:20:51] Speaker 2:** I think he's got a

**[00:20:52] Room 2:** Yeah, I've suggested you reach out to a couple of senior devs.

**[00:20:56] Speaker 2:** Yeah, how he goes.

**[00:21:00] Speaker 2:** Yeah.

**[00:21:07] Room 3:** How we go um Well you've got uh a thing at eleven and I've got chat to uh Mr Denton at eleven as well. Um have we got everything that we need for this chat with Pete? Um are you happy that kind of everything exists?

**[00:21:26] Speaker 1:** I think so. Like, short of us doing a test now. Um

**[00:21:32] Speaker 1:** So I don't know how easy it is for you to like use that end point there that I've just given you. Um, with the user pass for it to like literally just ping me ping a fake order through.

**[00:21:42] Room 3:** Yeah, let me if I get my agent on it because it can do like a smoke test kind of situation.

**[00:21:48] Speaker 1:** Yeah, if we if we can get that done before 11.30.

**[00:21:48] Room 3:** Um

**[00:21:52] Speaker 1:** with the with the CSV format that we know they're using. At least then we have like a we know it works sort of scenario. going into the talk with Peter Lumpay. Um and then it's um I think it's gonna be open-ended. I think we need to decide how much we want. I know Pete doesn't want to touch the API because it's like Merrick in his head, but I think your point of making this a As long as we're clear this is a stopgap.

**[00:22:16] Room 3:** Yeah.

**[00:22:18] Speaker 1:** As a like, yes, we can get your API working, but Again, that may change in the future too. when we expand. Um My problem is I'm trying to control because they're talking they're already talking about their second and third customer. about rolling out Dispatch Cloud to it.

**[00:22:33] Room 3:** Yeah.

**[00:22:33] Speaker 1:** And I'm trying to like. rein that all back in and and at least with your system. We'd control it and we'd have a bit more like. management of it than dispatch. Um'cause they're already talking about like dev changes they need for dispatch. It's such a waste of time and effort for everybody to go through that process. When like you would be able to do that in like 10 minutes, if they were like, oh, we need this button. And you're like, okay, cool, done. You know, it's, it, it's such a different.

**[00:22:56] Room 3:** Yeah.

**[00:23:01] Speaker 1:** Different area because their dispatch is just not built for US. Um at all. Um I've um we've got a trial running as well on selector to where I've changed all the time on the server.

**[00:23:12] Room 3:** Oh yeah.

**[00:23:12] Speaker 1:** So US, I don't think anything breaks. I think. but I'm gonna have to run it for 24 hours to figure out how the carriers' interactions work. Um'cause they will push at different times. But I've done like a test push, but Um The reality is it might

**[00:23:28] Speaker 2:** fucking keel over somewhere along the line, but I'll keep an eye on it.

**[00:23:32] Room 2:** Yeah.

**[00:23:32] Room 3:** Um What what I've done is I've kicked off an agent to go and set up the user and put the config in for selector. So Um it will do that. I've asked it to update you as well'cause it I appreciate we both have Um Things at 11, but hopefully we should be all set up. If not, I'm sure Peter will be fine with the demo. You've seen how fusers acted, so

**[00:23:56] Speaker 1:** Well, yeah, as long as as long as you can share as long as you can show it's like working, which you ha you can. Um, it would be cool if we can do like a live one because it's even better. And then I get, yeah, the conversation is going to be around what we do with Meric and API and. Or the fact is not Merrick, I guess is what I mean by that.

**[00:24:12] Room 2:** Yeah, I I know what you mean. Yeah, I think I think we'll be able to

**[00:24:12] Speaker 2:** Um

**[00:24:17] Room 2:** If we can steer them and just kind of

**[00:24:18] Room 3:** Get them to calm down. Uh I I'm sure Peter Be all for it.

**[00:24:25] Speaker 1:** Sounds good, man. All right, I'll see you at Limpei.

**[00:24:26] Room 3:** Nice one. Cool.

**[00:24:28] Room 2:** cash then but like

**[00:24:33] Room 2:** Yeah.

**[00:25:52] Room 4:** Yeah. Side project is ramping up. Yeah, it's like what if we can print labels, so why don't we just rebuild dispatch files?

**[00:25:58] Speaker 1:** Yeah.

**[00:26:04] Room 4:** I'll go like um

**[00:26:10] Room 4:** For all purposes. I told you about this already. Many people can sort of look into the album and purge in all this rubbish.

