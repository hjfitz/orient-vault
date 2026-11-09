A label does not bill anyone. Selector's upload puts a row in central `SHIPMENTS`, and a separate billing app bills that row on the customer's next invoice run. For contracts billed on scan, a carrier scan must also have moved the row's status past 200. This page follows one shipment from label to invoice and names each system on the way.

Billing belongs to Finance, not Selector. It is a Delphi 7 app that reads central `SHIPMENTS` directly, and Selector has no billing interface. Written 9 Nov 2026 from the Billing space and [Legacy Selector - Day End and Billing Handoff](https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/353566845/Legacy+Selector+-+Day+End+and+Billing+Handoff). The billing app facts were read from its source at `develop` @ `3dcdc299` on 15 Sep 2026, and the counts come from Finance queries of a backup to 20 Oct 2026. How scan status reaches `SHIPMENTS` is on [Selector and ECM Coupling](https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/354418743/Selector+and+ECM+Coupling).

## In short

- **Selector sends nothing to billing.** Billing selects one row per consignment number and carrier from `SHIPMENTS`.
- **A shipment bills only if it reaches central.** A station that is off, a commit that never happens or a failed Slipway export loses it, and nothing alerts.
- **Scan-billed contracts wait for ECM.** `BILL_ON_SCAN = 1` bills only when the status is above 200 and not 310.
- **Each customer has its own schedule and there is no cut-off.** A late shipment lands on the next invoice.
- **The pages end at the emailed or printed invoice and the NetSuite file.** Payment collection is not confirmed.

## The chain

| # | Step | System | What happens | Evidence |
| --- | --- | --- | --- | --- |
| 1 | Create the label | CSS (SOAP) or Client4 | A consignment number comes from the site's `SHIP_RANGES`. The shipment and label are saved in the site database `GFS.FDB` | Code |
| 2 | Commit | CSS `CommitShipments`, or Client4 auto-commit | The day's printed shipments close and the database event `SHIP_COMMITED` fires. Fuse's `selector-adapter` never commits, so it relies on each site's auto-commit and auto-upload settings | Code |
| 3 | Upload | Client4 on the station flagged `UPLOAD_STATION = 1` | Client4 catches the event and posts the shipments to the central upload server. CSS cannot upload | Code |
| 4 | Register | Upload server, `REG_SHIP*` procedures | It writes `SHIPMENTS` and `SHIP_PIECES` in central `SRV_GFS.fdb`. It skips a row only when 10 columns match exactly. Otherwise the row goes to a recycle table | Code |
| 5 | Register, second route | DataBridge | Every 10 minutes, in batches of 1,000, it moves carrier manifests, third-party CSVs and Slipway documents from the upload-service MongoDB collection into `SHIPMENTS` through `REG_WILKO_*` | Code. The procedures were not checked |
| 6 | Set the scan status | ECM | For scan-billed contracts, ECM tracking writes the status back to Firebird | See the coupling page |
| 7 | Start the invoice run | Billing app | Each schedule runs standard invoicing, then supplementary, then MANI | Billing source |
| 8 | Freeze the rates | Billing app | Live rate tables are copied to `STG_*`, then archived to `ARCH_*`. If any step fails, the run aborts with no partial recovery | Billing source |
| 9 | Select shipments | Billing app | The query covers the despatch window, the customer, the contract list, the bill trigger and "not yet invoiced". It excludes `DEL_SHIP_USE`, which bills separately as used labels | Billing source |
| 10 | Rate | Billing app | Sale is rated first. Cost is rated only when the sale charge is above 0. The result goes to `INVOICE_SHIPMENT` | Billing source |
| 11 | Build the invoice | Billing app | Fuel is pooled and converted after the loop. Notifications and VAT are calculated, a PDF is made and the invoice is committed. Numbers are allocated at production, and the lines are snapshotted | Billing source |
| 12 | Add supplementary and MANI invoices | Billing app | Carrier EDI charges bill as differences. MANI invoices come from a prepared spreadsheet | Billing source |
| 13 | Send | Billing app | If `EInvoicingEnabled` is set, the invoice is emailed over SMTP to the schedule's To, CC and BCC lists. Otherwise it is printed. The run also writes a Direct Debit CSV and a NetSuite CSV | Billing source |
| 14 | Publish | Finance, then `legacy-invoice-translator` and CCDIS | Finance publishes as a separate step, because runs are sometimes rolled back. The translator writes the files to Cloud Storage and publishes `invoices_published.v1`. CCDIS matches lines to `shipments.v2.identified` on consignment number plus carrier and publishes `invoiced_shipments_published.v1` | Code and Datadog. CCDIS itself was not read |
| 15 | Export to finance | Finance, weekly | `GL_DATA_NETSUITE` writes `netsuite_<from>-<to>.csv`. Accounts import it into NetSuite. Cost posts to 5001 and sale to 4001 | SQL and Finance interviews |

## What billing needs from a row

A replacement for Selector's upload has to write what billing selects:

- one row per consignment number and carrier, with the parcels in `SHIP_PIECES`
- customer, site, contract, service and package
- `DESPATCH_DATE`, packs and weight
- receiver postcode and country, reference and surcharge flags
- `INVOICE_NUMBER` empty or -1, and a contract that is GFS-billed (`BILL_TYPE = 1`)
- the row written exactly once

