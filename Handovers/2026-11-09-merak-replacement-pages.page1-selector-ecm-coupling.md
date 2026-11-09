Selector and ECM can each be replaced on their own, as long as the replacement honours Firebird's contract on its side. Central Firebird is the seam between them. Selector is the main source of shipments for ECM, and Slipway is a second. ECM sends raw carrier scans back, and Firebird derives the status that billing and Seeker read.

This page maps each seam and says what a replacement must honour if either side goes first. It lists duties the old systems perform without anyone having written them down. It names three places a replacement could take over. It gives evidence and options. The choice between them is the Merak team's. Volumes cover the 15 days to 6 Nov 2026 unless stated. The full path of one shipment is on [Shipment Journey Through ECM](https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/354975746/Shipment+Journey+Through+ECM).

## In short

- **ECM learns of most shipments only after Selector uploads them** into central Firebird. Slipway is a second source, for Amazon shipments, at pilot volume. It publishes the same Firebird-shaped message straight to ECM and also exports a masked copy for billing.
- **ECM sends raw carrier scans back, and Firebird derives the status.** The Scan Injector calls `SET_PARCEL_HIST` and `SET_SHIPMENT_HIST`. Selector's own IE service calls the same procedures. Bill-on-scan billing and Seeker read the result.
- **Six seams carry the Selector and ECM traffic.** The table below lists them. The data platform, billing and Seeker also read Firebird directly.
- **Either side can go first if its successor honours Firebird's contract.** A Selector successor must write central `SHIPMENTS` for billing. It must also publish the create message for ECM. An ECM successor must publish raw carrier scans to `scanners.consignments.V1`.
- **Retiring Firebird means taking over every seam,** because billing, reference data, scans, tickets and manual status all read or write it.

