**[00:00:00] Speaker 1:** Force, you know.

**[00:00:01] Room 1:** Yeah, slightly slightly, um slightly personal.

**[00:00:05] Speaker 1:** Yeah, just a probably not safe to take a young baby out in. Yeah, um kind of fairs. So Uh good. And how's things otherwise um getting back up to speed and bits?

**[00:00:16] Room 2:** Yeah, should be. It seems to be well under control. Looks like Matt handled a bunch of it. Looks like Snap's had a fucking paddy, eh?

**[00:00:25] Speaker 1:** Uh, Snap is just shit. Uh, like I said out in my update yesterday and I asked Matt to just pull some notes together for Ryan just to make sure before I sent that update that something was sent to Ryan individually. So it wasn't just calling him out on a stakeholder update, even though it's not Ryan's fault by any means. People will just Attributes, all right. But yeah, I mean. I don't know what the fuck they're doing. Obviously, we had all those incidents last week, and then it seems that since they've done these version upgrades, which have to happen because there's changes in them for De minimis, so if they're not done by the first of November, then we can't ship to the EU, that the performance has somehow got worse, which is impressive, to say the least.

**[00:00:57] Room 2:** Yeah.

**[00:01:06] Room 2:** Yeah, like the the update they put this morning, like there's there's a very a point at which the update's gone through, looking at that graph.

**[00:01:16] Speaker 1:** Well, that's it. And then they were like, oh, we think it was the cluster migration. I was like, I'm 99% sure it is not the cluster migration. It's whatever the fuck they've just released to prop that's causing it. Mm-hmm.

**[00:01:28] Room 1:** Yeah god that's horrendous.

**[00:01:29] Speaker 1:** Anyway.

**[00:01:31] Room 1:** dude.

**[00:01:31] Speaker 1:** Yeah, I mean, it's been a shit show. I know they had a P1 yesterday with some master data fuck up as well. So, um

**[00:01:38] Room 1:** Oh shit, so it's not even latency, it's just like actual functionality of the application player.

**[00:01:42] Speaker 1:** Oh. Yeah, Snap just being shit, full stop. Like I was on the floor. In Bracknell's last week. And everyone I spoke to, like, literally was like, fuck Snap, fuck this, fuck that. Is like, fair enough. Apart from the guys on dispatch, because they don't use Snap, they do everything manual. So it was like, oh yeah, this is great. Well, they don't need to because the orders are already dispatched at that point. They just put it on the trucks. So they're just like, yeah, cool.

**[00:02:10] Room 1:** Yeah, it's sound.

**[00:02:10] Speaker 1:** Um so They're they're living life, everyone else, maybe less so.

**[00:02:15] Room 1:** Yeah.

**[00:02:17] Speaker 1:** It's yeah, not great with peak starting next week, but there we are. What can you do? Uh

**[00:02:18] Room 1:** Jesus Wats.

**[00:02:24] Speaker 1:** We'll see how quick John can vide code the WMS.

**[00:02:27] Room 2:** Yeah, well I thought Ryan's message in that um channel last week was pretty funny. It's like can you guys build a WS please?

**[00:02:35] Speaker 1:** And I was like, well, we can. Unfortunately, I don't think it'll be ready for peak, but yeah. Definitely on the radar. But yeah. But yeah, I know things have been all right, obviously. You've seen the bits and bobs, but the team-wise, Matt's been doing a fab job. Friday was very quiet. And then yesterday there were some bits and bobs, but to be honest, nothing drastic to be honest. Uh

**[00:03:01] Room 1:** That's good. Mm-hmm.

**[00:03:04] Speaker 1:** Diane gone.

**[00:03:06] Room 1:** That I like crack home.

**[00:03:08] Speaker 1:** I was just going to say the only thing to catch you up on is the you know we got the feedback around work orders and pick pack.

**[00:03:15] Room 1:** Yes.

**[00:03:16] Speaker 1:** Matt nicely drafted those all up last week and put them in the sprint at the bottom of the sprint. I asked him yesterday to reprioritize against the raw payload stuff to rank it higher. The reason for that being one, just completeness, just so we can take it off and close it out, but two, because.

**[00:03:34] Room 1:** Yeah, yeah, it's gonna be higher for a while, isn't it?

**[00:03:37] Speaker 1:** Yeah, it's been hanging because of QA delays, which we know and they've now caught up on, which is a good thing. Um but also because those use cases are needed for CT. So when CT start testing, if it starts showing back things they don't expect.

**[00:03:42] Room 1:** Hmm.

**[00:03:50] Room 1:** Fucking hell.

**[00:03:53] Speaker 1:** Now that's a few weeks away for these use cases, so it's not like an urgent thing.

**[00:03:56] Room 1:** Yeah.

**[00:03:58] Speaker 1:** I'd prefer to not have that lot of feedback twice and just address that now and then. the next cycle of feedback just be anything for CT if that makes sense.

**[00:04:05] Room 1:** Yeah.

**[00:04:08] Room 1:** No, I completely agree, like it's highest priority for the business so why wouldn't we put it on top of the sprint?

**[00:04:09] Speaker 1:** Um and to be honest.

**[00:04:14] Speaker 1:** Well, exactly. It's not directly CT because obviously it benefits many other places, but it will become a CT problem. Yeah.

