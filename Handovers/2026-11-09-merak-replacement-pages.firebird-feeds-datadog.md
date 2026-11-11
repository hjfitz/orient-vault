---
tags: [handover, research-copy, ecm, firebird, datadog]
date: 2026-11-11
tldr: "Research copy: Datadog evidence on which Firebird change feed is live (Transfer Service live, legacy publisher no data), window 2026-10-23 to 2026-11-07 UTC."
status: research-copy
---
This is a research copy of the findings file `firebird-feeds-datadog.md`, kept in the vault so it can be found and cited. The synthesis is [[Systems/ecm/firebird-change-feed]]. Where the two differ, the synthesis note is the later reading. Read-only, Datadog only. No credentials are kept.

# Firebird feeds in Datadog: which publisher is live

Run date: 2026-11-11 (read-only, Datadog MCP only).
Window W: 2026-10-23 00:00 to 2026-11-07 00:00 UTC (15 days).
Window L24h: the 24 hours to the run time (about 2026-11-10 11:00 to 2026-11-11 11:05 UTC).
Note: the Datadog MCP reported that the client uses the deprecated endpoint `/api/unstable/mcp-server/mcp`. It should move to `/v1/mcp` on the same host. Requests were served normally.

## Bottom line

- Feed A, the Firebird Transfer Service (`gfs.firebird_transfer_service`), is live and busy in production. Host `MEDC-APP-01-P`, environment `production`. Its latest log line is 2026-11-11T11:04:25Z.
- Feed B (GFSPublisher / legacy publisher / GCPUploadService): NO-DATA. There is no metric under any of the searched names, and no indexed log under any of the searched service names, in the last 7 days. This is absence from Datadog. It is not proof the process is stopped, because it may simply not report to Datadog.
- The data does not directly say which service produces `fb.shipments.v1`. No Pub/Sub topic metric was found for `fb.*` topics (NO-DATA). The indirect evidence is in the cross-check section. It points the same way as Feed A but does not prove it.

## 1. Metric discovery

Method: `v1.MetricsApi.listMetrics({q})` and `v2.MetricsApi.listTagsByMetricName`. These cover metrics active in roughly the last 30 days.

| Search term | Result |
|---|---|
| firebird / firebird_transfer / transfer_service | 140 names, all under `gfs.firebird_transfer_service.*` and `gfs.firebird_transfer_service_weblogins.*` (plus other `firebird` names such as `gfs.legacy_invoice_translator.firebird.*` and `gfs.monitor_firebird.*`) |
| legacy-publisher, legacy_publisher, gfs.legacy-publisher | 0 names |
| GFSPublisher, gfspublisher, gfs_publisher | 0 names |
| gcp_upload, upload_2_gcp | 0 names |
| gfs.legacy | 121 names, only three families: `gfs.collections_dispatcher`, `gfs.legacy_invoice_translator`, `gfs.legacy_shipment_update_service`. None is a Firebird-to-Pub/Sub shipments publisher. |
| publish | `gfs.fenghuang.*`, `gfs.gfs_modernizer.published`, `gfs.shipment_identity_service.messages_published`, `gfs.legacy_invoice_translator.pubsub.*` and others. Nothing named for a legacy publisher. |
| uploadsvc | `uploadsvc.*` is the customer file upload service (Cloud Run `gfs-upload-svc-v2-prod-cr`, importer types dpd_trinny, evri_excel, ups). It is not a Firebird publisher and is not Feed B. |

Feed A metric families (names as emitted, including the misspellings `recieved` and `transfered`):

