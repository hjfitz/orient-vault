**[00:00:00] Room 1:** I sorry. I thought, ah, my father told me before.

**[00:00:06] Room 2:** Um so yeah. I always forget to start it and then I wonder why now you should be fine. Can you just do that word for word again?

**[00:00:24] Room 1:** No no that's cool. Alright cool. The next uh topic we're going to just move on to is boundaries. So data arrives from a customer system. Where would you check the data and what happens when it is wrong? Well, this is all the data. The data validation type. So, where would you check it? At what boundary? At what point would you check it? And what would you do if the data?

**[00:00:51] Room 3:** So the use case is related to

**[00:00:56] Room 4:** To the curious when you are okay. So It depends what sort of data we have. I I can classify them into two parts. One of them is the tracking data and the other one is the real data which is like the status of the delivery or the customer

**[00:01:06] Speaker 1:** Yeah.

**[00:01:20] Room 1:** Information. So yeah, I'll make it work. I'll make it simple. Because it's a little bit of a vague question. Okay, sure. So, think about an API where a client is calling us with a payload. Okay. There's lots of data in the payload.

**[00:01:35] Room 2:** Our idea is then to book that parcel, grant the parcel, and return a status that says, yes, we're good to go, and here's our basics.

**[00:01:37] Speaker 1:** Yeah.

**[00:01:44] Speaker 1:** Yeah.

**[00:01:45] Room 1:** for encoded later for you to just let Box. So I think about it from a navigator point of view, if you know what we'll just give you some context to make.

**[00:01:54] Room 2:** Yeah yeah so

**[00:01:55] Room 4:** So uh the the e the end uh the other end is just an API or yeah a PR for example the precarious API. So uh in that case, please quote me Tamum when the application needs going to update some sort of data while uh the person who's delivering the parcel. So in in that case, if something wrong with data, Uh so In that case we we really just need to know How did we detect the data is more Uh But then if Uh We we we have two two uh HTTPS status codes. One of them is When Um the server. Let's say database is now receiving five hundred Uh sort of uh Yeah. If it's related to uh really good data, it's four hundred uh four hundred um Uh uh range of uh HTTP status scope. So again, I'm sorry about really not exactly graph the question.

**[00:03:21] Room 1:** The question is when you have data coming from clients, not from a client, a customer to client, and we do whatever with that data we have, where would If that data was incorrect, where would you do the validations? Okay. And how would you handle it if that touches incorrect?

**[00:03:43] Room 3:** Okay, okay, exactly. So

**[00:03:46] Room 4:** Let's He got it. Uh scenario for that. For example, a customer had a parcel and the parcel is

**[00:03:49] Speaker 1:** you

**[00:03:54] Room 4:** Or by limit for example, something like that. Yeah.

**[00:03:57] Speaker 1:** Yeah.

**[00:03:58] Room 4:** So in in that case uh Uh we would have policies for each area that accepting that data. So we are ranking this according to They could be a selector of the one of the carriers. policy. So based on that we validate the data Causing to Okay, yeah. So if it is okay then that's task. If not, we never let go to Kya because why shouldn't we do that? We already have policy, then we send back to the client application that you need to fix those data. forward proceeding. Sending to the

**[00:04:42] Room 3:** Yeah. Okay. Alright. Anything more for yourself than that?

**[00:04:46] Room 5:** No, nothing tied on that one. Okay, cool.

**[00:04:49] Room 1:** Um the next one is shade contracts. Okay. So we have several services and they're depending on one shared type. We have several services different, you know, whether they be APIs or any services run and they all depend on one share type. Um how would you change that with upgrading on the service?

**[00:05:12] Room 4:** So shift shift type. Type. Okay. Okay, so you have one type. Let's say the label. Yeah, dialogue, a message. Okay.

**[00:05:22] Room 1:** structure. How would we change that without breaking all the all the um services that share that one type?

**[00:05:28] Room 4:** Uh In C sharp we are using interface. breaking down we we couldn't distract if we go to the solid We have one of the principles is uh Talking about how to Maze. Uh interfaces to Uh

**[00:05:55] Room 4:** into uh small pieces in case, for example, we have some general data that all of the some of them specific. In that case, we Uh take out those Yeah, um making an interface when we Uh We have and you can go change anything so. Uh We we already have an interface and just change this interface and doesn't affect the OS. Yeah. So if I understood already. Um yeah it depends also actually In SaaS platform also I use another uh approach when You have uh Jason? Data. It it's not good but sometimes it's good when Don't need to uh define a type, so you just have a JSON in a database for contributions, whatever you change, it doesn't matter. Mm. you just update the data. That's it. So but it depends on the use case how you choose Um yeah.

**[00:07:12] Room 2:** Boards. Anything else I don't share?

**[00:07:16] Room 5:** Um I guess if we're thinking just to reframe the question um

**[00:07:23] Room 4:** Think uh I I work upon in in I use a lot of pipeline interfaces as well. Yeah. Could be, yeah.

**[00:07:34] Room 5:** Yeah, I I wonder if like if we look at it through the lens of like an API response, um if we wanted to change that response and there's a few dependents. Um how could we do that without breaking the people that rely on that response type?

**[00:07:50] Room 4:** Okay. So yeah, definitely for that. Uh for any response, what I usually do uh I define and type Uh with Uh message Iraq. Um standards as well. So They Mess it the the era and the uh status. they are always the same. But the data could be anything. In that case I use generic types, for example. Whenever you whatever you pass, that genetic type will be accepted. Yeah. So in that case you don't have any problem.

**[00:08:31] Room 1:** Okay. Um are you familiar with uh solid principles? Yes. Um So just a quick question, maybe a bit of a hint, but

**[00:08:41] Room 2:** Um what does the O win solid stand for? Mm. Uh the old.

**[00:08:49] Room 4:** Let me extract the whole thing. I'm telling you the fine stuff, but that's fine. Single Day. Solid, so.

**[00:09:04] Room 4:** OE's

**[00:09:20] Room 4:** Principle is when

**[00:09:24] Room 4:** We are not modifying. anything we have because this might break something but we are hoping to extend. So we are designing the classes in a way that it's flexible for extension.

**[00:09:38] Room 2:** Okay, all right, cool. Perfect. Alright. The next we've got failures and retries. Okay.

**[00:09:48] Room 1:** Um so a call to a third party API um fails halfway through a batch. So we're processing a batch of transactions and third party fails halfway through that batch. Uh what do we do?

**[00:10:03] Room 4:** Uh so in in that case definitely we would in retry to rematch the data because there there's nothing wrong with the data. We just missed the data maybe halfway. So in that case we would uh retry. So it depends on we we we need to consider the uh right limit of the figure how frequently we can retry.

**[00:10:34] Room 3:** And then I

**[00:10:38] Room 2:** I'm gonna throw a curveball at you, you try it, retry it, and it just carries on failing. It's it seems to be it.

**[00:10:43] Room 4:** So uh th there there should be on the cap what is the max. And again, so based on the Euro type as well, so sometimes if there is a post request, you are passing something like all the IDs wrong, for example. Even if you

**[00:10:52] Speaker 1:** Yeah.

**[00:11:11] Room 4:** do hundred tries still you get the same results. So in that case we are not going to retry this. But if it's a failure from the back end, for example, five hundred or uh four hundred twenty nine, which is federal effect, in that case we show that we we get some data, but something happens in a way. So in that case we we try Yeah, but you need that.

**[00:11:35] Room 5:** Cool. Are there any principles that you can add to that to avoid like a retrace form so that you don't take the service offline? from the solid principle? Uh no, this is like a general principle for um to to retry such that you don't have like fifty concurrent requests going out at the same time.

