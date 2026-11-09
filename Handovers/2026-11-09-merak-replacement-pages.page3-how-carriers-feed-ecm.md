ECM receives carrier events by three routes: polling connectors, webhooks and SFTP files. All three publish to one topic, `raw_tracking.v1`. They differ in who starts the exchange, how an event is matched to a shipment, what is deduplicated and what each message carries. This page sets out how each route feeds ECM, where they differ, and which route each of the 12 carriers in `carrier-playground` uses.

Carrier proxies are not a route. They serve Selector for labels, cancels and manifests. The one link is Amazon Logistics, whose polling connector calls the Amazon proxy. Volumes cover the 15 days to 6 Nov 2026. The requirements that follow from ECM's failures are on [Tracking Events and Webhooks: What v1 Needs](https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/351502339/1.+Architecture+Design). The path of one shipment is on [Shipment Journey Through ECM](https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/354975746/Shipment+Journey+Through+ECM).

## In short

- **Polling does almost all the work.** It brought about 5.44M of about 6.25M events, from about 142M carrier calls. Webhooks brought about 215k, all from Royal Mail. Files brought about 54k.
- **The routes do not produce the same message.** Webhook services leave `rawData` empty. `rawData` is optional on the topic, and whether each connector fills it is not confirmed.
- **Nothing deduplicates across routes.** Each route dedupes on its own, so a carrier that is polled and also sends webhooks feeds the topic twice.
- **The 12 mocked carriers produce about 9% of events.** Evri, DHL Parcel UK, DPD Local and DPD, none of which is mocked, produce about 89%.

## How each route feeds ECM

| | Polling connectors | Webhooks | SFTP files |
| --- | --- | --- | --- |
| **Who starts it** | A connector asks the carrier's API about each due parcel | The carrier sends `POST /tracking` to a Cloud Run service | `file-ingestion-ftp-proxy` polls the carrier's SFTP every 20 minutes and publishes `file_tracking.v1` |
| **What is tracked** | GFS decides. `tracking-core` fills `active-parcels` from `shipments.v2.identified` for every carrier, unless the contract is on the `untracked` list. A parcel expires after 90 days | The carrier decides what it sends. Evri sends about 25% of its volume today | The carrier's file decides |
| **How an event meets its shipment** | The parcel was chosen from `active-parcels`, so it is already matched | The service matches carrier plus consignment number, then parcel. Unmatched events wait in Mongo for up to 90 days | `tracking-file-processor` matches each row against `shipments.v2.identified` |
| **Carrier credentials and auth** | The connector holds them. Most use one GFS account in a SealedSecret. DPD, DPD Local, Panther and FedEx fetch per-contract credentials from `carrier-credentials-manager` | Evri sends an API key header. InPost signs the body (HMAC). Royal Mail uses an OAuth client-credentials token, checked as a JWT | `[??]` |
| **Deduplication** | `response-publisher` dedupes against stored events on date plus status code | Local to each service | `[??]` |
| **What the message carries** | A parcel block, dates, status code and description. Optional: signatory, location, depot, delivery window, raw carrier payload | The same shape, with `rawData` empty and a `carrierIdV2` attribute | `[??]` |
| **When it fails** | No retry and no dead-letter queue. The parcel is picked again next cycle. There is no rate limit or backoff. Only DPD and DPD Local pause a contract after a credential error | The service publishes to an interim topic and then acknowledges. The depth of the dead-letter topics is not known | 12.4k processing errors were logged. A retry job later published 7.0k of them |
| **Volume (15 days)** | About 5.44M events from about 142M calls. About 7M calls failed | Royal Mail about 215k published. Evri about 561k received and 0 published | About 54k by the processor's count, 61k on the topic |
| **Delay** | Set per carrier by `TargetPollingMinutes` in prod etcd. No repo holds the values | `[??]` | 20-minute poll, then `[??]` |

## Where the routes differ in what ECM gets

