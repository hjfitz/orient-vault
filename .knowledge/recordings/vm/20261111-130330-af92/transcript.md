**[00:00:00] Speaker 1:** Is in order there. Puddy and Figs peak, which I'll caveat with not the volumes we expected, but at least the uptick of volume over the weekend held fine, and all the orders went in with 100% success. So that's fantastic news. And also on the CT project side, the Edicom, who are the intermediatory between CT and us, have been able to make a connection to our SFTP, which is good. So hopefully we can start progressing with some of the more testing of the files and actually making progression on that piece. In terms of stuff done recently, so some stuff has gone in for hardening the round peak. So I know Harry's been a busy bee looking about how we interact with Snap and make sure that that's safe. and how those safety controls kick in, those are there now. Uh stock sync. Uh stuff is in progress. So obviously we've got Sync for Shopify in QA, but we're building it for the SFTP element as well. So we've added some stuff around showing it in the transaction history. And if it fails for a particular product, rather than having to play the whole sync again, you can play it for that particular product. Um on the support side, we're still building the captured raw payload work, that's progressing well. We've picked that back up after having to prioritise some other work last week.

**[00:01:15] Room 1:** Oh my goodness.

**[00:01:23] Speaker 1:** On the apps and config side, we've made some UI level changes. So there's quite a few the announcements in Slack for those who want to see it, but essentially. Given the UI a refresh where it needed some love, some helpful features added on top of that is, for example, every record like in the transaction history now has its own unique URL. So you can easily share that with someone else easily.

**[00:01:46] Room 1:** Mm-hmm.

**[00:01:48] Speaker 1:** Um and we've also put some stuff around based out the back of the Google Cloud incident to make sure that Fuse can keep running if the cache hosted in the cloud goes down. On the onboard and legitibit side, we have completed a series of work order fixes. Tom reviewed that yesterday and provided some feedback on a couple items. So we're just addressing those now. Those tickets are in flight. On the pick pack side. We've made some fixes. Liam's just provided some feedback and got some questions on those. So Liam, Tom, I'll catch you after this if that's all right, just on those. But the hope is once we can resolve that, we're good.

**[00:02:30] Room 1:** Yeah.

**[00:02:30] Speaker 1:** Uh, roadmap perspective, really we're kind of in the Edifac build. So there's stock sync, we've got the raw payload stuff that's going, and then we'll be starting the jitter bit parity for Shopify stuff and keeping some capacity reserved for the CT functional testing and what that surfaces as a part of that. I anticipate with the current we may start the jitter bit parity a little bit later, maybe towards the mid to end of November, but that causes no risk in terms of

**[00:02:58] Room 1:** Mm.

**[00:03:00] Speaker 1:** What's gone on there?

**[00:03:05] Speaker 1:** Bear with me a sec. technology. But that causes no risk in terms of the Jitabit migration program. We still expect that those features will be there in time, but I will.

**[00:03:12] Room 1:** Okay.

**[00:03:19] Speaker 1:** keep you updated as we go. Um In terms of what's coming, so StockSync, Stock API are both in QA. We got some early feedback about Stock Sync this morning, so we're gonna have a look at that and triage that. Uh work orders I've spoken about, pick pack I've spoke about, Edifact, waiting really to see what the testing service is, SFTP stock sync, the wiring has been done, we've just got a few things like scheduling and the UI to finish off.

**[00:03:44] Room 1:** Yeah.

**[00:03:48] Speaker 1:** Uh the raw payload stuff, we've we're doing the captures, the capture parts have been done and we're moving on to the next leg of that now.

**[00:03:48] Room 1:** Um

**[00:03:56] Speaker 1:** And for the Shopify requirements stuff, that's been captured and I haven't been made aware of any additional requirements out the ones we've already flagged. So hopefully we've got those all captured now, which will start in the next sprint.

**[00:04:10] Speaker 1:** But yeah, that's it, otherwise. Any questions?

**[00:04:16] Speaker 2:** Good, I think. Um I think that's h possibly answer the couple of questions I've got in a minute, but I'll I'll go through those with a wider group. Mm-hmm.

**[00:04:27] Speaker 2:** Or or now if there's no further questions on that.

