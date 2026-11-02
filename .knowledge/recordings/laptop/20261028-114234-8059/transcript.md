**[00:00:00] Speaker 1:** is making sure that The first instance of a US customer using us is not Dispatch Cloud. I'm like very, very keen to make sure that doesn't fucking happen.

**[00:00:08] Harry:** Mm.

**[00:00:08] Speaker 1:** Which is where We need a front end UI. That's that you to implement that on top of views, if that makes sense.

**[00:00:18] Harry:** Yeah.

**[00:00:18] Speaker 1:** For the customer.

**[00:00:19] Harry:** Yeah, we we can so we we can definitely look to do something, um, kind of make a bit foundational for this stuff. I did um catch up with Denton earlier and I'm gonna take sort of

**[00:00:20] Speaker 1:** Um

**[00:00:31] Harry:** At least whilst I have capacity because I'm outside of my team, I don't know if things will change later, but for the time being on anything like Merrick related I'm going to uh be taking technical leadership on. just so that we can coordinate these things. Um

**[00:00:50] Harry:** For a For a UI, do do we know what we need?

**[00:00:57] Speaker 1:** Uh well, it we've got uh do we work off of the premise of

**[00:01:02] Speaker 1:** They've been sold that Dispatch Cloud is what they can use. So do we work off of like look at look at what Dispatch Cloud does, copy, paste into, or do we

**[00:01:05] Harry:** Yeah.

**[00:01:12] Speaker 1:** Try and get a little, because they have meetings every single day this week with the US team. So we try and get in there and figure out, oh, what do they actually need? Because I have a feeling that Phil's probably gone in there and been like, He might have structured what they think they can do around Dispatch Cloud instead of finding the solution for what they actually need.

**[00:01:32] Harry:** His

**[00:01:35] Harry:** I guess if

**[00:01:36] Speaker 2:** Let me let me send you this actually. This is

**[00:01:38] Harry:** Yeah, so um I'm gonna make a bold suggestion.

**[00:01:38] Speaker 2:** But this would be a good starting round.

**[00:01:42] Harry:** we don't have any input from product.

**[00:01:43] Speaker 1:** That's um

**[00:01:45] Harry:** or we're waiting for input from product.

**[00:01:46] Speaker 1:** Yeah, this is all This is all outside of them. Let me send you.

**[00:01:48] Harry:** Yeah. So If I'm taking

**[00:01:51] Speaker 1:** I think this will answer a lot of your questions.

**[00:01:54] Harry:** technical leadership side of this. I think what would be really helpful from your side is if you could You said yesterday that you wanted to

**[00:02:06] Harry:** be responsible for and influence the process side of things. Um Let's look at

**[00:02:16] Speaker 1:** So that that's a message to feel to me about that's the templates they're uploading to Dispatch Cloud.

**[00:02:24] Harry:** Here's what we do. Um

**[00:02:28] Harry:** That is a Merak board and in there I'm going to create An ethic.

**[00:02:40] Harry:** Um And let's distill.

**[00:02:47] Harry:** like No access in here. Okay. We'll create an epic somehow. Um I'll go talk to Harrison. And in that epic, let's create like L let's do a proper product engineering style. Let's put all of the requirements into the epic, break it down into tickets and then I can start to split this stuff out with um Kyle and I and then we actually know what we're building instead of kind of Um vibes.

**[00:03:15] Speaker 2:** Yeah, I do you think that we don't do this currently?

**[00:03:19] Harry:** Um I mean

**[00:03:21] Speaker 1:** Do you think I'm I'm just trying to understand where your view of like our workload is? Because We have this for every product. We have full epics, we have full sprints that we're doing off the design. Like everything you showed me before, we've implemented that we're doing this as correctly as. We can. I'm just confused. Like, do you think that I'm just like vibe coding on the day? Like, I'm just hoping for the best.

**[00:03:42] Harry:** It's the impression that like as an outside observer that that's the impression that we get because we don't we don't see any ticket tickets and I appreciate that works in the background. Um

**[00:03:54] Harry:** We ask for designs and like info and it all it all just seems to be like Flawed output without kind of them thought around it. That that's that's perception, so it it could be completely wrong. But e e even here, right, if we're going on a UI and we don't have any concrete requirements. You like

**[00:04:14] Speaker 2:** No, this is like

**[00:04:14] Harry:** What what's gonna lead me to think more?

**[00:04:20] Speaker 1:** But in the same way that like how you're approaching this. In terms of You don't know the requirements for this, right, currently, so you would go and find out from the relevant parties. that are involved, yeah.

**[00:04:31] Harry:** Yeah, yeah, so we had that conversation yesterday. We popped a design on the board and we said, you know I told us what the intent would be and what would be built. and where it would be shed.

**[00:04:42] Speaker 1:** But that's more like large pitch and merrick, right? That's not this immediate customer that we have to get live within a week.

**[00:04:46] Harry:** No, that that was the so that That diagram with the selector adapter how we plummet through, like, that is existing and an addition.

**[00:04:54] Speaker 2:** Okay, then that that we were we were talking about different

**[00:04:57] Speaker 1:** Things then in my in I was not viewing that. That was like a larger oh, we how we could implement going forward.

**[00:05:04] Harry:** Yeah, and part of that conversation was, you know, let's not budge anything because there is nothing more permanent than a temporary solution. Um if if you