**[00:04:20] Room 1:** But it it's necessary. Like it's it's necessary in order to get them across the line.

**[00:04:25] Speaker 1:** And I said, truthfully, with the raw payload stuff, we've lived without it for the best part of 12 months. I'm sure we could do another two weeks without it, you know? So, um,

**[00:04:38] Speaker 1:** Yeah, it's just the SFTP bit that's the problem. But even then we still have ways to get files if we need to. Like and it's far and few in between. So I'm like, well, I'd rather just get this finished off. Like stock sync still remains top because that's CT enabler and we want to close that out. But then just those three or four bug tickets and then get back onto the raw payload after. And

**[00:05:02] Room 2:** Mm. Uh sounds good. Sounds um oh. As expected, everything's good. That's it.

**[00:05:11] Speaker 1:** Well, in our space, yeah. Everywhere else, maybe less so. But we'll take that.

**[00:05:12] Room 2:** would have been. Yeah. Yeah, that last minute eccentric thing was, um, shocking.

**[00:05:20] Speaker 1:** Yeah, it was a bit. Um I mean the the wash up conversations for another time. I I Darren and Tom earlier. One, just to make sure: can the client go live? Which the good news is the client can and is going live. So that's good. Some context that I wasn't aware of that made it less of an issue was that in the UK they do wholesale and e-comm. So the stock adjustments is necessary because they have two stock pools which they move between. Um Whereas in Poland they're only doing e-comm at the moment. They have no wholesale component. So there's no stock adjustments happening within the warehouse because it's only when purchase orders come in. Um Now they will have a wholesale eventually, but it's not going to be probably in peak. Um so what they said is well because Shopify automatically deducts Quantities when it creates the orders, doesn't it? In Shopify itself. Like, you don't need a stock adjustment for that. Um it's only for movements that we care about. But for UK they'll have the stock adjustments on because of the wholesale component. For the Poland, one, they'll just, if there is any transfer orders from the UK to Poland, they will just contact. Accentric direct and Eccentric will just manually rectify their inventory levels because they're expecting between two transfer orders between now and the year, end of the year. So it's very minimal. So It's not like it we need it, but it's not like urgent drop everything needs to be done kind of thing. So I've said to them, that's fine, we'll capture it under the shop figure bit of parity work that we're going to be doing in November anyway.

**[00:07:02] Room 1:** Yeah. Yeah, I caught your email, I thought that was a good one.

**[00:07:04] Speaker 1:** And we'll just tackle it as well.

**[00:07:07] Speaker 1:** Well, it it's the right time for it. I'm glad it got surfaced af before the client stock started getting fucked up, which was great. And, you know, there's a different conversation to be had about that should have probably been tested a lot earlier, but so should have been the dual store thing, and they know that. Um, but yeah, it's kind of like, yeah, they're happy with that. I think they said until like December, if it's not there post-December, it'll be problematic, but up until December.

**[00:07:31] Room 1:** Mm.

**[00:07:32] Speaker 1:** And the customer's happy with it as well. They don't care.

**[00:07:36] Room 2:** That that is like the um calmest, most understanding customer. Ever.

**[00:07:43] Speaker 1:** Well, if you think about their situation, they've had Poland stock sat there for about five weeks. They're just happy they're now shipping out of Poland. So, um,

**[00:07:50] Room 1:** Yeah, god.

**[00:07:53] Speaker 1:** And so they're they're actually not that bothered because it's like 20 minutes of work for them. And if it means they can ship out of Poland, that makes a lot of problems go away, especially before there's the minimum deadlines, which is I'm guessing is what was driving a lot of the urgency. Yeah.

**[00:08:07] Room 1:** Yeah, that makes sense.

**[00:08:11] Speaker 1:** So, but yeah, otherwise, I think it's okay. Me, Ollie, and Matt did catch up yesterday. I don't know if you see. Um but I can give you the TLDR.

**[00:08:20] Room 2:** I mean like ma Matt's got more value than I have at this point for like few specific catch ups I think.

**[00:08:29] Speaker 1:** Yeah, I mean, just to recap, obviously, we spoke about Snap. The go-lives are fine. Flir, we haven't had anything for yet. It as Tom said yesterday in the channel, their website just broke apparently. So they're not expecting any orders. So still haven't seen or heard any yet. I think the big one for you was around the support conversation and where that was going.

**[00:08:52] Room 2:** Yes, I need to put something in with um Ollie Ryan and Dennis.

**[00:08:52] Speaker 1:** Uh

**[00:08:58] Speaker 1:** Cool. Um, because obviously, Matt mentioned about the out of hour stuff, and I was like, that's great. I was just wondering where we're at for the um. overall interim support model going into peak really.

**[00:09:10] Room 2:** Yeah. We we're basically good to go. We've got some runbooks together. Um So it just needs to make sure they're okay and agreeable. And also I kind of ensure that on the Ryan Dennis side of things that they can respond with as much urgency as they would expect from us.

**[00:09:30] Speaker 1:** Yeah, I'm gonna. There is an action on me to basically decide, well, get everyone to agree who has a flare gun. So I'm basically gonna turn around and say Lee, Ryan. Darren, you guys are the leaders of your team. You only call urgent if it's urgent. If anyone else tries to call it, we're going to root them to you. Essentially. Um I'd prefer that to be less than those three per se, but unfortunately I've gotta play the politics game there a little bit, but.