- **Who chooses what is tracked.** For polling, GFS chooses the parcels and asks for them. For webhooks and files, the carrier chooses what to send, and ECM holds or drops what it cannot match.
- **The raw carrier payload.** The topic's `rawData` is optional. The webhook services leave it empty. A consumer that needs the carrier's own words for an event cannot rely on it.
- **Cost grows differently.** Polling cost follows parcels still being asked about: about 26 calls for each new event. Where a connector's DELIVERED state is on, delivered parcels keep being polled. Amazon re-polled 2.6M of them. Webhook cost follows events.
- **Dedupe stops at the route.** Consumers dedupe on the event `id` alone, and each publisher mints its own. The same scan from a connector and a webhook lands twice. See requirement 2 on [What v1 Needs](https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/351502339/1.+Architecture+Design).
- **Moving a carrier between routes is a manual cutover.** A webhook in shadow mode records events but publishes none, and turning publish on does not backfill. Evri's plan has five steps: Evri enables webhooks for all GFS customers, GFS reconciles the account IDs Evri sends, the team reviews the mapping, publish goes on, and both routes run for about 2 hours before the connectors are switched off. Evri's terms forbid running both for long.

## The 12 mocked carriers, by route

| Carrier | Route today | Events (15 days) | Note |
| --- | --- | --- | --- |
| Amazon Logistics | Polling, through the Amazon proxy | 226,991 | The only carrier whose polling uses a proxy. A push handler, `gfs-amazon-push-handler`, is deployed and idle |
| Royal Mail | Webhook only | 215,319 | About 21k events never matched a shipment |
| UPS | Polling | 105,720 | |
| BJS | SFTP files | 15,706 | |
| DPD Europe | SFTP files (DPD NL) | 9,730 | DPD DE has a feed set up and sent no files |
| Coll8 | SFTP files | 3,929 | |
| OCS | SFTP files | 1,409 | |
| InPost | Polling | 305 | The webhook is not deployed, and its pull request is open |
| FedEx | Polling | 21 | |
| Exelot | SFTP feed set up | 0 | No files arrived |
| Amazon SFP | `[??]` | `[??]` | Slipway publishes these shipments straight to `fb.shipments.v1`. No page says how their tracking arrives |
| Veho | None | 0 | Tracking webhooks are planned (CID-347). Nothing is built |

These carriers add up to about 579k events, about 9% of the total. The four largest sources are not mocked:

| Carrier | Route today | Events (15 days) |
| --- | --- | --- |
| Evri | Polling. The webhook runs in shadow | 2,301,636 |
| DHL Parcel UK | Polling | 1,485,343 |
| DPD Local | Polling | 1,008,906 |
| DPD | Polling | 752,850 |

Together they add up to about 5.55M events, about 89% of the total. No webhook plan exists for DHL Parcel UK, DPD Local, DPD or UPS.

## Questions this leaves for Merak

- Which route will each Merak carrier use? UPS and FedEx are polled today, and Veho's webhooks are planned.
- Will every Merak event carry the raw carrier payload, whichever route it came by?
- Where will deduplication across routes happen?

## Not confirmed yet

- The prod etcd values: polling interval, batch size and which states each connector polls.
- Whether each polling connector fills `rawData`.
- How file tracking authenticates, deduplicates and times its events.
- Webhook delivery delay, and the depth of the webhook dead-letter topics.
- How Amazon SFP shipments are tracked.
- What is on the `untracked` list.

## Sources

- **Polling:** `tracking-core` at `c081108`. The page [Polling Connectors](https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/353697880/Polling+Connectors).
- **Webhooks:** `tracking-webhooks` at `9777dd4`. The page [Tracking Webhook Services](https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/353533985/Tracking+Webhook+Services).
- **Files:** `tracking-file-processor` at `e6da4bf`.
- **Per-carrier events and routes:** the page [Carrier Ingress Services](https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/353206337/Carrier+Ingress+Services). Mocked carriers: the `ilg-merak/carrier-playground` `apps/` folder at `d98fd9b`.
- **Dedupe across routes, ordering and cost:** the vault explainer on ECM's event world. Figures are from Datadog, 15 days to 6 Nov 2026.