**[00:05:13] Speaker 1:** No what I okay so Yeah, from my my viewpoint on this at the moment is They're bodging it right now with Dispatch Cloud. So we need to get ahead of them doing that. try and get control of the situation that they're already fucking up. because it's they go into the US with like our current config with like a random Like they're all doing everything with no plan. That's what they're currently doing. I'm trying to like drag that back into us before they set push that live next week.

**[00:05:41] Harry:** So what

**[00:05:46] Speaker 1:** 'Cause I was dragged into a c into a call yesterday.

**[00:05:46] Harry:** So where where is the current plan then?

**[00:05:48] Speaker 1:** And they were like, we're going live Monday was their plan.

**[00:05:54] Harry:** I mean, what happens if we just let them...

**[00:05:58] Harry:** let them fuck it up.

**[00:05:58] Speaker 1:** Whole point is that, yeah, yeah, but the whole point of this, and the reason we're being brought into America is so that our customers. Our customer experience is not dog shit. And Like their first experiences as a company expanding is not, it failed. So now let's get other people in to do it. Like that's mental. That we would even want to let them fail like that when we can just, as a company, get ahead of it and do this properly.

**[00:06:21] Harry:** Yes. You kinda have to sometimes, something that I've learned from a lot of the View staff, is like you

**[00:06:26] Speaker 1:** But we've been we've been letting that fail for years, Fitz. Like this is not like...

**[00:06:31] Harry:** It's not failed if they've continued it with that approach.

**[00:06:31] Speaker 1:** This was meant to be the point at which we get ahead of these people that are dog shit and don't don't communicate and don't plan and stuff.

**[00:06:34] Harry:** Yeah.

**[00:06:38] Speaker 1:** I mean, I don't know what I need to show you in terms to get you your view of like Everything you showed me about your boards, we've implemented. I've done like four episodes. I'm reading through all of our PRs. We've built like Talos, which is now in BM2, which is live using all of your infrastructure.

**[00:06:56] Speaker 1:** And to be look, I I know there's a hell of a lot of like dynamic, especially I think this is going to be the same for any junior dev coming in across all companies. There is going to be this disconnect between devs that have been around before AI and devs that have been around after where prove that you know what you're doing is a very different process than it used to be because it was gradual. Like you had to you did it by over a much longer period of showing evidence, right? Whereas nowadays A lot of the stuff that you used to have to hand do. is now not done, you're you're more reviewing, right? on a on a day to day basis. It it's a different job now than it was five years ago, for example.

**[00:07:34] Harry:** Yeah. Yeah, we we're still rev reviewing and we're still designing and we're still kind of

**[00:07:39] Speaker 1:** No, no, I'm sorry, I'm not I'm not saying you're not, I'm saying like for a new junior dev to come in is a completely different scenario than it was five years ago. Like in terms of what what you can put through.

**[00:07:47] Harry:** Yeah.

**[00:07:49] Speaker 1:** My problem now is I realise that we're We're coming into this and your view is that I'm just like recording shit on her like randomly and just hoping for the best. That is what I, I mean, I have all the evidence, like I have all the boards, I have. All of the conversations back and forth. I have the reviews, I have the everything. We are not vibe coding the shit out of this and just being like, YOLO, Claude, just go do whatever you want to do. There is a hell of a lot of areas where you have way more knowledge. And I'm hoping that the whole point is that we, you're there to lead and mentor us as we come through as a team. That was the whole concept of this, right?

**[00:08:25] Speaker 1:** And I am and I'm not in any way being like, oh, I you know. That I don't think you shouldn't be the technical aid of this at all in any shape or form. But what I do think I need to have at home is like I'm not I have way more knowledge than I think you're giving me.

**[00:08:42] Speaker 1:** in terms of like The fact that you think I would be okay just like sending shit out into the void vibe coding. Is a little insulting. Like, I'm not gonna just release shit that I have no concept of how it works. Our team has a rule that like whiteboard test. If someone comes to you and says, what is your product doing? You have to be able to answer that question. You can't.

**[00:09:05] Speaker 1:** I mean I I do I have the same conversations with people like Darren and other people around the company and billing and stuff. And they they can't even do that and they're in their jobs currently. So I'm asking them, and they're like, well, I don't actually know what this bit does, but it's sort of, I know the concept is this. And like, people are moving forward with AI array of knots. every department seems to be implementing it their own little way, but

**[00:09:29] Speaker 1:** We have very much kept to the structure of how you showed us to do the releases.

**[00:09:36] Harry:** That's good, and I I'm sorry, like all

**[00:09:36] Speaker 1:** You know, like I've really taken what you what you said to the heart. Like Oh, how we should be. That's why I want to look to all of your boards and essentially like. Copy the structure you do on like a basis. And why I asked you about like. The backflow of like how you handle Things that aren't done at the end of sprints and things like that. And like. Don't get me wrong, we're new to this in terms of the that structure of how to do it, but I'm certainly not just sending stuff out into the void and vibe coding it.

**[00:10:06] Harry:** No, okay. Well that that's on me then, because all all I've got is kind of what I've seen. Um You know, based on like... Today's things for the UI, like asking for the requirements there, or whether it's kind of hopping in on some of this logging stuff, like there is... I I guess there's gaps or stuff that kind of my gut has me concerned about. Um

**[00:10:30] Speaker 2:** Yeah, I I

**[00:10:30] Harry:** I I can't articulate that.

