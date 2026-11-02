**[00:00:00] Speaker 1:** Core replacement. we could use things like that in terms of my area. Um But then a bunch of stuff from that was about how we're structuring.

**[00:00:11] Speaker 1:** From the get-go, in terms of the US policy that will affect the core data consumption. requirements later on, basically.

**[00:00:19] Harry:** Yeah. Yeah, which makes sense. Right. It makes sense to host everything in the States.

**[00:00:22] Speaker 1:** Um like let me let me fucking ping this basically

**[00:00:27] Speaker 1:** I That this is the fucking clawed version of it. And from in response to what he's saying, but it's more

**[00:00:37] Speaker 1:** It was more about the US heightened requirements rather than like we need to do it this way, if that makes sense.

**[00:00:44] Harry:** Yeah. Mate, your agent's gone off on a fucking mad one.

**[00:00:48] Speaker 1:** It has you.

**[00:00:49] Harry:** Um

**[00:00:49] Speaker 1:** But this is because it's referencing everything. From the pre-discovery that someone's done. I found a bunch of files about the US, so I'm just checking that we don't need to do any of it, is what I'm getting at.

**[00:00:59] Harry:** Okay. Yeah,'cause it the sequel thing like fucking blew my mind this morning. It was like

**[00:01:07] Harry:** We don't even know what we're building, so why are we picking a database?

**[00:01:13] Speaker 1:** Yeah, we don't know what we're building, but I'm working off of the data that we know we have to bring in for shipping from the carriers. Mm-hmm. It's working for that concept, right?

**[00:01:21] Harry:** still like

**[00:01:26] Speaker 1:** Like it's not a complete unknown in terms of what I what my Git needs to handle, is what I mean.

**[00:01:31] Harry:** Yeah, so my my challenge to you would be YSQL?

**[00:01:36] Harry:** if you if you can articulate that at this point, that makes sense.

**[00:01:41] Speaker 1:** Uh

**[00:01:41] Harry:** And if if you can state why it's better than like Firestore, Redis, memory store.

**[00:01:46] Speaker 1:** No, there is no better. Yeah, there is no.

**[00:01:47] Harry:** Um GCS or Mongo.

**[00:01:49] Speaker 1:** Yeah, this is no

**[00:01:50] Harry:** then we shouldn't be jumping the gun.

**[00:01:57] Speaker 1:** Um yeah, okay, fair enough.

**[00:01:59] Harry:** Because yeah, like w we shouldn't be picking this in for until we've got a design on the page. We can't have a design on the page until we get a briefing in a couple of weeks from product.

**[00:02:10] Speaker 1:** My concern with the product briefing.

**[00:02:13] Harry:** I for context, I caught up with staff yesterday. There's a lot that they're doing. in the background. Um they they've been quiet about it, but like

**[00:02:26] Harry:** Yeah, when we when we have that catch up, um we're going to be very busy people.

**[00:02:34] Speaker 1:** Okay, so you think it's just a case of like

**[00:02:38] Speaker 1:** Hold breath until

**[00:02:40] Harry:** Yeah, yeah, I think like Don't get me wrong, your intentions are fad. Um do not want to pee poo that.

**[00:02:50] Harry:** Um

**[00:02:53] Harry:** We shouldn't be diving into Infra before we've got a design on the page, and we shouldn't get a design on the page until we know what we're designing.

**[00:03:02] Speaker 1:** Yeah, I know what you're saying, but my pushback is my area is known already. Like, I know the data I have to consume for this, and I know the data. I look, yeah, I 100% agree. I, this is too, this is literally just a massive deep dive plan so that I could start from something basically. Um,

**[00:03:19] Harry:** Agreed, yes, that there will be data from your area, that's why you've been brought in. But do you know what data and how it's going to be used in which capacity?

**[00:03:30] Speaker 1:** In terms of shipping. Requirements.

**[00:03:33] Harry:** Um Well I guess it's like...

**[00:03:38] Harry:** I I think we're getting ahead of it far too soon. if I'm completely honest.

**[00:03:46] Harry:** Like, I'm with you. I wanna get on it and get started ASAP. Um But we we

**[00:03:54] Speaker 1:** This is not. I don't want you to think this is like any official, like, we have to do it this way. This is literally, I'm just like. sent out Claude to be like, has anyone ever referenced expanding into the US, what did they find? What are the requirements?

**[00:04:08] Harry:** Yeah.

**[00:04:08] Speaker 1:** Use the context of what we have. This is just a Perusal over everything we have. And it brought up some stuff about how we're setting up the regions for the GCP, which I wanted to get ahead of now.

**[00:04:17] Harry:** Yeah. So So the reasons make sense, right? If if if we have to make a conscious decision at the point at which we create the project. and that becomes immutable. Then yes completely agreed. Um we we should feed that into the request.