- Counters/rates: `rows_transfered`, `recieved_events`, `recieved_events_aggregated`, `rows_failed`, `rows_dead`, `heartbeat_successes`, `reconnection_attempts`, `reconnection_successes`, `bulkhead_rejections`, `retry_count.{count,avg,max,median,95percentile}`.
- Gauge: `queue_length`.
- Timers (each with `.count/.avg/.max/.median/.95percentile`): `transfer_latency`, `read_transfer_list`, `read_transfer_list.select`, `read_transfer_list.delete`, `get_table_data`, `get_table_data.select`, `insert_into_transfer_list`, `insert_into_dead_letter`, `report_stats`, `report_stats.get_queue_length`.
- A second instance `gfs.firebird_transfer_service_weblogins.*` with the same shape.

Tag keys (from `listTagsByMetricName`):

| Metric | Tag keys |
|---|---|
| `rows_transfered`, `retry_count.count` | application, environment, host, maintainer, service, **table_name** |
| `transfer_latency.*` | the same, with `table_name` values |
| `queue_length`, `recieved_events`, `recieved_events_aggregated`, `read_transfer_list.*` | application, environment, host, maintainer, service (no table tag) |
| `rows_failed`, `rows_dead` | no tags (no data in either window) |
| `weblogins.*` | no `table_name` |

- Only one host and one environment appear: `host:MEDC-APP-01-P`, `environment:production`.
- There is no `topic` tag and no `event_type` tag (insert, update, delete) on any Feed A metric. The event_type share cannot be reported: NO-DATA.
- Metric types per Datadog metadata: `rows_transfered`, `recieved_events`, `retry_count.count` and `read_transfer_list.select.count` are `rate` with a 10 s interval. `queue_length` is a `gauge`. `.as_count()` on a rate converts it back to a count. Treat the totals below as counts as reported through that conversion.

## 2. Feed A totals

All values are production, host MEDC-APP-01-P. Scalar aggregation is `sum` unless stated.

### rows_transfered by table_name

Query (W): `sum:gfs.firebird_transfer_service.rows_transfered{*} by {table_name}.as_count()` with aggregator sum, from 2026-10-23T00:00Z to 2026-11-07T00:00Z.
Query (L24h): the same over the last 24 hours.

| table_name | W (15 days) | L24h |
|---|---:|---:|
| shipments | 1,715,298 | 155,655 |
| ship_pieces | 692,234 | 66,814 |
| ship_shipper | 460,049 | 45,459 |
| v_ships_comments | 91,872 | 8,335 |
| v_collections | 32,026 | 2,629 |
| v_tickets | 24,855 | 2,498 |
| gfs_international_export_5 | 3,575 | 360 |
| shipment_extra | 1,759 | 138 |
| cust_contract_services | 458 | 19 |
| cust_contracts | 420 | 4 |
| carrier_scan_codes | 94 | 0 |
| products | 43 | 0 |
| cust_sites | 37 | 1 |
| customers | 36 | 0 |
| carriers | 36 | 2 |
| ship_status | 15 | 0 |
| **Total** | **3,022,807** | **281,914** |

Shipments are 56.7 per cent of rows transferred in W (1,715,298 of 3,022,807). Shipments plus ship_pieces are 79.6 per cent.

### Other Feed A metrics

| Metric (query form `sum:<metric>{*}.as_count()` unless stated) | W | L24h |
|---|---:|---:|
| `recieved_events` | 590,876 | 49,641 |
| `recieved_events_aggregated` | 99,030 | 7,612 |
| `retry_count.count` (total) | 2,970,098 | 274,988 |
| `retry_count.count` shipments | 1,687,842 | 152,426 |
| `retry_count.count` ship_pieces | 675,978 | 64,626 |
| `read_transfer_list.select.count` | 100,435 | 7,767 |
| `read_transfer_list.delete.count` | 100,079 | 7,741 |
| `read_transfer_list.count` | 100,440 | 7,768 |
| `get_table_data.select.count` | 3,364,070 | 324,813 |
| `get_table_data.count` | 3,364,104 | 324,812 |
| `queue_length` avg / max / last (`avg:` or `max:`, aggregator avg / max / last) | 33.1 / 20,630 / 28.7 | 66.9 / 13,978 / 5.2 |
| `rows_failed`, `rows_dead` | no data | no data |
| `heartbeat_successes` | 21,161 | 1,412 |
| `reconnection_attempts` / `reconnection_successes` | 44 / 45 | 1 / 1 |
| `bulkhead_rejections` | 491,828 | 42,029 |
| `transfer_latency.median` avg of per-interval medians (all tables) | 7,478.6 | 8,126.7 |
| `transfer_latency.95percentile` max of per-interval p95 (all tables) | 1,584,972 | 677,661 |