**[00:10:34] Speaker 1:** No, I I understand. I I think you're 400. From my point of view, I think what you're seeing is the things I'm trying to plug. Like, I have the concerns because things like, Like how this is being handled the US. I'm trying to stop that happening, not. Push it further along the line. Like, I am, you say you want to know the requirements of the CSV that they're importing, right? And that I can't answer that. That's because I haven't been told this is happening until two days ago. And I am playing catch up in the same way that like Your now. Like I'm speaking to you and saying. Can we get a UI on the front of queues? That's my first question. Because if you say to me, no, I've got to then go figure out: okay, we can't do that. What can we do? 'Cause like the what they need in the CSV. Is irrelevant if I can't provide a UI. If we can't do that, then they have to use Dispatch Cloud because they want to go live in a week. You know?

**[00:11:31] Harry:** Yeah.

**[00:11:31] Speaker 1:** If you say to me, Yes, I can go I can overlay a UI and we can do SFTP. file collection to Do the CSV import. Okay, cool. Right. So you can go do you deal with that. You, and I'll go and get all the information I possibly can and provide it to you. And I'll actually speak to the guy on the ground in the US and figure out how they actually are using the system. That they currently have. Because that is not happening currently with these customers. Like no one is actually speaking to the person using it and figuring out what the fuck's going on.

**[00:12:02] Harry:** Yeah, I mean well let let's use this as a test bed to help me like clear out whatever I've got in my head. create the epic, split it down, let's work as a team to do that. Um if you want to do the process side of things still then that's like absolutely I'd I'd love to see that happen.

**[00:12:16] Speaker 1:** Yeah.

**[00:12:21] Harry:** Um then keep

**[00:12:22] Speaker 1:** I mean, there is also an aspect of this like

**[00:12:25] Speaker 1:** Do you think Denton would be pushing me? be in the roles I am if he didn't trust what I'm doing.

**[00:12:32] Speaker 1:** We both trust Denton.

**[00:12:37] Harry:** Okay.

**[00:12:40] Harry:** have to answer because I don't really know what. Ollie's technical background is like in terms of complex systems.

**[00:12:52] Harry:** Um but I am kind of Old school, stuck up, academic, well not really academic, but you know, like, do it right and with rigour.

**[00:13:06] Harry:** Um but rigor needs time in the trenches. And that, like, it basically receipts the thing that kind of helped me build trust. So What what I want to do for this is if we want to produce a UI and use Fuse and make it part of Merat, Um because I I know like

**[00:13:28] Harry:** The three of us have been in possession for like senior manager roles, right? outside of this. I I know the area that I'm going to own, which will be back end, so I'd rather do it right now and work as a team, rather than

**[00:13:46] Harry:** you and your guys go do a siloed thing that ends up becoming throwaway and doesn't add to merit.

**[00:13:51] Speaker 1:** Well yeah, I I I don't know what you mean by silent, like we're not building anything out of view of people. Like you have access to everything we're building. Literally everything.

**[00:13:59] Harry:** Yeah, but I also don't track everything that you do.

**[00:14:04] Speaker 1:** No, I know, but that's not my fault if you don't want to look at it. Like, you can't say you don't trust me and then not look at the stuff we're doing. Like, you can't, it doesn't work both ways. I like I'm. We have in no way hidden anything from you.

**[00:14:14] Harry:** I mean we we've got channels for working out loud. Like we we've got you in our PR channels, we've got you in our general channel, we've got you in a shared channel as well, so like it it it's very clear what we're doing.

**[00:14:27] Harry:** Um But in terms of your day to day, like I don't want to do that bi like I don't want to go and inspect your commits because that feels like micromanaging and that's not a thing that I like doing.

**[00:14:38] Speaker 1:** Yeah, yeah.

**[00:14:40] Harry:** So like

**[00:14:41] Speaker 1:** But if you if it's just not if it's Is that not just okay, no, I understand what you're saying. You want you want visibility without the requirement of having to hunt for it.

**[00:14:49] Harry:** Yeah, the the info is there, like like a thing that I preach to my team is that they work out loud so that everybody can see what they're up to.

**[00:15:02] Speaker 1:** I understand what you're saying. I I mean I can literally we have a Talos and an Iris. Y'all channel. that is pumping stuff back and forth between us. Um

**[00:15:13] Harry:** And I'm not like

**[00:15:14] Speaker 1:** Which I I invite you to to to.

**[00:15:16] Harry:** if if if we want receipts, like let let's let's do this UI infuse integration like

**[00:15:17] Speaker 1:** look at.

**[00:15:23] Harry:** Let's work you and I as a dev team.

**[00:15:28] Harry:** Get an epic, get some tickets, get a project, get some PRs.

**[00:15:35] Harry:** and like handle it in the way that you're telling me that you're handling things.

**[00:15:39] Speaker 2:** I mean, do you want to show you what we've got?

**[00:15:41] Harry:** No, I I I don't I don't need you to take me through everything. Like, if if you're doing it like that, I I would trust that you're saying that.

**[00:15:41] Speaker 2:** Yeah. Praise them.

**[00:15:53] Speaker 2:** Yeah, it doesn't feel like

**[00:15:55] Speaker 1:** I get a very nervous vibe from you in terms of what you think. I'm not going to, we're not planning on pushing stuff out that is. You don't know about at all, especially when it comes to Merrick. There is nothing that is going to be done that doesn't. That you didn't, you know, we haven't even started anything on this. This is, I've purely been ambushed about the fact that they're going live next week.

**[00:16:14] Harry:** Yeah, I mean, so my other perspective from this is like, I get a call from Denton and he says that

**[00:16:15] Speaker 1:** And

**[00:16:21] Harry:** you're building a UI and some stuff outside of Fuse for this, right? That that could have been um the wrong set of words, um and you might actually not be building that stuff.

