**[00:00:01] Speaker 1:** Yeah, I know.

**[00:00:05] Harry:** Testing out my granola clone. Do you guys mind if I? transcribe this.

**[00:00:11] Speaker 1:** Go for it, mate.

**[00:00:12] Harry:** Cool,'cause I transcribe stand up regardless.

**[00:00:14] Speaker 1:** I expect a massive watermark to show on your camera, say transcribe it right now.

**[00:00:19] Harry:** How how's that?

**[00:00:22] Harry:** If it if it stops moving, I'll pause it.

**[00:00:22] Speaker 1:** That's the one thing I do like about Grin.

**[00:00:24] Harry:** Yeah.

**[00:00:25] Speaker 1:** It's so annoying they don't have that on Windows because on Mac you can force it for users that it shows that they're transcribing. But

**[00:00:32] Harry:** Yeah, I mean I could probably build this in. Um Matt, for what's oh no Jack, I didn't tell you about this either. I built Granola except it's all local into um Orient.

**[00:00:44] Speaker 1:** course she did.

**[00:00:45] Harry:** Um but it's great'cause it hooks into the Orient Calendar integration.

**[00:00:49] Speaker 2:** Yeah, that's fine.

**[00:00:52] Speaker 1:** To share some of these skill packs so I can start baking it into my daybook as well. Because I've got Granola linked into my daybook, but it doesn't work the best.

**[00:00:56] Harry:** Yeah.

**[00:01:00] Speaker 1:** I also don't granola a lot, which is probably the problem.

**[00:01:00] Harry:** Far enough.

**[00:01:03] Speaker 2:** Yeah.

**[00:01:04] Speaker 3:** I'll have to show you um uh mocks at some point. Which is my version of your orient, which is Matt's operational command system.

**[00:01:10] Harry:** Brilliant.

**[00:01:15] Speaker 2:** Yeah. Oh, I thought you had M-O-X. I feel like that's more catchy. Mox. Like Moxy Phone or Roxyphones, whatever it is. Roxy Bingo.

**[00:01:25] Speaker 3:** Maybe rebuilding Palantir locally.

**[00:01:31] Harry:** Excellent. Um stock sink.

**[00:01:34] Speaker 1:** Cool. Yes, poor mind.

**[00:01:35] Harry:** So probably don't need line-based stuff because it's just stock. Same as uh

**[00:01:42] Speaker 3:** This is what?

**[00:01:43] Harry:** The other thing.

**[00:01:45] Speaker 3:** Yeah.

**[00:01:46] Harry:** Uh yeah, that's really handy. Stock adjustment.

**[00:01:46] Speaker 3:** That's kind of where

**[00:01:50] Speaker 3:** That's kind of where I was going as as well. I mean, I don't know whether uh line based mapping gives us uh any kind of future flexibility for for kitting. Uh it kind of feels like overkill at this point.

**[00:02:03] Harry:** Yeah. Yeah, I think if we Uh I even think kits would be fine to be fair.

**[00:02:10] Harry:** Um

**[00:02:10] Speaker 1:** Yeah, I think as long as it denotes what's a kit and not a kit, they I mean, the customer tends to just take the skew and the amount and reconcile that against their ERP. Plus over over SFTP, the only customer that's actually intended to use that at the moment.

**[00:02:26] Speaker 2:** Although we may want to introduce this for other customers in the future to remove the need for snap reporting. is Charlotte Tilburg. So the question is, is what format it needs to get in that you can pass it into Edifact and send it across, which is. obviously what you've built, Harry, from that side. So.

**[00:02:44] Harry:** Yeah. I mean, like, we we'll be able to As this lands, we'll be able to do chasing chasing L C S V and Edifact on the SF TP.

**[00:02:52] Speaker 2:** Nice. Yeah. Yeah,'cause it'll be good to move away from snap specific reporting for those kind of things'cause

**[00:02:55] Harry:** Mm.

**[00:03:00] Speaker 2:** Thank you.