**Diagram:** [Container diagram: Selector, central Firebird and ECM](https://lucid.app/lucidchart/ea0a71eb-4fb1-4124-9fe5-e70720cb5e20/edit?invitationId=inv_3816a5ec-9ded-417b-ae96-e83a761e0214), in Lucid.

## The six seams

| Seam | Runs from and to | What crosses | Who depends on it |
| --- | --- | --- | --- |
| 1. Shipments | Selector to central Firebird to ECM | Each uploaded shipment becomes `fb.shipments.v1`, then `shipments.v2`, then `shipments.v2.identified`. 17 subscriptions in the ECM project and 2 webhook subscriptions receive the last one | Tracking, customer and staff portals, claims, proof of delivery, reporting |
| 2. Scans and status | ECM to central Firebird | `raw_tracking.v1` events become legacy-shaped scans on `scanners.consignments.V1`, carrying the carrier's raw code. The Scan Injector then calls the status procedures, and Firebird maps the code. It received 4.51M messages | Bill-on-scan billing, Seeker scan history. Selector's IE service is a second writer through the same procedures |
| 3. Manual changes | Portals and agents to Firebird, partly echoed to ECM | Mark as deleted or delivered, customer care status changes, tickets, comments, collections | Staff, customers, claims, support |
| 4. Reference data | Firebird to ECM | Customers, contracts, carriers and products as `fb.*` change feeds. Manager writes the customer and contract tables behind them. Carrier credentials as `carrier-credentials.v1`, for six carriers | Customer and contract lookups, carrier names, tracking connectors, proof of delivery |
| 5. Billing | Firebird to billing to ECM | The billing app reads `SHIPMENTS`. Invoices return as `invoices_published.v1` and `invoiced_shipments_published.v1` | Finance, claims, portals |
| 6. Identity | `shipment-identity-service` | Consignment number plus carrier gives each shipment its ID. Invoice lines match on that same pair | Every ECM store, invoice matching |

The seams form a loop. ECM scans change Firebird rows, and those changes flow back into ECM as re-announcements. About 610k `SHIPMENTS` updates arrive a week. About 162k land inside the 180 s window and are absorbed, and 449k re-announce a known shipment. Daytime Scan Injector writes appear to cause about half of the updates.

## If Selector goes first

- **ECM stops learning of new shipments.** Nothing starts tracking, and portals, claims and reporting see nothing new. The exception is a replacement that publishes `shipments.v2` or the `fb.shipments.v1` message that feeds it. Slipway already does this for Amazon shipments.
- **Reference data keeps flowing while Manager and Firebird stay.** Manager writes customers and contracts into Firebird, and the change feeds carry them to ECM. A Selector successor must replace Manager's set-up, or the feeds stop.
- **Billing loses its rows.** Finance bills from central `SHIPMENTS`. See [Legacy Selector - Day End and Billing Handoff](https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/353566845/Legacy+Selector+-+Day+End+and+Billing+Handoff).
- **Day end disappears.** That covers commit, upload, carrier manifests and [pre-advice files](https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/353697842/Carrier+Integration+Methods#Pre-advice-by-file).

## If ECM goes first

- **Firebird stops receiving scans unless the successor publishes them.** A successor that publishes raw carrier scans to `scanners.consignments.V1` keeps status moving. Without it, status stops past 200, apart from manual changes (100 and 1003) and Firebird's own "assumed delivered" closure (1005).
- **Bill-on-scan contracts wait on that status.** They bill only once it passes 200 and is not 310. The Billing space counts 1,309 such contracts.
- **Seeker loses scan history** for new shipments.
- **Customers lose tracking** in the portals, Connect and webhooks, and claims lose the scan dates that open claim windows.

## Duties nobody wrote down

| Duty | Where it lives | Why a replacement inherits it |
| --- | --- | --- |
| Roll parcel scans into one shipment status. It is the lowest parcel status of 200 or more, or 999 when only some parcels are delivered | `SET_SHIPMENT_HIST` in Firebird | Customers see one status per shipment |
| Close shipments nobody scans. Status 1005, "assumed delivered", is set after the maximum scan days | `CHECK_SHIP_STATUS` in Firebird | Without it, unscanned shipments stay open |
| Classify an unknown carrier code. It gets status 207 (202 for DPD and Interlink code 17) and joins a mapping table | `GET_SCAN_CODE` in Firebird | A new carrier code would otherwise break status |
| Absorb bursts of change. `gfs-modernizer` holds each shipment for a sliding 180 s | `gfs-modernizer` | Without a window, every change fans out to every subscriber |
| Guard re-uploads. A known consignment goes to `RECYCLE_SHIPS`. Manager's replace renames the old row and inserts a fresh unbilled copy, which can bill twice | `REG_SHIPMENTS`, System 4 Manager | The same consignment can arrive twice |
| Expire things. Identity lasts 30 days from first insert. Tracking stops 90 days after the last new event | `shipment-identity-service`, `tracking-core` | A re-sent old shipment gets a new ID |
| Hold early scans. The Royal Mail webhook parks about 146k of 343k events until the shipment is known. Evri keeps them up to 90 days | Webhook services | Carriers scan before GFS knows the shipment |
| Carry carrier identity three ways: Firebird's alias, the almanac's legacy name and a numeric ID | `gfs-modernizer`, the carrier almanac | Every ECM store keys on one of them |

The first three rows come from a December 2025 dump of the central procedures and from the Scan Injector's error logs. The live database may differ. The only caller of `CHECK_SHIP_STATUS` in the dump is commented out, so who runs it is not confirmed.

## Three cut points

Each of these has a defined message or call and an alternative producer or consumer. A replacement can take over there without cutting the seam.

1. **The shipment message.** A replacement for Selector, Firebird and the Transfer Service can publish either of two messages. One is what `gfs-modernizer` publishes (`shipments.v2`). The other is what the Transfer Service publishes (`fb.shipments.v1`). Slipway already does the second for Amazon shipments: about 66 records since August 2026. It also exports a masked copy for billing. A new publisher needs the carrier in the almanac, or the message is rejected. The company is looked up from the customer ID, and the parcels travel on `fb.ship_pieces.v1`.
2. **The scan write-back.** A replacement for ECM's tracking can publish legacy-shaped scans to `scanners.consignments.V1`. The scan must carry the carrier's raw code. Firebird maps it, and an unknown code becomes status 207. The Scan Injector then keeps calling the status procedures. `patina-service-2` does this today from `raw_tracking.v1`.
3. **The manual status route.** The legacy shipment update service sets `STATUS` 100 or 1003 for one consignment and carrier. A replacement for the portals can keep calling it.

Each cut point keeps the legacy side running. None removes Firebird.

## Where Firebird is a weak seam

The contract exists, but it is leaky:

- About 30 procedures write `STATUS`, from commit and legacy scanners to the portals.
- Some columns carry more than one meaning, so `node-modernizer` hard-codes carrier rules.
- The December 2025 dump holds no triggers, and nobody has read the production ones.
- Nothing in the feeds or the procedures is versioned.
- No team owns `patina-service-2` or the Scan Injector.
- The data platform extracts about 70 tables straight from Firebird.

## Not confirmed yet

- **The production Firebird triggers.** The repo script has a syntax error and allows fewer updates than prod sends. They decide what reaches ECM.
- **Which carriers hold the 1,309 bill-on-scan contracts,** and which carriers `patina-service-2` writes back. Its list sits in an Azure DevOps variable group. Together they show who would stop billing if ECM went first.
- **Who owns `patina-service-2` and the Scan Injector.** No team does.
- **What else reads `SHIPMENTS.STATUS`.** The billing app and Seeker are confirmed. The full list is not.
- **Whether DataBridge writes Slipway's billing export into Firebird in production.** The code suggests it does. The production configuration was not read.
- **Who runs `CHECK_SHIP_STATUS`.**

## Sources

- **ECM and Firebird path:** [Shipment Journey Through ECM](https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/354975746/Shipment+Journey+Through+ECM) and its sources.
- **Billing:** [Legacy Selector - Day End and Billing Handoff](https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/353566845/Legacy+Selector+-+Day+End+and+Billing+Handoff) and Billing space page 311394359.
- **Central Firebird procedures:** a December 2025 dump in `gfs-data-services/gfs-pipelines`, plus Datadog logs from the Scan Injector.
- **Code read for the Firebird contract:** Slipway `shipment.mapper.ts` and `usv2export.service.ts` at `f604bdd`, Selector `V4-Server-IE/Source/uSQL.pas`, `node-modernizer` `shipment-translator.js`, `patina-service-2` `ReadMe.md` and `FIREBIRD_DDL/procedures.sql` in `gfs-pipelines`.
- **Volumes:** Datadog application metrics.