**[00:12:03] Room 4:** For example? Uh yes. Uh based on what I got for my platform, I have a number of random insulin. So each request or each uh p uh group, let's say, has different nature of uh rate of that request. So b based on the KIA and based on uh our the platform, uh we we will define the uh uh rate limits. But I'm trying to uh have a general, let's say, class that handles that but with different plugins one for each careers or situations let's say yeah so but based on that especially depends on the type of the request I'm sure that there are more than one types of requests we could it could be or it could be based of course based authentic or it could be API key for example or API key so it is different with auth for example so in that case we we define or We will have multiple approach for the breakthrough minutes based on the request.

**[00:13:32] Room 5:** Cool. Is there anything you could do with like a client that's making a request to the server um other than um honouring the four two nine um other than honouring the rate limit to kind of Okay. Uh Avoid knocking the server offline to opt over to um if if I've got like a number of clients making requests um and say I'm like making a request to a very fragile server, which is something that we're doing in my world at the moment. Is there anything you can do as you retry your requests to kind of Um I guess take it easy on the server.

**[00:14:25] Room 4:** Uh okay, for to to avoid the trouble.

**[00:14:29] Room 5:** Yeah. Okay. Okay. Yeah, so if if you're retrying, how can you reduce the load on the server with each retry?

**[00:14:36] Room 4:** Okay, so we we do have good balance, uh that's one thing but uh actually the uh benefit of the rate unit is to Uh reduce the uh Backend requests if it's not necessary. So uh I I I define two types of uh uh rate limiters. So one of them is for let's say uh with n amount of requests and another one is specific to, as I mentioned, an end point or a service or whatever. Yeah. So uh ba based on that I will try to uh uh to order them in a way that the least privileged one goes first. Okay. And uh Also uh I I usually define something like bucket tokens. Yeah. So you uh let's say you can have a a certain amount of requests for that particular end point for example fifty per second for that end point. So if it's if it reaches that point, say uh uh will notify the uh client application. So that that's how I would manage actually the uh uh requests. Because sometimes maybe the request is not digital as well. Yeah. Yeah, so in that case uh uh I need to check or uh actually th th that that's a good point. So sometimes when especially for web hooks we we need to check something like the the the sign as well. So we have to check the uh the request is has valid sign to make that request as well. So Uh yeah, but based on that, so you can limit the request at least from the gateway or to pass to the back end to make more requests when it's not necessary.

**[00:16:49] Room 5:** Cool. That's perfect. Thank you.

**[00:16:51] Room 3:** Okay, look, that's thanks. The next one is in the context of data. Okay. It doesn't really matter if it's documents or relational or whatever. But I'll put

**[00:17:02] Room 1:** The problem is that a query that was fast last month it suddenly got very slow. Okay? We look first. Index of course. Okay.

**[00:17:10] Room 4:** Okay, anything else you would see all of the things that we do and uh

**[00:17:25] Room 4:** So definitely uh the the regulations we we need to uh optimize the query based on the uh relations on different tables. Uh

**[00:17:39] Room 1:** Yeah. Is there anything else that you think could have affected the query to make it go slower? The fast or slow. What caused the slowdown? Is there anything else you would look at that might have been a culprits other than connectors?

**[00:18:04] Room 2:** Sorry, we're gonna talk and we're just keeping that.

**[00:18:10] Room 4:** So Oh so I sometimes I bet um They uh queries into some queries as well, so

**[00:18:22] Room 1:** Yeah, yeah, and yeah, I isolate different parts of the query itself. Okay, um good any more questions on that one? No, nothing on my side. Okay, I think that's quite quite a quick one. We'll we'll move on to production sure. Okay, tell us about the last production you uh problem you found. Um how did you know it was a problem? And what did you do to ch what did you check first to try and solve the problem? Okay. Yeah.

**[00:18:49] Room 4:** Lots of problems because I mainly was uh fixing bugs in the production. Uh the most w uh the the the most difficult ones were uh the environment issues when network and embedded m uh machines were communicating with each other. So uh one of them was the uh the payment, I think was the payment. So there there was an issue that during the payment uh the uh reality was taken and everything is processed, but even for the tax as well, because in in payment you have one process is handling the taxes sending to the government bodies. So uh in that situation

**[00:19:46] Speaker 1:** you

**[00:19:53] Room 4:** we had to find out which company is really making the issue. So the problem was related to one of the pumps where lost the network and couldn't send instructions to complete the payments. Uh so uh that is one of the problems that I have. So what I did actually uh first thing I had to investigate starting from the logs. So based on the logs I had to find out where is uh telling me that the problem is okay. So based on that, yeah, I I was spending lots of time on logs to find out the issue. Um for that one it was really difficult to reproduce because most of the times I um tried to reproduce the issue to find out uh the the issue, but sometimes some issues are not reproduced like that easy. Uh however we had simulators uh but again uh the the main source was blocks to look at this.

**[00:21:13] Room 1:** Um is there any any change you made to the bar? That part of the system, that part of the solution, did you change anything after that production issue?

**[00:21:25] Room 3:** proposed I propose that

**[00:21:28] Room 4:** uh uh because there wasn't uh yeah another problem that we had when every For example, uh a site they have pricing. So suppliers were sending prices in files. So the files were goes to the local sites and the app was picking up in a a certain amount of time. And during that process there is there was those you you have multiple components involved not only the application itself for example the server the network and uh back office as well so all of them were working together so there there wasn't a proper

**[00:22:04] Speaker 1:** Yeah.

**[00:22:21] Room 4:** let's say uh mechanism telling you where was the problem actually. So because you you couldn't trace back, for example in Windows you need to manually check all of the uh event uh logs from the window. Sometimes you have logs from the application itself. So and even for the networks. So I I was uh proposing to have a proper method of it's like a saga if you're familiar with sag saga approach to maintain the state of the workflow. It's really important nowadays how to manage the state of the uh work workflows. So but that one is not only application. It was network operating system and set the hand application, four components at least. Yeah, that helps. So I I was proposing to have a proper uh workflow uh status management to handle that. For me it was taking lots of time to find out. If we have something in place, easily you can find out the only thing.

**[00:23:42] Room 1:** Just a side question. Side quest. Just a side quest. What what's uh what what's your kind of favourite logging tools? What logging tools have you had exposure to when you guys do? Logging. Yeah, for logging. Okay, logging and monitoring. You know, because that's really what we're speaking about.

**[00:24:00] Room 4:** Yeah, absolutely. So So I'm working on.NET C is one of the built-in libraries, but

**[00:24:13] Room 3:** I'll also say a background is a seashore detector.

**[00:24:15] Room 4:** It's really well designed to be integrated with Grafana, for example, if you have a uh community environment. I like Grafana and Lukeys. is inspecting all the API locks easily. They are very well integrated.

**[00:24:32] Room 2:** Okay, cool. In fact, the farm is what I call the Grenada idea, isn't it? Yeah. What do you use actually? We actually, at the moment,

**[00:24:42] Room 1:** we use Data Doc. What's that other one? Splunk. Yeah, Splunk is. Splunk and drive and Logfinet and all that kind of stuff. I mean Logfinet is more than logging provider now.

**[00:24:57] Room 3:** It is painful because you have to. It's not like open source, right? I think there's a free tier of it, but from open source.

**[00:25:05] Room 1:** might be a self-hosted version. I'm not sure.

**[00:25:08] Room 5:** Yeah, I I have no clue. I it's extremely comprehensive though at least. Once you got it you

**[00:25:13] Room 1:** Yeah, I mean from it's not just logging, it's logging, it's metrics, it's monitoring, it's reporting, it's yeah it's it's

**[00:25:22] Room 5:** It's on top of like the whole Open Telebratory stack as well, so it's um yeah. Supposedly possible. Supposedly.

