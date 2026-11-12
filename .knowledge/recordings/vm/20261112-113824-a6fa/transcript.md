**[00:00:00] Speaker 1:** Yeah.

**[00:00:00] Speaker 2:** everything is minimum four weeks discovery the guy said. Take their existing file now that they do manually to automatically transfer it onto an SFTP. But then the guy, the guy, was it Ryan Oliver? I think it was Ryan, yeah. just going on about so many complexities. around it. But I think that's potentially to do with scale as well. Okay.

**[00:00:27] Speaker 3:** Yeah. Yeah. So but there.

**[00:00:31] Speaker 3:** That doesn't blow the solution out of the water, right? They're still happy to use FT SFTP by dragging files across this.

**[00:00:37] Speaker 1:** This is where it went on. So Wilson spoke up and was essentially like, Should we even be looking at this? MVP2 is around the corner. That's API. And that's where the conversation got into the whole. Like moving to API for this solution, which the one we built as a replacement for dispatch allows that. Like we can plug in the API system, like whatever they end up doing. into this as a stopgap basically. So it allows continued use of Selector with the API system in place that they're planning. For now. And then in the short term, they can continue dragging and dropping. It's still quicker than Dispatch Cloud, less clicks. Um and Phil can help us like zone in on where the areas specifically for this customer we can speed up as well. Um And we'll probably it's probably worth his having like an hour or something fits and I think all of us to be honest with Chris as well, is for all of us to basically go through what the customer's doing on this system and do a pseudo run and then just find where we can streamline. And the I think we can get the API system working. Pretty rapidly. I mean, it's working now, right, Pitts, technically? Like, the calls work. We're talking about

**[00:01:45] Speaker 3:** What is that? we're just creating another veneer over the top of Selector again.

**[00:01:51] Speaker 1:** And it's just using the soap calls. But go into so that's already got that.

**[00:01:54] Speaker 3:** That's something Because it creates a pit, right?

**[00:01:57] Speaker 1:** Yeah, it's it's just to work off of the the interface. So you can upload it.

**[00:02:02] Speaker 2:** Things the UI is just going to be working the same way as the way DC is doing it now, isn't it? It's just calling the SOAP API. Yeah.

**[00:02:09] Speaker 3:** Just to my understanding, what you're What's the difference that you're proposing in an API approach. you like for want of a better phrase. Um versus what they're integrating to in the legacy or stepping stone REST API that they're already working on integrating.

**[00:02:29] Speaker 1:** We're not, I'm not saying to change it, that's what I mean. I think that's just the soft interface we've built is just to get them off as dispatch clouds so we have more control over how we're what we need to change and how we're managing it. This is not about getting onto a new

**[00:02:41] Room 1:** It's

**[00:02:43] Speaker 3:** And that's CSV, we're still saying that's CSV based or manual in input of data of some sort via a UI.

**[00:02:51] Speaker 1:** I'm I'm pretty sure we can just with their CSVs as well, we can convert it into the calls that they need. Um

**[00:02:59] Speaker 1:** I the problem is I don't feel you've had the conversations about their direct integration outside of using like an interface. They don't seem like they've done a bunch. Um From the calls, from the questions they're asking you. I guess.

**[00:03:14] Speaker 3:** expecting to have that ready by the end of November.

**[00:03:16] Speaker 1:** Yeah. Which for them is quick.

**[00:03:20] Speaker 2:** And go and go and go out of the API they scheduled it, I think. January.

**[00:03:27] Speaker 3:** Um

**[00:03:29] Speaker 3:** Um I guess I the where I where I'm seeing the value of What you started to create. Yeah. where the API goes either now or in the future with um with Merac.

**[00:03:44] Speaker 3:** There are all whenever we've introduced an API integration into a customer, there's always that, hang on, but what happens if I've got Do a bunch of shipments that aren't going through my WMS or aren't going through my ERP, I still need to be able to type a An ordering or do a manual batch with a CSV? Do you mean there's always those customers? Um For me, that that is where this could ultimately replace dispatch cloud in what we're doing here, but also potentially That's what we use a lot of this patch cloud for more broadly in Oh, well, so whilst it's a pro, you know, we're probably almost treating this as a proof of concept. I do think we can take the learnings of whatever you're creating now forwards into. Into the you know. What we want our labelling and dispatch platform to become in the future, which has to be kind of multimodal in that sense. Um yeah. That's how I'm kind of sort of seeing it color we don't want to be relying on dispatch cloud and As we've seen, it is so painful for customers that are using anything other than a uh channel integration

