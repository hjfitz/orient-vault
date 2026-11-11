---
tags: [handover, research-copy, ecm, firebird]
date: 2026-11-11
tldr: "Research copy: what can be read about production Firebird triggers and the change feed to GCP, with the trigger catalogue, DBA queries and gaps (Selector V4-Server-Database at 82dde6b, 2026-11-11)."
status: research-copy
---
This is a research copy of the findings file `firebird-triggers-findings.md`, kept in the vault so it can be found and cited. The synthesis is [[Systems/ecm/firebird-change-feed]]. Where the two differ, the synthesis note is the later reading. Direct-message text is paraphrased and no credentials are kept. Nothing was edited in Confluence, a repo or Firebird.

# Production Firebird triggers and the change feed: findings (11 Nov 2026)

Read-only research. No database or host was contacted. No Slack, Jira, Confluence or vault writes. Slack and Confluence text is treated as data.

Status tags: CONFIRMED (read in source or DDL), STATED (a document says it), UNKNOWN. A document that describes a trigger stays STATED until the trigger source is seen. Nothing below is production DDL: the only trigger source we can read is Selector's own update scripts, last committed in 2023.

## 1. Headline

1. **Two change feeds leave central Firebird, and we can read the DDL for neither in full.**
   - **Feed A, `TRANSFER_QUEUE` to the Firebird Transfer Service to `fb.*` topics.** STATED only. The AFTER triggers that write `TRANSFER_QUEUE` are in no source we can read.
   - **Feed B, `POST_EVENT 'UPLOAD_2_GCP'` to an unnamed publisher ("GFSPublisher").** The trigger is CONFIRMED in source. The publisher is STATED and its code is unread.
2. **The `TRANSFER_QUEUE` trigger text is not in the Selector source.** `V4-Server-Database` holds a 2014 base schema plus incremental scripts `update_1` to `update_411` and `4.50.0.1`. `TRANSFER_QUEUE` appears nowhere in it (grep over all local clones: zero hits outside the vault, the knowledge-system repo and the IRIS toy schema). The Tech Services vault reached the same conclusion on 15 Jul 2026.
3. **The most likely home of the `TRANSFER_QUEUE` trigger DDL is the Firebird Transfer Service repo's `sql/` folder (ADO, project GFS Legacy Migration, sha 8569227).** An earlier session cited `sql/0` to `sql/4`, including `sql/4_fts_doppelganger_updates_3.sql`, and drew "new shipments plus a filtered set of updates, about 1.8 per new shipment" from it. I could not re-read it. The ADO local MCP failed to connect and the remote ADO MCP needs a browser OAuth step that I did not start. That repo is not cloned anywhere on this machine. This is the one artifact to fetch first.
4. **Even if `sql/` holds the DDL, it is repo SQL, not proof of what runs in production.** Only a `RDB$TRIGGERS` read settles that (section 7).

## 2. Artifacts found, where, and what each held

Ranked by closeness to DDL or code.