**[00:16:30] Speaker 1:** No, no, so that's that's that's what started it. That we were in the call. Uh on I can't even remember the day now. Uh like Monday or whenever it was. And they were like, we're using Dispatch Cloud to go live in America with the current setup that we currently have. And I said,

**[00:16:45] Harry:** Yeah.

**[00:16:46] Speaker 1:** I think that's the wrong idea. We should be using we shouldn't be expanding on software. immediately. that one, we don't own and two, doesn't actually fit the purpose going forward. Is there something we could be doing our end? to roll this out instead if we buy another week or two weeks. At that point, I then spoke to Ollie and was like, Can we like can we use fit? I had to basically just pitch that we would build something. To be able to get control back into our area. And then I came to you and was like, hey, what could we do? That's all that's happened there. We haven't built anything. We have the capability. It's a fucking simple process. Like, if we have to replace Dispatch Cloud, it's a CSV.

**[00:17:19] Harry:** Yeah, so

**[00:17:30] Speaker 1:** integration with a with a real billy basic front end. to get it across. That's like the if we have to just brute force replace dispatch cloud. That's not what we want to do. If you can come in and be like, oh, actually, we can use all these cool. Things from Fuse. And all we have to do is build a front end that's fit for purpose for this customer because they're very much like. This doesn't have to be the end product. They just need this customer and they want ownership over it. for this like because this is meant to be beachhead whatever their plan was for that It's just come forward rapidly. Now I've literally gone from that meeting. Gone to Ollie, gone to you.

**[00:18:07] Speaker 1:** There's been no

**[00:18:08] Harry:** Yeah.

**[00:18:09] Speaker 1:** Hidden building or anything like that. But we already have in place.

**[00:18:11] Harry:** Okay, so

**[00:18:14] Speaker 1:** We've already built for other UK customers CSV integration that does this. In the past, because we needed it for a couple of bespoke customers. So that's what Ollie's talking about. Like, we have the process to be able to do this. But you have a structured process to do this. is like and that's way better to use and I'm There is zero argument from me that we shouldn't be using Fuse to do this. Now I'm just calling you to be like, hey, they're pushing me. Do we have a front end for Fuse? Or do we need, is that what we need to rapidly build? Or is that something you don't think is doable in two weeks?

**[00:18:47] Harry:** Yeah. Yeah, I mean like Okay, so may maybe I miss her dolly or ma maybe he um Him aspoke.

**[00:18:55] Speaker 1:** Well this is I'll be honest with you, like the amount of phone calls I'm getting, it seems to be chang they're changing their fucking minds every like hour. And I'm getting told one thing by Pete, one thing by Dan, one thing by like Ollie, and I'm just trying to be like,

**[00:19:01] Harry:** Well yeah, fucking they'll do they'll do anything to like keep a fucking marquee customer happy, won't they?

**[00:19:08] Speaker 1:** Yeah, I'm just I'm just trying to like get us on the same page so that Because we as long as we get a product out in two weeks. we're happy with that we control the means we can grow from. I think that's a win for us, you know, in terms of how we. I really don't want Dispatch Cloud to be leading the way in America. I think that's an awful way to go ahead.

**[00:19:29] Harry:** Yeah. Yeah,'cause we just look like a like effectively a drop shepherd for drop shepherds, won't we? But yeah, um like th this is a thing So the the only context I've got is that like the the call that we're having now, the call I had with Denton before this where he said like Some other stuff happened outside of the conference room, which is fair enough, I had to shoot home so I missed out on that. If that if that even was the case as well. Like I say, some holidays we may have just misspoken. But let let's figure out what we want in the UI. Um get ethic together and then then we can just like fucking build like a team of devs. You know, I was saying to him that I want to I I want to use this as an opportunity to build some credibility for you guys.

**[00:20:07] Speaker 2:** Yeah, I mean it it I I think it is yeah.

**[00:20:15] Harry:** Clearly in my mind I have to do that for for me, but also for the business. If I can take you along and sponsor you then. That's great for your team too.

**[00:20:25] Speaker 1:** Like just

**[00:20:27] Speaker 1:** The business side of this is I think I you're the biggest hurdle I've hit so far in terms of this, like to be honest with you. We have products that are released. and live and are working. Um I'm currently fighting to retrospectively be like, look, we we have products, we are Carl and Jake are doing dev work, like by every definition in a book, like they are doing that. You know, I, this is.

**[00:20:48] Harry:** Yeah, I'm I'm not I'm not saying no, so like Cook, can you? Help me understand how I've been a hurdle, because I'm not saying no.

**[00:20:56] Speaker 1:** No, no, you're not a hurdle. I'm I'm saying that you're the first. Like, I'm getting a very, very strong or like conversation, unless as we talk more about it, but like your initial like, These guys are kind of just like eating stuff into Claude and hoping for the best. is like we've we've taken a lot of steps to make sure that Isn't what's happening because I knew that that would be the response if we, if I just rock up with a product and they're like, Where how did you build this? And I'm just like, well, I just called it it. No one's going to respect it. How the fuck you maintain something like that? Like. We have Not that anything like that.

**[00:21:33] Harry:** 'Kay.

**[00:21:33] Speaker 1:** You know, like. I use a lot of claw to Find out information about stuff I don't know. And then I basically come to you and go, hey, is this how this works? Like, you have the real life, like, like the whole. Re region thing, I know that it's locked by. uh a cost because I literally went on and tried to change ours and it wouldn't let me. So then I did some research, and it was like: if you build up originally in the US, that's why I brought it up to you because. I'm doing research, I'm finding out, and then I'm asking you the technical lead on it. You know, if you then tell me no, I'm like, okay.