Notes on these numbers:

- `retry_count.count` is close to `rows_transfered` per table (shipments 1,687,842 against 1,715,298). It looks like a per-row attempt counter, not a count of failures. This is an inference from the numbers. Its meaning was not checked in source.
- `bulkhead_rejections` is large (491,828 in W). What it means for delivery was not investigated.
- The `transfer_latency` unit is not declared in metadata. If it is milliseconds, the overall median of about 7.5 s matches the earlier vault shipment lag (median 7.5 s). The shipments table alone gives avg-of-medians 7,451.8 (W) and 7,860.5 (L24h), and avg-of-p95s 8,033.7 (W) and 8,572.7 (L24h). These are averages of per-interval percentiles, not true window percentiles.
- `read_transfer_list.delete.count` is about 100,079, nearly equal to `read_transfer_list.select.count` at 100,435. That is consistent with the service reading the transfer queue, then deleting what it read. This is an inference.

### Second instance: firebird_transfer_service_weblogins

| Metric | W | L24h |
|---|---:|---:|
| `rows_transfered` | 38 | 2 |
| `recieved_events` | 38 | 2 |
| `queue_length` max | 0 | 0 |
| `heartbeat_successes` | 20,732 | 1,391 |

It is alive (heartbeats) but carries almost no rows.

## 3. Feed B (GFSPublisher / legacy publisher)

Metrics: NO-DATA. No metric exists under `gfs.legacy-publisher.*`, `gfs.legacy_publisher.*`, `gfspublisher`, `gcp_upload` or `upload_2_gcp`. See section 1.

Logs, last 7 days (2026-11-04 to 2026-11-11), aggregated by `service`, indexed logs only (`indexes:["*"]`). Count of matching logs:

| Query | Result |
|---|---|
| `service:*legacy-publisher*` | 0 |
| `service:*legacy_publisher*` | 0 |
| `service:*GFSPublisher*` / `service:*gfspublisher*` | 0 |
| `service:*GCPUploadService*` / `service:*gcpupload*` | 0 |
| `service:*firebird-transfer*` (hyphenated) | 0 |
| `service:*firebird_transfer*` (underscored) | gfs.firebird_transfer_service 472,180; gfs.firebird_transfer_service_weblogins 21,185 |
| free text `legacy-publisher`, `GFSPublisher`, `UPLOAD_2_GCP`, `GCPUploadService` | 0 each |
| free text `fb.shipments.v1` | 0 |
| `service:*publish*` OR `*uploader*` OR `*gcp-upload*` | only tracking_response_publisher (13,320), tracking-core.response-publisher.tracking-mapping (268), tracking-core.response-publisher.tracking-status (21). These are tracking publishers, not Feed B. |
| `host:MEDC-APP-01-P` | the transfer service (472,209), weblogins (21,185), plus gfs.doppelganger.scan-injector (1,693) and its healthcheck (672). No publisher service shares that host in the logs. |

Latest Feed A log: 2026-11-11T11:04:25.759Z, "New event recieved from Firebird with Counts: 1". Preceded by "Found 12 new items to transfer." and "Handling new Firebird event". The service logged 16,739 info and 1 warn lines in the last 6 hours.

Caveat for Feed B: NO-DATA only means Datadog holds no telemetry under those names. The publisher may run on a host without a Datadog agent or under a name that was not searched. Logs outside the indexed tier (Flex or archives) were not searched.