**[00:04:33] Speaker 2:** Okay, thank you, Jack. So the previous project plan we had was very much started off as a brain dump a number of months ago and then it is being used to capture are they Shopify, are they CSV, what interfaces they have, blah, blah, blah, blah. But sort of speaking with Tom and sort of Over recent sort of weeks, it's clear that the actual detail involved with all these counts and also from the legitimate extracts, that's kind of slightly irrelevant for the project plan because we've got all that information captured in better places in a lot more detail than what was just sort of exported onto that plan. So to try and make it a bit easier for us, we've just put together a new plan. made it a lot smaller in terms of the interface sort of build stage, the interface UAT stage, because again, you've got all that capture on Jira boards, et cetera. But if I just share what I've got,'cause there's just a few dates that I want to clarify with you guys, but I think one of them's just been moved anyway. So Let me know if you can all see my screen okay.

**[00:05:33] Speaker 2:** All good.

**[00:05:37] Speaker 2:** Yeah, cool, perfect. Okay, thank you. So. The Shopify build stage, um we had down, I think. Jack, yes, as you mentioned there, sort of mid-December for some of those bits. I think this is just the outstanding bits that we've been speaking about, like stock sync and some of the other bits. But eighty three percent, so again, that's all fine. And then the support functionality, I've got a funny feeling that was the raw payload bit that you just made reference to back there, so I've just bumped um was that right that that's the end of November now? Does that need a bit of an update on that time?

**[00:06:08] Speaker 1:** Yeah, I'd say around the end of November.

**[00:06:11] Speaker 2:** Okay, perfect. So those bits there, again, it's all on track at the moment, but I think for the purpose of this we just have a one line and just say roughly where we are as I say the details behind what these numbers are are kept elsewhere, so it's silly trying to keep everything ma you know, a hundred percent like for like. Um Tom, in terms of well Tot Tom, Liam and Haley, in terms of sort of the the testing phase for Shopify we've got seventy six per cent but also Was saying that was going to be the ninth of November, which obviously it can't fully be, but does seventy-six per cent sound about right on what date do we need to bump that back to? guessing it's gonna be towards the end of December given that The full build isn't going to be completed until around the eleventh or there thereabouts.

**[00:06:50] Speaker 3:** Is this like overall shopified Darren for like the main interfaces or main elements of that particular

**[00:06:58] Speaker 2:** Medium. Yeah, ju ju j just the main bits, like if if we've got other bits that we're adding later date, obviously we can't keep putting that. Um but it's just I say it was a bit sort of there was too much detail and we were capturing it in too many different places for me. So I just wanted to try and summarise it just to get a one liner.

**[00:07:14] Speaker 3:** Yeah, to be honest, the for the most part, Shock Buy is there and Harry Jack. So charming if you think I'm talking utter rubbish. Um far the stock sink. So as far as I'm concerned, it's it's We've seen the stock sync work. There's a couple of things that Alex has flagged that I've flagged. So. think in general. probably a few percent higher than that for the most part. Would that would that be fair to say Jack Harry from like a dev product standpoint as well?

**[00:07:44] Room 2:** Yeah.

**[00:07:46] Speaker 1:** I j I'm assuming what we're getting at here is if the interfaces exist for these connectors rather than the individual edge cases we have,'cause there's customers that have edge cases that haven't been built yet and You know, that applies to the API, for example. But if we're talking about use cases available via connector, then yeah, I would agree with that because stock syncs to Link UA.

**[00:08:11] Speaker 2:** Yeah, I mean well There's two ways of looking at this. If need be, I can strip this bit out completely and we can just have this all about customers. Oral terms is to say we can have one bit. I mean. In my head, I'm thinking if we're saying that shop for our customers we can get over For January, then we should probably be looking at being sort of at least 95% built on Shopify and tested on Shopify. Albeit there might be, I don't know, but there might be this. What is it that not necessarily what Eccentric needed with the split, but was it um Manicurist and possibly yeah, academic gift. I think that's quite, but then Boo Clem as well has a very complex routing bit. So, like, would we still be looking to try and get that sort of out in the open and completed by December? Or are we saying actually no? Let's just make this about what we know the customers that are in the sprint in January need, and that's you know, not going to include any of these extra bits.