**[00:22:10] Harry:** Help me help you then. That let's let's do it proper.

**[00:22:17] Harry:** I will I'll chat to Harrison I'll I'll get the board set up'cause it it doesn't look too happy. Um And then

**[00:22:25] Speaker 1:** Yeah, I mean this is This is obviously, we need to streamline. Who and how for this because of the timeframe, right? We might get a more effective build if you do just take full control of building this. It may be that because of the timeframe we've got, we don't have time to do a shitload of back and forth between A dev team. 'Cause you essentially I mean, correct me if I'm wrong, but Is this a case of we kind of We know the limit we know what the CSV integration is that they need. because I've just I've just sent you the file now. That's what they're currently going to be formatted against. Um which is easy enough to fix because you have all the headers. And then The UR requirements of that is potentially a conversation with Phil. where we say, Okay, what can Dispatch Cloud currently do that they want to do?

**[00:23:12] Harry:** Yeah. Yeah, like'cause

**[00:23:17] Harry:** C CSV is nothing to Fuse, right? Fuse will take in any CSV and it will just process it. Like, doesn't matter what the headers are.

**[00:23:24] Speaker 2:** Super easy.

**[00:23:25] Harry:** Um But yeah, what what I what I want to do as an actor from this is just understand what this front end needs to build. Um catch up once we know that and then just start dealing stuff out and Print it.

**[00:23:42] Speaker 1:** Context of that, that's exactly what I came into this call wanting to know: is do you think you can just add on a UI if I go find out the spec for you? If the answer is yes, I'll go if I can get all that information for you and then give it to you.

**[00:23:52] Harry:** Oh yeah, like, wait, like, do it, cause this has got fucking custom-built programming language, like, it it's got everything that you need and more.

**[00:24:01] Speaker 1:** That that's literally all I need to know because I don't want to waste time us building something. Because I'm being told you need to have it done in a week's time versus, because they hadn't even included. You and Darren, and like I was like, this is me. Why are they not in this? 'Cause I wasn't in the call. Until they basically added like a line at the end that was technical services will support this once live. And I was like, that's, well, that's not a, you know.

**[00:24:23] Harry:** Excellent.

**[00:24:25] Speaker 1:** That's not enough information for going for going live with a product. Um

**[00:24:32] Speaker 1:** Yeah, I'm happy to follow. Any process you want in terms of getting the development on this.

**[00:24:38] Harry:** Yeah, I I mean e even if it's something as simple as just um

**[00:24:38] Speaker 1:** Um

**[00:24:44] Harry:** Like Just act like like the dev team that we want to be. Um I'm gonna So that we avoid silos I'm gonna pop in like a Heck stand up. Um every few days or so.

**[00:25:01] Harry:** so that we avoid like conversations. happening without without each other because it's just useful context to have. Um But then yeah, we can go from there, like we we can we can treat this as kickoff.

**[00:25:16] Speaker 1:** Yeah,'cause they they want this live button like, basically.

**[00:25:21] Speaker 1:** That's their go-live for this.

**[00:25:23] Harry:** Yeah, that'd be fine. Like the the tricky stuff really exists.

**[00:25:28] Speaker 1:** But yeah. Mm-hmm.

**[00:25:36] Speaker 1:** And then this is maybe my maybe I mean being more defensive than I need to be. But it pretty much felt like I was like. Presented the Republican. I went, oh shit, Fitz needs to be involved in this. I brought it to you. And then you were like, you don't know anything. Fuck off. Is how it felt. Like, and I kind of felt like,

**[00:25:55] Harry:** Yeah.

**[00:25:56] Speaker 1:** If I because if I just cracked on to solve this.

**[00:26:00] Speaker 1:** I could I I am more than confident I could do that. I didn't want to do it that way because of this exact reason I want you to be like in control of it. Mm-hmm. And it felt a little bit like a kick in the teeth when I came to you and you were essentially like. YOLO vibing don't work it you know.

**[00:26:16] Harry:** Yeah, I I'm sorry if it came across like that. I just

**[00:26:20] Speaker 1:** Well no, I I clearly am not doing a good enough job of of portraying what we're doing as a team. which if you feel like this, other people will feel like this. And I need to make sure that isn't a thing.

**[00:26:29] Harry:** Yeah, I I am

**[00:26:29] Speaker 1:** Um because that's not that's not how we're working.

**[00:26:33] Harry:** Yeah, like like th this is something that I want to um

**[00:26:33] Speaker 1:** Mm-hmm.

**[00:26:40] Harry:** What are the words Sorry Laugh to bear with who only got a couple of hours of sleep?

**[00:26:44] Speaker 2:** No, I get it, I get it. I was either my children older, I only got a couple of hours as well if I can dealing with all this bullshit.

**[00:26:44] Harry:** Um

**[00:26:51] Harry:** Uh yeah, now it's in A and E all night.

**[00:26:52] Speaker 2:** Okay.

**[00:26:53] Harry:** Um

**[00:26:54] Speaker 2:** Yeah. Everyone alright?

**[00:26:56] Harry:** Yeah, yeah, we're all good. Um yeah, I I think if if perception at this level from where we've to help and guide you. is is a thing then yeah I think we need to work on on branding which is why like yeah this needs to This can be a springboard. I it's it's like I was saying to Denton, right? Um I'll I'll leave it technically. And I will like take you and Kyle and whoever else along as a sponsor. get you the tools that you need to workouts, dance, um I like to think I've got enough um