**[00:09:58] Room 2:** Yeah, I feel like one of those heads will play urgent when it's not urgent, but we will see. We will see how it goes.

**[00:10:02] Speaker 1:** Mm-hmm. I agree, but yeah.

**[00:10:06] Room 1:** I would like to be surprised.

**[00:10:06] Speaker 1:** Indeed. One thing I have started doing as a part of that is I've started looping in the head of CS on the ILG side to our cons for stuff like incidents, product updates, Joe Pinder, just so she has visibility because her team will over time start to play a bigger role in what.

**[00:10:19] Room 1:** Yes.

**[00:10:27] Speaker 1:** Dennis's team is doing today, a lot of the remediation is done within CS rather than necessarily within Ryan's team. Um That's not going to be in place before peak.

**[00:10:42] Room 1:** there.

**[00:10:45] Room 1:** Mm-hmm.

**[00:10:45] Speaker 1:** Um and then on the recruitment side, obviously the engineering side, you know, just on my side, um, JD's been wrote. I'm just waiting for Steph to send it to HR. And post. I think Matt has some people, obviously, as I mentioned, I've got someone I'm putting forward as well. I did say I haven't spoken to Steph about the interview process, but I'm going to recommend that Matt is in that interview process, given he's going to be working with this person on a day-to-day basis.

**[00:11:12] Room 2:** Yeah, yeah, it makes sense. I mean o Ollie gave me the option to kill it. Um he's like what do you think of Jack?'Cause if you if you don't think he's any good I'll say no.

**[00:11:21] Room 1:** So whoa! Okay.

**[00:11:22] Speaker 1:** Yeah. Well, I appreciate you saying not saying no. I appreciate that.

**[00:11:28] Room 1:** I I mean I I tried my fucking best mate but here we are.

**[00:11:31] Speaker 1:** Uh well I know what Steph's like. When he wants something he gets it, eh? So, um

**[00:11:36] Room 2:** Yeah. Yeah, th that that's good. I I think that's a that's a good shout. Um

**[00:11:45] Speaker 1:** And yeah, that w that was really it. We we we tried to request the postponement of the snap upgrades, but with the de minimus information, it's not something we can do unfortunately. So they've just got to accept the degradation in service. I think the only other thing that came up was Matt's transition and how you guys are planning to bring Matt up to the fore as Merrick. comes out, which I'll come around to in a minute and catch you up on that.

**[00:12:10] Room 1:** Mm.

**[00:12:10] Speaker 1:** Um In terms of, I think, some of the tooling you've got. So, stuff like the support bot and the PR updates and those kinds of things, it was like, it's probably good to get that distilled to map. Team, so they can use it when you taper off. Obviously, the rest of it is personal to your workflow. So that's irrelevant. It's just the shared utilities that are pretty.

**[00:12:27] Room 2:** Yeah.

**[00:12:35] Speaker 1:** if it's up, shall we say, or helpful. Um

**[00:12:39] Room 2:** Yes, agreed. I think um I mean I can tell you what my plan is for that, which is...

**[00:12:45] Speaker 1:** Yeah, go ahead. Not sure.

**[00:12:46] Room 1:** By Frost catch up tomorrow, I will H have you told everybody what's happening on your side, or is that, I suppose. bit more sensitive

**[00:12:52] Speaker 1:** No, so I was gonna hold. So basically with the Merak stuff, once it got green lit, Tom

**[00:13:03] Speaker 1:** Uh Steph asked me to you know, I've been doing this video stuff.

**[00:13:07] Room 1:** Yeah.

**[00:13:08] Speaker 1:** Uh they asked me to put together a video that's a bit of a hearts and minds for the tech team. So basically Because what we don't want to end up in the mentality is us versus them mentality where they're like, oh, they're getting to go work on Merak and doing pretty North Star things when actually they're all doing North Star, they just don't realize it.

**[00:13:27] Room 1:** Yeah.

**[00:13:27] Speaker 1:** Um So they asked me to put something together that's kind of just a bit of a video to storytell that a little bit, which I've done. I can send it to you and give it a watch. And it's just really kind of a fun little character association they can build a brand with as we go forward. But it goes through every room and the work they're doing today and how it relates to North Star. showed that to Tom and Steph on Friday. They love it. So and then I showed it to Pete later in the day. So I think Pete wants to call an all hands this week at some point. to basically go through North Star to the whole tech team. So I basically talk about North Star, how people play their part in it, what Merak is, because Merak's just an acceleration of that room. Um From that point, it will be open knowledge at this point. It's only a small snippet of people that actually know anything. So I haven't gone around telling anyone until that all hands happens, essentially. Steph said he was speaking about it today, but. Until then, I'm just maintaining the status quo until otherwise, because otherwise, people will just jump to their own conclusions on what things are and where they're going.

**[00:14:38] Room 2:** Yeah, okay.

**[00:14:41] Room 2:** In which case, that changes what I was gonna do. I think if we're gonna

**[00:14:45] Speaker 1:** I I thought the context might.

**[00:14:47] Room 2:** Yeah, no, very helpful. Um I'll wait for after that but what I'll do is um Yeah. By first catch up that follows the Miracle Hands. I'll announce things and then. The week after that, I will myself with Matt.

