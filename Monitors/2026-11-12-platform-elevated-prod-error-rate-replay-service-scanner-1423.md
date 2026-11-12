---
tags: [datadog-triage]
date: 2026-11-12
monitor: "[FUSE][Platform] Elevated production error rate (2m window)"
service: replay-service
business_id:
snap_instance:
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1794493494104109"
opened_at: "2026-11-12T14:23:37Z"
resolved_at: "2026-11-12T14:38:00Z"
minutes_spent: 14
severity_assessed: P4
flapping: true
outcome: monitor_mistuned
escalated_to:
ticket:
session_id: 7f84afae-380e-4959-8dc8-c8b0cbe9f19d
status: resolved
---
# 14:23Z firing: 3 replay-service "Error unhandled" lines (HTTP 415 and 400) from an internet scanner burst; second replay-service trip of this monitor (6 Nov was the first); no customer impact found

## Fired
Monitor 180072217 (log alert, more than 2 matching error lines in 2m) Triggered 14:23:37Z, Datadog Recovered event 14:24:37Z, monitor status OK when re-read at about 14:33Z. Alert thread C099WKQTE8G / 1794493494.104109 (posted 14:24:54Z), no replies when read. Run as a read-only subagent; the watcher posts the reply.

## Investigation
- 1 Monitor query run for 14:21:37-14:23:37Z (analyze_datadog_logs, the monitor's exact query from the definition): 3 lines, all service replay_service, no businessId. 2 x `unsupported content encoding "br"` (UnsupportedMediaTypeError, HTTP 415, 14:22:07.953Z and 14:22:08.327Z) and 1 x `Failed to decode param '%C0'` (BadRequestException, HTTP 400, 14:22:57.294Z). Per-minute re-run 14:20Z to about 14:33Z: 14:22 x3, 14:23 x1, nothing after. The 4th line is a second `%C0` error at 14:23:43Z. The same filter without the monitor's exclusions (all prod domain:fuse error lines since 14:21:37Z) returned only these 4 replay_service lines.
- 2 Same service, same minutes: replay_service warn lines 14:22:00Z 324, 14:23 565, 14:24 526 (first 14:22:07.369Z, last 14:24:39.267Z), nothing in 14:25-14:33Z. Sampled lines are `404 Not Found: GET /proc/self/environ`, /private.pem, /private.key, /phpinfo.php, /php.ini, /paypal_credentials.json, /payment/stripe.json, /opencode.json, /openai.json, /old/.env, /msmtprc and similar credential-file paths. Every replay_service warn line per day 5-12 Nov matches "404 Not Found" (the 404 count equals the warn count each day: 158, 705, 1126, 459, 1023, 394, 843, 2423 so far today), so this is constant background scanning.
- 3 Mechanism, replay-service at 6ee4022d (git show): all-exceptions.filter.ts calls logException; logException's default branch logs ErrorEvent.UnhandledError (error level, "Error unhandled") for any Error whose name is not ValidationError/DecodeError/UseCaseNotFoundError/DatabaseError/ServiceError, so framework 4xx from body-parser and NestJS routing are logged as errors. Matches the earlier 6 Nov record's lead.
- 4 Recurrence: replay_service error-level lines in 7d: 5 on 6 Nov 02:22:42-43Z (malformed JSON, monitor Triggered, [[2026-11-06-platform-elevated-prod-error-rate-replay-service-scan-0224]]) and these 4 on 12 Nov. Monitor events: 32 Triggered and 32 Recovered in 7d, 1 of each in the last 24h (aggregate_events).
- 5 Client IP of the replay probes: not in replay_service logs (the warn lines carry method, path and correlationId only; `@request.client.ip` is not present on replay_service). The config-service scanner IP 82.165.94.38 (@request.client.ip wildcard, 14 days): 12 requests on each of 5, 7 and 11 Nov, none on any other day including 12 Nov. config-service logs last 24h: warn 2269 (hourly 15-192, diurnal), error 2 (both "Postgres ping took longer than 2000ms", 01:02Z and 09:35Z), no line with a 5xx status.
- 6 Snap involvement: no snap_adapter line matched. snap_adapter error lines in 24h (transient/exhausted/mode by business): 3 transient (all routing_persistence, exhausted false, deliveryAttempt 1, HTTP 503 then redelivered and "Entity created in SNAP"): EPARFUM DC127895000 (shipment EPAR9F27D3DB89F, 11 Nov 17:51:39Z), STUBBLE SC17421906 (STUB3F1544A4201, 11 Nov 17:51:42Z), ESCENTRICPL #140782 (ESCE2A6DBA1934E, 12 Nov 13:50:23Z); 11 non-transient data rejections (DOCKBAY 4, SPORTLUX 3, STUBBLE 1, PURDYFIGG 2, EPARFUM 1), all exhausted false. None in 14:21-14:24Z. The warn "Firestore routing metadata write failed" precedes each of the 3 transient errors.
- 7 Read-only Snap checks (get-snap-connection production, GET /v2/shipments/{id}, GET /v2/attachments/SHH/{id}): all 3 shipments exist (EPAR9F27D3DB89F stage 90, STUB3F1544A4201 stage 90, ESCE2A6DBA1934E stage 20). Expected PRODDETAIL LineId per `createDeterministicId` (ESCENTRICPL::PRODDETAIL:0:<SHIPMENTID> etc., read from snap-adapter code): STUBBLE STUB3F1544A4201 has PRODDETAIL at STUBEA3BDE (present). EPAR9F27D3DB89F has DANGERGOODS and NETCCAR but no PRODDETAIL (EPAR151FE2); ESCE2A6DBA1934E has DUTY only (ESCE56DE9D absent). For both, the other shipments sampled today carry no PRODDETAIL (ESCENTRICPL 6 recent shipments all DUTY only; EPARFUM 4 sampled with TXT or none), so none is expected; STUBBLE's other sampled shipments do carry PRODDETAIL. No expected attachment is missing.
- 8 Breaker: snap.breaker.state (0 closed, 0.5 half-open, 1 open) max over 24h for environment:prod, hosts ilg001-ilg005 live: 0 on every host; snap.breaker.opened and rejected for environment:prod: no data in 24h. The max of 1 seen at 14:24Z in an unfiltered query is environment:dev, host crackle.devtools.fuse.freightops.dev (the fuse-mocker simulator); dev test hosts 0.
- 9 Held in replay-service (replay-list-failures production, createdAt 2026-11-12): 80, attempts 0 and replayed false on all (replayed:true total 0), none created after 13:36:12Z. 72 goods_out_confirmation PURDYFIGG "Fulfillment order ... is CLOSED in Shopify" (confirmation.delivery_shopify); 7 snap-adapter rejections: SPORTLUX purchase_order "DK KIDS" x2 and "DK KIDS 2" x1 (XDoc invalid order stage / SKU no product found), DOCKBAY sales_order UK-915225 x2 (City > 30 chars), STUBBLE SC17420739-1 (Line1 mandatory), PURDYFIGG #6719265 (Name > 50 chars); 1 ESCENTRIC sftp ingest row (create.sftp_row, "Invalid input: expected string, received undefined"). Not caused by this alert, but 7 are records Fuse could not submit to Snap and are held.
- 10 Deploys and changes, last 24h: GitHub terraform-prod deployments (26 active gfs-bifrost repos): replay-service 6ee4022d success 11 Nov 15:07:25Z (Datadog logs serve 6ee4022d, revision replay-prod-00039-cnw; no replay-service change stories 11 Nov 14:00Z - 12 Nov 14:40Z); sftp-connector 6272f527 success 13:31:33Z (logs switch to it 13:31:12Z); snap-adapter d5df6f69 (#338, snap-queue-polling-service per-host cap 5, 3 instances) success 14:22:49Z, snap-polling-service logs switch to d5df6f69 at 14:23:45Z, warn volume 6121/6233/about 6.4k per hour before and after, no errors; observability 032a45ce (#89, new snap breaker monitors, snap-adapter files only) success 14:21:49Z; tracking-service 0dd73355, fe6ef983 (flip prod to MongoDB, 11 Nov 16:28Z), 83ffea49, 6a723664 (11 Nov) and d5aa3d1d (#44) and e34d8214 (#45) (12 Nov 11:08Z and 11:16Z) all success, e34d8214 serving. Not applied: sftp-connector 895f59c5 (only `waiting`), snap-adapter 48683209 Renovate (two deployments, both only `waiting`; snap_adapter logs serve 841717ea throughout 13:00-14:30Z).
- 11 Maintenance vault: no record with a window on or after 5 Nov 10:00Z (latest by date 4 Nov); no Snap host was implicated, so no timed probe or instance check was run.

## Not established
- The source IP of the replay-service probes, and whether replay-service is meant to be internet-reachable (ingress not visible in Datadog).
- Which of the probe requests carried the br-encoded body and the %C0 path (not logged).
- Whether any probe request got a 2xx (replay_service request lines for the burst were not read; only warn 404 lines and a steady info volume of 45 in 14:22 vs 51 in 14:20 were seen).
- Whether support already knows about the 7 held Snap rejections in 9.
- Why the 3 transient failures show "Firestore routing metadata write failed" (cause of the write failure not investigated).

## Outcome
P4 monitor_mistuned, no customer impact found. Verdict basis: the only lines that tripped the monitor are replay-service framework 4xx logged at error level during a scanner burst; nothing processing-related matched, prod breakers stayed closed, the three transient snap_adapter orders all exist in Snap with no expected attachment missing, and the monitor recovered at 14:24:37Z. Leads, not findings: log body-parser and NestJS 4xx at warn in replay-service (and config-service), and/or exclude them in the monitor query (Terraform-managed, `managed-by:terraform`, so the change goes in the observability repo); 7 held Snap rejections need data fixes then replay.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1794493494104109
- Monitor: https://app.datadoghq.com/monitors/180072217
- Prior: [[2026-11-06-platform-elevated-prod-error-rate-replay-service-scan-0224]], [[2026-11-11-platform-elevated-prod-error-rate-config-service-scanner-0524]]