**[00:27:40] Harry:** enough of a brand that that will that will help.

**[00:27:48] Speaker 1:** Yeah, yeah, I mean a hundred percent. Like having your Your name against it. I understand you won't. Your name is against this, so how the the fucking end result is very important. Um

**[00:28:01] Speaker 1:** And yeah, I I I just want yeah. I I think you're completely right in How the structure of this will help. show the white light. Um

**[00:28:15] Speaker 1:** I And so just, I think, slightly disappointed that

**[00:28:21] Speaker 1:** your belief was is that bad of us at the moment. Um

**[00:28:27] Speaker 1:** mainly'cause we put in we put in so much effort to to

**[00:28:28] Harry:** Yeah.

**[00:28:31] Speaker 1:** work to the standard you wanted us to originally. Um But that's something that is hopefully just a visibility thing. And By shoring that up. You'll see that we have taken literally everything you've ever said to us on board. And we take very seriously.

**[00:28:48] Harry:** Well that it

**[00:28:52] Harry:** If I thought you were shit, I wouldn't say let's do it as a team and I wouldn't say let's bring you in Kylan and work on whatever ticks we've tickets we create as a team, right?

**[00:29:04] Harry:** Um so yeah thi this is this is me on a few hours of sleep so I'm I'm gonna be bunter in the wrong way. Um

**[00:29:13] Speaker 1:** Like I said, it doesn't bother me, mate. I'm expecting to have lots of lots of fun, heated discussions in the future about how we handle stuff. It's that's part of why we're being.

**[00:29:18] Harry:** No, no, like

**[00:29:23] Speaker 1:** hopefully paid what we get paid, is to have these conversations with the adults about it.

**[00:29:25] Harry:** Yeah. No, it

**[00:29:28] Harry:** Yeah. No, I I mean like

**[00:29:32] Harry:** Y you can say it doesn't bother you but it would fucking bother me, so yeah, let let's Let's do it like a tab team.

**[00:29:40] Speaker 1:** Yeah, for sure. Well, you take technical lead completely on this. Um Again, it's I am willing on the special on this to take your, if you think this is some because of the time frames, it's something you need to just run with. To get done. Um Do so. There's going to be lots and lots of time in the future as we build out, especially the labelling process, because Me and Cole do have a do have the most knowledge on that system in the company at the moment. Um And If you think your visibility of what we've been developing is bad, you have no idea about the visibility of how no one knows about this labelling system. Um

**[00:30:20] Speaker 1:** It's it's so I I think you'll be amazed at how much stuff has been bodged together. Um, to the level where it's in like the the gaps we've filled isn't that. over the years. Um and we are hoping that you come in and apply some fucking structure to it. That's kind of and your technical leadership on it. Mm.

**[00:30:41] Harry:** Yeah, well we we will nail it. We will.

**[00:30:45] Speaker 1:** I've I've no doubt that between me, you and Darren, we fucking have the capability to everything. Um And look, I we there's a lot of politics going on at the moment. I'm actively trying to remove fine integrations from their role because they're so bad at it. Um And we need to shift. around how that's handled. Um and we need to think about the technical support of the product post live. Um

**[00:31:12] Speaker 1:** which is going to be my area of expertise. Um

**[00:31:17] Speaker 1:** But how we handle the building of this is I'm kind of You're not going to get any pushback from me.

**[00:31:22] Harry:** Yeah.

**[00:31:22] Speaker 1:** Um

**[00:31:23] Harry:** No, it should should be.

**[00:31:24] Speaker 1:** But just take into con you know, taking I would just like to take into consideration.

**[00:31:25] Harry:** It'd be all good.

**[00:31:30] Speaker 1:** We are working to everything you've shown us.

**[00:31:33] Harry:** And th that's that that's why I'm saying that's let's work as a team because like

**[00:31:33] Speaker 1:** Mm-hmm.

**[00:31:38] Harry:** I want to get that out of my head, and the only way I can do that is by working as a team of developers with you.

**[00:31:49] Speaker 1:** conventional setup.

**[00:31:54] Speaker 1:** Yeah. I mean it's Especially when it comes to Jake and Carl, like Jake literally used to be employed as a developer and then came into our team. So he's helped implement stuff as well.

**[00:32:08] Speaker 1:** I guess it's the downside of shifting so much internally within a company. Like if we were hired as devs. you probably wouldn't have the same concerns. if we'd been like hired externally in, if that makes sense. Um at least to the same extent.

**[00:32:20] Harry:** Yeah.

**[00:32:23] Harry:** I see what you mean.

**[00:32:25] Speaker 1:** Um'cause we, you know. We have come from product support email reset up to where we are, but that's not because I was a product support email reset guy. That's because I got a job because I needed one. And we are now, you know. You know.

**[00:32:40] Speaker 1:** We've all been working on ownership for years. before this.

**[00:32:47] Speaker 1:** Um but yeah, I look

**[00:32:50] Speaker 1:** There I don do you wanna do you want me to go into this call this afternoon? See what the fuck's going on because unfortunately there is two parallel conversations happening of like a bunch of people pushing Disk Rex Cloud and few people being like, no, stop. We need to not do that. That's what I'm trying to manage at the moment.

**[00:33:09] Harry:** Yeah.

**[00:33:10] Speaker 1:** Um and I'm I'm trying we kind of need I kind of need you to like start the process of building the the fix.