**[00:25:30] Room 1:** Yeah. And once once again I thought the g the guru when it comes to that is is it's it's hoary. He's got some very impressive software boys to use. I only found that now how to do something.

**[00:25:45] Room 2:** Okay, cool. That was just a soft question. Yes, just out of interest.

**[00:25:50] Room 1:** Um only two to go, you know, to hear. Um no, why? Only one to go. Um testing. All right. So the question really is what makes a uh test worth keeping and what do you not test? And I might have touched on this in our first chat that we spoke about, but Kind of thinking about the testing permit and how that comes in. So, what makes a test worth taking, and what are you not tested at all?

**[00:26:20] Room 4:** To be honest, I would test everything because we are human so we can't rely. So testing is to me is like if we have a very good infrastruct uh design, let's say, back end especially. So testing is like a backup verification of any code changes. So that's why I really would like to test everything. Um ho however, for they uh such kind of uh environment, so there there might be different sort of tests. And to end you test, so it it depends on how you test, but Uh definitely uh if I prioritize them, security ones is the most important and in in this situation IOGs uh communication is uh the most important one, how to test that. I'm sure that lots of cases they have sandbox to to test. Uh the yeah, well yeah, I I would say that I'll test everything.

**[00:27:34] Room 1:** Then how how do you how do you separate your your tests up? How would you decide what tests?

**[00:27:40] Room 2:** guys in. What what piece of functionality gets tested and in which test? How how do you delineate between tests? Yeah.

**[00:27:49] Room 4:** But of course. I I like DVD test. This is one of my favourite because it can be uh shared among different parties like testers, developers, product owners. Uh but for some sort of like functional test I would prepare using having unit tests for example when there are lots of calculations. Definitely we we do need a unit test for that to test individual function or individual lines as well. Uh for the communication end to end is really good to have like black boxes to test and expect what you expect.

**[00:28:31] Speaker 1:** Yeah.

**[00:28:35] Speaker 1:** Yeah.

**[00:28:36] Room 4:** Uh for for that one I I would really use B D D to to test that. And if it's possible I would like to have something like real note mocking because sometimes you need to uh mock the uh the the other end. Yeah. Yeah. Charge GPT I think twenty nineteen. We had a chatbot which was dealing with Google APIs for intent detections. So based on the interfaces we defined, we could mock that. But it was really difficult to have a real case at that time. And nowadays easier because all the providers they provide sandbox to test. So okay. So yeah, so something very, very

**[00:29:07] Speaker 1:** Yeah.

**[00:29:31] Room 4:** Makes my heart sore because they don't sorry I interrupted

**[00:29:37] Room 3:** Yeah.

**[00:29:37] Room 4:** Yeah, yeah.

**[00:29:38] Room 3:** So yeah in that case definitely you need to mock that as much as possible to the look library. Yeah some of the biggest some of the biggest providers are the worst at this

**[00:29:48] Room 1:** sandboxes, you know, Amazon. Um you all said that one was the least and it was the worst. Okay, no that's cool. Um and then just uh I don't know if you've got any more on the testing. Um

**[00:30:06] Room 5:** You mentioned security testing. What kind of security testing do you look at? Can really

**[00:30:13] Room 4:** It depends. For example, if we have authentication and authorization, uh for authentication you do really need to test all the uh use cases related to the account. For example, characters, you are entering What sort of accounts can be accepted and password as well. But for permission, one of the hardest ones that I did in Maintel I was trying to have a big test that go i it's not easy to test the permissions. I was trying to simulate that in a test. I had a whole bunch of the permissions at that time and I was trying to b based on the dictionaries in dot net, I I had a very uh massive uh dictionary to hold all of the use cases and against the API uh to test the permissions. And of course there are others Uh when when you have a API key, definitely you need to test that. Again, it depends on the use cases.

**[00:31:31] Room 5:** Yeah. Ah cool. Cool, that's good.

**[00:31:36] Room 1:** Okay, cool. Last side quest question is what's your understanding about contract based testing? If you don't know, that's fine, that's just the same question.

**[00:31:46] Room 2:** Contract bias tests. Um Fine if you have it.

**[00:31:52] Room 4:** N not not really to mind. But based on my understanding, contract is kind of when an API communicating with the third party APIs. Yeah, yeah. So based on the policies and the the uh because definitely they have something to make sure that the multiple request is not going to let's do something harm on the

**[00:32:18] Room 1:** Then so but to be honest I haven't got and you you haven't have you used any frameworks for for defining those contracts Spager, open API.

**[00:32:32] Room 5:** Whatever again, packed. So it's like, yeah, it's a very good way of marking your own homework. It's a very, very opinion of it. That's fine. You know, they can't.

**[00:32:43] Room 1:** Yeah, that's not because it was taken over by OpenAPI, but we use that quite a lot, which is just a standard for defining APIs. But yeah, that's a very good way of. Forcing tests and whatever. All right, I'm going to quickly just create a

**[00:33:01] Room 2:** Yeah, and the next part is also just really simple. Don't worry too much about it. I just got a figure, I can't remember the actual

**[00:33:16] Room 1:** maybe if this was TypeScript or JavaScript.

**[00:33:22] Room 2:** So it's just drama script with the card, the card snippet.

**[00:33:28] Room 5:** Yeah, yeah, just type scripts.

**[00:33:30] Room 2:** Time script or JavaScript.

**[00:33:32] Room 5:** Ah, the language server for TypeScript to pick up, would it?

**[00:33:37] Room 1:** Okay, I also know what time to create a base um

**[00:33:47] Room 4:** Just for your earlier question regarding optimizing queries, so sometimes things can be to your mind. So park partitioning also I was because when you have uh uh all data as well, yeah. So park partitioning is kind of a good uh approach to take just to search for the listening.

**[00:34:09] Room 5:** Good shout. Yeah, I think.

**[00:34:12] Room 4:** I'm sure that sometimes you deal with the uh all bitter gears, so you don't need to go to all the years to find that particular

**[00:34:24] Room 5:** Yeah. Yeah, I think we've got some I I'm pretty sure in the carrier as well Chris, there's some really old orders aren't there. Just kind of sat in an old Mongo store somewhere. Yeah, or if you're doing volumes like, you know, we did a million records over the last week of this sale.

**[00:34:41] Room 1:** But we've got quite a few things that need that need addressing.

**[00:34:50] Room 2:** Sorry, I'm just creating this. So the next part of the exercise, and the last part of phase one, so to speak, is just a quick code read. So I'm just creating a file in There's a very short little piece of uh code over here. I'll just

**[00:35:13] Room 2:** I'm getting to rubbish the dog.

**[00:35:15] Room 1:** People sending me silly questions. Yeah, you're just coded with me. You create a karaki for me. That's fine. I'm going to just And that's it just in Visual Studio Code. Well you can put up a tree here, I guess we could just pop it up on the screen if you want. Sorry? We could pop it up.

**[00:35:40] Room 5:** It's gonna work. Yeah, this live demo of the tech, so we'll see how one goes. Okay, so I should just have to press this button to the back. I think what we can do is we can...

**[00:35:58] Room 1:** If I hit if I pull this off, Chris, we can hit allotte and then okay. I'm just going to see if I can I've got my mouse with me which is terrible. I gotta zoom in, what's the shortcut for zooming in? Control plus. Control plus. I want to use controller and my mouse. Oh that might give us a little bit bigger. Um and you should be able to zoom as well just by Okay. Um so here we have a um pretty standard uh ju just uh very quick um API or sorry, it's a pump sub message handler, this handling order message coming in. Um if you could just read through the code I think the idea about this is just if you spot anything, if you see any bugs, if you see any code smalls, if you see any security issues, it's just to then highlight those. I don't know if there's anything else you want to do. I think it's just.

**[00:37:11] Room 5:** get a taste of Yeah, it's still how you well with a pull request really. So yeah, there's there's no binary tree inversal or anywhere. Yeah.