**[00:09:04] Room 2:** Hmm.

**[00:09:05] Speaker 2:** What I don't want to do is have something here saying we're a hundred percent, but then actually us saying we can't make a customer live because something's missing.

**[00:09:12] Speaker 1:** Yeah, I think also from my standpoint, it's hard to say on that as well because, like, take the Blue Plem scenario. I'm not aware of that one at the moment. So, like, I can't. Surface back if a connector is what we consider jitter bit parity complete, if we haven't got all the requirements for that yet. So

**[00:09:30] Room 2:** Mm-hmm.

**[00:09:31] Speaker 1:** I I maybe by customer enabled, Darren, makes more sense. So we say a customer is supported and therefore we can schedule them because then we can look at the ones that aren't and say why can't we support them? Um

**[00:09:44] Speaker 2:** Yeah, so I think yeah, so So if we just make this about what we know about today rather than anything that might be down the track. So, okay. Um so eighty three per cent and then I'm just gonna bump that back a week after. We're saying that the stuff's going to be done. And then CSV Tom, what is it that's outstanding on CSV?

**[00:10:06] Speaker 3:** Just works orders uh well. To be honest. CSV and JSON you can probably combine together because they all root via the SFTP. So if one medium works, the other one will. So Works orders is the last thing apart from SFTP stock sync, which is in essence kind of just a report. At least to what we would see at the end product. So you're probably about on the money there, where it is. Right now, like work sort of is very nearly there. There's more of a couple like UI related things, nothing massively related to the flow itself.

**[00:10:38] Speaker 2:** Let me bump that back then and just see where we are by the twentieth. Okay, and then as I say, I'm less interested in this bit, if I'm honest, because I know that's taken care of and it's being looked after everywhere else, so that's why I didn't want as much on here. But basically, the point is. They're the two that we got over. As you mentioned, Jack, Indu, we're looking to move over on Monday. Um these week commencing date proposed, uh James, Tom and myself have caught up with the CAMS and I've seen communication going out to all of these customers about sort of you know these the weeks you've been given.

**[00:11:05] Room 1:** Mm-hmm.

**[00:11:09] Speaker 2:** I've booked a follow-up meeting today because I don't want it to be a week. I actually want it to be a date. And then once we've got those, we can move them back up into the migration dates booked in. These migration dates to be locked in, typically these are more sort of um your API customers or your self-portrait that got a bit as a donk as well. So we've just got a few bits that we need to wine out before we do that. And then not necessarily for today, but I think over the coming weeks we just need to have a look at these disco uh discussions. Be held and decisions to be made. So, Abbott Line, strictly speaking, although they are different to Dock and Bay, Abbott Line can use the RG API now. So, again, that one should be okay. BAT, some of you will be aware, but they're moving over to SAP. So again, we've got conversations with them about what that integration is going to look like,'cause that's gonna change. Boot Clem as we mentioned previously. Um I'll set up a little call just to go through that because I've got a very weird mapping sort of diagram which I drew. It's not technical at all, but kind of shows you their free stores and what happens with the orders'cause ILG takes some but not all. However, it might be worth us having a conversation now about your best bet is just to do X and Y and then it'll just run a lot better for us and any other free PLs that they might be working with in the States, in the UK or wherever it might be. Bustrum Punch we've spoken to by Terry. I think there has been conversations, but again, they're on Netsweep. Charlotte Tilbury, as you've mentioned, Jack migrating to SAP. Flat Lay again unleashed along with Percy and Reed. So if Indu goes well, then hopefully we'll be sort of 95% of the way there for those guys. And then there's Net Suite Connector with This Works. But I believe, Tom, you said to Liam the other day that you had a call with Harry and he's kind of Waiting for conversation to be picked up about how that integration needs to change, which is all good. So, really, the only one which is a complete unknown and we're not sure about is going to be this good health naturally who are on WooCommerce. So, we just need to have a discussion with them about Are they going to change or not that I want to, but do we need to look at a supply lens type solution? Um