**[00:15:05] Speaker 1:** Makes sense. And I don't know in terms of we haven't sat down and had a conversation about like the upramp of the work on Merac and getting started on that yet. That you can catch up with Steph separately, but Amazon's have loads of issues, and GFS's side is burning a little bit at the moment.

**[00:15:23] Room 2:** Yeah, Chris I caught Chris earlier, sounds like he's not had a very good time.

**[00:15:28] Speaker 1:** Yeah, it's not been good. So they've kind of been wrapped up with dealing with that. Um

**[00:15:34] Speaker 1:** But I think, yeah, the intent is to get the ball rolling fairly soon-ish essentially. So. Yeah, fingers crossed and then we can announce obviously Did you? case it's unique to you and agreed with Ollie. In my case, I'll continue. Taking an ion fuse, obviously, wouldn't map. Stewart in. Um until we get a backfill essentially. So um

**[00:16:00] Room 1:** Yeah. Yeah. should be decent.

**[00:16:05] Speaker 1:** It should be status quo till the end of the year anyway. Now after these go lives, given Snap doesn't die on us, but

**[00:16:13] Room 2:** Yeah.

**[00:16:13] Speaker 1:** Hi.

**[00:16:14] Room 2:** I think we might um I might look at choking requests to snap a little bit more.

**[00:16:21] Speaker 1:** Yeah, potentially. I I wanna I was saying I was trying to think this through with Steph because I was like, this is going to just become a problem that's not a few specific problems. It's just an everyone problem real quick.

**[00:16:34] Room 1:** Yeah. What

**[00:16:34] Speaker 1:** Oh, it's alright. Synergy just need to sort their shit out, to be honest, is my take on it. Um

**[00:16:43] Room 2:** Yeah, yeah, I mean like

**[00:16:44] Speaker 1:** Uh

**[00:16:47] Room 2:** Not fucking hard. Like it it is not hard.

**[00:16:50] Speaker 1:** Yeah.

**[00:16:51] Room 2:** It's just a fucking crud bucket. I don't understand why this is... Like, m maybe there's some like huge nuance.

**[00:16:51] Speaker 1:** Right.

**[00:16:58] Room 2:** I don't understand, but it is just

**[00:16:59] Speaker 1:** Let's be honest, there isn't.

**[00:17:01] Room 1:** complete bullshit. You'll have to bear with because my headphones have just died.

**[00:17:03] Speaker 1:** Yeah.

**[00:17:05] Speaker 1:** Ah no worries mate, you're all good.

**[00:17:06] Room 1:** Yeah, but

**[00:17:15] Room 2:** And even that though.

**[00:17:19] Speaker 1:** Eh omega.

**[00:17:22] Speaker 1:** There he is. So it, um So so yeah, but that that's it. I think really Darren did send more C T files across. Um so I'll attach those to the Epic, but my expectation is that they'll start sending files in very shortly. Um I believe the config work has been done now. Um The eccentric issue this morning wasn't latency. I forgot to send the feature flag on in prod. But I will tell them that it was latency.

**[00:17:49] Room 1:** Yeah.

**[00:17:54] Room 1:** I mean it it it's latency of some kind.

**[00:17:57] Speaker 1:** Yeah, exactly. Latency and remembering that we have a feature flag on it. So there we are.

**[00:18:07] Speaker 1:** But Yeah, otherwise I think things things have been okay. Um Yeah, not I'm trying to think now. What else?

**[00:18:16] Room 2:** I mean I've I've got thing that's spicy if you've got nothing else.

**[00:18:16] Speaker 1:** Minute.

**[00:18:20] Speaker 1:** Oh go for it. I love spice. You know me?

**[00:18:23] Room 2:** I mean it's it it's actually um positive um and I think Merak adjacent.

**[00:18:30] Speaker 1:** Alright, go on.

**[00:18:31] Room 2:** So there is like A customer go like for a like selector in the States, I've forgotten who, but I know the tech services team have had fuck all notice for it.

**[00:18:42] Speaker 1:** How is this flower?

**[00:18:42] Room 2:** Uh No, it's not Flair, it's somebody else. I I think it's like some acronym starts with T.

**[00:18:46] Speaker 1:** Yeah.

**[00:18:49] Room 2:** Um

**[00:18:50] Speaker 1:** I put it.

**[00:18:52] Room 2:** But anyway, they've like effectively...

**[00:18:56] Room 2:** That then I'll have done the thing I've said like, yeah of course we can do this, give us some money. Um and we can't do this.

**[00:19:04] Speaker 1:** classic. Oh.

**[00:19:06] Room 2:** Um, but what it is. is and I'm sorry Ollie or nobody else has come with you, um this is what I ended up spending the whole morning in the office talking about. Um is actually using Fuse as the data pipeline to get stuff into Selector.

**[00:19:18] Speaker 1:** But

**[00:19:25] Speaker 1:** Right, right.

**[00:19:27] Room 2:** So

**[00:19:29] Room 2:** Effectively, instead of having snap as a backend, you'd have a selector backend. with a selector that uh um

**[00:19:38] Room 2:** Normal SF TP integration, dropper, sales order in. and then it just flows through each select for instead of the snap.

**[00:19:48] Speaker 1:** Makes sense.