**[00:04:59] Speaker 3:** So so they were asked, I mean, I know you m early mentioned earlier in the week that you'd be ready to do some form of demo to them today. Which filled me with a little bit of dread. because that's pretty quick. And I'd the other thing, obviously, I've spoken to in the past, once if you say something to them, they kind of latch onto it. And all of a sudden, you're committed to marrying their daughter. A lot of stuff. Um So I'm just under Always just mindful of how much we kind of promise. Well, they see as a promise rather than us seeing as a best endeavor. Do you know what I mean? Yeah. Yeah, yeah. I mean it's yeah the

**[00:05:38] Room 2:** With it. Would it help to show you what we've got, Pete?

**[00:05:39] Speaker 3:** Sorry, going the

**[00:05:42] Speaker 2:** That'd be great, yeah. I think if we can show this this this improvements and The CSV import is a lot quicker and and things like that than what they've got now. And we can say, look, you can drag and drop your CSV file manually rather than the B having to be an SFTP your end. You know, there is then some benefits of potentially them moving to it from DC, quickening up that process. So they do say it takes five minutes at the moment to create the label. I think that's more what they'd have to do, extract out of Raise your eyebrows there, Harry. I know it is. I was a bit like that when they first started saying it, but

**[00:06:16] Room 2:** Yeah.

**[00:06:19] Speaker 2:** That that's not just our end, that's Getting the CSV file out of Manhattan, which is their WMS system, and other things they have to do before they import it in, yeah. Yeah.

**[00:06:30] Speaker 3:** Does they feed that information back to Manhattan as well afterwards? So they'll go back. This is the order number, these are the tracking numbers. Yes.

**[00:06:31] Room 2:** Makes sense.

**[00:06:38] Speaker 2:** Yeah, so there's the kind of shift in extra holding that.

**[00:06:41] Speaker 3:** Part of the journey.

**[00:06:43] Speaker 2:** Yes, they're getting a shipping extract file back out of uh Dispatch Cloud. In a certain format and importing, and they've done it, and they've actually developed an import for that particular format back into back into Manhattan as well.

**[00:06:55] Room 2:** Okay.

**[00:06:58] Speaker 2:** which we would need in this.

**[00:07:00] Room 2:** Yeah, so of

**[00:07:01] Speaker 2:** platform as well.

**[00:07:02] Room 2:** I've kind of built this up I'll work off a screen share. We can kind of chat as we go above. built this with kind of effectively cloning what they do, so like all of the templates are built around um Dispatch Cloud. Uh I don't know if screen sharing works on Teams on this machine. So shout if you've got it. Excellent. Cool. Okay.

**[00:07:20] Speaker 3:** Can see it, yeah.

**[00:07:24] Room 2:** Um so we have this Beachhead demo customer um As you can see we've got like a nice little drag and drop field here. I can drag and drop a CSV um course it won't work during the um demo.

**[00:07:43] Room 2:** And it should import them so you can see that they're in a ready state. We've got a failed order that you can go in and. give it an address, kind of do all of the modification here. All of the CSV format for data in will kind of marry up to what you'd expect with Dispatch Cloud. Um so you can go and like bulk pack or bulk dispatch some things. Um hit dispatch to ready.

**[00:08:14] Room 2:** That will then go out to selector and kind of Do everything appropriately. Um we can either get our labels here or um Hop over to the Humans tab and do like a bulk print or a bulk preview to make sure everything's happy too. Um can export your CSV for Manhattan. There you go. Um I will double check this file type though, Phil, because that's not something I had in had in mind when I was thinking of exports.

**[00:08:42] Speaker 3:** Okay.

**[00:08:50] Speaker 3:** Scott, so does this use the um

**[00:08:54] Speaker 3:** I don't know what the app's called now, that printer app or whatever is called to allow the browser to print to a local QZ trail.