## 4. Volume cross-check against fb.shipments.v1

Direct topic volume: `sum:gcp.pubsub.topic.send_message_operation_count{topic_id:*fb*} by {topic_id}.as_count()`, `byte_cost` on the same filter, and a `*shipments*` topic filter all returned no series. That is NO-DATA, so the `fb.shipments.v1` volume was not measured directly.

Downstream counts over W (production, from `gfs.gfs_modernizer.*` and `gfs.shipment_identity_service.*`):

| Metric (all `.as_count()`, sum) | W | L24h |
|---|---:|---:|
| `gfs.shipment_identity_service.messages` total | 1,589,233 | 147,150 |
| of which `message_type:shipment` | 1,585,447 | 146,864 |
| of which `message_type:shipment_number_update` | 3,786 | 286 |
| `gfs.shipment_identity_service.messages_published` | 1,589,225 | 147,150 |
| `gfs.gfs_modernizer.messages` `type:shipment` | 1,906,654 | 178,812 |
| `gfs.gfs_modernizer.messages` `type:shipment_identified` | 1,586,175 | 146,852 |
| `gfs.gfs_modernizer.messages` `type:windowed_shipment_parcels` | 1,585,459 | 146,858 |
| `gfs.gfs_modernizer.published` `type:shipment` | 1,585,439 | 146,858 |

Side-by-side with Feed A `rows_transfered` for the same window:

| Feed A table | Feed A rows (W) | Modernizer `messages` type (W) |
|---|---:|---:|
| carriers | 36 | carriers 36 |
| customers | 36 | customer 36 |
| cust_contracts | 420 | customer_contracts 420 |
| cust_contract_services | 458 | customer_contract_services 458 |
| products | 43 | products 43 |
| v_ships_comments | 91,872 | shipment_comments 91,873 |
| shipment_extra | 1,759 | shipment_extra 1,821 |
| v_collections | 32,026 | collections 59,353 received; collection 32,232 published |
| ship_pieces | 692,234 | parcel 790,277 |
| shipments | 1,715,298 | shipment 1,906,654 |

Reading:

- Five small reference tables match exactly (36, 36, 420, 458, 43), and shipment comments match to within one message. That is hard to get by chance. It shows the modernizer's input counts line up with Feed A's per-table row counts. A different source with the same counts is possible but would be a coincidence.
- For shipments the modernizer received 1,906,654, which is 191,356 (11.2 per cent) more than Feed A's 1,715,298. For parcels it is 790,277 against 692,234 (14.2 per cent more). The gap is not explained by these data. Re-sends, redrives or another source adding shipments are possible, but none was checked.
- The shipment identity service's 1,589,233 is the stage after identification (the modernizer's `shipment_identified` is 1,586,175, `windowed_shipment_parcels` 1,585,459). It is closest to the modernizer's `published type:shipment` (1,585,439) and not to either feed. Counts at that stage are already filtered or windowed, so they do not size the `fb.shipments.v1` input.
- Closest to the modernizer's `shipment` input of 1,906,654: Feed A `shipments` at 1,715,298 (90 per cent). Feed B has no count to compare. So Feed A is the only candidate with numbers, which does not rule Feed B out.
- It cannot be inferred from Datadog alone that `fb.shipments.v1` comes from Feed A. Confirming needs the topic's publish count (Cloud Monitoring on the project that owns the topic) or the transfer service's publish code or config.

## 5. Monitors

Searched via `search_datadog_monitors` with queries "Firebird", "publisher" and "transfer". No monitor mentions GFSPublisher, GCPUploadService or UPLOAD_2_GCP. No monitor was found with "Replication Service" in the title beyond those below.

