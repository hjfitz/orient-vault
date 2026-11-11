This group answers four delivery questions. Which carriers does GFS use? How is each label made? How much does each carrier carry? How does carrier data come back? The most useful fact is that most volume never touches a carrier proxy. Selector draws most labels from templates in its own database and tells the carrier about the shipment later, in a file. The two biggest carriers, DPD Local and DHL Parcel UK, work this way. The pages say the estimate is 51 to 68k shipments a week each.

Tags (CONFIRMED, STATED, INFERRED, UNKNOWN) appear where the source research gives one. Volumes cover 23 Oct to 7 Nov 2026 (UTC, 15 days) unless a line says otherwise.

## What is in this group

| Page | The question it answers | State |
| --- | --- | --- |
| [Carriers and Volumes](https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/353566754) | Which carriers does GFS ship with, how is each label made, and roughly how much does each carry a week? | Live |
| [Carrier Integration Methods](https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/353697842) | Which methods carry data to and from carriers (REST, XML, SOAP, files, webhooks), who sends each, and when? | Live |
| [Carrier Proxies and Labelling](https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/353697822) | What is a carrier proxy, why do proxies exist, and which ones run in production? | Live |
| [Carrier Integration Uses](https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/353206310) | What are the integrations used for beyond printing a label, and which uses are live? | Live |
| [How Carriers Feed ECM](https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/355074111) | Which route (polling, webhook or file) does each carrier's tracking take into ECM, and how do the routes differ? | Published draft, unverified |

## What we know

- Selector handles about 270k shipments a week, at about 1.19 parcels per shipment (Sep 2026). The peak week, in Dec 2025, was about 589k.
- Ten carriers have proxies. Royal Mail (about 13.8k labels a week) and UPS (about 2.8k) carry nearly all proxy traffic.
- Proxies exist so that carrier changes and credentials live in one place. About 1,000 Selector sites are registered, and a new Selector build reaches each by hand or by staged download.
- Six methods are in use. Most volume goes by file: a central service sends each template carrier a pre-advice file over plain FTP after upload.
- Tracking comes back by three routes to one topic, `raw_tracking.v1`. About 6.29M events arrived: polling about 6.01M, the Royal Mail webhook about 218k and files about 62k.
- Evri, DHL Parcel UK, DPD Local and DPD produced about 5.59M events (88.8%). The nine carriers that `carrier-playground` mocks produced about 587k (9.3%).
- Proxies are not in the event flow. Selector calls them for labels, cancels and manifests. The one link is the Amazon polling connector, which polls through the Amazon proxy.
- Evri's webhook runs in shadow: about 563k events received and none published. The pages say no webhook plan exists for DHL Parcel UK, DPD Local, DPD, Amazon or UPS.

## Where to start

1. Carriers and Volumes, for who carries what.
2. Carrier Integration Methods, for how data moves.
3. Carrier Proxies and Labelling, for the proxies behind labels.
4. Carrier Integration Uses, for what else the integrations do and which uses are live.
5. How Carriers Feed ECM, for how tracking comes back.

## Not confirmed yet

- **Calls against polls.** The pages cite about 142M carrier calls, and the Polling Connectors table sums to about 114M. Nobody has reconciled them. They may be different measures.
- **DPD Europe proxy.** Logs show 21 failures in 15 days. The proxy's own metric shows about 710 requests (about 330 a week) with 5% errors. Whether these are real labels is UNKNOWN.
- **Live pre-advice jobs.** Which V4-Server-IE jobs run, for which carriers and to which hosts, lives in central-database rows that nobody has read. How DPD (Parceline) is pre-advised is also open.
- **Nightline.** The Selector Interface page names Nightline. Four pages name only Nightfreight. They are two carriers, so those pages cover one.
- **Amazon SFP tracking.** No page says how tracking arrives for these shipments. Slipway publishes them straight to `fb.shipments.v1`.
- **Owed correction, How Carriers Feed ECM.** Its "12 mocked carriers" row counts 12 rows, but Amazon SFP is unresolved, and Veho and Exelot sent nothing.
- **Owed correction, How Carriers Feed ECM.** It says polling has "no retry and no dead-letter queue". That holds for polling. The inbound `shipments.v2.identified` subscription has a dead-letter topic after 10 attempts.
- **Owed correction, How Carriers Feed ECM.** It says "a parcel expires after 90 days". The expiry resets on each new event, by carrier and status bucket, and the 90 is not confirmed.

## Related groups

- [Tracking: How GFS Follows a Parcel](https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/357597186) covers what happens to a parcel once it is shipped.
- [Proof of Delivery](https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/357236740) covers the signatures and photos fetched from carriers on request.
- [ECM Platform: How a Shipment Moves Through It](https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/357662721) covers how a shipment's information moves after Selector creates it.
- [1. Research into Existing Services](https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/351502339) is the research root.