**[00:37:27] Room 1:** I don't work on that. That's what I think is. Yeah, I don't work with that.

**[00:37:35] Room 3:** There we go. I don't know where the NSA switch NSAs off. But anyway, if you need me for scrolls, tell me my scroll. I'll get from the dump. Yeah.

**[00:37:47] Room 4:** So if you use some control minus to make it smaller, I can see yeah that's fine. There you go, that's it now.

**[00:37:57] Room 1:** Alright, that is the code. There's nothing after that. There's one closing bracket after that, I think. There we go. Okay, okay, okay. Take it to us.

**[00:38:07] Room 2:** I'm not even sure I'm going to do that this property.

**[00:38:13] Room 5:** Yeah, this is um

**[00:38:14] Room 1:** I think this is more fuse adjacent, but for a code, for a quick code check, I just left this the same as the fuse stuff. I mean, I could replace this with the native. Um I thought that's what started. It's like we're you and I are the core back end teams anyway, so it's not like um exactly.

**[00:38:41] Room 1:** If there's any questions or anything, just I do understand you have quite a bit of C-shot background, so I will see.

**[00:38:50] Room 4:** That is

**[00:38:59] Room 2:** You just put me. What if it?

**[00:39:10] Room 2:** So there are a few problems in the code. If you spot it, you just give me a shout.

**[00:39:18] Room 5:** Yeah, it it's probably worth saying that this is the um so when we get a Sorry, I've got some brain problem at the moment. This is the handler for a message that we receive on our own. Yeah, if you're familiar with Google's pub sub then excellent.

**[00:39:38] Room 4:** I never use them. It's not my experience. I haven't used it to be honest before. No, that's okay. Yeah, I I understand the concept. pass some sort of like acknowledge negative acknowledge uh then accordingly handling that or forwarding to the other services. The concept is okay but yeah uh think of it think of it like an idea. Yeah yeah so I'll call Ruby. Yeah.

**[00:40:09] Room 5:** Yeah. I mean a lot of our pub staff pub sub stuff we just use push anyway so we get post requested.

**[00:40:17] Room 1:** So you'll notice that this one isn't really doing much. It's receiving something and then it's calling another API. So if you find any issues on there,

**[00:40:25] Room 4:** Yeah. So first of all, I can see the handling response could be better by not just saying if it's not okay, it could be something very generic. So especially in retry we really do need know to know about the excuse me the HTTP status based on that we can add or update or retry whatever. So that that's one of the points that we really do need to uh handle that and checking the response type based on that when we go.

**[00:41:10] Room 4:** Um yeah, I think we do really need to have a proper looks as well for each steps when we go through to make sh sure that support teams can find out the issue is it. So logs can be improved, for example, when we receive or when we do any actions, we do really need to look at as well. For example, here, here for all of the So starving skate.

**[00:41:45] Room 4:** And again. So yeah, we put a test tree

**[00:41:57] Room 4:** And there there there is no condition to meas when when you reach that to not exceed another step further. Very nice. Um what what the notes?

**[00:42:16] Room 4:** So what would we do if we receive the response back then what should we do with that? So yeah. Maybe it's up to the pubs and soft to handle that, but as I can see we only fetch the data and

**[00:42:39] Room 4:** No, just just as a hint, the last three the last three lines yeah. So yeah, based on that we we do that yes and uh okay, that's fine. So but yeah, I think as as a as a hint, what would happen if the the warehouse is done for a complete hour?

**[00:42:57] Room 1:** if the if the warehouse has gone down. So in other words that We recalling the URL but that warehouse is completely down for one hour. What would happen to our code?

**[00:43:14] Room 4:** Uh so this is an API, right? And you are talking about the warehouse it's done.

**[00:43:24] Room 5:** I think um for context, what we do in my team is we we take orders and we put them in the warehouse management system. Um that's got a REST API, so that's kind of Yeah, what we're simulating here.

**[00:43:37] Room 4:** Yeah. Um so so yeah, this is receiving a message and it's calling the warehouse. Sorry, I'll talk about the warehouse stuff. So the question is uh what what would happen in a code if the warehouse had gone down completely? Power failure? So uh when we make any request we you really need to uh check the status of that request, what happens to that. So in in that case the URL is only pointing to that warehouse, so We are expecting something like the server is down. Yeah. For example. So once the server is down, But based on the uh I I don't know there are some set of policies to retry again, for example. Uh and again there is a uh threshold based if it exceeds that threshold then they throw an error, for example, without retrying it, for example. Yeah.

**[00:44:46] Room 1:** Yeah, no? So you and like yeah, and this kind of sorry if that if that threshold is is it, what would this kind of do? So uh if we have a threshold somewhere just three on round nineteen we've got a three it's gonna tie top. Dude three cars, isn't it? Yeah.

**[00:45:08] Room 4:** We have feed attempts. Okay, so so what's your

**[00:45:12] Room 1:** if the watch is done completely.

**[00:45:17] Room 5:** Or to reframe what happens after three failed requests. Failed three times because based on the cook or whatever. Based on the code, yeah, okay, that's fine. So if we uh

**[00:45:30] Room 4:** the three times, one second, so The uh th this is the end of the file, right? Yeah. So we retry and we are not getting to here, so definitely does nothing this the the loop and straight away going to broker. Okay, that's the point. So Uh yeah, definitely before doing any action in the message broker, let's say in general, so we we should check the what's happening on the based on that the we are'cause if we go something wrong here and put in a message or so, everybody knows that this is working normally. So in that case process goes with multi Response, let's say. So we would prevent that from happening. Yeah, thanks. Okay. So, yeah.

**[00:46:27] Room 2:** And I think that kind of answers my crew as well, doesn't it? Sorry about that, but no, no, no, no, no, no, no, no, no, mix pick the

**[00:46:35] Room 1:** It's it's tucked away, isn't it? It's hidden away and that's fine. That's exactly there's no right or wrong. Right or wrong answer. I mean, obviously, the code itself isn't great. Yeah. Edward's not great, though. Edward Self told the user send out a message saying that water's been created, although actually it hasn't. The point is that.

**[00:46:56] Room 4:** Yeah, it never checks whether it succeeded in one of those calls or not. Yeah, I I I mentioned in the beginning, so we only have the okay, so what happens if it's uh successfully done, for example, two hundred? Hmm so but here he always counted that i it's not done here, so he's succeeded. So in that case go to this step which is really dangerous because we are putting wrong data into the message of the broker.

**[00:47:28] Room 2:** And just quickly what's happening on Mounds 38 and 32 31 and 32.

**[00:47:33] Room 4:** The line here thirty one and thirty two thirty one and thirty two so

**[00:47:42] Room 4:** So

**[00:47:45] Room 4:** save an error

**[00:47:55] Room 4:** Yeah, that is another problem. So silently we let the era go. So we just thank you. Not in the so we we should throw an era. Yeah, absolutely. Yeah.

**[00:48:08] Room 1:** We're swallowing everything. If there's a problem we're just logging in and making as if it never happened.

**[00:48:14] Room 5:** Is we're looking at talking. We've been doing a lot of Go Code to our team recently.

**[00:48:18] Room 1:** Yeah. See, so we we're not we're not pressures on any s specific syntax or language, whatever at all for the job. So they're using Go and we've got we've got all kinds of stuff. Our team also have a lot of old older stuff in C shop. Okay. And Delphi. We

**[00:48:38] Room 4:** We

**[00:48:42] Room 3:** I'll be very very careful about making that in a CMR before you guys working on selector, you know? So, yeah, they will.

