Selector and ECM cannot be replaced one at a time. Central Firebird couples them in both directions. Selector's uploads are ECM's only source of shipments, and ECM's tracking writes back the status that billing and Seeker read.

This page maps each seam, says what breaks if either side goes first, lists duties the old systems perform without anyone having written them down, and names three places a replacement could take over. It gives evidence and options. The choice between them is the Merak team's. Volumes cover the 15 days to 6 Nov 2026 unless stated. The full path of one shipment is on [Shipment Journey Through ECM](https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/354975746/Shipment+Journey+Through+ECM).

## In short

- **ECM learns of a Selector shipment only after Selector uploads it** into central Firebird. Slipway is a second source, for Amazon shipments, at pilot volume.
- **ECM writes status back into Firebird.** A Dataflow job and an on-prem Scan Injector set `SHIPMENTS.STATUS`. Bill-on-scan billing and Seeker read it.
- **Six seams carry all of this.** The table below lists them.
- **Replacing one side first breaks the other.** Replace Selector first and ECM loses its shipments and reference data. Replace ECM first and Firebird loses its scans and status.
- **Retiring Firebird means taking over every seam,** because billing, reference data, scans, tickets and manual status all read or write it.

## The six seams

| Seam | Runs from and to | What crosses | Who depends on it |
| --- | --- | --- | --- |
| 1. Shipments | Selector to central Firebird to ECM | Each uploaded shipment becomes `fb.shipments.v1`, then `shipments.v2`, then `shipments.v2.identified`. 17 subscriptions in the ECM project and 2 webhook subscriptions receive the last one | Tracking, customer and staff portals, claims, proof of delivery, reporting |
| 2. Scans and status | ECM to central Firebird | `raw_tracking.v1` events become legacy-shaped scans on `scanners.consignments.V1`. The Scan Injector then sets parcel and shipment status. It received 4.51M messages | Bill-on-scan billing, Seeker scan history |
| 3. Manual changes | Portals and agents to Firebird, partly echoed to ECM | Mark as deleted or delivered, customer care status changes, tickets, comments, collections | Staff, customers, claims, support |
| 4. Reference data | Firebird to ECM | Customers, contracts, carriers and products as `fb.*` change feeds. Carrier credentials as `carrier-credentials.v1` | Customer and contract lookups, carrier names, tracking connectors, proof of delivery |
| 5. Billing | Firebird to billing to ECM | The billing app reads `SHIPMENTS`. Invoices return as `invoices_published.v1` and `invoiced_shipments_published.v1` | Finance, claims, portals |
| 6. Identity | `shipment-identity-service` | Consignment number plus carrier gives each shipment its ID. Invoice lines match on that same pair | Every ECM store, invoice matching |

The seams form a loop. ECM scans change Firebird rows, and those changes flow back into ECM as re-announcements. About 610k `SHIPMENTS` updates arrive a week. About 162k land inside the 180 s window and are absorbed, and 449k re-announce a known shipment. Daytime Scan Injector writes appear to cause about half of the updates.

## If Selector goes first

- **ECM stops learning of new shipments.** Nothing starts tracking, and portals, claims and reporting see nothing new, unless the replacement publishes `shipments.v2` or the `fb.shipments.v1` message that feeds it.
- **Reference data stops flowing.** Customers, contracts, carriers and credentials reach ECM from Firebird change feeds.
- **Billing loses its rows.** Finance bills from central `SHIPMENTS`. See [Legacy Selector - Day End and Billing Handoff](https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/353566845/Legacy+Selector+-+Day+End+and+Billing+Handoff).
- **Day end disappears.** That covers commit, upload, carrier manifests and pre-advice files.

## If ECM goes first

- **Firebird stops receiving scans.** Status stops moving past 200, apart from Firebird's own "assumed delivered" closure (1005) after the maximum scan days.
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

The first three rows come from a December 2025 dump of the central procedures and from the Scan Injector's error logs. The live database may differ.

## Three cut points

Each of these has a defined message or call and an alternative producer or consumer, so a replacement can take over there without cutting the seam.

1. **The shipment message.** A replacement for Selector, Firebird and the Transfer Service can publish what `gfs-modernizer` publishes (`shipments.v2`) or what the Transfer Service publishes (`fb.shipments.v1`). Slipway already does the second for Amazon shipments: about 66 records since August 2026. A new publisher needs carrier almanac entries, the customer's company name and the parcels in the same message.
2. **The scan write-back.** A replacement for ECM's tracking can publish legacy-shaped scans to `scanners.consignments.V1`. The Scan Injector then keeps writing Firebird. `patina-service-2` does this today from `raw_tracking.v1`.
3. **The manual status route.** The legacy shipment update service sets `STATUS` 100 or 1003 for one consignment and carrier. A replacement for the portals can keep calling it.

Each cut point keeps the legacy side running. None removes Firebird.

## Not confirmed yet

- **The production Firebird triggers.** The repo script has a syntax error and allows fewer updates than prod sends. They decide what reaches ECM.
- **Which carriers hold the 1,309 bill-on-scan contracts,** and which carriers `patina-service-2` writes back. Its list sits in an Azure DevOps variable group. Together they show who would stop billing if ECM went first.
- **Who owns `patina-service-2` and the Scan Injector.** No team does.
- **What else reads `SHIPMENTS.STATUS`.** The billing app and Seeker are confirmed. The full list is not.

## Sources

- **ECM and Firebird path:** [Shipment Journey Through ECM](https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/354975746/Shipment+Journey+Through+ECM) and its sources.
- **Billing:** [Legacy Selector - Day End and Billing Handoff](https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/353566845/Legacy+Selector+-+Day+End+and+Billing+Handoff) and Billing space page 311394359.
- **Central Firebird procedures:** a December 2025 dump in `gfs-data-services/gfs-pipelines`, plus Datadog logs from the Scan Injector.
- **Volumes:** Datadog application metrics.