**[00:19:49] Room 2:** would would theoretically work.

**[00:19:53] Room 2:** Um but obviously like keen for your input on that'cause I mean Stop my products at the end of the day.

**[00:20:01] Speaker 1:** No, no, no, no, but I mean, if it's related to merit, then it's all of ours. Um

**[00:20:02] Room 2:** Uh

**[00:20:07] Speaker 1:** Well, you always knew Fuse was going to be the engine powering behind that, or at least Fuse. As in the services rather than the product itself.

**[00:20:15] Room 2:** Yeah.

**[00:20:16] Speaker 1:** So I think it makes sense. I think we'll just need to look at the experience of it and how we surface that in the UI, because obviously the requirements would change. As a part of that. In terms of the mechanical flow, yeah, I think it absolutely makes sense with what Fuse is doing, the deduplication, the mappings if needs be. All that stuff, like absolutely. It's just how do you segment it away from. Fulfilment versus delivery, I guess it's the next iteration, which could mean an answer we saw as part of Merak rather than a necessarily a fuse problem to solve.

**[00:20:45] Room 2:** Yeah.

**[00:20:52] Room 2:** Yeah, it's it's a tricky one to sort of type. I I think we've got a couple of weeks at least. Um it's

**[00:20:57] Speaker 1:** Okay.

**[00:20:59] Room 2:** really bugged me. I'll I'll open up her threads um with you and Ollie in our group chat.

**[00:21:02] Speaker 1:** Yeah, yeah, it's cool. I mean, I know everyone's in the office today and uh if If it was a thing yesterday, I spoke to Steph at like four o'clock, so I assume he would have mentioned it if it was a known entity then, so I'm assuming it's surfaced this morning and has come full circle.

**[00:21:19] Room 2:** when they are looking at things. So it's

**[00:21:19] Speaker 1:** Oh, okay. Well, I'm not reading that shit after work. So

**[00:21:22] Room 2:** Yeah no don't fucking blame you but

**[00:21:24] Speaker 1:** So don't worry if I've been out the loop. It's just, you know, we haven't built anything. So it's not an issue.

**[00:21:30] Room 2:** Yeah, and I mean what what we can do at least config side of things is just hide some stuff and not surface anything in the UI. For the time being.

**[00:21:40] Speaker 1:** Potentially, that's a we just use the mechanics of fuse and just keep it. I don't want to pollute what the ILG guys are doing. And maybe it's something we only surface to the admins, potentially. There's ways around it.

**[00:21:51] Room 2:** Yeah.

**[00:21:51] Speaker 1:** Um if we need to do something quick in terms of getting the mechanics in for selector, that's fine. We can go back and reimagine the UI experience after, but Flow of it. I mean, the capability is there. You guys have built it. As long as we're confident that would work. I see no reason why not. Um it's only gonna benefit as on the delivery front. So

**[00:22:09] Room 2:** Yeah.

**[00:22:12] Room 2:** I mean I I'm gonna go do do a bunch of build and like run some synthetics. Um on my side, first pass will be without the UI'cause like you say I think. with the likes of people using feuds, um putting selector in there when it's already a known entity is going to be confusing as fuck.

**[00:22:34] Speaker 1:** Yeah, Danny will start trying to configure selector as a back end and it'll be like, no, no, no, no, you don't need to do that.

**[00:22:41] Room 1:** Yeah, James has started raising bugs for no reason.

**[00:22:41] Speaker 1:** Um

**[00:22:45] Speaker 1:** Oh well yeah. Mm-hmm.

**[00:22:47] Room 1:** Yeah, that's fantastic.

**[00:22:50] Speaker 1:** No, it's good to know. I think it makes sense, absolutely. And if it's a critical priority to the business, then yeah, have it prioritise as needs be.

**[00:23:04] Speaker 1:** I see. Now we're onto the beachhead. Okay. Good to know.

**[00:23:07] Room 2:** Yeah, so

**[00:23:09] Speaker 1:** Um

**[00:23:12] Speaker 1:** But yeah, I think it makes sense. I think the only other thing from me, it's not related to that necessarily, but one thing I did want to catch you on was around the load testing in relation to the snap. Um

**[00:23:22] Room 1:** Yes, I've not done that yet. Um

**[00:23:25] Speaker 1:** That's no worries, I've left it open ended. I just think it would be good if at least over the next week or so we can get some numbers back to snap on that test instance. We know it's going to be shit anyway, let's be honest, but

**[00:23:26] Room 1:** Because

**[00:23:34] Room 2:** Yeah.

**[00:23:37] Speaker 1:** Um

**[00:23:38] Room 2:** Every time I think it's a good time to do it, they're like, ah, more maintenance!

**[00:23:44] Speaker 1:** Yeah.

**[00:23:44] Room 1:** It's like

**[00:23:45] Speaker 1:** Yeah. Well

**[00:23:45] Room 1:** Wh when do you test such that it becomes representative?

**[00:23:50] Speaker 1:** Yeah, true. Well, I think for the non-production DBs, I think none of those are going under maintenance this week. It's only production DBs that are having upgrades this week.

**[00:24:04] Room 2:** Yeah.

**[00:24:08] Speaker 1:** The only the only reason of a benefit

**[00:24:08] Room 1:** I I'll take that away as a thing to do.