**[00:48:54] Room 4:** lots of problem with in memory. I I I faced lots of Issues with the memory management. Especially with the file server. Yeah. Also. Yeah. So our warehouse management system that calls most of our APIs, this isn't this is more kind of fuse related. Yeah. All of our API proxies and they don't normally call it from the system. Is there any like Google services? Bungies. We don't know what the fuck they do, but there's about there's about fifty services and we've no idea what they do.

**[00:49:33] Room 1:** No, we do have Windows services running on... we don't have any bare metal left. Virtualized now in Google. We used to still have a bit of a little data center until about a year ago. Yeah, I think we're all virtualised now. But we do have Windows app servers running. And I get scared every time I look at the services running on there because they've got very important names, but I have no idea what they're doing. Yeah.

**[00:50:00] Room 4:** In my previous work with Maintel, mainly the back office, let's say the main server was Windows servers.

**[00:50:09] Room 3:** Oh no, it's so cool.

**[00:50:11] Room 1:** It's a written property, a design property, and designed extensively and solid and all the rest. You know, at the time they did what they were planning to do, but they had a way to do. But they also

**[00:50:24] Room 4:** Yeah, the problem was when you are dealing with XML objects we had lots uh not let's say compatibilities with the UI. One of the problem was that. And the other problem in maintainer was looking in DB six. It wasn't supporting TLS, so there was a separate application that was securing that.

**[00:50:54] Room 5:** Uh anyone can be v six B V six when you cross for yourself. Alright um anything else from on the code base from you, Harry? Uh I I think that Yeah. Yeah, yeah, and unless you really want to nitpick the code I think we can um I'm happy.

**[00:51:12] Room 1:** Okay, cool. All right. They're the same. I think I think that's that's it's as far as the code is concerned. Um we are do you want to sorry, we've we

**[00:51:22] Room 2:** haven't offered you your luck of coffee or a glass of water or a sprout and have three coffees so you don't want to fairly

**[00:51:32] Room 4:** This one is everyone. I I I ask until I don't eat anything except coffee and water. So definitely I have already coffee so I

**[00:51:43] Room 5:** I think I would perish if I um blasted. Harry's a coffee of fiction by website of how to bright grew the perfect cup of coffee. Oh, I rewrote the website as well.

**[00:51:56] Room 1:** No, that there's a few very serious coffee.

**[00:51:59] Room 5:** Have you gone down the rabbit hole for coffee or are you just probably for the best. I feel I feel like I don't know I'm like I'm a coffee infidel.

**[00:52:15] Room 1:** I I'll have just Don't kind of tissue as well, Brendan. These guys become a flyer coffee, huh?

**[00:52:24] Room 5:** Yeah, we've got we've got scales and we figure out our ratios and brew times and everything.

**[00:52:29] Room 4:** I love coffee and making coffee, that's funny. Oh, cool. I recently bought a poem. Oh, yeah. Like a filtered coffee. It's really amazing. So What do you just put on the fire? So Oh, the locker pot? Yeah, they're really good. Yeah. I didn't know that some sort of kind of was available to make a coffee. Oh no, th th that's like that that's it that's an eye over the rabbit hole, isn't it?

**[00:52:58] Room 5:** Yeah. Yeah, yeah, we've got I think um I think it's safe to say that those of us that have hobbies are quite intense with them here. I think like yeah Chris is the mad scientist.

**[00:53:15] Room 3:** I saw his remote podo. Oh yeah.

**[00:53:20] Room 4:** instruments Robotics. Yeah.

**[00:53:22] Room 1:** Some people just call it a DHD. You're the chef and the coffee affection owner, also the romance artist. Little bit, yeah.

**[00:53:34] Room 5:** Not to your degree, but I double. We've got people that are eight to five.

**[00:53:40] Room 3:** some some yeah Matt and we've got John who's interesting and yeah.

**[00:53:45] Speaker 1:** Yeah.

**[00:53:45] Room 1:** And he has a Ferrari. Oh, he's arrived at work in his sports guard again, not joining. Yeah, yeah, the red car. Yeah, the red car. I think he bought it just to make us work harder. Oh, yeah. We huge hold it. Yeah. One by the car. Yeah. He's only two notches above us. Maybe one day we could own one of those.

**[00:54:08] Room 2:** Ha ha ha. Um okay, so this one, once again, no right or right wrong or right answer.

**[00:54:19] Room 1:** So this is the one where we will hand you the pen with the whiteboard in front of you. So before you start, We're not expecting you to write any code or anything like that, but just um some kind of high level design um design diagram on uh what we propose. Um so the brief is uh we need a public facing our API that our customers can call. When we ask our customers it could be a client application because it's the API of course. Or we might just give it to our customers and they get all down software out to our so we're standing up a RESTful API. And then what it does is um it it reaches out to um our providers. Okay. So let's say one of our carriers. Okay. Um Let's say it's FedEx. And so this is what we're designing is really a proxy that sits in front of. Of that carrier. We don't want our customers calling the carrier directly because there's a lot of complication and a lot of things that have to be mapped properly and things that don't really make much sense to the customer anyway. So this needs to sit in front of it to the proxy. Um so it takes the customers requests. It uh does what it needs to do with it. There might be a little bit of remapping, a bit of validation. Maybe a little bit of data look up in transformation. Um it will then call me being the provider of credits. Um and then depending on what FedEx gives us back. We will return the appropriate results. So using just block diagrams, so lunch code has to do that, just block diagrams. And this is your solution. Completely your solution, Greenfield. We're not telling you what to use, we're not telling you where to host it, we're not telling you How to secure it, it's you know, we're just the customer. We're the user in this case. So you come up with a solution and then we will, you know, and feel free to ask us questions. We are users after all. So yeah, as you go along, we might we might um we might you know do what users do and give you the wrong answers or the incorrect answers or change our answers or change our requirements as we as our users

**[00:56:35] Room 3:** So just you want a big picture of what you are doing, how you gonna design how you're gonna design a solution. You got a blank GCP account or or AWS or Pay natural if you really don't think that's a great you got a blank blank uh

**[00:56:54] Room 1:** You've got a blank design document, you've got a blank checkbook, how are you? What are you going to put in place for us?

**[00:56:59] Room 4:** Yeah. Uh yeah. So Yeah, based upon so do you want me to design then talk about it or yeah absolutely talk talk me through the design as well. So uh

**[00:57:07] Speaker 1:** Yeah.

**[00:57:14] Room 4:** Of course, we have an H8PI here. Scope, sorry, you might need to go to brushes. So let's say we have Customer or public facing with them, for example. Uh can't call it a gateway.

**[00:57:39] Room 4:** But it's not completely API actually because we have multiple things I can call it

**[00:57:54] Room 4:** So this could be gateway

**[00:58:01] Room 4:** APA which is the single point of everything. And of course we have all. I usually design all as a separate service that can be accessible as well because we may have client applications should not be on the local one, but we external bodies. As I designed all the AI can communicate, so these bodies usually provide all of the way of communication, like the communication could be based on both or could be API or whatever. So everything will be Yeah. And Gateway as I mentioned is another uh placing then in Okay, is we can also have Yeah, message kind of humbling message. Depending on Hammer or can be key or score. So here we will see many This is quite a application. Doesn't matter it's web or mobile application, it doesn't matter. They all go to this box. And from here Gateway handles the the routes where it should go. Uh usually I put a number of services behind the API and also uh I don't wanna blindly access all of these services. I uh there there is something called uh zero trust API security I can provide here as well. So in that case Gateway asking us uh a look uh local both for the services. When any request received the gateway strips out the header and it guesses with a long a short term short of the token, something like sixty seconds. And also the gateway is

**[01:00:27] Speaker 1:** Yeah.