| # | Artifact | Where found | Holds trigger DDL? | What it gave |
|---|---|---|---|---|
| 1 | Selector `V4-Server-Database` (ADO legacy org, project Legacy GFS Ticketing, repo `V4-Server-Database`), local clone `/home/hjf/code/selector/V4-Server-Database` at `82dde6b` (2023-10-11, "Initial source commit") | Local clone. A Selector team member named the V4 repo in a direct message on 28 Oct, but this is a different, already-cloned repo of the same project | **Yes, for the Selector-era triggers** (166 in the 2014 base `Updates/server_db.sql`, many more in the updates). **No `TRANSFER_QUEUE` triggers.** | Section 4. `SHIPMENTS_AI2` posts `UPLOAD_2_GCP`. The `RM_REPLICA` triggers. `SHIPMENTS_AU7` feeds the web-scanner queue |
| 2 | Selector `V4-Server-UploadServer` at `5773b8e` (2026-04-15), `IUploadServerImpl.pas`, `uplConst.pas` | Local clone | No, but it is the consolidation code | Uploads call `REG_SHIPMENTS`, `REG_SHIP_ITEMS`, `REG_SHIP_CUSTOMS`, `REG_SHIP_UNITS`, `REG_SHIPPER` and `REG_SHIP_INFO` (`uplConst.pas:66-268`). It issues no direct `UPDATE shipments` |
| 3 | Confluence 206274620, *Modernizer Shipment Data Ingestion: Firebird Transfer Service Bypass and Message Format Overview* (Carrier Integrations, 4 Jun 2026, v1) | Confluence search | No | Best description of the Transfer Service's output. STATED (author read the repo config and modernizer). Section 5 |
| 4 | `ilg-tech-services/knowledge-system` vault (clone `apiky-survey/gh/ilg-tech-services_knowledge-system` at `3493146`): `guides/firebird-to-ecm-sync-and-write-back.md`, `systems/legacy-manager-write-path.md`, `systems/firebird-legacy-db.md`, `systems/legacy-capability-register.md`, `systems/royal-mail-synchdataservice.md`, `systems/ecm-cacs.md`, `issues/ecm-sfp-country-code-overwritten-missing-deduplicator.md` | Local clone, found by grep | No. Describes triggers from a metadata read of the Test replica on 10 Jul 2026 | Trigger counts, `TRANSFER_QUEUE` columns, the `GFSPublisher` lead, the unidentified publisher. All STATED |
| 5 | Datadog metric names `gfs.firebird_transfer_service.*` and `gfs.firebird_transfer_service_weblogins.*`; `#sre-alerts` monitors | Metric search; Slack search | No | Names only: `read_transfer_list.select`, `read_transfer_list.delete`, `get_table_data.select`, `recieved_events`, `queue_length`, `rows_transfered`, `retry_count`, `heartbeat_successes`, `bulkhead_rejections`. No values were queried |
| 6 | Two claude.ai artifacts a Selector team member shared in a direct message (4 Nov): a Selector deep-dive page and an issues page for the `fb.*` feed | Slack, read via the Artifact tool | No | Only a trigger count (345), the `fb.*` topics and `GFSPublisher` in an architecture diagram, and a note that `TRANSFER_QUEUE` and `rm_replica` carry the transfer-service and Royal Mail feeds. No mechanics |
| 7 | Slack direct messages with the Selector team, 27 Oct to 11 Nov | Slack | No | Section 6 |
| 8 | Slack `#sre-alerts` (22 and 25 Oct), `#incidents` (18 May) | Slack search | No | Monitors on `gfs.firebird_transfer_service.rows_transfered` and `queue_length`. A May incident note says invoices are replicated into ECM, so the transfer service had already moved them |
| 9 | `ilg-tech-services/iris` `code/tools/diff-harness/testdb/schema.sql` at `bc69193` | Local clone | Looks like it, **is not** | Its own header calls it "a toy SRV_GFS" built from the vault note. It must not be cited as production DDL |
| 10 | Vault: `Systems/ecm/architecture.md`, `known-context.md`, `Systems/selector/architecture.md`, Explainers 2026-11-06, Handovers 2026-11-09 | Local vault | No | Existing position (section 8). Nothing here is repeated beyond what is needed |