**[00:24:11] Speaker 1:** Yeah, the only to add more context, a bit of urgency and the reason behind it is with the issues we're seeing with Snap holistically. I've got like Tom Ashley, Simon Clifford and that asking what the results were. So

**[00:24:24] Room 2:** Well, you just tell them it's fucking shit and like we'll we'll follow up the data.

**[00:24:24] Speaker 1:** Um

**[00:24:27] Speaker 1:** Yeah. I they know it's shit. They just want to know the numbers basically. Um so. Yeah, I knew you'd been off, so I was like, I'll just catch you and come back on that one. I'm assuming it hasn't been done given how last week was with all the incidents, which is fine. But it's just probably one we need to just. tick off quickly, get a clanker to go do it in the background, you know what I mean? The usual.

**[00:24:50] Room 2:** Yeah. Well, I mean we can orchestrate it through our um little fused web portal. Mm-hmm.

**[00:24:55] Speaker 1:** Yeah, however you want to do it. Obviously, it's testing against Snap's infrastructure. As long as we're doing that as part of the load test, then it doesn't really matter how you do it.

**[00:25:02] Room 2:** Oh yeah yeah. Yeah, I'll um I'll take that away as it to do. What I can do is get some if if you've got Tom in your case, I'll go get some preliminary. Um results in.

**[00:25:12] Speaker 1:** Yeah, Tom Tom's less on my kids this week'cause he's in a different time zone, but I know he'll it'll be top of his list when he returns from Tokyo, so

**[00:25:24] Speaker 1:** Yeah, he should be back next week. He flew out on Friday. I think he comes back later this week.

**[00:25:25] Room 1:** Mm.

**[00:25:31] Room 2:** Sounds good. Okay. Um

**[00:25:34] Room 2:** Cool that that's all I wanted to cover from my side. I'm gonna build the selector adapter. just so I can prove out that flow. I'll get

**[00:25:43] Speaker 1:** Hmm.

**[00:25:47] Room 2:** I'll start start the thread with you and Ollie so Ollie can share some more info and we can think about how the different backend manifests. Well I think you're right for the time being if it's just time to like the fucking admin user flow.

**[00:26:04] Room 2:** then that's all good.

**[00:26:04] Speaker 1:** Yeah, who just out of curiosity who was in that conversation this morning.

**[00:26:09] Room 1:** 'Cause Wilder's Denton and me.

**[00:26:13] Speaker 1:** Okay, it may be one that we just Throw in the Merak channel instead, then, because then, like, Tom and Steph have got visibility as well. Because if it's going to affect selector long term, obviously, that goes into. Steph's world a bit at the moment until that bat feels there. So

**[00:26:28] Room 2:** Yeah.

**[00:26:31] Room 2:** I mean it it's not it's not a change to selector on the bright side, it's just how we get data to selector.

**[00:26:37] Speaker 1:** Oh yeah, yeah, not a change director selector, but if you started for whatever reason dying, then selector dies, right? So it's knowing the dependency there and all that. If it's the beachhead, it's directly North Star related, which is Obviously, product strategy for North Star and stuff. In terms of the technical how, it's fine, like whatever you guys call the shots, but it's just that awareness piece, I think, because otherwise they won't. I hear just be like what the fuck is this i just know how it goes

**[00:27:07] Room 2:** No, good call. Yeah, that that's a good call to get in there.

**[00:27:08] Speaker 1:** Mm-hmm.

**[00:27:12] Speaker 1:** We're all in that channel anyway. So it saves that in another channel. And it is Merak related to an extent, as you said.

**[00:27:18] Room 2:** Yeah, I mean very tangentially related, so even though we're gonna be um

**[00:27:24] Room 1:** reading this letter from scratch, hopefully.

**[00:27:28] Speaker 1:** Well exactly, but you just the concept at least, right? Is it something you may want to replicate or may may not, but Yeah.

**[00:27:37] Room 1:** Two.

**[00:27:39] Speaker 1:** Um But yeah, let me just check my notes and make sure. It's not for now. Um Another one that got mentioned last week and I just captured on the backlog for later work was around sending bill of materials through the API.

**[00:27:59] Room 1:** Okay.

**[00:27:59] Speaker 1:** So that's sending in a skew, but then it's also its component tree. As well. So you have a kit and then it's components. At the moment, you can only send in a kit individually. or a stock item individually and then you need to link them up within Snap.

**[00:28:15] Room 2:** Right.

**[00:28:16] Speaker 1:** Um

**[00:28:16] Room 2:** Is uh what what entity type is that?

**[00:28:20] Speaker 1:** Uh master data.

**[00:28:22] Room 2:** Right, okay.

**[00:28:23] Speaker 1:** So, it's a master data link record. Jitabik did it. I've gone through the extracts, and basically, what they did is they had like a component section which you'd send in and add the component linked and the type out to be master skew essentially.

**[00:28:38] Room 2:** Right.

**[00:28:38] Speaker 1:** but it's it's not an urgent need, but

**[00:28:39] Room 2:** And there's a

**[00:28:42] Room 2:** That's an alternative to a work order then, right?

**[00:28:47] Speaker 1:** Alternatives.

**[00:28:50] Room 2:** As in like you you you could either create a work uh a kit through work order or

**[00:28:50] Speaker 1:** What do you mean, sir?