**[00:13:12] Speaker 2:** We'll pick these up over the coming weeks to have these conversations or so, and then start looking to lock some of these dates in for. when they're going to move over. I'd say some of these will be easy and others. Some of them like former brands, I think it's tomorrow. We've already got a call with those guys anyway. So they will be well, all of these should be aware, but it's just understanding when we can start looking to move them over.

**[00:13:33] Speaker 1:** Just a quick Quick question on this, Darren. It's probably maybe not for your plan, and maybe Tom it's at the board level, but some of these customers already have a leg on Fuse. Is that recorded anywhere? I'm just thinking, like, when the config team gets to it, being aware that the business is already there set up for like wholesale, for example, because if I like Lisa Eldridge, for example, is that. Built for athletes, shackle turn. I think something that's already there for aim, it's just not the setup, so forth.

**[00:14:09] Speaker 3:** I can add comments onto the board, Jack, for those who take not a tag, but Stereotypically those that do have an existing fuse interface for manual CSV would be completely off book from their system. So it would just be the existing config is retained and then any any new connector put in place for the integrated elements. But I can add some degree of tag or something on each one if that helps.

**[00:14:32] Speaker 1:** Yeah, I was just thinking like so you don't accidentally set up another host interface, for example. It it I guess there's like two different playbook paths. There's creating a customer from net new and then there's a creating a customer that already exists. It just needs to be configured, right? So

**[00:14:54] Speaker 2:** No, that's cool. And I think I can't remember again where it's tomorrow or or actually tomorrow is Thursday, so I think it is tomorrow that this API meeting we've got. And again, we we probably just need to have a couple of sessions on that, just just focusing on these customers that are going to be a bit more complex and are potentially going to have to do more work their side than just sort of downloading an app in Shopify. So but we can pick that up offline tomorrow on that sort of API call.

**[00:15:22] Speaker 2:** Any call outs on this?

**[00:15:26] Speaker 2:** Excellent, okay, I'll stop sharing. Um James Tom from a sort of customer piece other than Indus or anything to call out this week?

**[00:15:37] Speaker 3:** I wouldn't say from my standpoint massively. Only thing I think is for Those clients penciled in for week commencing the fourth is more so just to wait until we got comms and contact back from those clients to progress the ones we haven't already started. So I know academically gifted and sister co is just waiting a couple of bits and ticket wise to enable them for the final couple of test cases. But Just need them to be engaged or get some degree of confirmation back from CAMS. I don't know what you think, James. Yeah, we've only had a confirmation back from Dr. Sam so far, the ones that have been contacted. So yeah, I agree with Tom.

**[00:16:18] Speaker 2:** No, that's cool. So I'll book that follow up call for next week'cause I'm just conscious if we don't speak to them again before Excuse me, last week of the month, we're not going to hear from until the middle of December after the Black Friday madness. And yeah, I'm going to send an email out to everyone on that group. Later today, just in terms of by that meeting, I don't want to be s sitting there in the same place we were this week, you know what I mean? By that stage I want their engagement and and to have locked in a date, to be honest with you. Um just so then we can start moving on to the next bunch.

**[00:16:50] Speaker 2:** let's see how it goes. So I know Victoria's contacts all her customers. I've seen Luke reaching out to a few of his as well. And like I say, James, there has been a little bit of feedback from Doctor Sands, which was good and they seem engaged and ready. So it might just be a case of, you know, we we have to go back to them and say, okay, that's brilliant. Let's plan the move for this date and then just look in the Tuesday or the Wednesday that week. Yeah, so I went one of the one of the last ones on the plan, aren't they? Turn down a little bit, so not nearly anyone's come back. Yeah, no, indeed, indeed, indeed. But no, look, we will get, as I say, we'll keep pushing them. And then, as I say, we're probably one or two messages away from telling you moving this date. If you haven't installed the app by this date, then we won't be importing your orders. And I'm sure then all of a sudden they'll start doing whatever we need them to do.

**[00:17:39] Speaker 2:** Cool, excellent. Any call outs, any questions from anyone?

