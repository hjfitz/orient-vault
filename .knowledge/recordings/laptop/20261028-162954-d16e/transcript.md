**[00:00:00] Speaker 1:** They need to know feedback in terms of. Obviously, this is all fucking data. I'm sending over to you so you can actually refer to it properly. But things, things like: if an import fails,

**[00:00:07] Harry:** Yeah.

**[00:00:12] Speaker 1:** Wherever they get an error, once it's all imported, can they go in and change the data against what's imported before it goes through? Um Can they check that the consignment reference is right? Can they make changes to it? It's basically like a portal for what they've imported. Being able to make changes to that data and then push it on themselves. And then to be able to send. So, like with Selector, with CSS, you can send validate calls, you can send manifest calls.

**[00:00:31] Harry:** Right.

**[00:00:39] Speaker 1:** And via the API. So the ability to do that from that interface, which is really simple. Like the manifest and all that is literally just a fucking API call. It's super simple. So that's that's easy to do.

**[00:00:48] Harry:** Well so does does a sorry, does the portal end up being like a holding area prior to sending stuff off to selector then?

**[00:00:49] Speaker 1:** Um

**[00:00:57] Speaker 1:** Yeah, basically. So it would be like a

**[00:00:59] Harry:** Okay.

**[00:01:00] Speaker 1:** A view for them to be able to import, check that it's actually, and then the validation that Fuse would do against like. Is it in the expected formatting? Have they given it the right info, like all the validation you would expect of an import system?

**[00:01:13] Harry:** Yeah.

**[00:01:13] Speaker 1:** And then Um the ability to change data if required. So like when they double click on the import line, it will be The ability to like change number nine hatchwork on lane to number 10 hatchwork on lane because they mess up on that sort of info all the time and they manually change it.

**[00:01:28] Harry:** Yeah, oh, don't don't fucking get me started on addresses.

**[00:01:33] Speaker 1:** Exactly. So, and then the manifest process is a really simple call. We also set up auto-commit manifests on Selector. So, we would double-edge it. We generally set up an auto-commit because customers always forget to do the manifest, but they also want to have the ability to send that call. But that's all in place already. That's that would literally be a button done.

**[00:01:34] Harry:** Fives. Whoop.

**[00:01:39] Harry:** Okay.

**[00:01:47] Harry:** Yeah.

**[00:01:54] Speaker 1:** Um But you you can block it essentially. Like there's Y your allowances of how you want to validate against whether you know What's been manifested, what hasn't. the import queue to show They manifested the day before a search feature for the for like Ship references. This is all in the information, by the way. I'm not just expecting you to fucking remember. But yeah.

**[00:02:14] Harry:** No, no. I've um

**[00:02:17] Speaker 1:** Don't sound like a particularly complex UI thereafter. It's basically like, Shows everything they've imported, make sure it has validation, make sure they can make changes, and make sure it has a search feature.

**[00:02:30] Harry:** Yeah, interesting. Okay, so they wouldn't want SFTP then, they'd just upload it through the portal.

**[00:02:37] Speaker 1:** Now, this is the caveat of it. They want it to. Think they want the CSVs to go into this automatically from their WMS system, which is via. A file location dropping, which is why SFTP was mentioned, because they would essentially have Manhattan send the CSV to that location, get automatically picked up into this.

**[00:02:48] Harry:** Okay.

**[00:02:58] Speaker 1:** And then At the end of the day, when they click manifest, this would Um, the UI we build will export a CSV of everything that was imported and manifested that day, which they will then handle feeding back into Manhattan.

**[00:03:14] Harry:** Right.

**[00:03:16] Harry:** Interesting. Okay. And it sounds like it might Fuse might not be the right thing to build this on.

**[00:03:25] Speaker 1:** Is it too many changes you reckon?

**[00:03:25] Harry:** Which is fine. Yeah, I I think it's um Like fu fuse is intentionally dumb. Uh It it doesn't it might actually like simplify things to be honest. Um

**[00:03:43] Harry:** like it might simplify things in a really big way.

**[00:03:46] Speaker 1:** Cool. It's sent for all the notes to you, so you can obviously look through.

**[00:03:51] Harry:** Yeah yeah let me

**[00:03:52] Speaker 1:** Once you know that.

**[00:03:54] Harry:** Let me take a look because actually this existing outside of Fuse would make everybody's life a bit easier, especially from a maintainability perspective.

**[00:04:05] Harry:** Uh

**[00:04:06] Speaker 1:** Yeah, I mean, I'm you know. Again, as I've said. Fully happy to how you want to build this. This is kind of why we approached it from the like, oh, well, we know CSV integration really well. We know SFTP. It doesn't sound like that hard to add all the essentially the SOP calls that exist that they need for this are a thing already for us. Um

**[00:04:25] Harry:** Yeah.

**[00:04:25] Speaker 1:** Mm. The complicated part is always the validation of the data coming in. That's the bit that has that selector does really poorly currently. So CSV integration, it like basically, if like one line, if line 14 out of 16 fails, it bricks the whole thing.

**[00:04:41] Harry:** Yeah. Oh, that's that's fine though,'cause we can