**[00:28:57] Room 1:** Master Days uh

**[00:28:59] Speaker 1:** Yes, yeah. So the work orders flow is completely different because that is kits after they've come into ILG. So that is creating net new kits. This is kits prior. So when they come in.

**[00:29:06] Room 2:** Right.

**[00:29:11] Room 2:** Yeah, so you you ship a kit preassembled.

**[00:29:11] Speaker 1:** Take lab eight.

**[00:29:14] Room 2:** or like like

**[00:29:15] Speaker 1:** Yes, exactly. That's it.

**[00:29:16] Room 2:** Hit arise pre-assembled at an IoD warehouse.

**[00:29:20] Speaker 1:** That's it, you've got it. So, like a great example is lemonade dolls. Lemonade dolls do all kits. So, when they send their master data in, it's all kits. It's no individual stock items, but obviously. They will have individual stock items there because you need the individual batch tracing on each of those items. and their D G requirements and all the blah blah blah blah. So I've just drafted it on the backlog. We can tackle it with parity work when we get around to it. It's not urgent.

**[00:29:52] Room 1:** That sounds good. Sounds very good.

**[00:29:56] Speaker 1:** Um I think that's pretty much it, to be honest. And just going through Testy's alright, he's just his mute, his usual self.

**[00:30:06] Room 2:** Yeah, yeah, no shock there. I've worked. Bearing the brunt.

**[00:30:11] Speaker 1:** Pretty much.

**[00:30:13] Room 2:** I I feel like

**[00:30:17] Room 1:** Okay.

**[00:30:20] Room 2:** Lightly related, I feel like we need to start Cutting um head of applications and then directly calling layout on our other documentation.

**[00:30:30] Speaker 1:** Mm-hmm. Well, Snap totally loves enough to do that. Not shall I say synergy but

**[00:30:37] Room 2:** Yeah.

**[00:30:38] Speaker 1:** But I I don't see them putting Ryan's name on there coincidentally.

**[00:30:41] Room 2:** Yeah. That that is

**[00:30:43] Speaker 1:** Never guess why.

**[00:30:44] Room 2:** Hmm.

**[00:30:47] Speaker 1:** Yeah um

**[00:30:48] Room 2:** So, yeah, it's interesting to see that they've used, um

**[00:30:49] Speaker 1:** Our brains

**[00:30:52] Room 2:** confluence of their release notes.

**[00:30:55] Speaker 1:** Yeah, I was surprised there with that tech advance. I was expecting a Nightpad Plus Plus document, but here we are. Uh

**[00:31:04] Speaker 1:** To be fair, I think that's IOG's confluence but there we are.

**[00:31:07] Room 2:** Mm-hmm.

**[00:31:09] Speaker 1:** Yeah. But yeah, apart from that, I think we're good, to be honest. Um neither

**[00:31:16] Room 2:** takes

**[00:31:16] Speaker 1:** has done some UI changes I just asked her to look at. Something on the replay service in terms of how the data is presented because it was presented as one massive block with every field. And I was like, that is going to be a bitch to navigate. Um But apart from that, it looks fab. Sprint work seems fine. Matt said the only thing I said to Matt was when I asked Tom to go have a conversation with him is. Get stock API and stock sync, and how we want to test that. I know Alex has been doing bits of it as we go, but. It'd be good to get. Now they've cleared that Q and his team. Start looking at that when we're happy with it, but I've said to let you guys make the call on when that's the case.

**[00:31:59] Room 2:** Yeah, okay.

**[00:31:59] Speaker 1:** Uh

**[00:32:00] Room 2:** I I think what what we need to do is get Alex better integrated with the ILG QA team. because there's like some there's there's overlap. Al Alex is like a skill and actually and actually Alex is also a skilled QA engineer, so his side offs should have bearing, so he should have access to their stuff and to their stuff and

**[00:32:06] Speaker 1:** Devin?

**[00:32:10] Speaker 1:** Hmm.

**[00:32:22] Room 2:** work as part of that team.

**[00:32:23] Speaker 1:** I agree. Um the the only thing.

**[00:32:25] Room 2:** Xertend.

**[00:32:27] Speaker 1:** Go me. No, no, go on mate, sorry.

**[00:32:29] Room 2:** Yeah, I I don't wanna have like this duplicated effort of like Alex signs off a thing and then oh actually it has to go through ILG QA because like that's No good for Alex, um and it's also just like fucking wasted effort in the business.

**[00:32:43] Speaker 1:** Yeah, exactly. I think the only thing that's probably worth the with Ollie on it came up Alex came up yesterday because technically He's on secondment from carriers, and with what's going on over there, and with Chris potentially moving more towards Merak, he may be needed more back in that carriers space. Um

**[00:33:02] Room 2:** Yeah.

**[00:33:03] Speaker 1:** So worth a conversation. I don't know what it, you know, at the end of the day, is an engineering resource to an extent. So, um,

**[00:33:11] Room 2:** Yeah, we we need to um

**[00:33:15] Room 2:** As long as he's not treated as an afterthought. That's Michael.

**[00:33:22] Room 2:** It it so often is the case with QA.

**[00:33:22] Speaker 1:** I am.

**[00:33:26] Room 2:** like mor morale can take a hit, especially like if we're duplicating stuff with the LGQA side of things.

