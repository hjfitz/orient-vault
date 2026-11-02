**[00:00:02] Speaker 1:** Indeed, indeed. Lee's going to run a few minutes late so so we can possibly make a start without him. I'm the least qualified person to speak about anything to have SFTP or folders, so I'll just sit in the background and uh yeah, observe. So I don't know, Jack or Harry, if you if you want to start off from where we are on on our side and then just try and Agree the approach and the steps forward.

**[00:00:27] Speaker 2:** Yeah, I guess so. Darren sent over a question in terms of I think you guys asked around the routing for the files between returns and goods in Um because obviously they use the des adv message type. Um And Eddie Com's inability to kind of put those into two separate folders. So. I spoke with Harry and the team. Harry's the lead engineer on Fuse, the integration platform we're plugging you guys into. And the challenge from our standpoint is to take them in the same folder. And I'll let Harry add all the technical detail and the explanation behind it. But it essentially would be a substantial rebuild of our integration platform just because of how it segments today. Harry, I don't know if you've got anything additional to add to that.

**[00:01:17] Room 1:** Okay.

**[00:01:20] Room 1:** Nothing outside of what you've mentioned. I mean like, yeah, all of this stuff is pretty well tied to where everything lands and how that kind of travels through views. So it is... Yeah, I guess safe to say it's not a trivial change that can be made here.

**[00:01:36] Speaker 2:** Y your microphone's a bit quiet, mate. Struggled to hear you there. Mm-hmm.

**[00:01:44] Room 1:** Try that. Is that any better?

**[00:01:46] Speaker 2:** Much better.

**[00:01:47] Room 1:** Excellent, yeah. I mean as I was saying, um it is look, you you've covered all of the rather detailed jack like the stuff, it's all pretty tightly coupled to where stuff gets um uploaded to, so it would be a pretty non-trivial like piece of work to go and change that and would like adversely impacts any kind of integration timelines.

**[00:02:08] Room 2:** Yeah.

**[00:02:12] Speaker 2:** Yeah, thanks, Harry. So I think the the purpose of the call really wanted to explore what our options are. Obviously, you know, we can go do a more detailed assessment on the fuse side, but I'm conscious we're on tight deadlines here and Want to get CT live for March. But also exploring the possibility of a way we can solve this problem up the chain, either at the SAP level or at the EDICOM level. Um Get around this problem.

**[00:02:40] Speaker 3:** And So because we we are going to send you uh a lot of ASNs, no, a lot of the sadive type of messages. You are saying that you are not able to

**[00:02:56] Speaker 3:** handle those EDI messages differently. based on the on the content you You need to have uh each one of them in a separate folder.

**[00:03:10] Speaker 2:** A little bit. So if it's a goods in, so if it's an advanced shipping notice, just generally, i.e., you're booking, stocking, or a transfer order along those lines, that can go into the purchase order folder and we ingest that. But because returns go through a different flow in the warehouse management system, even though it is like an ASN, to your point. We land it as a separate type and it goes through a separate flow, which is the separate folder essentially. Which is where the challenge lies for us, is if it lands in that goods in folder, Fuse will treat it as a goods in rather than a return.

**[00:03:46] Speaker 3:** Okay, so it's only for the returns that you need to separate from from the other ones.

**[00:03:53] Speaker 2:** I think returns, it might be good to check work orders as well, if that's dependent on the message type there. I don't have that off the top of my head, sorry, but if that's a similar message type, that may be another one we need to look to split as well.

**[00:04:07] Speaker 3:** Which one? I I didn't understand.

**[00:04:10] Speaker 2:** work orders. So this is like when you need kitting done essentially. Um

**[00:04:22] Speaker 3:** Okay, well uh I can I can talk to Ericom since those messages kitting and returns are they come from a different IDOC from SAP. Maybe if they can do something, I don't know, I will have to talk to them again. to see if those two can be Rooted. So a different folder.

**[00:04:51] Speaker 3:** It should be in case the kitting You in case you need it in a different folder, it should be a different one. So we you we will have three different ones for the same EDI message, which is the salibre.

**[00:05:05] Speaker 2:** Yeah, so in in Fuse we have uh I think the whole folder structure is on an email somewhere, but it's like create underscore work orders, create underscore purchase order, create underscore return goods authorization. Essentially, that's how we do the segmentation. Plus

**[00:05:28] Speaker 3:** Okay. Well, uh let me speak uh with Elikoma about it and I uh I will come back to you on this.

**[00:05:39] Speaker 3:** Yeah, if they can do anything or not, and if they don't We talk again, but

**[00:05:47] Speaker 2:** We can come back to the drawing board. I think an important thing to highlight is the egress leg. So the confirmations coming out, it's the same thing as well. So there's a separate folder for the confirmations. Hopefully that's less of an issue'cause it's just pulling butt. Um In terms of the passing and everything, when the files land, that's the same. So we they we don't need any comm to change the contents of the message or anything like that. It's just purely the landing it in the location. Yeah, really. Uh-huh. Okay.

**[00:06:17] Speaker 3:** And about the connection, uh are you able to connect using AS two or Or VAN or a ban? Instead of SF TB or not?

**[00:06:32] Speaker 3:** because they are having trouble with this uh with with the key and then

**[00:06:33] Room 3:** Yeah, maybe I'll stop checking off a little bit more button

**[00:06:37] Speaker 3:** not not connecting with user and password.

**[00:06:41] Room 1:** Mm.

**[00:06:42] Speaker 2:** Uh Harry, probably a question you could help with on that one.

**[00:06:45] Room 1:** Yeah, I'm afraid it's public key crypto oil for the SFTP service. Um that that's what we offer as much as drink plan advice.

**[00:06:45] Speaker 2:** Tasking.

**[00:06:52] Room 3:** Undersized man. Uh yeah, you're putting a lot of pressure on that. That's catching nicely.

**[00:06:53] Speaker 3:** Okay, so you didn't use AS two for example. You are not able to connect okay.

**[00:07:00] Speaker 3:** Okay, so I will talk to Edicom and we'll come back.

**[00:07:05] Room 3:** box cutter then

**[00:07:07] Speaker 1:** Sure, and yeah, if we need another call, just let me know. I'm more than happy to get something in the dio for us to discuss any sort of matters further.

**[00:07:09] Room 3:** our knowing is more than Yeah with Carpy. Yeah. Just cuts on just so that the wheels run outside that you need to move generally and then you could

**[00:07:15] Speaker 1:** Okay, okay. Thank you. Lovely. All right. Have a good rest of your day. Thank you. Thank you.

**[00:07:19] Room 1:** Excellent. Cheers, guys.

**[00:07:20] Room 3:** I mean you get a cheek.

**[00:07:22] Speaker 1:** Uh-huh.

