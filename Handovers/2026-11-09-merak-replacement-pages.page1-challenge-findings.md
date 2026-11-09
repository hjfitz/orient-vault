Findings from the challenge to "Selector and ECM Coupling" (MPK 354418743), 9 Nov 2026. Three agents read the code from different lenses. Harry's view was that Firebird is a seam.

## Verdict

The lead sentence overstates. Selector and ECM can each be replaced behind Firebird if the replacement honours Firebird's contract on its side. Firebird is a real contract, but a leaky one. Neither side can go without it.

## The contract at Firebird

| What | Written by | Read by | Seam-like? |
| --- | --- | --- | --- |
| Shipment row, keyed on `(CONS_NO, CARRIER)` | Selector upload (`REG_SHIPMENTS`), DataBridge (`REG_WILKO_SHIPMENT`), Manager | Billing, the Transfer Service, the data platform | Yes. The key is stable |
| Create feed: 13 tables to `fb.*.v1` through `TRANSFER_QUEUE` | The Transfer Service | `node-modernizer`, then ECM | Yes. One way and documented |
| `STATUS` | About 30 procedures: commit, legacy scanners, `SET_SHIPMENT_HIST`, `CHECK_SHIP_STATUS`, portals | Billing, Seeker | No. Many writers |
| Scan write-back | ECM's `patina-service-2` sends raw carrier codes to `scanners.consignments.V1`. The Scan Injector then calls `SET_PARCEL_HIST` and `SET_SHIPMENT_HIST`. Selector's own IE service calls the same procedures | Firebird | Yes. Small message and a defined procedure |
| Manual status | `legacy-shipment-update-service` sets 1003 or 100 | Billing, Seeker | Yes. One narrow route |
| Reference data | The same feed. Credentials cover only six carriers | ECM | Partly |

Firebird derives status itself. `patina-service-2` forwards the carrier's raw code, and `GET_SCAN_CODE` maps it. An unknown code becomes 207.

**What makes it a poor seam.**
- Many writers set `STATUS`.
- Some columns are overloaded, so `node-modernizer` hard-codes carrier rules.
- The December 2025 DDL dump holds no triggers, and nobody has read the production ones.
- Nothing is versioned.
- No team owns `patina-service-2` or the Scan Injector.
- The data platform extracts about 70 tables by JDBC, straight from Firebird.

## Couplings that go around Firebird

- **Slipway** publishes the Firebird-shaped create message straight to `fb.shipments.v1`, bypassing Firebird for ECM. It also exports a masked copy to a Mongo collection for billing. Whether DataBridge writes that copy into Firebird in production is not confirmed.
- **Carrier almanac:** ECM resolves carrier names to Firebird's legacy names, so the vocabulary is Firebird's.
- **No direct Selector to ECM call exists.** A search of the whole Selector repo for Pub/Sub, `raw_tracking`, `tracking-core` and Google APIs found nothing.

## Statements on the page to change

| Statement | Status | Change to |
| --- | --- | --- |
| "Selector and ECM cannot be replaced one at a time." | Overstated | Either can be replaced if the successor honours Firebird's contract on its side |
| "Selector's uploads are ECM's only source of shipments" | Wrong | Selector is the main source. Slipway and DataBridge also feed it |
| "ECM's tracking writes back the status that billing and Seeker read" | Wrong | ECM forwards raw carrier codes. Firebird derives the status |
| "A Dataflow job and an on-prem Scan Injector set `SHIPMENTS.STATUS`" | Overstated | The Dataflow job sets no status. The Scan Injector calls the procedures. Its source is unread |
| "Replace Selector first and ECM loses its shipments and reference data" | Overstated | ECM loses shipments unless the successor publishes them. Reference data stops only if Manager or Firebird retire |
| "Replace ECM first and Firebird loses its scans and status" | Overstated | Only if nothing publishes legacy-shaped scans to `scanners.consignments.V1` |
| A new publisher needs the company name and the parcels in the same message | Wrong | The company is looked up from `CUSTOMER_ID`. Parcels arrive on `fb.ship_pieces.v1`. An unknown carrier is rejected |
| Slipway "already does the second for Amazon shipments" | Incomplete | Slipway also exports a masked copy for billing |
| "Six seams carry all of this" | Overstated | The data platform, Seeker and billing also read Firebird directly |
| `SET_SHIPMENT_HIST` rule: "lowest parcel status of 200 or more" | Imprecise | Ordered by attention level first, then lowest status of 200 or more. 999 when only some parcels are delivered |
| `CHECK_SHIP_STATUS` closes shipments nobody scans | Unverified | The only caller found is commented out |
| Seam 2: "who depends on it" | Missing | Add Selector's IE service as a second writer through the same procedures |
| Seam 4 and set-up | Missing | Manager writes customers and contracts. ECM's reference feeds depend on it |

Cut point 2 and "none removes Firebird" hold. Cut point 2 needs one addition: `carrCode` must be the carrier's raw code.

## Also affects other published pages

- **Carrier Tracking and Proof of Delivery:** "Amazon SFP shipments skip Firebird" is true for the ECM leg only.
- **Diagram text twin** `…diagram-selector-ecm-coupling.md`: regroup around Firebird as the seam, and show Slipway as a second producer.

## Checked by hand

- Slipway's `shipment.mapper.ts` builds a message shaped like a Firebird row (`data.SHIPMENTS`, `CONS_NO`, `CARRIER`).
- Slipway's `usv2export.service.ts` writes a PII-masked copy and keeps postcode and country because they are "needed for billing".
- Selector's `V4-Server-IE/Source/uSQL.pas` runs `SET_PARCEL_HIST` (line 848) and `SET_SHIPMENT_HIST` (line 851).
- Nothing in the Selector repo references Pub/Sub, `raw_tracking`, `tracking-core` or `scanners.consignments`.

## Not verified

- The production Firebird triggers, and whether the filtered update trigger ever ran.
- The Scan Injector source, which is in the unreachable legacy ADO org.
- The billing app and Seeker source.
- Whether DataBridge writes Slipway's export into Firebird in production, and whether its Mongo collection matches Slipway's target.
- The live `shipment-identity-service`. Only a legacy copy was read.
- `patina-service-2`'s supported-carrier list.
