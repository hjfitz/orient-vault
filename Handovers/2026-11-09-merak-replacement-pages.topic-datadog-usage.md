---
tags: [handover, research-copy, ecm, tracking]
date: 2026-11-10
tldr: "Research copy: Datadog counters for the ECM Pub/Sub topics over the 15-day window, which topics have metrics and which have none (2026-11-10)."
status: research-copy
---
This is a research copy, 2026-11-10, of the findings file `topic-datadog-usage.md`, kept in the vault so it can be found and cited. The synthesis is [[Systems/ecm/tracking]]. It is the Datadog side of [[Handovers/2026-11-09-merak-replacement-pages.topic-usage-map]]. Nothing was edited in Confluence, a repo or Firebird.

# ECM Pub/Sub topic usage from Datadog

Pulled 2026-11-10, read-only, Datadog MCP only. Window 2026-10-23 00:00 to 2026-11-07 00:00 UTC (15 days), one scalar per series with `.as_count()`. Last 24 h means 2026-11-09 12:13 to 2026-11-10 12:13 UTC. JSON copy: `topic-datadog-usage.json` beside this file.

## Headline

- **The GCP Pub/Sub integration does not collect `gfs-ecm-prod-uk1`.** Over 30 days `gcp.pubsub.*` reports only `gfs-ecm-dev`, `gfs-data-service-sandbox1`, `ilg-merak-dev-b5e3`, `bifrost-dev-global1` and `bifrost-prod-global1`. Backlog, oldest unacked age, ack count, dead-letter count and topic send count are therefore **NO-DATA** for every prod-uk1 topic and subscription. I have not inferred zero.
- **Application metrics worked** (`gfs.<service>.pubsub.<alias>.handled_messages`, the `messages_published{topic}` family, webhook counters, the CSS portal counters). Every series is `environment:prod_uk1` (or the webhooks' `production`). None was staging only.
- Verdicts across the 41 topics: **ACTIVE 26**, **LOW-RATE 2** (added: window traffic, nothing in 24 h), **NO-DATA 13**, STALLED 0, QUIET 0, NO-CONSUMER 0. The last three cannot be assessed without backlog and ack data, so none is asserted.
- Dormant topics from the findings (`tracking.v1`, `legacy_tracking.v1`, `parcel-eta-update`, `warehouse-*`) have no metric at all, so they read NO-DATA here. The code and manifest evidence of dormancy stands; Datadog neither confirms nor refutes it.
- The obsolete `shipment_tracking_status` topic still carries the full 4.08M (ICIS 4,077,200; shipment-update-service 4,077,143).
- `gfs-tickets` is only visible under project `gfs-ecm-dev` in the GCP integration. Its volume (40,763) matches ccp-api's prod ticketAction outcomes (40,925) within 0.4 percent, so it is probably the topic ccp-api consumes (inferred).

## Verdict key

- ACTIVE: published or handled count above zero in the last 24 h, from an application metric (not a GCP ack).
- LOW-RATE (added): traffic in the window, none in the last 24 h.
- NO-DATA: no metric names the topic or subscription. Not read as zero.
- STALLED, NO-CONSUMER, QUIET: not asserted for any prod-uk1 item (needs the missing GCP metrics).
- For every subscription below: backlog, oldest unacked age and dead-letter count are **NO-DATA** (GCP integration absent for the project).

## Topics (the 41 from tracking-events-findings.md)

| # | Topic | Published, window | Published, 24 h | Count source | Verdict | Note |
|---|---|---|---|---|---|---|
| 1 | `fb.shipments.v1` | 1,906,654 | 197,396 | proxy: gfs.gfs_modernizer.messages{type:shipment} | **ACTIVE** | Modernizer messages by type. Mapping type to topic is inferred from names. Counts messages the modernizer processed, not Pub/Sub publishes. |
| 2 | `fb.ship_pieces.v1` | 790,277 | 91,628 | proxy: gfs.gfs_modernizer.messages{type:parcel} | **ACTIVE** | type:parcel mapped to ship_pieces by name only (INFERRED). |
| 3 | `fb.ship_pieces_hist.v1` | NO-DATA | NO-DATA | none | **NO-DATA** | No modernizer message type or other metric names it. |
| 4 | `fb.shipment_extra.v1` | 1,821 | 164 | proxy: gfs.gfs_modernizer.messages{type:shipment_extra} | **ACTIVE** |  |
| 5 | `fb.scan_access_data.v1` | NO-DATA | NO-DATA | none | **NO-DATA** | No modernizer message type or other metric names it. |
| 6 | `windowed-shipments-parcels` | 1,585,459 | 159,613 | proxy: gfs.gfs_modernizer.messages{type:windowed_shipment_parcels} | **ACTIVE** |  |
| 7 | `shipments.v2` | 1,585,447 | 159,346 | consumer: gfs.shipment_identity_service.messages{message_type:shipment} | **ACTIVE** | Consumer side only. The modernizer's own shipment_identified type reads 1,586,175 / 159,613. |
| 8 | `shipment-number-updates` | 3,786 | 292 | consumer: gfs.shipment_identity_service.messages{message_type:shipment_number_update} | **ACTIVE** |  |
| 9 | `tracking-events.v2` | NO-DATA | NO-DATA | none | **NO-DATA** | No metric. Code and catalogue say no subscriber; not measured here. |
| 10 | `customers.v2` | NO-DATA | NO-DATA | none | **NO-DATA** | No metric. Code and catalogue say no subscriber; not measured here. |
| 11 | `shipments.v2.identified` | 1,585,439 | 159,660 | publisher: gfs.shipment_identity_service.messages_published{topic} | **ACTIVE** | Publisher-side count with a topic tag. Every full consumer within 0.1 to 0.2 percent. |
| 12 | `shipment-number-updates.identified` | 3,786 | 292 | publisher: gfs.shipment_identity_service.messages_published{topic} | **ACTIVE** |  |
| 13 | `raw_tracking.v1` | 6,294,672 | 598,367 | consumer: CCIS handled (every full consumer 6,294,668 to 6,297,029) | **ACTIVE** | Publisher-side sources: tracking-core response publisher newandupdated_events.count 6,011,685 / 569,943 (proxy for polling publishes); Royal Mail webhook publish.success 218,082 / 22,548; tracking-file-processor messages_published{topic:raw_tracking.v1} 54,125 / 4,579; shipment-update-service messages_published 4 / 0 (no topic tag, not confirmed as raw_tracking). Sum of first three 6,283,896. Separate tracking_file_processor_errors.messages_published 7,384 / 994 plus 54,125 = 61,509 matches the earlier file figure of about 62k, so that figure included errored rows. |
| 14 | `file_tracking.v1` | 3,963 | 248 | proxy: gfs.file_ingestion_ftp_proxy.messages_published{topic:_object_object} | **ACTIVE** | The topic tag on this metric is the literal '_object_object', so attribution to file_tracking.v1 is INFERRED from the service. |
| 15 | `Evri interim tracking topic (gfs-selector-rest-prod-uk1)` | 562,788 | 40,757 | app metric tracking_webhook_evri.tracking.interim.messages.received{environment:production} | **ACTIVE** | Cloud Run project gfs-selector-rest-prod-uk1, outside the ECM project. interim success 562,977 / 40,425, failed 1 in window, plus 7 test messages. |
| 16 | `Evri interim dead-letter topic` | NO-DATA | NO-DATA | none | **NO-DATA** | Only the webhook-side failed counter exists (1 in window). No dead-letter topic metric. |
| 17 | `tracking_configuration_notifications.v1` | NO-DATA | NO-DATA | none | **LOW-RATE** | No publisher metric. Seven subscriber metrics each show 3 or 4 handled in the window and none in the last 24 h. Added verdict: window traffic, nothing in 24 h. |
| 18 | `unmapped-tracking.v1` | 11,622 | 1,049 | consumer: unknown.unmapped_scan_recorder...UnmappedScanHandler.handled_messages | **ACTIVE** |  |
| 19 | `expired_window` | 4,077,022 | 378,189 | consumer: deriver expired_window_* handled (three subs 4,077,022 to 4,077,026) | **ACTIVE** |  |
| 20 | `shipment_tracking_status.v2` | 4,077,032 | 378,190 | consumer: CCIS handled | **ACTIVE** | longmen subscription has no metric. |
| 21 | `shipment_tracking_status` | 4,077,200 | 378,200 | consumer: ICIS handled | **ACTIVE** | Marked obsolete in Terraform, yet carrying the full 4.08M. CCIS and reporting-ingestion have no metric for it. |
| 22 | `shipment_exception_status` | 4,077,022 | 378,186 | consumer: CCIS handled | **ACTIVE** |  |
| 23 | `tracking.v1` | NO-DATA | NO-DATA | none | **NO-DATA** | No metric. Producer (tracking-mapper) has replicas 0 per manifest; not measured here. |
| 24 | `legacy_tracking.v1` | NO-DATA | NO-DATA | none | **NO-DATA** | No metric. Flag said off in code; not measured here. |
| 25 | `scanners.consignments.V1 (gfs-ecm-staging)` | NO-DATA | NO-DATA | none | **NO-DATA** | No metric. Staging project is not in the GCP integration; any traffic would be staging only in any case. |
| 26 | `legacy_tracking_events` | NO-DATA | NO-DATA | none | **NO-DATA** | No metric. |
| 27 | `warehouse-tracking.v1` | NO-DATA | NO-DATA | none | **NO-DATA** | No metric. Manifest commented out; not measured here. |
| 28 | `warehouse-shipment-events.v1` | NO-DATA | NO-DATA | none | **NO-DATA** | No metric. Manifest commented out; not measured here. |
| 29 | `parcel-eta-update` | NO-DATA | NO-DATA | none | **NO-DATA** | No metric. replicas 0 per manifest; absence of a metric is not evidence of zero. |
| 30 | `invoiced_shipments_published.v1` | 633,190 | 685 | publisher: gfs.customer_credit_debit_service_subscriber.messages_published{topic} | **ACTIVE** |  |
| 31 | `invoices_published.v1` | 1,441 | 60 | publisher: gfs.legacy_invoice_translator.pubsub.invoice_published.time.count | **ACTIVE** | Consumers read 1,452 to 1,453 (small gap against the publisher count). |
| 32 | `credit_notes_published.v1` | 22 | 1 | publisher: gfs.legacy_invoice_translator.pubsub.credit_note_published.time.count | **ACTIVE** |  |
| 33 | `invoice_charges_published.v1` | 3,352 | 0 | consumer: reporting-ingestion and ccdis handled (translator entities_handled invoice_charge_published 3,338 / 0) | **LOW-RATE** | Traffic in the window, nothing in the last 24 h. Added verdict. |
| 34 | `shipment-comments.v1` | 91,873 | 7,698 | consumer: CCIS handled (modernizer type shipment_comments 91,873 / 7,700) | **ACTIVE** |  |
| 35 | `shipment-queries` | 30,956 | 2,754 | publisher: manage_queries_proxy_api 6,101 / 622 + manage_queries_proxy_subscriber 24,855 / 2,132 (messages_published{topic}) | **ACTIVE** |  |
| 36 | `shipment-collections.v1` | 32,232 | 2,609 | consumer: ICIS handled (collections_service messages.collection 32,264 / 2,612) | **ACTIVE** |  |
| 37 | `parcel-claim-eligibility.v1` | 3,279,568 | 367,208 | consumer: CCIS handled | **ACTIVE** | ICIS handled 3,281,457 (about 1.9k more than CCIS). |
| 38 | `claims.v1` | 21,592 | 1,638 | consumer: CCIS handled | **ACTIVE** |  |
| 39 | `marked-claimable.v1` | 5 | 2 | consumer: CCIS handled | **ACTIVE** | Very low rate; 2 in the last 24 h. |
| 40 | `gfs-tickets` | 40,763 | 3,791 | GCP integration, project gfs-ecm-dev: gcp.pubsub.topic.send_message_operation_count{topic_id:gfs-tickets} | **ACTIVE** | NOT the prod-uk1 project. The project tag is gfs-ecm-dev. Prod corroboration: ccp-api ticketAction outcomes total 40,925 / 3,392, within 0.4 percent of the dev-tagged publish count, so this is probably the topic ccp-api consumes (INFERRED from the volume match). The ack metric for gfs-ticket-actions-sub is absent (0 acks reported), backlog 0. |
| 41 | `connect.hooks_usage.v1` | NO-DATA | NO-DATA | none | **NO-DATA** | No metric. Dead code per the catalogue; not measured here. |

Counts marked 'consumer' or 'proxy' are what subscribers or the modernizer handled, not Pub/Sub's own publish count. 'publisher' rows come from the service's own `messages_published{topic}` metric.

## Subscriptions

Backlog, oldest unacked and dead-letter are NO-DATA on every row (see the key). `Alias` is the metric name segment, not a confirmed subscription id. Verdict per subscription: ACTIVE if 24 h above zero, LOW-RATE if window only, NO-DATA if no metric.

| Topic | Subscription alias | Service | Handled, window | Handled, 24 h | Verdict | Source or metric |
|---|---|---|---|---|---|---|
| `fb.shipments.v1` | modernizer (v2) | gfs_modernizer | 1,906,654 | 197,396 | ACTIVE | app metric gfs.gfs_modernizer.messages{type:shipment} |
| `fb.ship_pieces.v1` | modernizer (v2) | gfs_modernizer | 790,277 | 91,628 | ACTIVE | app metric gfs.gfs_modernizer.messages{type:parcel} |
| `fb.shipment_extra.v1` | modernizer (v2) | gfs_modernizer | 1,821 | 164 | ACTIVE | app metric gfs.gfs_modernizer.messages{type:shipment_extra} |
| `windowed-shipments-parcels` | modernizer (self) | gfs_modernizer | 1,585,459 | 159,613 | ACTIVE | app metric gfs.gfs_modernizer.messages{type:windowed_shipment_parcels} |
| `shipments.v2` | shipment-identity-service | shipment_identity_service | 1,585,447 | 159,346 | ACTIVE | app metric gfs.shipment_identity_service.messages{message_type:shipment} |
| `shipment-number-updates` | shipment-identity-service | shipment_identity_service | 3,786 | 292 | ACTIVE | app metric gfs.shipment_identity_service.messages{message_type:shipment_number_update} |
| `shipments.v2.identified` | ccis | customer_consignment_information_service | 1,585,591 | 159,591 | ACTIVE | app consumer metric (handled_messages, proxy for publish volume) (gfs.customer_consignment_information_service.pubsub.shipment.handled_messages) |
| `shipments.v2.identified` | icis | internal_consignment_information_service | 1,586,144 | 159,599 | ACTIVE | app consumer metric (handled_messages, proxy for publish volume) (gfs.internal_consignment_information_service.pubsub.shipment.handled_messages) |
| `shipments.v2.identified` | claims-service | claims_subscriber | 1,585,529 | 159,578 | ACTIVE | app consumer metric (handled_messages, proxy for publish volume) (gfs.claims_subscriber.pubsub.shipment.handled_messages) |
| `shipments.v2.identified` | reporting-ingestion | reporting_data_ingestion | 1,585,552 | 159,601 | ACTIVE | app consumer metric (handled_messages, proxy for publish volume) (gfs.reporting_data_ingestion.pubsub.shipment.handled_messages) |
| `shipments.v2.identified` | ccdis (credit/debit) | customer_credit_debit_service_subscriber | 1,585,449 | 159,598 | ACTIVE | app consumer metric (handled_messages, proxy for publish volume) (gfs.customer_credit_debit_service_subscriber.pubsub.shipment.handled_messages) |
| `shipments.v2.identified` | shipment-update-service | shipment_update_service_subscriber | 1,585,970 | 159,600 | ACTIVE | app consumer metric (handled_messages, proxy for publish volume) (gfs.shipment_update_service_subscriber.pubsub.shipments.handled_messages) |
| `shipments.v2.identified` | status deriver | shipment_tracking_status_deriver | 1,585,574 | 159,587 | ACTIVE | app consumer metric (handled_messages, proxy for publish volume) (gfs.shipment_tracking_status_deriver.pubsub.shipment.handled_messages) |
| `shipments.v2.identified` | tracking-patina-service (K8s) | tracking_patina_service | 1,585,452 | 159,605 | ACTIVE | app consumer metric (handled_messages, proxy for publish volume) (gfs.tracking_patina_service.pubsub.shipment.handled_messages) |
| `shipments.v2.identified` | query-categorisation | query_categorisation_subscriber | 1,585,607 | 159,605 | ACTIVE | app consumer metric (handled_messages, proxy for publish volume) (gfs.query_categorisation_subscriber.pubsub.query_categorisation_subscriber.handled_messages) |
| `shipments.v2.identified` | tracking-core consignment-manager | tracking_consignment_manager | 1,578,182 | 158,668 | ACTIVE | app metric gfs.fenghuang.tracking.consignment_manager.pubsub.consignment.success.count (success count only; 1 error in window) |
| `shipments.v2.identified` | customer-care-portal (ccp-api) | customer_care_portal | 1,585,917 | 159,680 | ACTIVE | app metric CSS.CSS.customer_care_portal.pubsub.shipment.outcome (enriched + no_match) |
| `shipments.v2.identified` | tracking-file-processor | tracking_file_processor | 1,589,459 | 159,853 | ACTIVE | app consumer metric (handled_messages, proxy for publish volume) (combined handler: also handles file_tracking.v1) |
| `shipments.v2.identified` | manage-queries-proxy-subscriber | manage_queries_proxy_subscriber | 1,610,415 | 161,727 | ACTIVE | app consumer metric (handled_messages, proxy for publish volume) (combined handler; also handles other topics) |
| `shipments.v2.identified` | gfs-pod-service | gfs_pod_service | 7,880,359 | 757,980 | ACTIVE | app consumer metric (handled_messages, proxy for publish volume) (combined handler: shipments.v2.identified plus raw_tracking.v1) |
| `shipments.v2.identified` | data-warehouse, longmen, webhook push subs | n/a | NO-DATA | NO-DATA | NO-DATA | none (NO-DATA: no app metric names them (push subs not queried)) |
| `shipment-number-updates.identified` | ccis | customer_consignment_information_service | 3,786 | 292 | ACTIVE | app consumer metric (handled_messages, proxy for publish volume) (gfs.customer_consignment_information_service.pubsub.shipment_number_update.handled_messages) |
| `shipment-number-updates.identified` | icis | internal_consignment_information_service | 3,786 | 292 | ACTIVE | app consumer metric (handled_messages, proxy for publish volume) (gfs.internal_consignment_information_service.pubsub.shipment_number_update.handled_messages) |
| `shipment-number-updates.identified` | reporting-ingestion | reporting_data_ingestion | 3,786 | 292 | ACTIVE | app consumer metric (handled_messages, proxy for publish volume) (gfs.reporting_data_ingestion.pubsub.shipmentNumberUpdate.handled_messages) |
| `raw_tracking.v1` | ccis | customer_consignment_information_service | 6,294,672 | 598,367 | ACTIVE | app consumer metric (handled_messages, proxy for publish volume) (gfs.customer_consignment_information_service.pubsub.tracking.handled_messages) |
| `raw_tracking.v1` | icis | internal_consignment_information_service | 6,297,029 | 598,398 | ACTIVE | app consumer metric (handled_messages, proxy for publish volume) (gfs.internal_consignment_information_service.pubsub.tracking.handled_messages) |
| `raw_tracking.v1` | claims-service | claims_subscriber | 6,294,679 | 598,362 | ACTIVE | app consumer metric (handled_messages, proxy for publish volume) (gfs.claims_subscriber.pubsub.tracking.handled_messages) |
| `raw_tracking.v1` | connect-hooks | connect_hooks | 6,294,668 | 598,372 | ACTIVE | app consumer metric (handled_messages, proxy for publish volume) (gfs.connect_hooks.pubsub.tracking.handled_messages) |
| `raw_tracking.v1` | shipment-update-service | shipment_update_service_subscriber | 6,294,796 | 598,388 | ACTIVE | app consumer metric (handled_messages, proxy for publish volume) (gfs.shipment_update_service_subscriber.pubsub.tracking.handled_messages) |
| `raw_tracking.v1` | status deriver | shipment_tracking_status_deriver | 6,294,727 | 598,376 | ACTIVE | app consumer metric (handled_messages, proxy for publish volume) (gfs.shipment_tracking_status_deriver.pubsub.tracking.handled_messages) |
| `raw_tracking.v1` | tracking-patina-service (K8s) | tracking_patina_service | 6,294,707 | 598,396 | ACTIVE | app consumer metric (handled_messages, proxy for publish volume) (gfs.tracking_patina_service.pubsub.tracking.handled_messages) |
| `raw_tracking.v1` | customer-care-portal (ccp-api) | customer_care_portal | 6,294,755 | 598,449 | ACTIVE | app metric CSS.CSS.customer_care_portal.pubsub.tracking.outcome (processed + no_match + invalid) |
| `raw_tracking.v1` | gfs-pod-service | gfs_pod_service | 7,880,359 | 757,980 | ACTIVE | app consumer metric (handled_messages, proxy for publish volume) (combined handler with shipments.v2.identified) |
| `raw_tracking.v1` | patina-service-2 (Dataflow) | patina-service-2 | NO-DATA | NO-DATA | NO-DATA | none (NO-DATA in prod: gcp.dataflow.job.pubsub.read_count exists only for project gfs-ecm-dev (708,054 in window, 0 in 24 h)) |
| `raw_tracking.v1` | tracking-mapper, parcel-eta-service, BigQuery rollback sub, data-warehouse, longmen | n/a | NO-DATA | NO-DATA | NO-DATA | none (NO-DATA: no app metric; code and manifests say replicas 0 or no workload) |
| `file_tracking.v1` | tracking-file-processor | tracking_file_processor | 1,589,459 | 159,853 | ACTIVE | app consumer metric (handled_messages, proxy for publish volume) (combined handler; cannot be separated from shipments.v2.identified) |
| `Evri interim tracking topic (gfs-selector-rest-prod-uk1)` | push to /events/interimTracking | tracking_webhook_evri | 562,977 | 40,425 | ACTIVE | app metric tracking_webhook_evri.tracking.interim.messages.success |
| `tracking_configuration_notifications.v1` | ccis | customer_consignment_information_service | 4 | 0 | LOW-RATE | app metric gfs.customer_consignment_information_service.tracking_mapping...handled_messages |
| `tracking_configuration_notifications.v1` | icis | internal_consignment_information_service | 3 | 0 | LOW-RATE | app metric gfs.internal_consignment_information_service.tracking_mapping...handled_messages |
| `tracking_configuration_notifications.v1` | claims-service | claims_service | 3 | 0 | LOW-RATE | app metric gfs.claims_service.tracking_mapping...handled_messages |
| `tracking_configuration_notifications.v1` | connect-hooks | connect_hooks | 3 | 0 | LOW-RATE | app metric gfs.connect_hooks.tracking_mapping...handled_messages |
| `tracking_configuration_notifications.v1` | tracking-core | tracking_core | 3 | 0 | LOW-RATE | app metric gfs.tracking_core.response_publisher.tracking_mapping...handled_messages |
| `tracking_configuration_notifications.v1` | status deriver | shipment_tracking_status_deriver | 3 | 0 | LOW-RATE | app metric gfs.shipment_tracking_status_deriver.tracking_mapping...handled_messages |
| `tracking_configuration_notifications.v1` | shipment-update-service | shipment_update_service | 3 | 0 | LOW-RATE | app metric unknown.shipment_update_tracking_mapping...handled_messages |
| `unmapped-tracking.v1` | unmapped-scan-recorder | unmapped_scan_recorder | 11,622 | 1,049 | ACTIVE | app consumer metric (handled_messages, proxy for publish volume) |
| `expired_window` | shipment-exception-status | shipment_tracking_status_deriver | 4,077,022 | 378,190 | ACTIVE | app consumer metric (handled_messages, proxy for publish volume) (gfs.shipment_tracking_status_deriver.pubsub.expired_window_exception_status.handled_messages) |
| `expired_window` | shipment-tracking-status | shipment_tracking_status_deriver | 4,077,023 | 378,190 | ACTIVE | app consumer metric (handled_messages, proxy for publish volume) (gfs.shipment_tracking_status_deriver.pubsub.expired_window_tracking_status.handled_messages) |
| `expired_window` | shipment-tracking-status-v2 | shipment_tracking_status_deriver | 4,077,026 | 378,189 | ACTIVE | app consumer metric (handled_messages, proxy for publish volume) (gfs.shipment_tracking_status_deriver.pubsub.expired_window_tracking_status_v2.handled_messages) |
| `shipment_tracking_status.v2` | ccis | customer_consignment_information_service | 4,077,032 | 378,190 | ACTIVE | app consumer metric (handled_messages, proxy for publish volume) (gfs.customer_consignment_information_service.pubsub.shipment_tracking_status_v2.handled_messages) |
| `shipment_tracking_status.v2` | reporting-ingestion | reporting_data_ingestion | 4,077,031 | 378,217 | ACTIVE | app consumer metric (handled_messages, proxy for publish volume) (gfs.reporting_data_ingestion.pubsub.shipmentTrackingStatusV2.handled_messages) |
| `shipment_tracking_status.v2` | longmen | n/a | NO-DATA | NO-DATA | NO-DATA | none (NO-DATA) |
| `shipment_tracking_status` | icis | internal_consignment_information_service | 4,077,200 | 378,200 | ACTIVE | app consumer metric (handled_messages, proxy for publish volume) (gfs.internal_consignment_information_service.pubsub.shipment_tracking_status.handled_messages) |
| `shipment_tracking_status` | shipment-update-service | shipment_update_service_subscriber | 4,077,143 | 378,213 | ACTIVE | app consumer metric (handled_messages, proxy for publish volume) (gfs.shipment_update_service_subscriber.pubsub.shipment_tracking_status.handled_messages) |
| `shipment_exception_status` | ccis | customer_consignment_information_service | 4,077,022 | 378,186 | ACTIVE | app consumer metric (handled_messages, proxy for publish volume) (gfs.customer_consignment_information_service.pubsub.shipment_exception_status.handled_messages) |
| `shipment_exception_status` | icis | internal_consignment_information_service | 4,077,067 | 378,200 | ACTIVE | app consumer metric (handled_messages, proxy for publish volume) (gfs.internal_consignment_information_service.pubsub.shipment_exception_status.handled_messages) |
| `shipment_exception_status` | reporting-ingestion | reporting_data_ingestion | 4,077,024 | 378,218 | ACTIVE | app consumer metric (handled_messages, proxy for publish volume) (gfs.reporting_data_ingestion.pubsub.shipmentExceptionStatus.handled_messages) |
| `invoiced_shipments_published.v1` | claims-service | claims_subscriber | 633,190 | 685 | ACTIVE | app consumer metric (handled_messages, proxy for publish volume) (gfs.claims_subscriber.pubsub.invoiced_shipment.handled_messages) |
| `invoiced_shipments_published.v1` | ccis | customer_consignment_information_service | 633,190 | 685 | ACTIVE | app consumer metric (handled_messages, proxy for publish volume) (gfs.customer_consignment_information_service.pubsub.invoiced_shipment.handled_messages) |
| `invoiced_shipments_published.v1` | icis | internal_consignment_information_service | 633,190 | 685 | ACTIVE | app consumer metric (handled_messages, proxy for publish volume) (gfs.internal_consignment_information_service.pubsub.invoiced_shipment.handled_messages) |
| `invoiced_shipments_published.v1` | shipment-update-service | shipment_update_service_subscriber | 633,190 | 685 | ACTIVE | app consumer metric (handled_messages, proxy for publish volume) (gfs.shipment_update_service_subscriber.pubsub.shipments_invoiced.handled_messages) |
| `invoiced_shipments_published.v1` | reporting-ingestion | reporting_data_ingestion | 633,190 | 685 | ACTIVE | app consumer metric (handled_messages, proxy for publish volume) (gfs.reporting_data_ingestion.pubsub.invoicedShipment.handled_messages) |
| `invoices_published.v1` | ccdis | customer_credit_debit_service_subscriber | 1,453 | 60 | ACTIVE | app consumer metric (handled_messages, proxy for publish volume) (gfs.customer_credit_debit_service_subscriber.pubsub.invoice.handled_messages) |
| `invoices_published.v1` | reporting-ingestion | reporting_data_ingestion | 1,452 | 60 | ACTIVE | app consumer metric (handled_messages, proxy for publish volume) (gfs.reporting_data_ingestion.pubsub.invoice.handled_messages) |
| `credit_notes_published.v1` | ccdis | customer_credit_debit_service_subscriber | 22 | 1 | ACTIVE | app consumer metric (handled_messages, proxy for publish volume) (gfs.customer_credit_debit_service_subscriber.pubsub.creditNotes.handled_messages) |
| `credit_notes_published.v1` | reporting-ingestion | reporting_data_ingestion | 22 | 1 | ACTIVE | app consumer metric (handled_messages, proxy for publish volume) (gfs.reporting_data_ingestion.pubsub.creditNotes.handled_messages) |
| `invoice_charges_published.v1` | ccdis | customer_credit_debit_service_subscriber | 3,352 | 0 | LOW-RATE | app consumer metric (handled_messages, proxy for publish volume) (gfs.customer_credit_debit_service_subscriber.pubsub.invoiceCharges.handled_messages) |
| `invoice_charges_published.v1` | reporting-ingestion | reporting_data_ingestion | 3,352 | 0 | LOW-RATE | app consumer metric (handled_messages, proxy for publish volume) (gfs.reporting_data_ingestion.pubsub.invoiceCharges.handled_messages) |
| `shipment-comments.v1` | ccis | customer_consignment_information_service | 91,873 | 7,698 | ACTIVE | app consumer metric (handled_messages, proxy for publish volume) (gfs.customer_consignment_information_service.pubsub.shipment_comments.handled_messages) |
| `shipment-comments.v1` | icis | internal_consignment_information_service | 91,876 | 7,699 | ACTIVE | app consumer metric (handled_messages, proxy for publish volume) (gfs.internal_consignment_information_service.pubsub.shipment_comments.handled_messages) |
| `shipment-comments.v1` | reporting-ingestion | reporting_data_ingestion | 91,873 | 7,699 | ACTIVE | app consumer metric (handled_messages, proxy for publish volume) (gfs.reporting_data_ingestion.pubsub.shipmentComments.handled_messages) |
| `shipment-queries` | ccis | customer_consignment_information_service | 30,956 | 2,751 | ACTIVE | app consumer metric (handled_messages, proxy for publish volume) (gfs.customer_consignment_information_service.pubsub.shipment_queries.handled_messages) |
| `shipment-queries` | icis | internal_consignment_information_service | 30,956 | 2,751 | ACTIVE | app consumer metric (handled_messages, proxy for publish volume) (gfs.internal_consignment_information_service.pubsub.shipment_queries.handled_messages) |
| `shipment-queries` | reporting-ingestion | reporting_data_ingestion | 30,956 | 2,753 | ACTIVE | app consumer metric (handled_messages, proxy for publish volume) (gfs.reporting_data_ingestion.pubsub.shipmentQueries.handled_messages) |
| `shipment-queries` | customer-care-portal (ccp-api) | customer_care_portal | 33,167 | 2,999 | ACTIVE | app metric CSS.CSS.customer_care_portal.pubsub.shipmentQuery.outcome (sum of outcomes) (differs from the topic count; outcome totals may include other inputs) |
| `shipment-collections.v1` | icis | internal_consignment_information_service | 32,232 | 2,609 | ACTIVE | app consumer metric (handled_messages, proxy for publish volume) (gfs.internal_consignment_information_service.pubsub.shipment_collections.handled_messages) |
| `shipment-collections.v1` | reporting-ingestion | reporting_data_ingestion | 32,232 | 2,610 | ACTIVE | app consumer metric (handled_messages, proxy for publish volume) (gfs.reporting_data_ingestion.pubsub.shipmentCollections.handled_messages) |
| `parcel-claim-eligibility.v1` | ccis | customer_consignment_information_service | 3,279,568 | 367,208 | ACTIVE | app consumer metric (handled_messages, proxy for publish volume) (gfs.customer_consignment_information_service.pubsub.claim_eligibility.handled_messages) |
| `parcel-claim-eligibility.v1` | icis | internal_consignment_information_service | 3,281,457 | 367,209 | ACTIVE | app consumer metric (handled_messages, proxy for publish volume) (gfs.internal_consignment_information_service.pubsub.claim_eligibility.handled_messages) |
| `claims.v1` | ccis | customer_consignment_information_service | 21,592 | 1,638 | ACTIVE | app consumer metric (handled_messages, proxy for publish volume) (gfs.customer_consignment_information_service.pubsub.claims_subscription.handled_messages) |
| `claims.v1` | icis | internal_consignment_information_service | 21,595 | 1,638 | ACTIVE | app consumer metric (handled_messages, proxy for publish volume) (gfs.internal_consignment_information_service.pubsub.claims_subscription.handled_messages) |
| `claims.v1` | reporting-ingestion | reporting_data_ingestion | 21,592 | 1,638 | ACTIVE | app consumer metric (handled_messages, proxy for publish volume) (gfs.reporting_data_ingestion.pubsub.claims.handled_messages) |
| `marked-claimable.v1` | ccis | customer_consignment_information_service | 5 | 2 | ACTIVE | app consumer metric (handled_messages, proxy for publish volume) (gfs.customer_consignment_information_service.pubsub.shipment_marked_claimable.handled_messages) |
| `gfs-tickets` | gfs-ticket-actions-sub | customer_care_portal | 40,925 | 3,392 | ACTIVE | app metric CSS.CSS.customer_care_portal.pubsub.ticketAction.outcome (sum) (subscription name from the gfs-ecm-dev listing) |

## Extras: topics seen in Datadog that are not among the 41

| Topic or item | Window | 24 h | Source | Verdict | Note |
|---|---|---|---|---|---|
| claims-submitted.v1 (name inferred from a gfs-ecm-dev subscription 'claims-submitted.v1.claims-service') | 1,006 | 0 | consumer: gfs.claims_subscriber.pubsub.claim_submitted.handled_messages | LOW-RATE | Topic name is inferred. |
| claim credit notes (topic name unknown; alias claimCreditNotes) | 1,006 | 0 | consumers: reporting_data_ingestion and customer_credit_debit_service_subscriber claimCreditNotes | LOW-RATE | Same 1,006 as claim_submitted, probably the same flow. |
| fb.customers.v1 | 36 | 2 | subscription name in metric: customer_and_contract_service ...subscriptions_fb.customers.v1 | ACTIVE | Topic name inferred from subscription name. |
| fb.customer_sites.v1 | 37 | 6 | subscription name in metric: ...subscriptions_fb.customer_sites.v1 | ACTIVE |  |
| fb.cust_contracts.v1 | 420 | 10 | subscription name in metric: ...subscriptions_fb.cust_contracts.v1 | ACTIVE |  |
| cust_contracts.v2 | 420 | 10 | subscription name in metric: ...subscriptions_cust_contracts.v2 | ACTIVE | Probably the modernizer's output of fb.cust_contracts.v1. |
| fb.cust_contract_services.v1 | 458 | 0 | subscription name in metric: ...subscriptions_fb.cust_contract_services.v1 | LOW-RATE |  |
| cust_contracts_services.v2 (dev name uses hyphens: cust-contracts-services.v2) | 458 | 0 | subscription name in metric: ...subscriptions_cust_contracts_services.v2 | LOW-RATE |  |
| dead-letters.v1 | 84 | 1 | LOG count, not a metric: service:gfs-deadletter-register "DeadLetter registered" | ACTIVE (log) | Log lines, one per stored dead letter. Not gcp.pubsub.subscription.dead_letter_message_count. |
| gfsmanager.ticketpresentation.prod (project gfs-ecm-dev) | 66,088 | 6,879 | GCP integration, project gfs-ecm-dev | ACTIVE (dev-tagged project) | Subscription gfs-ticket-presentations-sub reports no acks. Not prod-uk1. |
| gcp-logs.v1 (project gfs-ecm-dev) | 214 | 1 | GCP integration, project gfs-ecm-dev | ACTIVE (dev-tagged project) | Log export to Datadog (sub gcp-logs.v1-datadog, 214 acks). |
| modernizer message types carriers, products | 36 and 43 | 2 and 0 | gfs.gfs_modernizer.messages{type} | n/a | Message types, not confirmed topics. |
| gfs-data-service-sandbox1 (different project): eventarc-*, gfs-data-sandbox1-ecm-pipeline-extractor, container-analysis-occurrences-v1 etc. | see JSON | n/a | GCP integration, project gfs-data-service-sandbox1 | n/a | Data team sandbox; none of the 41 names. Backlog there is large (see caveats). |
| ilg-merak-dev-b5e3: sftp-parcel-inbound-files | 411 | n/a | GCP integration, project ilg-merak-dev-b5e3 | n/a | Merak dev project, not ECM. |

The `gfs-ecm-dev` project lists over 100 subscriptions named `<topic>.<suffix>` (dev only, all idle). Names that give extra topic ids beyond the 41, as evidence of existence in dev only: `adjustments.v1-validator2`, `carrier-charges.v1-validator2`, `carrier-credentials.v1.fenghuang.carrier_credentials_manager`, `carrier-credentials.v1.fenghuang.carrier_credentials_manager_legacy`, `carriers.v2.carrier-services-directory`, `claims-submitted.v1.claims-service`, `cs.bot.logs.*`, `cust-contracts-services.v2.customer-and-contract-svc`, `cust-contracts.v2.customer-and-contract-svc`, `estimated-costs.v1-validator2`, `fb.carriers.v1.*`, `fb.collections.v1.*`, `fb.cust_contract_services.v1.*`, `fb.cust_contracts.v1.*`, `fb.customer_sites.v1.*`, `fb.customers.v1.*`, `fb.gfsinternational.v1.shipments`, `fb.products.v1.*`, `fb.queries.v1.manage-queries-proxy`, `fb.scan_access_data.v1.modernizer.v2`, `fb.ship_comments.v1.modernizer.v2`, `fb.ship_pieces.v1.modernizer.v2`, `fb.ship_pieces_hist.v1.modernizer.v2`, `fb.shipment_extra.v1.modernizer.v2`, `fb.shipments.v1.modernizer.v2`, `fb.web_users.v1.fenghuang.collections_service`, `products.v2.carrier-services-directory`, `retries.retry-service.v1.retry-service`, `route_validation_import.v1.*`, `sales.v1-validator2`, `scanners.consignments.v1.scan.injector.v2`, `scanners.deadletter.v1.scan.injector.v2`, `report-run.reporting-service`, `(and the 41-topic subscriptions with the <topic>.<suffix> naming)`.

## Queries used (re-runnable)

- Window W = 1792713600000 to 1794009600000 ms (2026-10-23T00:00:00Z to 2026-11-07T00:00:00Z). 24 h = the 24 hours to 2026-11-10 12:13 UTC (2026-11-09 12:13 to 2026-11-10 12:13). Run via mcp__datadog__execute_code with v2.MetricsApi.queryScalarData, aggregator sum, one scalar per series.
- GCP integration probe: sum:gcp.pubsub.topic.send_message_operation_count{*} by {project_id}.as_count() ; sum:gcp.pubsub.subscription.ack_message_count{*} by {project_id}.as_count() ; max:gcp.pubsub.subscription.num_undelivered_messages{*} by {project_id}. Also 30 days for send_message_operation_count, ack_message_count, num_undelivered_messages, oldest_unacked_message_age, dead_letter_message_count, message_sizes.samplecount, each by {project_id}.
- gfs-ecm-prod-uk1 filters that returned nothing: ack_message_count{project_id:*ecm*} (only gfs-ecm-dev), topic.send_message_operation_count{project:gfs-ecm-prod-uk1}, {topic_id:raw_tracking.v1}, subscription.ack_message_count{subscription_id:*raw_tracking*}.
- gfs-ecm-dev detail: sum:gcp.pubsub.topic.send_message_operation_count{project_id:gfs-ecm-dev} by {topic_id}.as_count(); sum:gcp.pubsub.subscription.ack_message_count{project_id:gfs-ecm-dev} by {subscription_id}.as_count(); max:gcp.pubsub.subscription.num_undelivered_messages{project_id:gfs-ecm-dev} by {subscription_id}; max:...oldest_unacked_message_age{project_id:gfs-ecm-dev} by {subscription_id}; sum:...dead_letter_message_count{project_id:gfs-ecm-dev} by {subscription_id}.as_count().
- Per consumer: sum:<metric>{*} by {environment}.as_count() where <metric> is gfs.<service>.pubsub.<alias>.handled_messages (75 metrics: every consumer alias listed in the Subscriptions table, plus the tracking_mapping and customer_and_contract_service names). Every series carried environment:prod_uk1 (the tracking_mapping and customer_and_contract_service ones too); none came from another environment.
- Publish side: sum:gfs.shipment_identity_service.messages_published{*} by {topic,environment}.as_count() ; gfs.tracking_file_processor.messages_published by {topic,environment} ; gfs.manage_queries_proxy_api.messages_published by {topic,environment} ; gfs.manage_queries_proxy_subscriber.messages_published by {topic,environment} ; gfs.customer_credit_debit_service_subscriber.messages_published by {topic,environment} ; gfs.file_ingestion_ftp_proxy.messages_published by {topic,environment} ; gfs.shipment_update_service.messages_published by {environment}.
- Other: sum:gfs.gfs_modernizer.messages{*} by {type,environment}.as_count() ; sum:gfs.shipment_identity_service.messages{*} by {message_type}.as_count() ; tracking_webhook_royal_mail_sapient.tracking.messages.publish.success / .received ; tracking_webhook_evri.tracking.interim.messages.received / .success / .failed ; gfs.fenghuang.tracking.response_publisher.connector_response_handler.newandupdated_events.count ; gfs.fenghuang.tracking.consignment_manager.pubsub.consignment.success.count / .errors.count ; gfs.legacy_invoice_translator.pubsub.invoice_published.time.count / credit_note_published.time.count / collection_invoice_published.time.count ; gfs.legacy_invoice_translator.subscribers.entities_handled.count by {firebird_event_name} ; CSS.CSS.customer_care_portal.pubsub.{tracking,shipment,shipmentQuery,ticketAction}.outcome by {outcome} ; CSS.CSS.customer_care_portal.pubsub.messages.received. All .as_count().
- Errors: sum:gfs.<service>.pubsub.<alias>.errored_messages{*} by {environment}.as_count() for claims tracking (131 in window), deriver tracking (25), file processor (30), ICIS tracking (5), ICIS claim_eligibility (25); all others (CCIS tracking, ccds invoice and shipment, reporting shipment, shipmentQueries, shipmentComments, shipmentExceptionStatus, shipmentTrackingStatusV2, deriver expired_window_*) returned no series. None in the last 24 h.
- Dead letters (log proxy): Logs v2 aggregateLogs, query service:gfs-deadletter-register "DeadLetter registered", count, window and 24 h (84 and 1).
- Dataflow probe: sum:gcp.dataflow.job.pubsub.read_count{*} by {project_id}.as_count() (gfs-ecm-dev only).

## Caveats

- The GCP Pub/Sub integration does NOT cover gfs-ecm-prod-uk1. In 30 days it reports only gfs-ecm-dev, gfs-data-service-sandbox1, ilg-merak-dev-b5e3, bifrost-dev-global1 and bifrost-prod-global1. So backlog (num_undelivered_messages), oldest_unacked_message_age, dead_letter_message_count, ack_message_count and topic send counts are NO-DATA for every prod-uk1 topic and subscription. Not inferred as zero.
- Because backlog and age are missing, STALLED and NO-CONSUMER cannot be assessed for any prod-uk1 subscription, and QUIET is not asserted for any topic. ACTIVE here means 'handled or published counts above zero in the last 24 h, from application metrics', not 'acked in GCP'. LOW-RATE is an added verdict for topics with window traffic and none in the last 24 h.
- handled_messages is the application's own counter. It counts messages a handler processed. It is not a Pub/Sub ack count, so a handler that nacks or drops still counts. Where one publisher feeds many consumers the consumer counts agree to within 0.1 to 0.2 percent, which is why they work as a publish proxy.
- Subscription ids are not in the application metrics, apart from customer_and_contract_service and the tracking_mapping ones. The 'alias' column is the metric name segment. Real names follow <topic>.<suffix> per Terraform, and the gfs-ecm-dev subscription listing shows that convention, but dev is not evidence that prod has the same set.
- The alias to topic mapping is inferred from names (tracking = raw_tracking.v1, shipment = shipments.v2.identified and so on) and matches the wiring in tracking-events-findings.md and the counts. A few combined handlers (gfs_pod_service, tracking_file_processor, manage_queries_proxy_subscriber, query_categorisation) cannot be separated per topic.
- Project tags: gfs-tickets, gfsmanager.ticketpresentation.prod and gcp-logs.v1 report under project gfs-ecm-dev, not prod-uk1 or the findings' 'gfs-ecm'. Treat their GCP numbers as dev-tagged. All 'gfs-ecm-dev' subscriptions (over 100) show zero backlog and zero oldest-unacked age over the whole window, and no acks except gcp-logs.v1-datadog. That is an idle dev project, so it supports no LIVE verdict for any topic.
- The last-24 h window is 2026-11-09 12:13 to 2026-11-10 12:13 UTC, after the canonical window. Datadog GCP metrics lag a few minutes; application counters should not.
- Biggest backlogs seen anywhere in the GCP integration (not ECM prod): gfs-data-service-sandbox1, window maximum num_undelivered_messages 1,321,672 on gfs-data-sandbox1-sharepoint-doc-extractor-sub and 728,045 on gfs-data-sandbox1-ecm-pipeline-extractor-sub. These belong to the data team sandbox, not to the ECM topics. bifrost-prod-global1 is the Fuse project, also not ECM.
- Unmeasured: push subscriptions in gfs-selector-rest-prod-uk1 for the shipment feed (webhook shipment.messages.* metrics exist but were not queried), patina-service-2 Dataflow in prod, data-warehouse, longmen, tracking-mapper and parcel-eta-service. Silence from them is NO-DATA, not zero.
- Dead letters: 84 'DeadLetter registered' log lines in the window and 1 in the last 24 h (service gfs-deadletter-register) is the only DLQ evidence for prod-uk1. It cannot be attributed to a subscription.
- The Datadog MCP server reported the client is on the deprecated endpoint /api/unstable/mcp-server/mcp. The client configuration should move to /v1/mcp on the same host. Requests were served normally.