| Monitor | Id | State | Query (no secrets) |
|---|---:|---|---|
| Anomaly detected with the Firebird Replication Service Events | 13745110 | OK (muted indefinitely) | `avg(last_4h):anomalies(sum:gfs.firebird_transfer_service.recieved_events{environment:production}.as_count(), 'agile', 2, direction='both', alert_window='last_15m', interval=60, count_default_zero='true', seasonality='weekly') >= 1` |
| Anomaly detected with the Firebird Replication Service Transfer Count | 13745168 | OK | `avg(last_4h):anomalies(sum:gfs.firebird_transfer_service.rows_transfered{!table_name:customers} by {table_name}.as_count(), 'agile', 2, direction='both', alert_window='last_15m', interval=60, count_default_zero='true', seasonality='weekly') >= 1` |
| Firebird Replication Service not replicating any data | 13745313 | OK | `sum(last_2h):sum:gfs.firebird_transfer_service.rows_transfered{environment:production}.as_count() <= 0` |
| Firebird Transfer Service Queue Length | 15961608 | OK | `avg(last_30m):max:gfs.firebird_transfer_service.queue_length{environment:production} > 10000` |
| Firebird Transfer Service Heartbeat | 15961655 | OK | `sum(last_30m):sum:gfs.firebird_transfer_service.heartbeat_successes{environment:production}.as_count() <= 0` |
| INK Firebird Next Transaction Minus Oldest Transaction | 7792526 | No Data | `avg(last_5m):avg:gfs.monitor_firebird.gstats.firebird.NextTransMinusOldestTrans.avg{host:INK} > 12000000` |
| INK Firebird Next Transaction Minus Oldest Snapshot | 7792538 | No Data | `avg(last_5m):avg:gfs.monitor_firebird.gstats.firebird.NextTransMinusOldestSnapshot.avg{host:INK} > 1000000` |
| INK (Newlook) Firebird Next Transaction Minus Oldest Snapshot | 104683110 | No Data | `avg(last_5m):avg:gfs.monitor_firebird.gstats.firebird.newlook.NextTransMinusOldestSnapshot.avg{host:INK} > 1250000` |
| INK (Newlook) Firebird Next Transaction Minus Oldest Transaction | 104683322 | No Data | `avg(last_5m):avg:gfs.monitor_firebird.gstats.firebird.newlook.NextTransMinusOldestTrans.avg{host:INK} > 12000000` |

Only the transfer service has monitors. The four INK `gfs.monitor_firebird.*` monitors report No Data. They watch database transaction stats on host INK, not a publisher. Nothing is monitoring a legacy publisher in Datadog.

## 6. Re-run snippets

Scalar metric query, run in `execute_code`:

```javascript
import { client, v2 } from "@datadog/datadog-api-client";
const m2 = new v2.MetricsApi(client.createConfiguration());
const W = {from: Date.parse("2026-10-23T00:00:00Z"), to: Date.parse("2026-11-07T00:00:00Z")};
const q = "sum:gfs.firebird_transfer_service.rows_transfered{*} by {table_name}.as_count()";
const r = await m2.queryScalarData({body:{data:{type:"scalar_request",attributes:{
  from:W.from, to:W.to, queries:[{dataSource:"metrics", name:"a", query:q, aggregator:"sum"}]}}}});
return r.data.attributes.columns;
```

Swap `q` and the aggregator for any metric above (queries are quoted in the tables). For the last 24 hours use `from: Date.now()-24*3600*1000, to: Date.now()`. Log counts use `v2.LogsApi.aggregateLogs` with `filter.query` as in section 3, `groupBy` facet `service`, and a 7-day `from`.

## Caveats

- Rate metrics converted with `.as_count()` were summed. Totals are as Datadog reports them, and the conversion was not validated against another source.
- The time of "now" is the run time. L24h totals are partial-day rolling windows.
- Latency values are in an undeclared unit (assumed milliseconds) and are averages of per-interval percentiles.
- Logs were searched in indexed storage only.
- Feed B NO-DATA is evidence of absence from Datadog only.
- `uploadsvc.*` was ruled out as Feed B by its tags (customer shipment import, Cloud Run), not by source.