**[00:09:04] Room 2:** Um no, this has a web USB driver, so you you should be able to um Just interface. Thi this is the one thing that we've not tested yet, uh because I don't have a label printer at home. Um although my wife would love it if I bought one, uh'cause she's got a little handheld thing. Um you should so if I pop over to settings for our B ship demo uh customer should be able set up. printer. You can give it a name, give it a format. So ZPL, EPL and PDF. Um we base a driver around like the kind of standard printers that that we've seen around the business. So like theoretically it should work, but we also don't know what they've got on their benches, so it's kind of a kind of a guess. Um main point being they shouldn't need any extra software, it should work directly from the browser.

**[00:09:56] Speaker 2:** Does it matter which powers that will be quite a good win actually as well because I think they were reluctant on installing PQZ trade because of how all their internal security works.

**[00:10:00] Room 2:** Okay.

**[00:10:06] Room 2:** Yeah, it makes sense. Yeah, I I think they're um especially with like some of the Uh Like I know Sony's got some

**[00:10:12] Speaker 3:** W will this work in like edge? I'm not saying I'm pretty sure, for example, they I know that's underlying Chrome, right?

**[00:10:21] Room 2:** Yeah, I th I think anything chrome based is fine. Um I'm actually in Firefox now. Um but yeah, Chrome is generally or Chrome ish, like, you know, Edge or Safari. Um

**[00:10:24] Speaker 3:** Okay.

**[00:10:32] Room 2:** Uh probably the best bets.

**[00:10:35] Room 2:** Um

**[00:10:38] Speaker 3:** I hope they haven't got next. What's it called? I was thinking of the old one. I wanted to say Netscape. But Netscape Navigator.

**[00:10:45] Room 2:** Yeah. Yeah, as long as it's not Internet Explorer that should be fine. Um but we we can manage users for them as well. Um SFTP is a thing. Um and there's an API. It's not quite the stepping stone on Pete as well. So this API is just kind of

**[00:10:46] Speaker 3:** From nineteen ninety six. Yeah.

**[00:11:00] Room 2:** You've got an endpoint with an access key and you just upload your CSV through that instead of like the um API we designed a couple of years ago. So it's it's slightly different, but they can provision access on their end to it instead of us doing the whole rigmarole with API key and that.

**[00:11:05] Speaker 3:** Okay.

**[00:11:17] Speaker 3:** I mean, that sounds amazing. I don't

**[00:11:23] Room 2:** We can also hide the stuff. Yeah.

**[00:11:23] Speaker 3:** from them for now just because I know what they're like and they'll suddenly be

**[00:11:30] Speaker 3:** Yeah.

**[00:11:30] Room 2:** Yeah, I was saying to Wilders that this is making me not miss my time with corporate America. Um back on a well when he used to work with Stephanie enough.

**[00:11:41] Speaker 1:** Never seen people like at CC people in a Teams message like they do. It's insane.

**[00:11:46] Room 2:** Yeah.

**[00:11:47] Speaker 1:** But after every m after every message they C C you again.

**[00:11:50] Room 2:** Yeah. But yeah, we can I I can take that away and

**[00:11:50] Speaker 1:** Yeah, I mean

**[00:11:53] Speaker 3:** I'd almost done installed teams off the back of that those messages.

**[00:11:55] Room 2:** Yeah but yeah, I'll I'll hide the um API key um set up. Part of this, we can keep that running in the background in case they, you know, if there's like, you know, oh, we got massive, massive rush for an API and we can do like the oh, we've worked all weekend for this, like, look how good we are. Um here you go. Um but they'll they'll have like setup steps as well so they can see what needs to happen, what's missing.

**[00:12:21] Speaker 3:** Yeah.

**[00:12:22] Room 2:** Um and then, yeah, PFS accounts can kind of go in and see various customers. We can set up customers and yeah, I can provision us accounts if we want to want to have a look through as well.

**[00:12:35] Speaker 3:** Is this something

**[00:12:38] Speaker 3:** Like how much testing have we done with this kind of