**[01:00:31] Room 4:** uh providing not not gateway, so in in the configuration script manager they say providing a list of APIs who can access uh which service inside uh the the platform. Uh then based on the services we selected then we have uh Message broker is all about handling a long process workflow. Then, how I would design we have one interface Like, I can't say worker for example. Usually worker is a term that in work application when you have worker processes like in Google you do have. So the the worker means all about handling all the uh transactions or workflows. So from here we have one single interface because we are dealing with the brokers so the proxy that you mentioned because we are from here the proxy can be seen. here. See that it goes to the other providers. So what I would do uh here I have one interface but I have multiple providers put the interface icon exchange. which one should be selected to that particular request to be handled. For example, LX here. Okay, so no matter if basically we we can have n of providers endpoint. We just uh the new interface um will be plugged into the uh worker and then if I we can make a uh request to the providers. So that is yeah I can say

**[01:03:02] Room 4:** Uh Again, yeah, we we we might have different types of message handling. Could be payment, could be uh tracking, so all of them will be uh handled, yeah. Or could be multiple things at the same time. Yeah. Uh in term of Storage

**[01:03:32] Room 4:** Uh I think the storage we we we will have multiple storage because again for the providers each one of them they have different method of communication. Some of them may be uh dealing with files for example, some of them may be they are workbooks. So I I'll come to that part. For storage which is one of the main main data to me because it not only stores persisted data, but also stores if I classify them into three types. So manipulation

**[01:04:20] Room 4:** Mm-hmm.

**[01:04:25] Room 4:** So it could be Postgres, it could be whatever. And in case of the provider using files, so for that storage you definitely need uh Something like SA Buckets or Google within GCP. I don't know what is called GCS. GCS. Yeah. Everyone knows S3 though, don't they? GC, there's all the sort of coded S3 even. Some kind of

**[01:05:03] Room 5:** blob-based storage, right?

**[01:05:04] Room 4:** Yeah. So we we can have of course multiple of those for in that case is just for maintaining the the not environment like what we have in the or could be something different but to only maintain the uh files that is used by the applications. And the most important one is Uh I can say uh cash Like with this. So this one is very important because especially in your case because you really need to maintain the state of the workflow. For example, you have a pass and you need to check, you communicate with the provider, you need to rely, you have lots of things to do. So if you are using regional database, maybe you will have lots of costs to go to the d previous a database and edge data you should so in that case and slower of course than the cache memory, but we need to have lots of RAM of course to hold those data. So this previous is actually handling those kind of uh problems for us, maintaining the uh real state of the communication, let's say. For example, if we have something broken in in here. Di this rocker actually do need uh this kind of storage to manage this thing. Yeah. So uh i i if I have another one actually uh

**[01:07:02] Room 4:** Because yeah, here is not normal resp for IPR because we deal with different providers. That's why we need to consider all the types of communication. For example, web goods, or

**[01:07:19] Room 3:** Yeah. So Uh

**[01:07:24] Speaker 1:** Yeah.

**[01:07:33] Room 4:** or or or respond. So any any kind of this can be of course here I'm sure that uh we have all our

**[01:07:45] Room 4:** Because maybe you are using WordPress to get status from the provider or maybe you are providing WordPress to give an update from your site to the client applications. So uh yeah, again Here we can but basically providers and the workers design the way that the provider providing that method of communication. So of course here we need lots of consultation. Security, misleading, uh those kind of things we need to to uh design really carefully the workloads or the following uh following is fine when you just define uh repeatedly tasking for uh the status of the and any tracking for example in our case. Uh here, definitely uh we we set a set of uh right length which is really essential in in in in in your in this environment because For a number of reasons, maybe the attacker is trying to to deny service attack against some of the services, mainly for the security reasons uh etc. So we we uh define a number of uh well limit limits in here based on the uh requests and the providers. Uh then the last line again. Uh we have

**[01:09:46] Room 4:** Uh another I would define that. Spaces for the operations like supporting, we wanna explore or find out the root cause of the issue and how to do the environment. So the logs, this kind of sort of things are coming into this problem. So Uh yeah, that is very very general design, but I love this part uh because this will be the challenge on without making lots of changes you can plug in a new provider. So uh that's why uh I I will design this in a way. that I won't probably facing, but uh easy to plug in new providers. Okay, okay.

**[01:10:49] Room 1:** I'm just gonna throw a question away um quickly. Is um right so so that's that that's the solution. Um when we when we kind of came up with the solution or requested the solution we were thinking that we had to You know, two customers, two clients that might be cooling us. Over market suddenly jumped to like 10,000. How would this scale? How would you scale it up to go from two clients to 10,000 clients so that we didn't, you know, that we didn't fall like that? From an infrastructure point of view, how would it?

**[01:11:22] Room 4:** infrastructure definitely uh I would in in that case out of fifty Kubernetes. A Kubernetes uh environment is is really that that's why it's worth for that scalability. So you can scale the uh the endpoints on on your on on its go. So you you don't need to uh scale the server by adding another note. You just need to especially when you are on cloud, so you just need to increase or decrease the number on the

**[01:11:58] Room 2:** Okay, cool. Um any bits on the design?

**[01:12:09] Room 5:** I don't think so. Something might pop to mind. So I'm without sleep today. I've got I've got a a baby.

**[01:12:18] Room 4:** Oh so

**[01:12:21] Room 3:** She's keep she's keeping him on his toes. Okay, now that's fine. I think we

**[01:12:27] Room 2:** I guess for the final f final boost we were called Dan and John in. And you guys can just say hi and they can ask you questions, you can ask them questions and then when we're done we can do a walk around the office and we'll also call John in. Superfinable.

**[01:12:43] Room 1:** Yeah, I think it's just finished up with the SRE team. Oh, it's just finished up with that team. Okay, thank you very much for the for the lizard, um Zero. Um then yeah I'll go fetch John and and Dana quickly. Carry on if you've got any other questions.

**[01:12:55] Room 2:** Etc. etc. Yeah. And then we'll do the meet the team, but and then yeah, we'll let you get. As you get on your way. Sure.

**[01:13:11] Room 5:** I I must say I'm not sick, I've just got a lingering cough. For what it's worth. Um to be honest, these two three days the cold is it's bad, isn't it? Yeah, I hope I hope you've not had to deal with it, but yeah, it kind of

**[01:13:25] Room 4:** My golf is in the s fifth floor so I haven't had a proper resolution yet. My wife always asking when would you do that? I said, Just wait a minute. So that's why the fifth floor is colder than the ground floor. Yeah. So yeah. Yeah.

**[01:13:48] Room 3:** That's why I think Paul before the other guys in the house

**[01:13:53] Room 5:** Ah. So you were at Portsmouth for your PhD? Portsmouth unique. Yeah, so I think we were there at the same time because I was a 2015 through 2019. Really? Yeah. Really small world. So what what did you do? I did like uh just a bachelor's in computer science. Okay. Uh but we probably had like similar lectures like who who was your I had Philip Philip Scott as my uh tutor for my last year but yeah new um Nick and Gareth in the security world.

**[01:14:30] Room 1:** So yeah, Dan is one of the vendors on my integration team. Our candidate. John also did on the question Steve. And you've met another John who's our CTO. So yeah. Have a have a seat and then I guess um Zero can just quickly introduce himself. Then you guys have got any questions? If Zero's got any questions?

**[01:14:55] Room 4:** Yeah, just part of it. Yeah, so I'm a software engineer and help update. So watching in the UK commercial like seven years before that I was doing my PhD. At the same time was so so that yeah, so my my focus mainly on the back end but in block not uh not the so mostly spending my life on the back end using uh C sharp of the core. So recently I was just playing with the new project to get familiar with the new technologies as we face the cloud technologies or services nowadays. So building and implementing a SAS platform just to get familiar with those technologies and Okay. M my my previous role was actually in PDI. PDI is a company who provides services like petrol stations, if you have been in the petrol stations like Shell for example, was one of our customers. Uh in PDI I was uh in a maintenance team where only dealing with the business reproduction. So lots of bucks to solve even better. It's a great way of learning how not to write color from my experience. And that we we have like four hundred developers, I believe, across the company. So that's why they uh suggested to have a maintenance just to avoid the teams who are working with the features, they say.