**[00:04:31] Speaker 1:** That was the only thing that I think actually was actionable from it. This is just discussion shit in the background, basically.

**[00:04:37] Harry:** Okay.

**[00:04:38] Speaker 1:** Yeah, it's not. I'm not going to be like, this is what we're doing. Yeah, not by any stretch of the imagination. Yeah, for sure.

**[00:04:45] Harry:** I do on a database thing,'cause like Darren's getting autistic as fuck about this stuff and I'm I'm already getting fucked off about it. Like that the man has only ever written the front end, why sh why is he an expert in databases?

**[00:04:53] Speaker 1:** Yeah.

**[00:04:59] Speaker 1:** Yeah, I sure.

**[00:05:00] Harry:** Postgres is or like some kind of squirrel is very good if you're dealing with highly relational stuff and you need correctness. Like emphasis will need correctness, right? Um

**[00:05:11] Harry:** You know. Mongo is an option. and I will advocate for Mongo when you're doing very transaction heavy stuff. Um I I have worked on like billion transaction a day SQL systems and the thing that fucked us up was the database. Um, like we couldn't get past 600 transactions a second because the database became the choke point. If you pick something, um more suited to highly transactional rights. like Mongo. Mongo's the only example I've got in my head, but there's other stuff like um Alloy DB in that.

**[00:05:44] Speaker 1:** Yeah, yeah, like so. Well you you you preach what you know, don't you? So it's, you know.

**[00:05:46] Harry:** Um Yeah.

**[00:05:50] Speaker 1:** Okay, so you think we should go down the Mongo route? I mean, this should just be a rectangle chit-chat, you know. I'm not holding you to anything.

**[00:05:57] Harry:** Yeah. No, no, no. Um Uh I'm not I'm not opposed to like going sequel if it makes sense. Um it SQL makes a lot of sense when you need like Highly accurate, highly correct data in front of somebody ASAP. Not ASAP, sorry, but. Yeah, that that's completely r the wrong word.

**[00:06:21] Speaker 1:** I know what you mean.

**[00:06:22] Harry:** Relational databases make sense when you need to present all of the data at once.

**[00:06:30] Harry:** Um that that's what they excel at and they excel at correctness.

**[00:06:34] Speaker 1:** Yeah, that that's

**[00:06:34] Harry:** If you're hacking.

**[00:06:35] Speaker 1:** Essentially the route I'm going down with this is like

**[00:06:39] Speaker 1:** I've seen the problems we've had with the Mongo structure we've had now, and that might be because of the way it's implemented now and not the actual fact. And that's maybe why I'm like airing away from it because of my, like, I could only go for what I know here from how it's how it's worked, and it's gone. not great um

**[00:06:58] Harry:** Let me So The flip side of that is everything in the fuse Not everything. Almost everything in Fuse. And I'm gonna... share a screen and try and inspire a bit of confidence. Um sits on Mongo. Right. So this page powered by a MongoDB. This order tracker Here's palad uh fucking code starting, but this order tracker is palette by Another Mongo. Um This is cool, these are nilos changes, that's looking good. Um if you go on to like Uh

**[00:07:44] Harry:** This page. This is a mongover in its own right. Ignore services they're called starting because it's dev. We just click through it all.

**[00:07:51] Speaker 1:** Yeah, yeah, no, that's what I mean.

**[00:07:54] Harry:** So each and every of these has their own Mongo instance, and they're all highly correct. So The the issue that you've been seeing Um especially in the ECM world and like mate I will shit on E ECM to John Clark's face.

**[00:08:07] Speaker 1:** Okay, so it's more it's more config than rook Okay.

**[00:08:11] Speaker 1:** Yeah, I mean that's that shifts my I I'm only going off of what I know. Um

**[00:08:17] Harry:** Yeah, yeah. I mean like I've I've been in the trenches for Uh Longer than I'd like to admit.

**[00:08:26] Speaker 1:** I mean, it's literally why I've come to you about it to discuss it. Like, I am bringing this up with just you to be able to have a bit of a conversation.

**[00:08:28] Harry:** Yeah.

**[00:08:31] Harry:** There is

**[00:08:35] Harry:** Yeah. If you if you really want to go into things, this is your boy.

**[00:08:41] Speaker 1:** Oh yeah, yeah, yeah, I I actually have that now. You um showed me it, yeah.

**[00:08:43] Harry:** Yeah, it is uh there's a good couple of chapters like it's fucking dry, don't read it cover to cover, but like.

**[00:08:49] Speaker 1:** It is it is a a a slow burner.

**[00:08:49] Harry:** Find