Not reachable: ADO (local MCP failed to connect; remote MCP not authenticated). `ilg-tech-services/database-connector` `SnapshotService.cs` came up in GitHub code search for `TRANSFER_QUEUE` but returned 403 (SAML) on read, so it is unread. A Parcel Portal screenshot in the direct messages held nothing relevant. The MPK whiteboard 351601015 (*Legacy Selector - Component Diagram*, Harry's) was not opened. Confluence SRE page 275873798 (connectivity) was not read for triggers; its title and the vault note suggest none.

Other Confluence hits (searched in all spaces for `TRANSFER_QUEUE`, "Firebird Transfer Service", `POST_EVENT`, "firebird trigger", `CREATE TRIGGER`, "change data capture", `REG_WILKO`, `fb.shipments`, `GFSPublisher`): the Merak (MPK) pages, 206274620, Data Solutions page 67633184 (*Firebird - Incremental Extraction Analysis*, Dec 2025: BigQuery pipeline delta columns such as `INSERT_DATE` and `ship_pieces_hist.ID`; extraction is by query, not by trigger) and unrelated Bifrost pages. No Confluence page holds trigger DDL.

## 3. The trigger picture in one table

| Layer | What exists | Status |
|---|---|---|
| Selector-era business triggers on `SHIPMENTS` and `SHIP_PIECES` (status cascade, notifications, history, web-scanner queue) | 16 on `SHIPMENTS`, 10 on `SHIP_PIECES` in source | CONFIRMED in source (2023 snapshot) |
| `SHIPMENTS_AI2` posts event `UPLOAD_2_GCP` on every insert | Source | CONFIRMED in source; whether it is active in production is UNKNOWN |
| `TRANSFER_QUEUE` triggers (`CUSTOMERS_AI1`, `CUST_SITES`, `CUST_CONTRACTS` and "more") | Named in the vault note, which says they are AFTER triggers writing `(ROW_IDS, TABLE_NAME, EVENT_TYPE)` | STATED. Trigger text UNKNOWN |
| Whether `SHIPMENTS` and `SHIP_PIECES` have `TRANSFER_QUEUE` triggers | The vault note says Test has "~25" triggers on `SHIPMENTS`; source has 16 | UNKNOWN which ~9 are extra and what they do |
| Firebird Transfer Service drains the queue and publishes `fb.*` | Confluence 206274620 and the vault | STATED |

## 4. Catalogue: triggers in the Selector source (CONFIRMED in `V4-Server-Database/Updates` at `82dde6b`)

Reconstructed by applying the scripts in order (`server_db.sql`, then `update_N.sql` by number). Latest definition shown. Production may differ: the repo snapshot is October 2023, and the Test replica reports about 25 triggers on `SHIPMENTS` against 16 here. No credentials are in these excerpts.

### `SHIPMENTS` (16)

| Trigger | Event, position | Source file | One-line behaviour |
|---|---|---|---|
| `SHIPMENTS_BI0` | before insert, 0 | `update_334` | Large status and carrier rewrite on insert (not read in full) |
| `SHIPMENTS_BI` | before insert, 1 | `update_298` | Sets `doddle_store_id` from `DODDLE_STORES` for click-and-collect contracts |
| `SHIPMENTS_BI2` | before insert, 1 | `update_411` | PACKETA new shipments get status 202. GFS INTERNATIONAL `EEUT` gets 1000, `2CRT` gets 200 |
| `SHIPMENTS_AI0` | after insert, 0 | `update_91` | Royal Mail OBA alert event, deletes `ship_info`, Nightline and P2P hooks |
| `SHIPMENTS_AI1` | after insert, 1 | `update_164` | Deletes `future_parcel_hist` rows older than 90 days |
| `SHIPMENTS_AI2` | after insert, 3 | `update_285` | `POST_EVENT 'UPLOAD_2_GCP'` |
| `SHIPMENTS_AI3` | after insert, 0 | `update_316` | If status 100 or 200 to 999, inserts a row into `SHIPMENTS_SCANNING` (web-scanner work queue) |
| `SHIPMENTS_BU0` | before update, 0 | `update_133` | Sets `deliv_parcels`, rewrites status 98, Royal Mail 1005 and 3000 rules |
| `SHIPMENTS_B2U` | before update, 1 | `update_304` | For COLLECT+ turns 100 to 200+ into 101 |
| `SHIPMENTS_AU0` | after update, 0 | `update_133` | On some status changes copies the status to `ship_pieces`. Writes `del_ship_use` when old status is 100 |
| `SHIPMENTS_AU1` | after update, 1 | `server_db.sql` | Writes `ships_comments` when `gfs_comments` changes (history insert is commented out) |
| `SHIPMENTS_AU2` | after update, 2 | `server_db.sql` | On notifiable status changes calls `ADD_NOTIFY_ITEM` |
| `SHIPMENTS_AU4` | after update, 4 | `update_181` | On status 1005 or 1006 sets all live parcels to that status with "ASSUMED DELIVERED" |
| `SHIPMENTS_AU5` | after update, 5 | `update_245` | P2P and status 3000 to 3002: updates parcels and writes `ship_pieces_hist` |
| `SHIPMENTS_AU7` | after update, 0 | `update_330` | If status becomes 200, inserts into `SHIPMENTS_SCANNING` if absent |

Gaps in the numbering (`SHIPMENTS_AU3`, `AU6`, `AI4` onward) are the likeliest place for the ~9 triggers that exist in production but not here. That is an inference from naming, not evidence.

### `SHIP_PIECES` (10)

| Trigger | Event, position | Source file | One-line behaviour |
|---|---|---|---|
| `SHIP_PIECES_BI0` | before insert, 0 | `update_202` | Insert defaults and carrier rules (not read in full) |
| `SHIP_PIECES_BI1` | before insert, 1 | `update_200` | Parcel-history fill (not read in full) |
| `SHIP_PIECES_AI0` | after insert, 0 | `server_db.sql` | Nightline service 53: calls `REG_NL_CL_ITEM` |
| `SHIP_PIECES_AI1` | after insert, 1 | `update_200` | Moves `future_parcel_hist` scans into `ship_pieces_hist`, then calls `set_shipment_state_by_pieces` |
| `SHIP_PIECES_BU0` | before update, 0 | `update_190` | For 101 to 200 copies the latest history scan onto the parcel |
| `SHIP_PIECES_BU1` | before update, 1 | `update_304` | COLLECT+ 101 rule, as on `SHIPMENTS` |
| `SHIP_PIECES_AU` | after update, 1 | `server_db.sql` | `del_ship_use` counting when status goes from 100 to 200+ |
| `SHIP_PIECES_AU0` | after update, 0 | `server_db.sql` | Calls `ADD_NOTIFY_ITEM` on status 200 to 999. History insert is commented out |
| `SHIP_PIECES_AU2` | after update, 2 | `server_db.sql` | Nightline 53 item registration |
| `SHIP_PIECES_AU3` | after update, 3 | `update_190` | Calls `set_shipment_state_by_pieces` after a 101 to 200+ move with history |

**No source trigger on either table writes a queue row for the `fb.*` feed.** The only publish-style signal is `SHIPMENTS_AI2`. There is no `SHIP_PIECES` equivalent, so parcel messages (`fb.ship_pieces.v1`) must come from the Transfer Service queue or from something we cannot see.

### Related event and queue triggers (CONFIRMED in source)

| Trigger | Table | Effect |
|---|---|---|
| `RM_REPLICA_AI` (`update_335`) | `RM_REPLICA` | `post_event('RM_REPLICA')` on every queue insert |
| `CUSTOMERS_AI/AU/AD`, `CUST_SITES_*`, `CUST_CONTRACTS_*` (Royal Mail only), `CUST_CONTRACT_SERVICES_*`, `CUST_RM_PRODUCTS_*`, `RM_OBA_PARAMS_*`, `SHIP_RANGES_*` and others (`update_335`, `350`, `368`, `398`) | various | Insert `(tbl_name, replica_act 0/1/2, keys, new_keys)` into `RM_REPLICA`. Update triggers fire only on named column changes. Consumed by the Royal Mail sync service (STATED, vault) |
| `RELOAD_PUBLISH_SHIPMENTS_AI` (`update_285`) | `RELOAD_PUBLISH_SHIPMENTS` | `POST_EVENT 'RELOAD_2_GCP'`. The table is a re-publish request: customer, site, carrier, consignment range, despatch and publish date ranges |
| `update_285` DDL | `SHIPMENTS` | Adds columns `SHIP_PUBLISHED` (default 0), `PUBLISH_OBJ`, `PUBLISH_DATE`, then sets every existing row to `SHIP_PUBLISHED = 2`. Nothing else in source writes these columns, so the 0, 1, 2 state machine (STATED in the vault) lives in the external publisher |
| `update_210`, `386`, `388` | DHL and contract-services tables | `ALTER TRIGGER ... INACTIVE/ACTIVE`. Shows triggers are toggled in production by scripts |

Event names posted elsewhere in the scripts: `RM_OBA_ALERT`, `P2P_ADD`, `WARN_ALERT`, `ERROR_ALERT`, `LOOP_ALERT`, `RECYCLE_ALERT`, `RECYCLE_SHIPS`, `CARR_UPDATE`, notifier events, `LOCK_STATUS`, `SHIP_UPLOADED`, `SITE_UPDATED`. The last four are in client-database scripts, not the central database.

## 5. How a change in central Firebird becomes a message

### What the sources say (STATED, Confluence 206274620, 4 Jun 2026)

- "Modernizer currently receives shipment data from the legacy stack via the Firebird Transfer Service, which polls a transfer queue in Firebird and publishes Pub/Sub messages."
- Mode 1 of the planned Ingestor: `Ingestor, Firebird, Transfer Service, Pub/Sub, Modernizer`. Mode 2 skips Firebird and publishes the same messages itself.
- Envelope: `{published_timestamp, event_type: INSERT|UPDATE|DELETE, event_timestamp, data: {TABLE: {COLUMN: value}, JOINED_TABLE: {...}}, meta: {TABLE: {id_fields, isJoin}}}`. Timestamps are .NET `DateTime` with no zone suffix, server local time.
- `SHIPMENTS` is published with `SHIPMENT_EXTRA` as a joined sub-object (`meta.SHIPMENT_EXTRA.isJoin = true`, id fields `CARRIER`, `CONS_NO`). There is no separate `SHIPMENT_EXTRA` topic. Two modernizer subscriptions read the same topic.
- One message per table row: one `SHIPMENTS` message per shipment, one `SHIP_PIECES` message per parcel. Modernizer joins them in a window (the page says 120 s; the vault and explainers say 180 s).
- The publisher does no enrichment. `SHIP_SHIPPER` is published (`fb.shipment_shipper.v1.prod`) with no consumer. `SHIP_CUSTOMS` and `SHIP_PARCEL_ITEMS` are written by upload but never published.
- Topic names in config are `fb.shipments.v1.prod` and `fb.ship_pieces.v1.prod` in project `gfs-ecm`, which still disagree with prod Terraform (`fb.<x>.v1` in `gfs-ecm-prod-uk1`). Unchanged from the vault.

### What the vault and knowledge system add (STATED, from a metadata read of the Test replica, 10 Jul 2026, verified by a Selector team member)

- Triggers on `CUSTOMERS`, `CUST_SITES`, `CUST_CONTRACTS` "(and more)" insert `(ROW_IDS, TABLE_NAME, EVENT_TYPE)` into `TRANSFER_QUEUE`. The Manager source never touches `TRANSFER_QUEUE` or `rm_replica`.
- `TRANSFER_QUEUE` has a `RETRY_COUNT` column and a `TRANSFER_QUEUE_DEAD_LETTER` table (142,439 rows on Test, probably because no consumer ran there).
- `CUSTOMERS_AI1` is named as the `TRANSFER_QUEUE` trigger. It is not in source. `CUSTOMERS_AI`, `AI1` and `AI2` are named in the vault as the customer-first-trade, `TRANSFER_QUEUE` and `rm_replica` triggers.
- Event type values are 0, 1, 2 for insert, update, delete in the `rm_replica` source. For `TRANSFER_QUEUE` the toy schema guesses the same; the vault does not state it. UNKNOWN.
- Deletes: `rm_replica` captures deletes (source, `CUSTOMERS_AD`). The vault says contract deletes write delete rows to both queues. For `SHIPMENTS` and `SHIP_PIECES` deletes: UNKNOWN. Shipments are soft-deleted by status 100, and `isDeleted` is derived from status 100 downstream.

### Metric evidence for the Transfer Service's mechanics (names only, not queried)

`read_transfer_list.select` and `read_transfer_list.delete`, `get_table_data.select`, `recieved_events`, `queue_length`, `rows_transfered`, `retry_count`, `heartbeat_successes`, `reconnection_attempts`, `bulkhead_rejections`. These suggest: read a transfer list, fetch each row's table data, publish, delete the transfer-list row, retry on failure, react to received Firebird events. That is a reading of metric names, so STATED at best. A second instance, `firebird_transfer_service_weblogins`, reports the same metrics (a web-logins feed, presumably `fb.web_users.v1`; UNKNOWN). In `#sre-alerts` a monitor "Firebird Replication Service not replicating any data" fires when `rows_transfered` is 0 for 2 hours (25 Oct, recovered within a minute), and a "Queue Length" monitor fires above 10,000 (a test notification on 22 Oct).

### Feed B: the shipment publisher driven by Firebird events (CONFIRMED trigger, STATED consumer)

- `SHIPMENTS_AI2` posts `UPLOAD_2_GCP` after every shipment insert. `RELOAD_PUBLISH_SHIPMENTS_AI` posts `RELOAD_2_GCP` for re-publish requests. `SHIP_PUBLISHED` starts at 0.
- The vault names the listener as `GFSPublisher` (ADO `V6`, .NET Framework `GCPUploadService`, Datadog prefix `gfs.legacy-publisher.*`), publishing `SHIPMENTS` to a GCP Pub/Sub topic with `SHIP_PUBLISHED` going 0, 1, 2. That source was not read by us or, as far as the notes show, by anyone this year; the vault cites it as read ("nearest identified precedent"). A Selector team member's architecture diagram also lists the `fb.*` topics and `GFSPublisher`.
- **Open point.** It is unknown whether Feed B and Feed A both exist in production, which one produces `fb.shipments.v1`, and whether the Transfer Service replaced the publisher or runs beside it. The Transfer Service queue, the shipments deduplicator and the `.prod` topic names make a second shipment path plausible. `gfs.legacy-publisher.*` metrics were not in the first 709 metric names returned and were not checked.

### Ordering, batching, failure and resume (all UNKNOWN for the Transfer Service)

Not read anywhere: batch size, cadence, ordering within a table, whether a row is deleted from the queue before or after the publish returns, what resumes after a crash (the `RETRY_COUNT` column and dead-letter table suggest retry and park), and how the `SHIPMENT_EXTRA` join is read (the message carries it, so the service joins at read time). The vault's Datadog work gives a shipment median lag of 7.5 s and p95 under 10 s, which says the poll is fast, not how it batches.

## 6. Local to central consolidation and the triggers

- **Path (STATED by a Selector team member, 4 Nov direct message; matches vault).** Client4 (or CSS with Client4 as uploader) exports from the site Firebird to the upload server, which consolidates into the main Firebird. In their account the pub/sub push starts from the main Firebird, not from CSS, Client4 or the site database. They also said that few people know fully what the pipeline does, and that the terminology may be off because it comes from internal team documents. Treat this as STATED, with the source as informed but not authoritative.
- **Upload writes by stored procedure (CONFIRMED in `V4-Server-UploadServer/uplConst.pas:66-268`).** `REG_SHIPMENTS` per shipment, `REG_SHIP_ITEMS` per parcel, then customs, units, shipper and ship info. There is no `COPY` or direct table write for shipments.
- **Consolidation fires the insert triggers (CONFIRMED in source, `update_284.sql` `REG_SHIPMENTS`).** The procedure does plain `INSERT INTO shipments` when the consignment is absent, so every `AFTER INSERT` trigger fires, including `SHIPMENTS_AI2`. Source-level reading of `update_284.sql:195-401`.
- **A repeated upload does not update `SHIPMENTS` (CONFIRMED in source, same file).** If the consignment and carrier already exist, the procedure copies the old row to `RECYCLE_SHIPS` only when key fields differ (despatch date, site, contract, service, packs, address line 1, town, postcode, country), and does not run an `UPDATE shipments` in that block. A `REG_SHIP_ITEMS` path writes `RECYCLE_ITEMS` for duplicate parcels. A status 106 upload sets the shipment to 106. I read the start and the insert branch; the recycle, swap and carrier branches (DHL Express exworks, UK Mail, Parcelline and Interlink) are not read line by line.
- **Replace or rename visible as delete plus insert?** UNKNOWN for the Manager's "recycle-replace" and for any copy-then-delete path. The source has `delete from shipments` only in the swap-consignment branch of `REG_SHIP_ITEMS` (`update_284.sql:1681-1684`) and a commented-out block. Whether a delete reaches `fb.shipments.v1` as `DELETE` depends on trigger text we cannot read.
- **Consequence to test, not conclude.** Upload alone appears to generate one INSERT per shipment and one per parcel. The "about 1.8 updates per new shipment" seen on the topic therefore comes from later status writes (scan procedures, the Scan Injector, `CHECK_SHIP_STATUS`) passing whatever filter the feed applies. The source triggers that react to those writes are in section 4. The filter itself is the unread part.

## 7. Gaps, the DBA queries, and questions

### What is missing, exactly

1. The text of every `TRANSFER_QUEUE` trigger. It is in neither `V4-Server-Database` nor any other readable repo. Candidate locations: the Firebird Transfer Service repo `sql/` folder (ADO, GFS Legacy Migration, 8569227), which the ADO MCP could not reach; the unread `V6` repo (`GFSPublisher`, `SynchDataService`); production itself.
2. The 9 or so extra production triggers on `SHIPMENTS` (and any extra on `SHIP_PIECES`).
3. The live Transfer Service config: table list, topic names, project, poll interval, batch size.
4. The `GFSPublisher` code and whether it is running.
5. Whether `SHIPMENTS_AI2` and the `TRANSFER_QUEUE` triggers are ACTIVE in production.

### Read-only queries for a DBA (Test replica first, then production)

```sql
-- 1. Every user trigger, with type and active flag
SELECT RDB$TRIGGER_NAME, RDB$RELATION_NAME, RDB$TRIGGER_TYPE, RDB$TRIGGER_SEQUENCE, RDB$TRIGGER_INACTIVE
FROM RDB$TRIGGERS
WHERE COALESCE(RDB$SYSTEM_FLAG,0) = 0
ORDER BY RDB$RELATION_NAME, RDB$TRIGGER_NAME;

-- 2. Trigger source for the two tables
SET BLOB ALL; SET LIST ON;
SELECT RDB$TRIGGER_NAME, RDB$TRIGGER_TYPE, RDB$TRIGGER_SEQUENCE, RDB$TRIGGER_INACTIVE, RDB$TRIGGER_SOURCE
FROM RDB$TRIGGERS
WHERE COALESCE(RDB$SYSTEM_FLAG,0) = 0
  AND RDB$RELATION_NAME IN ('SHIPMENTS','SHIP_PIECES','SHIPMENT_EXTRA','SHIP_PIECES_HIST')
ORDER BY RDB$RELATION_NAME, RDB$TRIGGER_TYPE, RDB$TRIGGER_SEQUENCE;

-- 3. Every trigger that touches the queue or posts an event (pattern search, no row data)
SELECT RDB$TRIGGER_NAME, RDB$RELATION_NAME, RDB$TRIGGER_INACTIVE
FROM RDB$TRIGGERS
WHERE COALESCE(RDB$SYSTEM_FLAG,0) = 0
  AND (UPPER(RDB$TRIGGER_SOURCE) CONTAINING 'TRANSFER_QUEUE'
    OR UPPER(RDB$TRIGGER_SOURCE) CONTAINING 'POST_EVENT');

-- 4. Queue shape (no rows)
SELECT RDB$FIELD_NAME, RDB$FIELD_SOURCE FROM RDB$RELATION_FIELDS
WHERE RDB$RELATION_NAME IN ('TRANSFER_QUEUE','TRANSFER_QUEUE_DEAD_LETTER')
ORDER BY RDB$RELATION_NAME, RDB$FIELD_POSITION;

-- 5. Which tables feed the queue (counts only)
SELECT TABLE_NAME, EVENT_TYPE, COUNT(*) FROM TRANSFER_QUEUE GROUP BY 1, 2;
```

Run 1 to 4 on Test (a day-behind restore, already used for read-only metadata). Query 5 reads only counts and is best run on production by the DBA in a quiet period. If ADO becomes reachable, reading `sql/` in the Transfer Service repo is cheaper and settles most of the same ground, but still needs query 1 to prove it is what runs.

### Questions for the DBA and the service owners

1. Which service reads `TRANSFER_QUEUE`: the Firebird Transfer Service, `GFSPublisher`, or both? Does the queue row get deleted after publish, or flagged?
2. Which tables are in the live Transfer Service config, and what topic and project names does it publish to (the repo config says `fb.<x>.v1.prod` in `gfs-ecm`, Terraform says `fb.<x>.v1` in `gfs-ecm-prod-uk1`)?
3. Does the `SHIPMENTS` feed publish every update or a filtered set, and where is the filter (trigger `WHEN` logic, or service code)? Do `SHIP_PIECES` updates and `SHIP_PIECES_HIST` inserts publish?
4. Are deletes captured for `SHIPMENTS`, `SHIP_PIECES`, `CUSTOMERS`, `CUST_SITES`, `CUST_CONTRACTS`?
5. What are the live `EVENT_TYPE` codes?
6. How does the service batch, order and resume after an outage, and what drives the `RETRY_COUNT` and dead-letter handling?
7. Is `GFSPublisher` (`UPLOAD_2_GCP`) running, and does it publish a different topic from the Transfer Service?
8. Who owns the Transfer Service deploy and config? (The 6 and 7 Oct stand-ups named Rob Fletcher as a possible owner; unconfirmed.)

## 8. Existing vault position, checked so nothing is repeated

- `Systems/ecm/architecture.md` (seam 1, G1) says nobody has read the production triggers. This note adds: the Selector-era `SHIPMENTS` and `SHIP_PIECES` trigger source exists and is readable, that `SHIPMENTS_AI2` posts `UPLOAD_2_GCP` (a second feed the ECM notes do not mention), and that the `TRANSFER_QUEUE` DDL is the part that is missing.
- `Systems/ecm/known-context.md` already lists "the production Firebird triggers on `SHIPMENTS` and `SHIP_PIECES`" and "the Transfer Service's deployed config" as open. Both stay open, but the first is now narrower (queue triggers, not business triggers).
- The earlier explainer line "Firebird replicates new shipments and a filtered set of updates ... CONFIRMED" rests on `sql/4_fts_doppelganger_updates_3.sql` in the Transfer Service repo. This session could not re-read it, so it should be marked STATED until re-read. It is repo SQL, not the production trigger text, which the same explainer admits.
- `GFSPublisher` and `UPLOAD_2_GCP` appear nowhere in the vault yet.
- Source hygiene note: the Selector clones are ADO legacy repos at `V4-Server-Database 82dde6b` (Oct 2023), `V4-Server-UploadServer 5773b8e` (Apr 2026), `CSS-Enterprise 3650bfb` (Aug 2025). Only the first is old enough to lag the production database by years.

## 9. Evidence references

- `selector/V4-Server-Database@82dde6b` `Updates/update_285.sql` (`SHIPMENTS_AI2`, `RELOAD_PUBLISH_SHIPMENTS_*`, `SHIP_PUBLISHED`), `update_312.sql`, `316`, `330` (`SHIPMENTS_AI3`, `AU7`, `SHIPMENTS_SCANNING`), `update_133.sql:224-244` (`SHIPMENTS_AU0`), `update_181.sql:33-` (`AU4`), `update_245.sql:838-` (`AU5`), `update_164.sql`, `update_190.sql`, `update_200.sql` (parcel triggers), `update_304.sql`, `update_335.sql`, `350`, `368`, `server_db.sql:13483-13913` (2014 base `SHIPMENTS` and `SHIP_PIECES` triggers), `update_284.sql:3-` (`REG_SHIPMENTS`; recycle block 195-401).
- `selector/V4-Server-UploadServer@5773b8e` `uplConst.pas:45-268`.
- Confluence 206274620 (Carrier Integrations, 2026-06-04); 67633184 (Data Solutions, 2025-12-08).
- `knowledge-system@3493146` `vault/guides/firebird-to-ecm-sync-and-write-back.md` (section 1, pending-research paragraph), `vault/systems/legacy-manager-write-path.md` (global mechanisms), `legacy-capability-register.md` (evidence log, 2026-07-10), `royal-mail-synchdataservice.md`.
- Slack direct messages with the Selector team: 28 Oct (source location and access), 27 Oct (a Tech Services pointer), 4 Nov (CSS, Client4, upload server, where the push starts, the shared artifacts, the whiteboard). Slack `#sre-alerts` 22 and 25 Oct 2026, `#incidents` 18 May 2026. Message text is paraphrased, not quoted.