**[00:03:01] Speaker 1:** North Star and multi-WMS and not being reliant on the WMS producing good reports.

**[00:03:07] Speaker 3:** if it produces any at all.

**[00:03:09] Harry:** Yeah.

**[00:03:09] Speaker 3:** You could have just stopped with it be nice to move away from snack.

**[00:03:14] Speaker 1:** Yeah.

**[00:03:15] Harry:** Yeah, that's that's good. So, um I I think stock sync stuff otherwise there's a few transaction history things that we still need to bake in before we can make the announcement. Um and

**[00:03:25] Speaker 1:** 'Kay.

**[00:03:28] Harry:** gonna go at a head and assume we've got like some Observability, some kind of metrics, but it might be good to have a distinct dashboard for it.

**[00:03:39] Speaker 3:** Yeah, I don't know what has been put into the uh snap adapter or the uh yeah uh snap WMS seam side of things. Uh, I can take a pass over that. Um, there is

**[00:03:49] Harry:** Leave that one with me, bud. Um I'm operating outside of the sprint for this sprint.

**[00:03:51] Speaker 3:** Okay.

**[00:03:55] Harry:** Um

**[00:03:55] Speaker 3:** He's got

**[00:03:57] Harry:** Yeah.

**[00:03:59] Speaker 3:** The I think the another thing on the stock sync side, Harry, you me and Schuster talked about this on Thursday. You, me, and You Jack, or sorry, me, Jack, and Sheesa talked about it on Friday. And that was where we have multiple Shopify connectors against the same Shopify store instance. I think we've landed on the fact that because they are separate businesses, they are, you know, they are separate.

**[00:04:26] Speaker 3:** Oh, they set up separate businesses in Fuse, that is unlikely to be a problem. There was some concern about whether or not having multiple connectors for the same business would trigger. Um

**[00:04:41] Speaker 3:** unintended kind of duplicate mutations if one connector Or multiple connectors receive the same kind of stock sync message. But I think, based on what we talked about on Friday, Jack, it's going to be a non-issue. Um I don't know why I I

**[00:04:56] Speaker 1:** It probably still worth validating, but I think the assumption being made was the same business ID was being used across the Poland and UK, but they're separate business IDs, which means they'll have separate stock pools within SNAP. probably still worth checking just as a valid validity, but I think it

**[00:05:12] Speaker 3:** Yeah. Yeah. That can probably be a uh part of the the QA exercise for that, I would imagine.

**[00:05:19] Harry:** Excellent.

**[00:05:20] Speaker 1:** Sweet. Um only other one for me is snap load testing.

**[00:05:26] Harry:** Yes, uh not not kick that off, but they have I think we're still waiting on some testing to wrap up. we can perform some load testing. Um but Snap have a different host with the same

**[00:05:36] Speaker 1:** Okay, cool.

**[00:05:40] Harry:** a hardware spec as prod.

**[00:05:43] Harry:** So yeah, should be able to simulate everything against that. They seem pretty confident and their um their infra boys seemed... Um switched on.

**[00:05:53] Speaker 1:** It's normally their uh client services team that is the problem. When you get to the actual right people, sometimes they're pretty helpful.

**[00:05:57] Harry:** Hehehehe

**[00:06:01] Harry:** Yeah, yeah, I spoke to a bloke called Jake and he he got it all, so

**[00:06:06] Speaker 2:** No, it's

**[00:06:06] Harry:** Yeah, so so very good. Um yeah.

**[00:06:08] Speaker 2:** Peach shake.

**[00:06:09] Harry:** I I'll let you know how that goes. We'll get some up in Confluence.

**[00:06:13] Speaker 1:** Sounds good.

**[00:06:15] Harry:** Yeah, cool.

**[00:06:19] Harry:** Goes into it.

**[00:06:21] Speaker 1:** Have a nice day, guys. Catch you in a little bit.

**[00:06:22] Harry:** Nice one. Cheers folks, take care. Bye.

**[00:06:23] Speaker 1:** Yeah.