**[01:16:57] Room 6:** I'm interested how that worked.'Cause we did something very similar at a company we worked at about twenty years ago and we found there was a tendency for the debt teams when time got tight to declare a feature finished, throw it over the fence to the maintenance team who then discovered that these in fact weren't bugs, they just never bothered Rodging. Roiting the cat. Is that something you can?

**[01:17:24] Room 4:** So in the beginning it was really really hard to manage. I remember before the AI of course. Because the maintenance team they are not specific to work on a particular area, so they are working on everything. So a bug could take two weeks on average to be fixed. But after AI uh it changed. So uh the last rule was setting two days for their uh to be fixed. Uh i it it wasn't easy actually to because most of the time we were interfering to the other teams as well. Because it meant to be doing things independently. But Sometimes we really need their help to understand or give us some clues, things like that. But as I said, at AI, once the things changed, so we could fix independently without asking other things to help us. Did did they sort of pass back sort of did you pass back code to other people to fix, or was it a case of the maintenance team did all the changes and then basically it stayed with the maintenance team? Uh I I can give you an example. One of the problems that I had, if it it wasn't related to the team, it was related to the They say product managers actually. So in in that such kind of environment we have multiple customers, it's really not easy to change a thing because it would affect other customers. Maybe it's good for that customer, but the behaviour change is not good for the other customers they will survive, so yesterday was something and today is something else. So that's why you need to make the decision wasn't easy to be made. So that's why we need to have different parties into account. So I I was spending several days to get those parties together to make a decision and agree or something. That that was another issue that we faced actually.

**[01:19:54] Room 1:** Um the obviously there was uh a lot of support and maintenance in in that role. Does any of the the commercial roles that you've you've done um involve new projects or greenfield projects at all? Yeah, of course, yeah. In in main

**[01:20:08] Room 4:** Uh i it That that's why I focused in the last part when you are dealing with multiple providers. Uh uh we uh I designed and uh built a childboard in two thousand nineteen. So the childboard uh was supposed to handle or Response customers. when they ask questions that those questions are known by the system, like what is the price of this? When when you close on, things like that. Uh so that was one of the the the first project that I was working on was a Creek project and designed this way to be flexible For extension, at that time, it was only Google IPIs, but could be anything else in the future if you want to ask.

**[01:21:09] Room 2:** Kinda like what we did on CS is awesome.

**[01:21:13] Room 6:** Yeah, I was gonna say was was that using RAG or were you using contributor augmented generation into the chat box or?

**[01:21:20] Room 4:** Uh just just to do that. Yeah, it's it's it's not like yeah, you need to sometimes you send a request and waiting for the provider to send back. If it was just sending a text and the API is analyzing it and providing the intent detection based on the piece of questions, Well the sound is like a tree arching so

**[01:21:58] Room 3:** Any questions for for Zarek?

**[01:22:00] Room 2:** Was there any questions for the ask?

**[01:22:06] Room 1:** Lunch, where's the cafe? I don't know. Any any questions about kind of it doesn't have to be technically reactive. Yeah. Anything you want, bread. Yeah, yeah.

**[01:22:18] Room 4:** So ha ha how many days in the office? I think it's Two precedents or fifty

**[01:22:24] Room 1:** I think I think the target is two. Kind of we in our team anyway we're quite flexible. We try and kind of come in Tuesdays. It's pointless Dan comes in Monday, I'll come in Tuesday and John Wednesday. So we kind of do try and have but we don't have some of the teams I think have official days. Um at the moment we're kind of trying to I guess work around Tuesday seem to be seem to work well for most people. Yeah, I think most teams are in the yeah I think most teams are in there and it's also it's nice to come in and have a bit of a social and bounce off the other teams and get some questions asked, etcetera. However, that said, if we find we need to do a retrospective or workshop Mm any of that kind of stuff, then we'll pull people in as and when required. Um but yes we're quite flexible on that at the moment.

**[01:23:16] Room 4:** That's true. So, I I I really like socializing.

**[01:23:19] Room 1:** Yeah, I mean these to be hon to be honest, we obviously we have core we have core hours, we have a a core contract that we all work to, we have and all you know, we have all that. But I think like most people and like John will probably agree with me on this, we we're uh Results-driven team, not a clock-driven team. You know, obviously, as long as people don't.

**[01:23:47] Room 2:** And take a mickey, and we're getting results. We're pretty flexible. But we've never needed to tighten up our belts as far as that's concerned, because everyone just gets on and enjoys their work and does that. So it really is about kind of. What you do, and it's just getting stuck in. We have pretty much all gathered, as you can see. We you know, it's not we aim to not get too stressed, right? Yeah, yeah.

**[01:24:16] Room 1:** Yeah, exactly. Give me bus.

**[01:24:19] Room 2:** Some days where stress is good, you know, where we get in and you deal with absolute misbehaviour.

**[01:24:25] Room 3:** The tracking is working, Amazon giving us any labels there. Yeah, things, things there, I get a phone message away. I've managed to break everything. Yeah, John was giving me a lift one day and nothing was working. I answered his cause thing and said, did Chris break? And Claimback and said, you all yes, kind of.

**[01:24:46] Room 4:** So how early did you release? We don't have release cycles. We don't do release cycles.

**[01:24:55] Room 1:** John will get angry with us if we ever put release cycles in. we see a CD output. Yeah, um must be thoroughly tested. Of course, thoroughly reviewed. Um Once it's revealed, we release it. If we break it, we fix it. And that's the way we go. Some of the older things still have release pipelines that need to be approved and etcetera, etc. We tend away from that. We tend towards decent decent testing in CRCD. So we don't we don't I think the closest we come to release cycles is Selector with that old system. I told you that's written in Delphi, etc. And that needs to kind of have releases'cause it gets rolled out both to bare metal and to VMs for the clients. So we can't just like get oh there's clients on this and this clients on that, that we kind of do have releases for that. But we you know, our team kind of get involved with it, but it's mostly handled by external company called Versa NXI. Um they do the selective the Delphi sign stuff.

**[01:25:55] Room 6:** I mean fuse is a good example of the kind of direction we're going of what's you sort of you releasing multiple times a day, aren't you?

**[01:26:02] Room 5:** Yeah. Yeah, especially during peak.

**[01:26:06] Room 1:** Emerged masters of Reese.

**[01:26:07] Room 5:** Yeah, it's um trunk-based deployment as well for what it's worth. So we don't have like staging or dev branches. That's it.

**[01:26:16] Room 2:** We we have started creating some kind of you spoke about sandboxes earlier.

**[01:26:21] Room 1:** And we've for some of our APIs we've needed to have like kind of a neutral place, not to go there, prove it, approve the release push to prod, that's not what it's there for. It's just so we can go there and we can mess around and test things without breaking for some of our some of our providers. don't provide us at daily environments, et cetera, et cetera. So some of the things need to be marked out and worked on on in other ways. But yeah, we don't do the like releases. So yeah. Anything else? Anything from anyone? Bye.

**[01:26:57] Room 3:** Is it just maybe C sharp you've done? No, I've done lots of

**[01:27:02] Room 4:** Uh C language. I did C language in very early language. Yeah, because I I was doing my PhD and my PhD was fully based on security, they say how to detect side channel attack. So at that time I needed to have kernel access, kernel C or C passwords I g there were no choice to select anything else. And Python at that time as well for data analysis at that level. Um Yeah, Type TypeScript I do lots of TypeScript but in React I mean in in PD I I was responsible for the app server was written in Node but this totally depended uh what I was working in React, so it's pure JavaScript, no TypeScript.