**[00:33:26] Speaker 1:** Okay.

**[00:33:33] Speaker 1:** Yeah, I think um Tom and Alex have been speaking direct, so it's not like there's no chain of communication there, like they've been talking. But my understanding is Alex has been like unit testing or QA testing the individual tickets. So like for example, does Stocksync show on a UI run? But no one has done an official kind of end to end yet in terms of just running a stock sync or just pulling a get stock scenario.

**[00:33:56] Room 2:** Mm.

**[00:34:01] Speaker 1:** Um I mean if those have been done that's great but it'd be good to get those done and make sure that they meet the requirements and then we can put a pin in it really.

**[00:34:10] Room 2:** Yes.

**[00:34:13] Room 2:** Sounds good then. Cool.

**[00:34:16] Speaker 1:** But yeah, far from that, all peachy, just another day in the life, so.

**[00:34:20] Room 2:** What we'd like to hear.

**[00:34:23] Speaker 1:** But we'll see how this week unfolds. God knows what's going on. So.

**[00:34:29] Room 2:** Ah, nice one. Um Okay. I'm gonna go.

**[00:34:36] Room 2:** Uh Get some comms out. Yeah. Yeah.

**[00:34:38] Speaker 1:** Have a coffee.

**[00:34:42] Room 2:** Get some comms out, go for a piss. Um build a select redapter and pocket and do some um

**[00:34:51] Room 2:** Uh what's the word, Harry? Performance testing.

**[00:34:55] Speaker 1:** Makes sense.

**[00:34:55] Room 2:** both load and burst.

**[00:34:56] Speaker 1:** Um Appreciate it. Um and yeah, if you need anything from me, just let me know. Um

**[00:35:02] Room 2:** Yeah, we'll do likewise bud.

**[00:35:02] Speaker 1:** Mm. should have everything. I don't expect anything to change.

**[00:35:07] Room 2:** No, I think um just

**[00:35:07] Speaker 1:** Um we like Yeah.

**[00:35:10] Room 2:** With with um keeping expectations set as we have half the team out on sick.

**[00:35:16] Speaker 1:** Well now I know that, yeah. I definitely can. So. That's not a problem. I didn't realize because they were the max seemed okay yesterday. He seemed all right. So.

**[00:35:27] Room 2:** Yeah. He um is a fire.

**[00:35:33] Speaker 1:** I need to get on this sick business. Oh, um, just to catch you up, I'm taking two days out next week. Um Well 'Cause I had a family member pass away last week, so I got a funeral on the Thursday.

**[00:35:43] Room 1:** Second, I think. Ah sorry to hear that mate.

**[00:35:48] Speaker 1:** That's all right. They lived a long and happy life. It was a peaceful passing away. So it's just, yeah, Thursday's bereavement leave. And then Friday, I was like, well, there's no point in coming back in for a day. So I'm just taking it off. So.

**[00:35:58] Room 2:** Yeah, fair enough. Ah, cool.

**[00:36:02] Speaker 1:** Uh-huh. But yeah, just to give you a heads up, because that was decided at 8 p.m. last night. So. And But yeah.

**[00:36:14] Speaker 1:** Likewise mate, I sent you that video as well, so give it a watch and let me know what you think. It's really just a little bit. I call it John Lewis esque storytelling just to get people and that's why you'll see loads of people popping up with clay characters in their profile pictures.

**[00:36:30] Room 1:** Yeah, I'm trying to catch who's doing what, so that's quite cool.

**[00:36:33] Speaker 1:** It's all Steph. I didn't even agree to it. Now I've just got people pinging me. Can you make me a clay character? I'm like, guys, you haven't even seen the fucking video yet.

**[00:36:39] Room 1:** Mm-hmm.

**[00:36:42] Speaker 1:** Um Bye. But it it's nice that people are making the association of that brand and getting personable with it because it gives people a feeling to North Star, which is what we were trying to aim for. So that's good.

**[00:36:57] Room 1:** Lovely.

**[00:36:59] Speaker 1:** Sorry.

**[00:37:00] Room 1:** True.

**[00:37:00] Speaker 1:** All right, well, if nothing else, I'll let you crack on, but know where you are if you need me, but um I am looking gonna look at this week about that SFTP file explorer bit and bobs. I'm just playing.

**[00:37:12] Room 2:** Yeah, yeah, as long as we find as value in that.

**[00:37:16] Speaker 1:** That's what I'm playing around with. I'm struggling at the moment to find it as its separate entity. I think baked into a connector. level it might be, but I don't know, I need to play around with it a little bit more. Um

**[00:37:27] Room 2:** Yeah. Connector level feels feels right.

**[00:37:32] Speaker 1:** It feels right, but then also at the same time, I'm like, I easily just want to go to a location that I can see agnostic across a customer. But then it's like surfacing every file would be a pain. It needs to go through the houses a little bit. Well, and I've got some prototypes to share, I'll share them and get your thoughts and whatnot. But. Yeah, I'm starting to look at that this week when I get time. So

**[00:37:55] Room 2:** Sounds good.

**[00:37:59] Speaker 1:** Touch in a bit?

**[00:37:59] Room 2:** out if you need me. And uh yeah, take care.

**[00:38:00] Speaker 1:** Likewise, but Have a good one, bud. Catch you in a bit. Well

