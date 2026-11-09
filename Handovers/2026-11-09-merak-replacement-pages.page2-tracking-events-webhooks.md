ECM moves carrier scans between its own services. It was never built as a contract for outsiders, and ten properties that a v1 tracking API and webhook set needs are missing or inconsistent. This page lists each one with the evidence, and what v1 should do instead.

These are requirements drawn from ECM's failures. The product decisions stay with Stef and the Merak team. [Idea: Developer promise](https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/349110455/Idea+Developer+promise+Sandbox+Webhooks+Change+Radar) already asks for per-parcel ordering, a delivery log and replay as v1 items. This page adds the ECM evidence. Volumes cover the 15 days to 6 Nov 2026. The path of one event is on [Shipment Journey Through ECM](https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/354975746/Shipment+Journey+Through+ECM).

## In short

- **ECM attaches GFS meaning to a scan in many places,** so its services disagree. v1 should attach it once.
- **Each ECM publisher mints its own event ID,** so one scan from two sources is two events. v1 needs one event key that survives re-polls and source changes.
- **ECM keeps nothing to replay and drops failed customer webhooks.** v1 needs a log and replay from the start, because adding them later changes the API.

## Ten requirements

| # | v1 should | ECM today |
| --- | --- | --- |
| 1 | **Build one canonical event, once.** Carry the GFS status, the carrier's raw code and the mapping version. Define "delivered" in one place | `tracking-core` and six consumers each map every carrier code through their own sidecar and config copy: about 18.8M lookups a week for 3.0M events. `tracking-core` publishes the raw event and throws its own mapping away. Consumers freeze the mapping at ingest. "Delivered" has at least six definitions |
| 2 | **Key every event on the shipment, parcel, carrier and carrier event ID.** When the carrier gives no event ID, use its time plus code. Set the key before any publisher adds its own | Each publisher mints an ObjectId: `tracking-core`, both webhooks and the file processor. Downstream stores key on that ID, so one scan from two sources is stored twice. `tracking-core` dedupes only on date plus code, and only its own events |
| 3 | **Number events per parcel.** The platform assigns a sequence number, so a status never goes backwards and a gap shows | No `raw_tracking.v1` publisher sets an ordering key. Events from one poll publish in parallel across three replicas. Subscribers handle up to 1,000 messages at once. Only `shipment_tracking_status.v2` is ordered, and by shipment |
| 4 | **Carry two times:** the carrier's time with its offset, and the platform's received time | Carrier times arrive three ways: London wall time (Evri connector), UTC (Evri webhook), and local time stamped as UTC (Royal Mail webhook, an hour out in summer by inference). The customer webhook labels the received time `carrierEventTime` |
| 5 | **Handle scans that arrive before the shipment is known.** Hold them, release them in order, and set a limit and an alert | The Royal Mail webhook parks about 146k of 343k events. Evri keeps them up to 90 days, and one barcode prefix logged 2,901 retries and no matches in 7 days. The deriver drops such an event and acks it. Claims and the update service store a stub. The POD service loses a BJS event that beats the shipment |
| 6 | **Make unmapped codes visible.** Give them an explicit state and an alert, and let a mapping fix reprocess history | An unmapped code becomes "IN TRANSIT" with the carrier's own text, shown to customers and sent in webhooks. Only the CCIS sidecar reports unmapped codes, to BigQuery: 11.6k |
| 7 | **Treat a manual event like any other.** Same fields, same key, with a source marker | The synthetic `GFS_DELIVERED_EVENT` has no ID and no company. CCIS, ICIS and `connect-hooks` drop it. Claims and the update service store it under a string shipment ID |
| 8 | **Deliver customer webhooks at least once.** Retry with backoff, add an idempotency key, sign the body, and send the event ID, sequence, GFS status, carrier code, times and, when known, ETA, location and signatory | `connect-hooks` sent 407k webhooks (6.5% of events). A failed POST is logged and dropped. Nothing dedupes, so a double-fed event is a double call. The body has no event ID, status code, ETA, location or signatory. A shared-secret header authenticates the call. Nothing signs the body |
| 9 | **Keep events for a stated period and replay them from a cursor,** through the API: "everything since my last event" | No topic or subscription keeps acked messages. The dead-letter register stores dead letters but cannot replay them. `tracking-core` keeps an active parcel for 90 days after its last new event. A rebuilt consumer would map under today's config |
| 10 | **Name one source per carrier and parcel.** Switch it with a defined overlap and backfill. Pause polling when a carrier rejects the account | When the Evri webhook goes live beside the connector, both publish. The webhook skips `tracking-core`'s post-delivery filter and ETA, and a shadow run cannot backfill. DHL Parcel UK rejects about 15 contracts, and about 850 parcels are re-polled about 70 times a day with no pause. The error is generic |

## What ECM does well

- **It keeps the carrier's raw code and text beside the derived status.** Every event carries both.
- **It separates exceptions from status.** The deriver rates each shipment RED, AMBER or GREEN, and splits customer-visible events from all events.
- **It ranks "delivered" first** and reports part-delivered when only some parcels are delivered.
- **It orders status messages by shipment** on `shipment_tracking_status.v2`.

One thing to avoid: `tracking-core` attaches the full raw carrier response to every event, so it reaches every subscriber. That response may hold personal data.

## Decisions for the product owner

- **Ordering scope.** Per parcel or per shipment.
- **Retention and replay.** How long events are kept, and how far back a replay can reach.
- **Replay target.** Whether a replay re-sends to the customer's endpoint or only to the log.
- **Unmapped events.** Whether customers see them.
- **Manual events.** How a manual delivery appears to customers.

## Not covered

What each carrier sends. The UK carriers' formats are on [Carrier Tracking and Proof of Delivery](https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/353206337/Carrier+Tracking+and+Proof+of+Delivery). Carriers outside today's estate are not researched.

## Sources

- **ECM code:** `tracking-core`, `tracking-file-processor`, the two tracking webhooks, `shipment-tracking-status-deriver`, CCIS, ICIS, claims, `shipment-update-service` and `connect-hooks`.
- **Pages:** [Tracking Webhook Services](https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/353533985/Tracking+Webhook+Services), [Polling Connectors](https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/353697880/Polling+Connectors) and [Carrier Tracking and Proof of Delivery](https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/353206337/Carrier+Tracking+and+Proof+of+Delivery).
- **Volumes:** Datadog application metrics.