**[00:12:41] Room 2:** Not heaps. Not heaps, I'm afraid. I was going to um chat to Alex because he works quite closely with us on a few stuff.

**[00:12:41] Speaker 3:** and actually printing of labels. Not I

**[00:12:48] Speaker 3:** Yeah.

**[00:12:52] Room 2:** Um Yeah, if we've got other heads that are quite handy to happy to come and like break this as much as possible and just send reams of feedback, I'm absolutely happy to to involve whoever th we think's best.

**[00:13:06] Speaker 3:** Might be, Phil, you were taking a look at it because you're the one that uses the other system and obviously had those conversations. So, at least, even if it's not a funk, you know, like a, you know. Um looking for barcodes, just looking for the flow. If you know of it.

**[00:13:20] Speaker 1:** Yeah. You're going to know what the customer's doing.

**[00:13:22] Speaker 2:** The best out of all of us. Can I can I just ask a couple of questions?

**[00:13:25] Room 2:** Yeah.

**[00:13:27] Speaker 2:** Can we map shipping methods from the CSV file imports?

**[00:13:30] Room 2:** Yes you can.

**[00:13:31] Speaker 2:** So we can.

**[00:13:33] Room 2:** Um Here we go. So we've got shipping methods down here. you should be able to um

**[00:13:42] Room 2:** So I've had this cough for like two weeks now, I was sick like three weeks ago. It's a pain in the ass. Um yeah, shipping methods are a thing. The file layout by default is Dispatch Clouds um and that's for any files in. Um if they want to bring their own file type they can come and make that modification themselves too. Um that's a footgun we'll provide, but yeah, defaults Dispatch Clouds'cause

**[00:14:01] Speaker 2:** That's fine.

**[00:14:06] Room 2:** Uh it's known.

**[00:14:09] Speaker 3:** I think one of the things that they've spoken to them about on the TSV front was

**[00:14:18] Speaker 3:** The way that Dispatch Cloud CSV works is it's Key that product level I think is that each row represents a product within an order.

**[00:14:26] Room 2:** Yeah.

**[00:14:28] Speaker 3:** They I believe, and Phil, you might. Confirm or not, what would be easier for them is if they were able to declare the number of packages.

**[00:14:39] Speaker 2:** I was going to ask this.

**[00:14:40] Speaker 3:** We've done this CSV for so it's These products, but in two boxes. I don't think we need to use to say what's in each box, but.

**[00:14:49] Room 2:** Hmm.

**[00:14:51] Speaker 3:** that's where some a reasonable amount of their time goes in is in kind of then you know if it We're only doing single box orders at the moment. If I had to do, you know B to B, essentially what they're doing through this first customer, they might have an order of 10 boxes.

**[00:15:09] Speaker 3:** They know how many boxes are going to be. out through their WMS. It it's it's a known thing to them. It's not something they work out on the fly as they're, you know, the packers sat at the bench. So they should in theory go up to Tell us how many parcels there are. In a

**[00:15:26] Speaker 3:** I think That is a fundamental change in structure to the CSV file. format, isn't it? very level at that point.

**[00:15:37] Room 2:** Yeah, well I mean that's uh that's the selling point, isn't it? Like if we can tailor it somewhere headphones have just died. Um if we can tailor it to like their workflow, I think it becomes a bit more useful.

**[00:15:52] Room 2:** I hope that's my headphones back in.

**[00:15:56] Speaker 3:** Hopefully you can hear us.

**[00:15:57] Room 2:** Yep, there we are.

**[00:15:57] Speaker 3:** Okay.

**[00:15:58] Room 2:** Yeah, I'm back. Sorry guys.

**[00:16:01] Speaker 3:** Um Well yeah, I guess it yeah, I I think

**[00:16:06] Speaker 3:** That was definitely an area they were interested in. And also, I

**[00:16:11] Speaker 3:** I guess failed. Your comment as well. I think that the initial when we were originally speaking, they wanted to obviously do. domestic US and cross-border to Canada. Then it became too much of a challenge because they weren't sure data and everything else. Yeah.

**[00:16:31] Speaker 3:** Longer term, they would want to probably be able to do cross-border through here as well. So we wouldn't necessarily want to lose. The ability to take in that commodity information that that that That's skew level data. So