**[00:08:53] Harry:** Yeah, man, I wanted to fucking flow my eyes out. Um if you look at the chapters on I think Storage and retrieval, so chapters 3 and 5. Um it will play your fucking socks off. Oh sorry, chats of two as well.

**[00:09:09] Harry:** Characters two, three, and five. They're your boys. Um Mo Munga can be really safe, like

**[00:09:17] Harry:** You know, it's a company in its own right and people opt to it with like huge amounts of success. It's just how it's implemented. Um good'cause you could put shit into a SQL database. So I'm just trying to find um Here you go. I'm going to send you a couple of things to

**[00:09:38] Speaker 1:** is lost.

**[00:09:39] Harry:** Honder.

**[00:09:40] Speaker 1:** Okay.

**[00:09:41] Harry:** Uh And I'm like this is an

**[00:09:45] Harry:** Uh me saying we should use one over the other. Like my viewpoint is always right tool for the job.

**[00:09:54] Harry:** which is why in Fuse we've got like three different database types.

**[00:09:55] Speaker 1:** Yeah. Yeah. Yeah.

**[00:09:57] Harry:** and we've got three different housing models.

**[00:10:00] Speaker 1:** Mm-hmm.

**[00:10:03] Speaker 1:** Um Yeah, it was o I I mean this was just a byproduct of what I was um looking at. around the security things'cause I know um

**[00:10:14] Speaker 1:** Basically the reason I brought up the whole US based data is Uh my wife's company had the exactly the same problem.

**[00:10:21] Harry:** Yeah.

**[00:10:21] Speaker 1:** where they didn't they didn't preset in US and it was like a complete ball ache because Some of the requirements in some of the states are very heavily leaning towards it. Has to be US based data. Um Yeah.

**[00:10:34] Harry:** That's a really fucking good shell as well. like completely agree with you on that.

**[00:10:37] Speaker 1:** Um

**[00:10:39] Speaker 1:** So, but um yeah, sorry, that this was all just like a bio. I've essentially just got it to do like a real, real rough look at everything where we are today type thing.

**[00:10:46] Harry:** No, it's it's good. It's good because it stimulated a good conversation.

**[00:10:54] Speaker 1:** But yeah, I'll have a read. I mean, the Christmas stuff I've looked at.

**[00:10:58] Harry:** Yeah, cause like

**[00:10:58] Speaker 1:** When we we were looking before. Um about moving over.

**[00:11:01] Harry:** I mean less Less applicable depending on what language we choose for the back end. because there's a TypeScript thing. Same for Type on, but I'm assuming that you're more um familiar with like TypeScript instead of Go so I think they're still good examples of

**[00:11:19] Speaker 1:** I've actually personally written More in Go before. Yeah, it's what I did at uni a lot.

**[00:11:21] Harry:** I do, okay.

**[00:11:25] Speaker 1:** But the the TypeScript stuff we've just been doing. Hear a lot of

**[00:11:29] Harry:** Yeah.

**[00:11:32] Speaker 1:** building the apps and stuff. Um they Yeah, I'm I'm happy to go either way. I think it like I think goes s uh a great

**[00:11:40] Speaker 1:** path to go down for this.

**[00:11:42] Harry:** Yeah.

**[00:11:43] Speaker 1:** Um I'm kind of agreement in agreement with that. um like off the bat and you're not going to get any pushback from me.

**[00:11:47] Harry:** Hmm.

**[00:11:49] Speaker 1:** Um

**[00:11:52] Speaker 1:** I yeah, I am just uh bit bullion ideas about the structure of the actual back into the printing process. Um yeah and trying to avoid the hurdles we hit so at the moment.

**[00:12:06] Harry:** If if you want,'cause I think it'd be good practice regardless, like. It would be really good to or at least really instructive to go through a um I'm not used to going to bed late.

**[00:12:17] Speaker 1:** No, no, no, it's my mouth but I'm just watching that.

**[00:12:20] Harry:** Um

**[00:12:20] Speaker 1:** Oh yeah.

**[00:12:21] Harry:** It it'd be really good to like do a little system design session. Um

**[00:12:28] Speaker 1:** Yeah, that's essentially what I did yesterday because I didn't want to go into our first one empty-handed, if that makes sense. I wanted some sort of like, these are the pitfalls we currently have, this is how we can. completely avoid slash this is required, so let's we need a solution sort of thing and Things like that. Um That was all this is, mate. Just a quick Per reason.

**[00:12:53] Speaker 1:** I'm certainly not I'm not committing any decision to this point yet.

**[00:12:55] Harry:** Oh no. No, I think um

**[00:13:01] Harry:** be quite instructive. Have you got time later today?

**[00:13:06] Speaker 1:** Uh yeah, I can fit it in.