**[00:33:17] Harry:** Oh yeah, like

**[00:33:17] Speaker 1:** so that if I can convince him over. we're ready type thing.

**[00:33:21] Harry:** Maybe we we've got like two services deployed, it's just how we want to like show that out out to the user.

**[00:33:28] Speaker 1:** Yeah, it's literally just the front end. The UI of this that there. concerned about. Keep waffling on and saying, Oh, well, dispatch clouds are ready to go. And I was like, you know, it's literally a CSV integration. It's not that fucking complicated. There isn't that lot because they're very, it's like real basic shit they're doing in Dispatch Cloud of like, so they can see what they've imported so that they can like cancel orders so they can. Make changes to the data in the CSV that's been uploaded, that kind of thing that they're doing on the UI. It's all really basic stuff. I just need to get a spec list. I was just checking that you were fine with doing that.

**[00:34:09] Harry:** Yeah, let's let's do that. That's that runs down the spec list as well so we can Um

**[00:34:15] Speaker 2:** Well, they I don't think anyone's asked them, if I'm honest.

**[00:34:15] Harry:** I understand how everything fits.

**[00:34:17] Speaker 1:** I think they've literally gone to them and been like, this is what Dispatch Cloud does. No one's gone. So what do you actually need to do in your warehouse?

**[00:34:23] Harry:** Yeah. Well I mean like there's

**[00:34:25] Speaker 1:** And which is why I like that's that's the problem that I think we face all the fucking time with these customers we onboard is no one actually asks the right questions.

**[00:34:32] Harry:** Yeah. Well we not Might be right up your wheelhouse is like the process dude, right?

**[00:34:38] Speaker 1:** Well yeah, that's that's where my that's where the what literally what I deal with on a daily basis. plugging that gap. Um

**[00:34:47] Speaker 1:** and then feeding back to you, who can then lead the building of the solution for it. That's kind of how I viewed this dynamic. I'm not looking to be the technical lead in any stretch of the imagination, you know. Um I'll not retard it.

**[00:35:00] Speaker 2:** You know, like you know, um

**[00:35:02] Harry:** Yeah, no I know.

**[00:35:07] Speaker 1:** Okay. Well, I hope you don't think I'm, you know, I'm trying not to I'm trying to gauge how I can talk to you as well, because. Like I'm a very blunt person, um but I don't mean it in a bad way at all.

**[00:35:21] Harry:** quite similar in that regard to be fair.

**[00:35:23] Speaker 1:** I feel like we're going to get to the resolutions far quicker between us if neither of us takes offense to either. There's insane like We're both coming at this from a we wanna succeed mindset. Um You know, um And I think that's the way forward. Denton has faith in both of us to To do this. Um So I think we crack on with it but yeah if you so if you're are you I'll try and find out m as much spec stuff as I can now. Um Granted, you know, in the future this will be handled completely differently. It's only because of the time frame that they dropped on us.

**[00:36:01] Harry:** Yeah.

**[00:36:01] Speaker 1:** Um

**[00:36:02] Harry:** Yeah, I

**[00:36:03] Speaker 1:** Like it may be that we just have to get out of real basic version and then we can add to the features in the weeks to come. Um

**[00:36:10] Harry:** Yeah, I I mean o overall overall it should be fine. Um

**[00:36:16] Harry:** Even I'm getting harassed into sort of permissions because I can't create anything on um on Jira, but let's get let's get as much info as we can into that epic. E even the stuff that seems noddy to you, right? Um You're not retarded, but I am. uh especially when it comes to selector um and like the nuance there, so Even like in insofar as what it can do and what what they want to do with it, like I have no fucking idea.

**[00:36:36] Speaker 2:** Well selector, so for this instance.

**[00:36:45] Speaker 1:** Yeah, so for this circumstance, before we consider rebuild. If you

**[00:36:51] Speaker 1:** If you handle the getting the data in and the UI, I'll handle the getting that into selector working. Just for now.

**[00:36:59] Harry:** Yeah.

**[00:37:01] Speaker 1:** Because that is our wheelhouse. We own that currently. Um And then in the future like Merrick will be the replacement of Selector 100%.

**[00:37:10] Harry:** Yeah.

**[00:37:11] Speaker 1:** But right now, we don't need to worry about that because they're built, like Chris is building it to work with Selector.

**[00:37:16] Harry:** Yeah, so I I know there are um th this is how little context I have, like there are different actions you can do at Selector, right? Like, I think processing a shipment's one of them. I have no idea what that is. So e even that kind of stuff that would seem noddy would be really good to put into the epic.

**[00:37:36] Speaker 2:** Yeah.

**[00:37:37] Speaker 1:** Do you want to convolute it though at this point with Is this not just a get the front end sorted? 'Cause what I don't want to do is be like starting to worry about selector.

**[00:37:48] Harry:** else

**[00:37:49] Speaker 1:** If we're just going to go squeeze. Sheriff on it.

**[00:37:51] Harry:** There's there's get the front end sorted and then there's there is get it to selector. And that gets it to selector would need to go through fuse.

**[00:37:59] Speaker 1:** Yeah, that's it.

**[00:38:03] Harry:** Right.

**[00:38:03] Speaker 1:** But we don't we already have that?'Cause what you drop into snap Or or via direct API.

**[00:38:10] Harry:** Yeah.

**[00:38:11] Speaker 2:** But we already have that ready to pick up.

**[00:38:14] Harry:** Uh yes and no. So it's like when we get to putting it into selector which like which selector API are we calling?