**[00:16:48] Speaker 3:** Yeah, I don't know what that ultimately means because we might need to speak to them on today's call, Phil, and just say: look, these are the options we've got ahead of us. Which way do you want to go? rather than us trying to guess.

**[00:17:03] Speaker 2:** Yeah, agreed. Yeah. I I think the I think the abil and I I I didn't know till after the call actually, until I spoke to Ollie, the ability to drag and drop that that CSV file. And it just auto-imports it based on the mapping. I think that I think that is. That could be actually quite beneficial in the conversation. and actually take away the need for actually having to have Any automation there and to automate it onto an SFTP. I think, Ollie, that might be a good one, mightn't it? Yeah, yeah, for sure. Yeah, I think we should need to give it a test as well. Uh can we can we manifest in here like we do on DC or are we just gonna run it on the auto commit? On selector. Um I think it can do

**[00:17:48] Speaker 1:** Commit calls as well. Um Yeah. Tested the theory that it like technically works. It sent for call. Obviously, we haven't had a live account, that's the problem. I confirmed from Adam, I confirmed.

**[00:17:57] Room 2:** Yeah.

**[00:18:01] Speaker 1:** That it's a bit on scan, so we can technically hammer that live prod account for tests as long as I'm just deleting them after.

**[00:18:07] Room 2:** Yeah

**[00:18:08] Speaker 1:** Um So our plan was to do that this after like after the school, essentially, is to is to get some tests done today.

**[00:18:16] Speaker 2:** Can we hold two different references on an order in the system as well? Because that was one question, Pete, around importing the container reference for the order as well, especially if it's the reference and cons reference. So they could use the cons ref for the container ID. for the particular package.

**[00:18:36] Speaker 1:** Yeah, I mean there's there's no limitations on kind of folks. Data when we want to store. It's more we can build to the spec we want now rather than what you're supposed to call. I think the key thing for this if you can test the process as it as like would be best fit. Um we'll make adjustments. according to that so that we can d make the best thing for this customer. What will be there?

**[00:18:57] Speaker 2:** Perfect as well as if we could put the units of measure in centimetres and pounds. But I'm guessing we're probably working on kilograms, aren't we? Or is it already done? Yeah. Oh, I think that'll be that'll be good because they're having to convert it at the moment before. Yeah. Okay, perfect. We discussed that this morning conversion. So they can import the CSV total weights. As pounds, perfect.

**[00:19:21] Speaker 3:** The only thing I was going to mention on just on the demo where you showed us the ship methods, Harry, I don't know if this is a thing probably again.

**[00:19:27] Room 2:** Yeah.

**[00:19:33] Speaker 3:** if we've got a customer with more than one FedEx contract.

**[00:19:39] Speaker 3:** or we need the contract number in the I suppose we don't need that actually, do we? Because actually that mapping is then done in Selector, right? That's just a a label ultimately we're coming up with within within that. That you are, right? is the shipping method.

**[00:19:56] Speaker 3:** What are we par I guess what are we passing to selector off the back of those shipping methods? Are we passing the shipping method or are we passing the carrier contract and service code?

**[00:20:05] Speaker 1:** Uh I think they were offered the root codes. So it's if we

**[00:20:08] Speaker 2:** It's like

**[00:20:10] Speaker 1:** I I believe so. I'll have to double check. But I think we set it up for the root code so we can configure the contract as we see fit. Basically, okay. So we can yeah, you can you can create numerous Cool. Method, you know, shipping mappings. Yeah. Just be per contract sentence. Yeah.

**[00:20:27] Speaker 3:** Sounds good. I mean, it's like, yeah, can't believe you guys have come with that so quickly. It's phenomenal. So.

**[00:20:34] Room 2:** Teamwork. It's um yeah, yeah, a lot of a lot of useful info from Ollie on this one. Um

**[00:20:37] Speaker 1:** Yeah, but a lot of

**[00:20:41] Room 2:** can't be understated.

**[00:20:41] Speaker 2:** That's good. Yeah.

**[00:20:43] Room 2:** Um but

**[00:20:43] Speaker 2:** Can I get access to it?