**[00:13:09] Harry:** So I'm just thinking like if if you've got a component that you think needs building, Um what we can do between the two of us. Um and I promise to not speak at 600 words per minute and tell you you're wrong in everything that you're an expert in.

**[00:13:26] Speaker 1:** The no, I

**[00:13:28] Harry:** I'll just

**[00:13:29] Speaker 1:** I have I have zero issue. If you think, no, this is stupid and this is XY reason. Like, I would rather you not be around the bush and just fucking say because you're coming from a different experience background than me. Um I I'll be honest, I think my a ri my end point of this is going to be more about the processing from end to end. Yes, the core database and stuff is like the area I currently work in and I'm concerned about. Um But realistically. you've got a better buildup of the fuse stuff. is like the successful back end that we should try and emulate. How that's worked because you don't have the same issues we do on that. And yes, there's like different requirements, but. I definitely think we should go down. Like, speak freely, is what I'm getting at. Like, I'm not going to take offense. You literally won't be able to offend me. So.

**[00:14:22] Harry:** Yeah yeah.

**[00:14:25] Harry:** Wow, wow.

**[00:14:27] Speaker 1:** I promise you.

**[00:14:29] Harry:** Hold my fucking bit.

**[00:14:30] Speaker 1:** It doesn't bother me in this slide.

**[00:14:31] Harry:** Um

**[00:14:34] Harry:** Well I think it might be good actually is just like... take you through some of us and turn ons if you got a mo.

**[00:14:41] Speaker 1:** I have to hop off at half past I've got a call with D P D'cause they've broken all of us contracts. Um Yeah, so if I've got to go do that. They just deleted it because they said it was a number that was too high range. Yeah. got rid of it.

**[00:14:56] Speaker 1:** That was our house account across every login for GFS Hypercom. So that's fun.

**[00:15:01] Harry:** Fantastic. Um but yeah, we should we should chat.

**[00:15:04] Speaker 1:** Um I'll ping you after'cause at after like 10 o'clock, I should be free. I'll give it a shout and then when it fits in with you, let me know and we'll.

**[00:15:09] Harry:** Yeah. Okay.

**[00:15:13] Speaker 1:** We'll make it work.

**[00:15:14] Harry:** Yeah, I I've got nice um

**[00:15:14] Speaker 1:** Um

**[00:15:17] Harry:** empty day. I take all all I want to do is take you through Like i is your head out like I have a single database and that serves an application?

**[00:15:28] Speaker 1:** Uh not necessarily, no.

**[00:15:30] Harry:** Hmm.

**[00:15:31] Speaker 1:** The singular the singular entry point for me is are we still working off of c because They've in the past, they've always stayed away from like fully API carriers because of. several reasons for this, which means we have to account things like zip code based guzzeteers, which means We've in the past, we've always downloaded, extracted, pushed out to all systems. That's a terrible way of doing it. We should have a single point of truth that they're all calling against. So there becomes this like singular database, which actually there's quite a few areas that benefits us having this like. Yeah. database. Everything is calling as a singular point. Now, that doesn't need to be a monolithic like Postgres, it can be Mongo style. Set up. Like, it's, it doesn't have to be one or the other. Like, we can have a fucking Mongo just for gas, and then the service picks. goes and gets the information, yada yada yada. Yeah, like I I I am happy for any of it. I am working off the the premise of problems I've seen, but if your confidence is higher in Mongo and you can you've got evidence for it, I am more than willing to go down that route too, you know?

**[00:16:40] Harry:** Loving them. Well like I say it's right.

**[00:16:41] Speaker 1:** Sorry man, I've got to hop off that deadline.

**[00:16:43] Harry:** Nada you're you're good. Um

**[00:16:44] Speaker 1:** This. I'll give you a little shout in a bit and we'll discuss further. But I think, yeah, the U.S. about, I think the U.S. region location, if you're handling that, yeah, with Ronnie, I think we need to get that sorted straight away. But pop from that.

**[00:16:48] Harry:** No. US stuff definitely agree.

**[00:16:53] Harry:** Um

**[00:16:56] Harry:** Yeah, thi thing to ponder, right? If it's one database serving everything, what happens if the database dies?

**[00:17:03] Speaker 1:** No, well yeah, but there there's ways around that, like, you know.

**[00:17:04] Harry:** So Yeah, and and that's that's what I want to take you through later.

**[00:17:06] Speaker 1:** I s

**[00:17:10] Speaker 1:** Yeah, yeah, for sure.

**[00:17:10] Harry:** Um'cause like yeah, wait we lost a database, um Fuse was absolutely fine. Say uh uh Here's a shot when you're free and I'll take you through it.

**[00:17:19] Speaker 1:** Yeah, we'll do mate. We'll go for it. We'll go for it. Cool. In a bit. Is like