**[00:38:24] Speaker 2:** Uh okay. Oh we have yeah, we have all of our data here.

**[00:38:26] Harry:** Say it like that. Yeah, like like that kind of info I need because I I don't have that context.

**[00:38:32] Speaker 1:** Oh okay, right, okay, I'm with you now. Yeah, that's fine, I can provide all of that. That's fine.

**[00:38:35] Harry:** But like I say, um retarded, don't let the classes for you.

**[00:38:39] Speaker 1:** Well no, I yeah, you got I just You guys don't have visibility of what we're doing with this. I think half the fucking company doesn't even know what it exists. So, yeah, it's I'll I'll give you that. Um And we'll go for that also.

**[00:38:54] Speaker 2:** Yeah, if you fucking weigh, he's a dog. It's right.

**[00:39:00] Speaker 2:** Yeah, I know, he can wait, he's fine, he's a dog, he'll sit.

**[00:39:05] Speaker 2:** Are you going out there?

**[00:39:09] Speaker 2:** You can go, I'll feed him. Tilly. Yeah, I'll see the dog till. If Um yeah, I

**[00:39:17] Speaker 2:** Yeah, I'll get you that information.

**[00:39:20] Speaker 2:** Um

**[00:39:22] Harry:** 'Cause yeah, like Like it mostly exists there and it's mostly ready to go through. There's a there's a few like little bits I need to do in fuse. Um but Just so that I'm interfacing with the application correctly. Um and then I can

**[00:39:38] Speaker 1:** So you'll be bringing in the CSV, converting that into an a uh an API call and then sending that across?

**[00:39:44] Harry:** Yeah, pretty much. Like there's there's a few extra steps that are like fuse internal, but yeah. There are there are things that like

**[00:39:49] Speaker 1:** Yeah, it's just yeah, end end to end, I mean, you know, in terms of what goes in, what comes out.

**[00:39:53] Harry:** But yeah, like literally we will give you an SFTP login. Um of the customer in their SFTP login. they can drop their CSV in and then yeah it should be all good to go.

**[00:40:05] Speaker 1:** Cool, then it's all automatic and they don't have to worry because basically they dispatch patches like a manual upload process as well. Um which is what I Yeah, which I pick which is how I managed to pitch to them to say, let me. Go figure out if we can do something because if we can automate it. they're way happier.

**[00:40:21] Harry:** Yeah, yeah, like if if they drop it on the server, like we we can put in defaults and like dimensions and everything too.

**[00:40:22] Speaker 1:** Um

**[00:40:28] Speaker 1:** Sick. Okay, cool. Yeah. I mean, this is going to be, yeah. I hope you know that like the whole concept was I wanted to get you in and I was just trying to deal with the fact that I was fighting people doing the wrong thing to start with. Like. You know.

**[00:40:41] Speaker 1:** Well, I've, yeah, it was all of it was on the fly changing hourly. So I probably wasn't clear enough anyway. I was just trying to make sure that we got the project into our area.

**[00:40:49] Harry:** They're they're like yeah, like classic fucking gaps in the dev team, right? Um we'll do our things with in our own teams because we're still Working on that stuff, we don't catch up frequently. We're all at home half the time. So I'll pop in. I'll pop in a meeting every like Monday, Wednesday, Friday for us to catch up on this stuff as well. you know, stand-up style.

**[00:41:13] Harry:** Um

**[00:41:13] Speaker 1:** Yeah, going forward, yeah, for sure. And then I guess we just keep a really open comms. in the next week or so about how we're going to

**[00:41:19] Harry:** Yeah.

**[00:41:21] Speaker 1:** Yes. Cause if you can I'll get the spec you build the UI. get it over them to test um as fucking as soon as possible. Um and then I'll handle the the CSV working in selector plus testing. changes from FMXI to make sure that the API calls to the carrier work. Um That doesn't at the moment. We found a couple of bugs that they haven't fucking fixed.

**[00:41:46] Harry:** Guess it gas it all in the epic.

**[00:41:47] Speaker 1:** Um

**[00:41:51] Harry:** Leave a like.

**[00:41:52] Speaker 2:** and then we go to that.

**[00:41:53] Harry:** For for sake of my visibility, knowing how much work you guys have to put into it will like just help. demystify what your day-to-day looks like.

**[00:42:08] Speaker 2:** Yeah, I'll hopefully provide some clarity then. Um

**[00:42:13] Speaker 2:** It just sucks it's grown to that level. But you know. Um

**[00:42:18] Harry:** Better. better identifier like now than much later on right.

**[00:42:24] Speaker 2:** Well yeah, it's a learning curve for me as well as it is for how I present stuff.

**[00:42:31] Speaker 2:** going forward.

**[00:42:34] Speaker 2:** Yeah, it's all good. Cool. All right, mate. Well, um

**[00:42:35] Harry:** Trift one.

**[00:42:37] Speaker 2:** Thank you for the call.

**[00:42:38] Speaker 1:** Um I think we are in a better spot. And I'll go find out what I can. And they have a call every day this week. with the US team. Um I'm gonna try and ambush that and figure out what the fuck they're doing. Um and then grab what it can for us, I guess.

**[00:42:53] Harry:** M

**[00:42:53] Speaker 1:** Yeah, let me know when they when we can make changes to the to the board.

**[00:42:57] Speaker 2:** Um gala.

**[00:42:59] Speaker 1:** Bye mate, in a bit.

**[00:42:59] Harry:** Yeah, catching a bit late ticker.