**[00:20:45] Room 2:** Yeah, absolutely. Um I'll send you some credits after this Phil. Um please, please break it. Um

**[00:20:51] Speaker 2:** I don't want to break it, Harry. Don't touch it. I don't want to break it. I don't want to break it. I know, I know, I know, I don't I know what you mean, yeah. Yeah. Yeah. So we, Ollie, planning on showing this to them on the call at home?

**[00:21:05] Speaker 1:** I mean, that was kind of Pete's choice as to whether we're sorry, Pete. What are you how you do you want us to? Because ideally, we go away. We do a couple of tests against live like within the next hour or so for me and fits. And we proved that it works basically. Yeah, if you get comfortable with it.

**[00:21:27] Speaker 3:** Demos always go wrong because they're demos up and but ultimately if You guys have gotta feel comfortable demoing it.

**[00:21:35] Speaker 1:** I the my m I'm the apprehension I have is more like demoing it in that cool wild questions they're going to come up with and where it leads to, is where I'm more like concerned.

**[00:21:45] Speaker 2:** people in the call as well with different

**[00:21:50] Speaker 1:** Yeah, I think we had a call the other day where it was like Adam, Megan. And one other person. And it was easy because they know their areas of expertise, and it was just a process flow end to end, super simple. For some reason, it all goes out the window when they're getting that big call, and nobody seems to talk like a human being anymore. It's insane.

**[00:22:08] Speaker 3:** Is it worth asking to do the demo?

**[00:22:12] Speaker 1:** I asked for it to be separate. So a select number of people. Yeah. And then unfortunately, they pushed back and were like, oh, but we think this will be a Git Geeter. Basically, went, no, this is where we're doing all the demos and stuff. And I got put in my

**[00:22:26] Speaker 3:** Place by Geither.

**[00:22:27] Speaker 1:** Well I can

**[00:22:27] Speaker 3:** I can I've I've got a call calls that overlap that.

**[00:22:34] Speaker 3:** 'Cause yeah, demo the smaller audience, the better.

**[00:22:36] Speaker 1:** I think to get this sort of bled out into their system.

**[00:22:40] Speaker 3:** I mean, I I I could probably make the first half hour of that call.

**[00:22:46] Speaker 3:** Um by shifting around some other stuff, but It would have to mean we sort of like say that we've got half half an hour to do the demo. to it first. And I can say that to Geeta. and send her an email now. But I would only I'd rather send it. once we're happy that we're going to do a demo.

**[00:23:05] Speaker 3:** Hope you let me know that across the whoever. It can be testing.

**[00:23:10] Speaker 1:** Yeah. Okay to do a test straight after this, essentially. We'll we'll uh pump a call through or do you need more time for the changes I gave you earlier?

**[00:23:19] Room 2:** Let's um let let's get the changes through proper. I'll I'll drop you a note. Um

**[00:23:22] Speaker 3:** Okay, cool.

**[00:23:23] Room 2:** after lunch and then Yeah, we can Go ahead and take a look at that.

**[00:23:26] Speaker 3:** Chris, have you got a printer at home?

**[00:23:30] Speaker 2:** I've got a printer. I do, yeah.

**[00:23:32] Speaker 3:** We can we could even do you. an actual approach to anything.

**[00:23:38] Speaker 2:** Yeah, that's what I was thinking I'd like to do. I've got my power cable, I think, is in my drawer here, but yeah. Yeah, be good to get a test. Mm-hmm.

**[00:23:47] Room 2:** Um

**[00:23:48] Speaker 2:** So

**[00:23:48] Speaker 1:** So as it stands now, I'll wait for Fitz to come back to say that the changes Morning or in and then I'll set up a Hopefully before the call later. Um and we'll do a proper end-to-end test and then we'll We'll manage the conversation in that whether we actually do a demo at that point or whether we book in today we use today to like book in a smaller session with less people. Um yeah good smart. Yeah, and then we'll sort. Play it by here at that point, I guess then. But as long as you three are happy for us for me and fits to move forward with the demo, then we will.

**[00:24:18] Speaker 2:** Is um the the printers, the printer setup. I only saw the screen briefly, sorry. Is the printer associated to a user? Or is it associated to a packing bench I think I saw?