**[00:17:47] Speaker 4:** Our time in um I came in a bit late, so I obviously saw the comp with HNB, I think Victoria is doing all the comms. Are they one of the ones where they're getting them to download the dev store and support us with testing? I'm sure I saw that on the comms. Yeah, they they created Dev Store. But they didn't set they don't have any products, they don't have any ship methods or anything set up in there, so it's basically like a blank canvas. Wasn't that the reason we were just gonna like because I don't mean they're that big or complex right what we've got today. Isn't that right? In HMB, I don't think they're quite a straightforward account. Wasn't that going to be one of the ones where we would like? do our Shopify to kind of mimic what they got and then they don't need to do all of that.

**[00:18:30] Speaker 2:** We're giving them an option. If they don't want to, then they don't have to, but likewise I think there's a number on the list such as academically gifted, Lisa Eldridge, etcetera, who are a hundred percent are being engaged and actually want to do the testing. So if she doesn't want to then yeah, but then it's kind of on her. So if something doesn't go to pla as planned, then obviously, you know, it's not just case you told me this would be fine sort of thing. It's like, well, we gave you the option to test and you declined.

**[00:18:41] Room 1:** Mm-hmm.

**[00:18:52] Speaker 4:** Yeah, because didn't she come back and say I haven't got any time? which is what we thought everyone's gonna say.

**[00:18:57] Speaker 2:** Yeah, yeah, she she she did, so again, it's just a case for us now going back, so that's fine. If you haven't got the time, we can go live without, but you know, this is going to be your window to carry out any testing you might want to do.

**[00:19:07] Speaker 4:** Okay. So are we actually just so I'm clear? Are we actually going out to these customers saying, you know, as a first standpoint. Are we getting them to test first and download all the dev store? We're offering that. Okay.

**[00:19:25] Speaker 4:** All right.

**[00:19:29] Speaker 4:** I just want to be clear then, because I just want to be clear, like. Who's deciding the tip over point like to when we are going to go and do it ourselves then?

**[00:19:41] Speaker 4:** I I thought we'd already like agreed this, like where possible, we weren't gonna go to the problem of like even bothering to get them to do all the death.

**[00:19:51] Speaker 4:** And now it seems we are, but I want to know like, what's the window then for when we're deciding? I know They're not playing ball, they're not replying. We now need to pivot and do it. Like, what is that mechanism to do that?

**[00:20:03] Speaker 2:** We'll give them two weeks from this week. So we had a catch up from the cams and that's why we're keen to get all the conversations taking place,'cause like I said, last week in November, probably for two weeks of December, you're just not going to hear anything from them, which is why we're keen to reach out to these January customers. So a few of them already come back, which is good to say. Dr. Sam seemed fully engaged, and they are ones that I would expect them to want to do a bit of test, especially as they're changing the tag logic in their system to match what we're going to do. And they seem fine with that, which is great. But I just think with that, you know, it probably makes sense to do it. But there will be some. Vitality is probably a classic example where they won't do anything because we just tell them, you're moving on this date. You need to download the app.

**[00:20:26] Room 1:** Okay. Okay.

**[00:20:34] Room 1:** Yeah.

**[00:20:38] Speaker 2:** But we kind of left it with Sarah and the Cams on Monday, I think it was. We had a call with them that, What we don't see is how much of a fight are we in with these customers at the moment, because if James or Tom is suddenly went, we're stopping this, we don't know whether we're adding fuel to the fire and you know going to end up a customer leaving. So they they know how forceful to be with these customers, driven by what we suggest behind the scenes.

**[00:21:00] Speaker 4:** I'm not against it, by the way, but I feel like before we were just left to us to like steer everything. If they're now on board, the cams and they're assessing like... Yeah, yeah. the level of like severity or whatever's going on to make the calls and can push and support us. Great. Absolutely. I just didn't want to be in a position where we're all sitting around. in January, February and being like oh we're never going to meet the target date and it's because no one's responded to us.

**[00:21:22] Speaker 2:** No, no, no. But there there there'll be other reasons why we don't hit the date as we all know. But yeah, it w it won't be due to that. That's cool.

**[00:21:30] Speaker 4:** time with that then.

**[00:21:32] Speaker 2:** Excellent. All right. Uh anything else from anyone else?

**[00:21:40] Speaker 2:** Alright, thank you all very much. We'll keep you posted on these accounts and um yeah, catch up with you all next week. Chisel. Let's see. What?