**[00:04:43] Speaker 1:** That's what I'm that's the area I'm concerned about and that I don't know how to handle properly. Um

**[00:04:47] Harry:** Yeah, I mean like that for for what it's worth there is a lot of fused tech that I would um use for this anyway. Um it just probably wouldn't sit on like the the data pipeline, which

**[00:05:02] Harry:** Yeah. Not really problematic. Um but like what I'm trying to say is we've got a lot of the bu building blocks and we could just like ship a fucking executable pretty quickly.

**[00:05:14] Speaker 1:** Yeah, yeah. So I Basically, I think they want this web driven.

**[00:05:19] Harry:** Yeah.

**[00:05:19] Speaker 1:** Um as a UI, so nothing nothing locally installed if we can avoid it.

**[00:05:24] Harry:** Yes, that is like on

**[00:05:24] Speaker 1:** Um

**[00:05:26] Speaker 1:** The caveat of this is I don't know how we handle printing because I don't think Dispatch Cloud uses QZ Tray.

**[00:05:30] Harry:** Fucking headphones, sorry mate, I've just... Absolutely. piece of shit like buy and refund go on

**[00:05:35] Speaker 1:** Yeah. Um dispatch card uses QZ Tray to do local printing.

**[00:05:39] Harry:** That was your code is very important to me.

**[00:05:43] Speaker 1:** Um can you hear me? Mm pebba. Can you hear me?

**[00:05:49] Harry:** Okay, there we go. My bad.

**[00:05:51] Speaker 1:** You back?

**[00:05:52] Harry:** Yeah, yeah, I don't know why they're like, they're fine, they're fine, they're fine. And they're like, I don't want to connect to anything more, mate. And they just they just turn off.

**[00:05:55] Speaker 1:** It just ta out.

**[00:05:58] Speaker 1:** Okay. Yeah.

**[00:06:00] Harry:** But they've got like 40% battery on them, so yeah, I don't know what fresh bullshit that is.

**[00:06:03] Speaker 1:** Yeah.

**[00:06:06] Harry:** Um

**[00:06:06] Speaker 1:** And Dispatch card uses QZ train to do Printing.

**[00:06:10] Harry:** Yeah.

**[00:06:10] Speaker 1:** Um That is a like a paid for subscription because the open sources of it, the security on it is dog. So

**[00:06:17] Harry:** Mm.

**[00:06:18] Speaker 1:** there's like a layer on it that you have to pay for. Um

**[00:06:20] Harry:** We've got label printers in the office, right? Do we know what lab uh printers they've got over in wherever?

**[00:06:27] Speaker 1:** No one seems to be able to answer that for me at the moment. I do not, like, conventionally, we would send like Zeppelin EPL for Zebra printers.

**[00:06:28] Harry:** Okay.

**[00:06:35] Speaker 1:** And we have like some systems where we've we did like a conversion process we built for PDF into it, but

**[00:06:40] Harry:** Okay.

**[00:06:41] Speaker 1:** I I do not know and I'll have to find that out. That is

**[00:06:44] Harry:** That's fine'cause we can do like some web USB magic. Um and and yeah, if we've what was the what's the standard format, sorry?

**[00:06:53] Speaker 1:** Uh well the ZPL in EPL is but I think ZPL I Which one's the old one?

**[00:07:02] Speaker 1:** One of them's the old one. I can't remember off the top of my head.

**[00:07:04] Harry:** Well we'll we'll point them we'll point them towards the new ones. The the only reason I ask is like if it's known tech and GFS then like we've got some prior art to work from.

**[00:07:12] Speaker 1:** Yeah, yeah, for sure. Yeah, there's loads of documentation on it, especially on our knowledge system. Like all of that has been covered like tenfold. So if you just

**[00:07:13] Harry:** Mm-mm.

**[00:07:18] Harry:** Brilliant.

**[00:07:19] Speaker 1:** Point it at about that, it will feed you everything we've we know about the ZPL EPL setups. Um, because we built a bunch of image basically, you know, they're image strings that come out of um the API calls, we built a conversion tool to show the labels for that.

**[00:07:31] Harry:** Yeah, they're fucking hucky aren't they?

**[00:07:34] Speaker 1:** Um so uses the same uses the same concept basically. Um

**[00:07:35] Harry:** Yeah.

**[00:07:39] Harry:** Yeah, base 64 encoded images over Hycalls is fucking gnarly, but like everybody in the biz does it.

**[00:07:41] Speaker 1:** Yes, yeah, yeah, yeah.

**[00:07:46] Harry:** So Yeah, it can't can't argue. Um but okay.

**[00:07:50] Speaker 1:** So yeah, that's where we're at at the moment. I do want me to leave this plan with you as is for now to peruse overnight. And then We'll see sort of meet up tomorrow.

**[00:07:59] Harry:** Yeah, send it over'cause I've I've just Yeah, l tou touch base on it tomorrow. What what I'll do is try and get as much as I can into confluence up slash Kira. Um and get plan of attack. But really it sounds like we want an SFTP host where we can do some validation, we want like a UI where we can see the queue and then we want to be able to print stuff.

**[00:08:22] Speaker 1:** Basically.