## When a shipment bills

| `BILL_ON_SCAN` | Rule |
| --- | --- |
| 0 | Bill on upload, for any status except 100 |
| 1 | Bill after the carrier scan: status above 200 and not 310 |
| 2 | GFS International. The mechanism is not confirmed. 94.0% of these shipments carry an invoice number |

Statuses 100, 200 and 310 are data-only statuses from before any carrier scan. Status 1200 has the same description as 100, "formerly shipment cancelled", but value 0 does not exclude it.

## What sets the price

| Input | Keyed on |
| --- | --- |
| Tariff | Customer, carrier, contract and type. Types 0 (sale) and 1 (cost) are rated. Types 100 and 101 are not |
| Charge lookup | Carrier, then contract, charge code, service, package, zone and charge. Service and package fall back to `DFLT` |
| Zones | Origin and destination country plus postcode area, per carrier |
| Weight | The charge weight and billable service, not the actual weight. FedEx volumetric weight applies first |
| Fuel | Per tariff and effective by date, with a carrier-level fallback. The despatch date decides |
| VAT | Customer country, contract VAT eligibility, charge code, and whether sender and receiver are in the GB zone |
| Currency | A label on the schedule. No FX conversion happens anywhere in legacy billing |

## When it runs

- **Schedules:** Daily runs every date, weekly runs on Monday and monthly runs on the 1st. There is no cut-off: each run bills everything not yet invoiced.
- **Observed:** Datadog shows billing running from Saturday 00:00 to about midday Monday. Between 500 and 750 invoices a week reach ECM, on Monday afternoon.
- **Carrier charges:** Finance imports carrier EDI weekly. A charge whose shipment is not yet invoiced waits for a later run.
- **Month end:** Accruals run at month end only. Finance needs roughly the first 5 working days.

## Where shipments wait or are lost

- **Never reaches central.** Labels print, nothing is billed and nothing alerts.
- **Sale charge is 0 or less.** The shipment stays off the invoice and its cost is never rated. The reason appears only in the run log. It bills on a later run once the rates are fixed.
- **Supplementary exception.** The charge is written with zero money and never retried. 12,022 charges were in this state, and 1,428 were older than 90 days.
- **Supplementary pending.** The charge is retried on every run. 7,557 charges were pending, 1,624 were older than 90 days, and all carried £0.00.
- **Negative invoice numbers.** Shipments marked -3, -4 or -5 are never selected: about 57,500 shipments.
- **A contract on no schedule** never invoices. One report is the only safety net.
- **Duplicates.** Manager's recycle-replace can bill a shipment twice. Slipway and DataBridge have no duplicate guard.
- **Monitoring.** Nothing watches the backlog, and its owner is open.

## Not confirmed yet

- **Which billing run program and timetable are live, and whether split runs are on.** The pages disagree on the weekly run day. Customer Data Flow says Sunday. The Invoicing page says Monday, with Sunday for supplementary invoices only under split run.
- **How `BILL_ON_SCAN = 2` works.**
- **What `BILL_TYPE = 1` means.** Day End says GFS-billed. The Customers page lists the values as not decoded.
- **Whether cancelled shipments (status 1200) are billed.**
- **Where the October double billing came from:** Manager's recycle-replace, Slipway or DataBridge.
- **Whether the exclusion of negative invoice numbers is deliberate.**
- **What happens after delivery of the invoice.** The use of the Direct Debit file, NetSuite collections and payment are all not stated.
- **Whether Billing 2.0's planned unique source ID per shipment (FID-196) changes the hand-off.**

## Sources

- **Selector side:** [Legacy Selector - Day End and Billing Handoff](https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/353566845/Legacy+Selector+-+Day+End+and+Billing+Handoff), [Legacy Selector - Getting a Label](https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/352157738/Legacy+Selector+-+Getting+a+Label) and [Legacy Selector - Customer Data Flow](https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/352157700/Legacy+Selector+-+Customer+Data+Flow).
- **Billing side:** the Legacy Billing pages in the Billing space: [Overview](https://globalfreight.atlassian.net/wiki/pages/viewpage.action?pageId=311328794), [Invoicing & Scheduling](https://globalfreight.atlassian.net/wiki/pages/viewpage.action?pageId=311394359), [Customers, Contracts & Schedules](https://globalfreight.atlassian.net/wiki/pages/viewpage.action?pageId=311164981), [Tariffs, Zones & Rating](https://globalfreight.atlassian.net/wiki/pages/viewpage.action?pageId=311132225), [Finance Export](https://globalfreight.atlassian.net/wiki/pages/viewpage.action?pageId=311590953), [Exceptions & Reconciliation](https://globalfreight.atlassian.net/wiki/pages/viewpage.action?pageId=310673473), [Anomalies & Open Questions Register](https://globalfreight.atlassian.net/wiki/pages/viewpage.action?pageId=311394383) and [Operational Process: Weekly EDI & Accruals](https://globalfreight.atlassian.net/wiki/pages/viewpage.action?pageId=312279071).
- **Publishing:** Azure DevOps `legacy-invoice-translator` and Datadog `invoice_published` subscription traffic.