**[01:28:01] Room 1:** We we got a mention of first. We we were JavaScript and we kinda the newest stuff was going down into TypeScript. I think We finally convinced John. You're still not happy about it. So, um okay cool. I mean we could take you on a bit of a walk around and show you the offices um and yeah, then we all we'll shall bid you very well. Anyway, before

**[01:28:29] Room 3:** It's too dark and the traffic gets too bad. But thank you for your time. Let's go. So this is the border. I love the title.

**[01:28:39] Room 6:** Yeah, I think we could have got the bigger one though. I think we could have got the bigger one. Yeah, so Vicky was very upset when she saw. Because I saw the one they put in in Warrington and said I want one of those in Newbury and when we sized up the room sorry in South Apton we sized up the room we realized one wasn't going to be enough. They got one of these in Warrington and it fills the entire room. I'm led to believe this is the biggest one they've ever built. It's a lovely piece of wood there.

**[01:29:12] Room 4:** The difference is it's really wider than the

**[01:29:16] Room 6:** This room, when we drew it on paper, this room did not look as big as it is. When Ollie and I stuck our heads in here when they were building it, we both stuck our heads through the door and went, oh, that's a big room.

**[01:29:29] Room 1:** Although that that said, when we have our Town halls in our announcements. Yeah, we've got to be. So, just for IT and Talenton, this room will be full. We could like sack over the top of an answer, there's quite a few of us.

**[01:29:42] Room 5:** There's probably space for bleachers in there, isn't there? Probably space for bleachers in there, isn't there? Yeah, I definitely can.

**[01:29:51] Room 6:** Ah, here we go. We got access to it, so excellent.

**[01:29:55] Room 1:** Oh by the way Dan, if I just sorry, I just noticed behind John there, there's a black flag. Oh I already grabbed one of mine. I already grabbed one of mine. Okay, because I know you you Jan Dan came in and then his brain bursted open and there was waterfall out of the kitchen. So he had to shift. Why not? So he didn't he was in GFord other than before. But the eyes out all fixed now? Yes. So can not attach photographs on the floor.

**[01:30:22] Room 3:** Yeah, I have laminate, so you've got my father and married, so I'm so happy. So yeah. Thank you. Good to be here.

**[01:30:34] Room 4:** Yeah.

**[01:30:37] Room 4:** Yeah, this is the sort of one off that's unofficially drums off or something.

**[01:30:41] Room 6:** It's not my office.

**[01:30:49] Speaker 1:** Yeah.

**[01:30:50] Room 6:** Uh

**[01:30:50] Room 5:** Not bad. Shattered. Not bad. Did you not get much sleep? Yeah, self-imposed though. Oh. Yeah, my my only gym slot now is the evening,'cause mornings are tricky. Oh. Um'cause yeah, it turns out both the baby and the wife need twelve hours of sleep.

**[01:31:14] Room 5:** So it's a redline oneself kind of day. Oh dear. Uh but yeah, good otherwise. Excellent.

**[01:31:25] Room 5:** Did a little six month party for Ori yesterday. Yeah, gave her some apple. She likes apple. She loves apple. Yeah. When you got first Christmas coming up, that's a big one. Yeah, she might be crawling by then, I think. She's showing signs or? Yeah, she's doing a whole bum raise thing yesterday. I got I got a text from Chloe just now. It's like she just had a three-hour nap and must have downloaded a software update rolled back to front for the first time. So yeah. Yeah, she's been going the other way and it's great. And then she's just kind of She'll roll over and then get just completely fucked off that she can't roll back.

**[01:32:09] Room 6:** Yeah. Brilliant. No, we never had crawling with that. That's she never crawled. That went straight from can't be asked to move because somebody will move whatever I want to meet until it all looks like a war.

**[01:32:21] Room 5:** Sit close image when the the other way and she refused to walk because she could crawl faster.

**[01:32:27] Room 6:** Yeah, yeah, yeah, yeah. Both my nephews were like that. Oh, no, wait. Ridiculously fast forwarders, so they just never bothered walking.

**[01:32:36] Room 5:** Yeah, that's volumes.

**[01:32:38] Room 6:** Yeah, Alice just did it out of nowhere. At Christmas actually, she yeah, she wanted something that was the other end of the sofa. And we just went, no, we're not getting it for you. So she just stood up and walked along the safe room. We thought, look, I can do it. Oh shit, that was not what I was expecting. Yeah.

**[01:32:57] Room 5:** Yeah, yeah, good as well. It's just um it's a whole wild ride. Yeah.

**[01:33:07] Room 5:** They say they say the top athletes have girls Um apparently that's like a genuine thing. Oh is it? Yeah. It's like the stress that your body goes through if you're like working hard or like just generally stressed out dest destroys the male sperm. Because of their makeup or something. So yeah. It's the kind of thing you can imagine being right actually. Yeah well apparently it has something to do with like the dinosaurs going extinct as well because they were like temp the eggs were temperature based so like under a certain threshold it was male eggs and over it. Yeah.

**[01:33:41] Room 6:** Yeah, that would make sense because I've heard that I've heard that that um amphibians and reptiles can do that.

**[01:33:47] Room 5:** Yeah. So if you yeah, big meteorite hits obviously doesn't kill the planet but puts it into deep freeze. Yeah, pushes the temperature such that you only get one gender, you kind of break yourself out of existence. Yeah

**[01:34:01] Room 6:** You kind of missed off that realm.

**[01:34:03] Room 5:** Yeah. Interesting.

**[01:34:08] Room 5:** Right. Good interview? Yeah, I think so. As a as a person, good. I think um we managed to model some of the questions but overall got a decent feel for him. Um so yeah, it should be good. I would

**[01:34:26] Room 6:** Did you know we had a man called Matt Shaw? I heard you had Matt Shaw coming in. Yeah, so Ollie and I Ollie had actually already told me and I'd said, Well hire him and I'll hold her into interview just because I like the idea of the chaos it will cause.

**[01:34:38] Room 5:** Well I mean like it was a sure thing because the C V said that he liked board games and weightlifting. Oh Christ, yeah, you definitely don't need to interview. But he's um It's accepted an offer elsewhere. But he was like working on IBM Cloud's Kubernetes offering, so and also worked as like the Google style SRE over there as well. So kind of ticked every box and get him in. Shame. Yeah. But we've got a dude that's a, I think his name's Ed. Worked at Lynn Works, if you're familiar. I know Lynn Works, yeah. Yeah.

**[01:35:22] Room 5:** Yeah, it look it looks like their new offering is like very I think they're fully remote.

**[01:35:30] Room 6:** Yeah, I think they used to be in Chichester'cause I think I visited them a couple of times now and then.

**[01:35:34] Room 5:** Yeah. Um and then it was a platform engineer at Kinetic as well. So looked like he was doing um cloud deployments on ships. Sweet.

**[01:35:47] Room 6:** Yeah, that's gonna be a fun one.

**[01:35:49] Room 5:** Yeah. Who's he? Um he is Friday I think. Oh cool. Yeah, Matt's covering all the first. Remote and then we'll get them in for a bit of a whiteboard setup. The code review is always the interesting part.

**[01:36:11] Room 5:** Yeah, I'm I'm biased towards this man because we went to the same university at the same time. Ah, okay.

**[01:36:18] Room 5:** Ne never crossed paths, but might have

**[01:36:21] Room 6:** It's amazing how that does how that does that how that does. Yeah, I I quite often see what Solan Solomon is now and I'm immediately like, oh so going to a proper not proper university then. Yeah. Right. I'm just going to see how many emails I've missed in the last hour.

**[01:36:40] Room 5:** Enjoy, catch you in a bit.