**[00:08:22] Harry:** And then select will handle like the label creation side of things.

**[00:08:27] Speaker 1:** Yeah, and oh and exporting of a C end of day CSV to put into ma um Manhattan. as well. But that's not, you know, that's the easy bit. Um But yeah, the and selector will have used selector for the manifest process. And there is validation against. selector technically. You can do a validation call with the order. over API. Um it's a little bit like Yeah. In terms of the feedback it can give sometimes. Um, because it's reliant on CSS having the error stored in it. And it sometimes it will just be like error, and that's that's all it will say. So, like, yeah.

**[00:09:02] Harry:** Ha ha ha ha ha. But we can Yeah, we we can build this so that we can do the the validation as much as possible in the application. Um use selector as a last bet.

**[00:09:10] Speaker 1:** Yeah,'cause we have a very strict format of what what should be imported. Um we we know that. And they've only got four requirements. That we will need to figure out in terms of like, and it's in the plan, Pete listed it off in terms of like the cons number relates to something on their end, the ship ref needs to relate to something on their end that, um. And as long as we map those correctly, that will get into Selector on our end. Um it should be all all kosher.

**[00:09:36] Harry:** Cause we we can always like build some hard coding in as well for certain column values or like certain API calls.

**[00:09:43] Speaker 1:** Yeah, the format should be pretty strict and they have the ability to adjust their CSVs. So If it errors. As long as we're providing decent feedback, we don't need them to fix the error in import process. We so they can recreate the CSV and drop it in quite easily, apparently. Um which makes it a little bit simpler um in terms of the air of the back loop. So yeah. Um

**[00:10:09] Harry:** No, that that's excellent then. Um

**[00:10:13] Harry:** Yeah, let me... some design docs together and are you in office tomorrow or do you just wanna hop on a huddle?

**[00:10:21] Speaker 1:** Um I might be able to come down.

**[00:10:24] Harry:** I I'm easy either way, so um what whatever works for you?

**[00:10:26] Speaker 1:** Are you going are you going into office?

**[00:10:28] Harry:** Yeah, th Thursdays and Tuesdays are my normal days, so I'll be in regardless.

**[00:10:32] Speaker 1:** I w I don't know what my wife's doing with she's on a week off at the moment and she's been out with her friends every day, so I don't want to ruin her.

**[00:10:37] Harry:** Fair enough.

**[00:10:40] Speaker 1:** Time off with me being like, I'm taking the car. So if I can, I will.

**[00:10:42] Harry:** I completely get that. Yeah. Just m message me on the day. Yeah, yeah, there's no pressure.

**[00:10:47] Speaker 1:** Yeah, yeah, I mean, if I mean, I mean, I'm not, I'm not, you know, we'll we'll catch up either way. Um But yeah.

**[00:10:55] Harry:** one just flat mate that sounds really good much easier than the original epic uh that I had set up because I was like why don't we clone everything and just remove what they had

**[00:11:05] Speaker 1:** Well they were so genetic like yeah, unfortunately. They just was like saying random stuff. And I was like, I just need a call. Just let me just let me speak to them. So yeah, it it made it way easier. Um And then we'll handle the selector stuff, which should be nice and easy if the validation's done on the front end, to be honest. Um

**[00:11:26] Speaker 1:** All right mate, if you need anything from me, I'm about all evening. Um so feel free because of the time frame we've got especially, feel free to ping me if you get some action and you want us to start on stuff tonight. I'm three.

**[00:11:36] Harry:** Yeah, sounds sounds good. I'm gonna

**[00:11:37] Speaker 1:** Um So I you know, we'll go from there.

**[00:11:40] Harry:** Yeah, I th I think what I'm gonna do is like fucking Um

**[00:11:47] Harry:** What watch this space? Um I've I've been inspired by our earlier chat in the knowledge channel so yeah, should be should be good.

**[00:11:56] Speaker 1:** Do you feel a bit more like comfortable with the route we're going. in terms of in general.

**[00:11:59] Harry:** Yeah. I think like in general and s especially for this project Um yeah, it's all it's all good. just have to I will I will sleep better tonight and we'll go from there.

**[00:12:16] Speaker 1:** Okay. Yeah, I just want to, yeah, I want you to feel comfortable and that I'm not going to fucking torpedo us.

**[00:12:22] Harry:** No, no, I I'm sure you will. I think like a a big part of this is my fatigue and and the other part is like I've just not worked with you guys before. Um and that that's probably showing

**[00:12:31] Speaker 1:** Yeah. No, I look I wait no. We've appeared at a no-wheel and we're like. Hello, give us access to everything. So, no, I'm fully aware, Make. But I, yeah, this is. This dynamic is how we work. We're pretty

**[00:12:46] Speaker 1:** That's what I think actually did too.

**[00:12:48] Harry:** Yeah.

**[00:12:49] Speaker 1:** We'll get that.

**[00:12:50] Harry:** It'd be good. Right. I'm gonna go kick off some plant stuff and I will update you as I go.

**[00:12:56] Speaker 1:** Sounds good, man. In a bit.

**[00:12:57] Harry:** Take care of it.