**[00:24:32] Room 2:** It's benches, yeah, so each each customer signed up for this. should have benches set up and then think a user can pick a bench.

**[00:24:44] Speaker 2:** Okay, when did he pick that bench? At what point?

**[00:24:48] Room 2:** Um

**[00:24:48] Speaker 2:** Is or is that or is that assigned to their user profile?

**[00:24:53] Room 2:** Good question. I don't Um have an answer at the moment, but I can what I can do is like Get you get you your credits and if you'll have a hoke about and like make sure that workflow is the intended one because I'm completely unfamiliar with um like the warehouse side of things. Um if that's all right, please.

**[00:25:11] Speaker 2:** That's fine. Yeah, we can have a look at it. Yeah. Yeah. Sorry, I didn't mean to put you on the stop on the spot, Ben. Sorry.

**[00:25:14] Room 2:** No, no, no, no. Good question. Um yeah, like the the usability of it would be key when it

**[00:25:19] Speaker 2:** I'm just trying to think how they'll think when we say, look, you don't need QZ tray, it will auto-print. But I think they're then going to start asking, well, we've got multiple benches, we've got multiple users that work on those benches, how is it all configured? So if we've got that understanding, then that's obviously going to be.

**[00:25:33] Room 2:** Yeah.

**[00:25:35] Speaker 1:** Be fair to Pitts, the printing is the thing I lose about their setup, I knew literally nothing. So I've gave him like generic stuff to Try and set up against. Well, I'm manually printing.

**[00:25:45] Room 2:** Yeah, I mean like the

**[00:25:46] Speaker 2:** Reminding any princing now from a pop-up in DC because it was. too complicated to get QZ train store because of all the security they've got. And inst and installing third party software.

**[00:25:56] Room 2:** Yeah.

**[00:25:59] Room 2:** I mean ab absolute worst case we can do that.

**[00:26:00] Speaker 2:** Like they have like they have like they have with us installing Selector, for example.

**[00:26:08] Speaker 1:** And it looks like the time change on the server worked as well. Um Nothing's broken yet. So I am monitoring, but it seems to not have a major impact by just switching the server time.

**[00:26:22] Speaker 1:** One thing that only that came up, Chris.

**[00:26:24] Speaker 2:** get they wouldn't get errors around dispatch date is not today. Yeah, that should it should resolve it. Yeah. Perfect. Yeah. Okay.

**[00:26:35] Speaker 3:** Question that came up, Chris, this isn't related to this necessarily. I just wasn't sure if it was on your radar or not, if they had been brought up to you, but. on the scat on the the FedEx tracking. We get the tracking data through from FedEx and put it into PCN. coming up with UK localised time. the scan time as the the scan event times.

**[00:26:59] Speaker 3:** Which to me sounds weird'cause I would have expected FedEx's API to provide back and a non kind of time zone. implemented time if that makes or maybe it is maybe it has the time zone and we're converting it to UK as part of the ingestion. So we so We should be taking the local time.

**[00:27:23] Speaker 3:** Um what we we've yeah. We had this problem several times when we've done like tracking before, and like every time a new set of devs comes in, they They do it the way that should be, you know, from a logical perspective, I suppose, should be, it should work. But in essence, you almost need to ignore the time zone and just take almost. Treat it as a string to the point of like, this is the time it was scanned.

**[00:27:51] Speaker 3:** Because the the event happened locally. It shouldn't matter where you're presenting that that. time and day okay

**[00:27:59] Speaker 2:** I'll ask John what the what the sitch is on the on the scan times and see what he says. Petros lost his hair over this one.

**[00:28:12] Speaker 2:** Sorry.

**[00:28:17] Speaker 2:** Um Pete, can I grab you for two seconds about Talos? Yeah, fine. Happy to stay on the call, yeah. Cheers, yeah, Hanky. Alright looks yeah, it looks looks really good, guys. Yeah, it looks really good, guys. Thank you.

**[00:28:28] Room 2:** Cheers, guys.

**[00:28:29] Speaker 2:** Yeah,

**[00:28:31] Room 2:** Right.

