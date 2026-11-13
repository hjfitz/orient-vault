---
title: "Native Dispatch — Requirements"
tags: [bifrost, requirements]
created: "2026-11-13"
updated: "2026-11-13"
---
# Native Dispatch — Requirements

The 13 Nov feedback, broken into numbered requirements. Each one says who asked, what the portal does today, and which unit builds it. Progress lives in [[Native Dispatch/Migration State|Migration State]], never here; the narrative is in the [[Native Dispatch/Overview|Overview]].

**"Today" is checked, not reported.** A read-only pass over `ilg-merak/parcel-portal` `origin/main` at `621357e` produced every "Today" line. The three that carry the most weight (R01, R11, R13) were re-read by hand. Paths are relative to `apps/svc/internal` (svc) or `apps/ui/src/app/(app)` (ui). Selector2 means `ilg-merak/selector2`.

## Sources
- Phil, Teams, 13 Nov: testing feedback. Pete asked four questions in the thread and Phil answered them; both are kept below where they change a requirement.
- Chris, Teams, 13 Nov: a question about the fields in the payload examples for Yusen US.
- Oliver Wilders, Slack DM: his answers of 12 Nov 17:53 UTC (ShipperId, tracking) and two messages of 13 Nov 14:06 UTC (cancel a dispatched label; the live test worked).
- The 13 Nov team catch-up, recording `20261113-093409-e9a5` (auto-transcribed; names and terms are approximate).

## Dispatch lifecycle

### R01 — Cancel or delete a dispatched label, and set the order live again
- **From:** Oliver, 13 Nov: "if a label is 'dispatched' ability to delete / set live again. cancel label. not sure if noted elsewhere but required."
- **Today:** Part of it exists, on the shipment page only. "Void shipment" calls Selector `DeleteShipments` (`core/shipments/void.go:76`), then `ReleaseVoidedOrder` sets the order from dispatched back to ready (`repositories/postgres/queries/shipment.sql:56-58`), which is "set live again". A manifested shipment can't be voided (`void.go:67`). A dispatched order's own page has no void action. "Cancel" in the orders list only acts on invalid, needs-packing and ready orders, and a cancelled (voided) order stays dead (`queries/orders.sql:112-117`). There is no delete-order route.
- **Verdict:** partial.
- **Units:** L1 (void from the order page), L2 (delete an order, once Oliver says what he means).
- **Open:** Q1.

## Order page and editing (Phil)

### R02 — Add products to an existing order
- **From:** Phil: "Currently cannot add additional Products to an Order."
- **Today:** Lines can be edited, not added or removed. A line edit must name an existing index (`core/orders/edit.go:195-197`) and a quantity of 1 or more (`:237`). A re-import or `POST /v1/orders` with the same order ref replaces the whole editable order (`core/imports/plan.go:59-64`).
- **Verdict:** gap. **Unit:** O4.

### R03 — Edit a product's weight
- **From:** Phil: "How to edit a product weight". Pete asked whether Yusen are unsure of their CSV data; Phil: they have had to update weights for some orders in Despatch Cloud before.
- **Today:** An order line has no weight (`models/order.go:54-62`). Weight sits on parcels and is editable in the Packing panel (`ui orders/[id]/packing-panel.tsx:236-248`); dispatch shares a parcel's weight across its items by quantity (`core/dispatch/request.go:183-205`).
- **Verdict:** gap, but it may be the wrong word: Phil may mean the parcel weight, which is editable. **Unit:** O5, after G1.
- **Open:** Q3.

### R04 — Show the total weight, and keep it in step with the package weights
- **From:** Phil: "Cannot see where the Total Weight is displayed and editable. If a package weight on an order is changed, does this automatically update the Total Weight."
- **Today:** The order's `TotalWeight` is stored as the file states it (`models/order.go:17`) and returned by the API, but the UI type doesn't carry it. Selector receives the sum of the parcel weights (`adapters/selector/client.go:259-263`). The export prefers the file's stated total over the parcel sum (`core/exports/csv.go:82-85`), and packing never changes the stored total (`core/orders/pack.go:67`).
- **Verdict:** gap, with a quiet defect: after a parcel weight is edited, Selector gets the new sum while the export to Manhattan can still carry the file's old total.
- **Unit:** O2. **Open:** Q5 (derived and read-only is the proposal).

### R05 — Show recipient email and phone beside the address
- **From:** Phil: "Recipient Email and Phone Number need to be displayed with the Shipping Address within an order and editable." Pete asked why they'd ever change. Phil then accepted "displayed and read only", as in Despatch Cloud.
- **Today:** Both are stored (`models/order.go:40-44`), mapped from the Email and Phone One columns, returned by the API and sent to Selector (`core/dispatch/request.go:129`). The order form has no contact fields (`ui orders/[id]/order-form.tsx:16-27`), and `OrderEdit` has none. A missing phone already blocks dispatch: Check with carrier rejected it on 12 Nov.
- **Verdict:** partial (stored and sent, not shown). **Unit:** O1, read-only. Editable stays off the list unless Phil asks again.

### R06 — Carrier service as a dropdown of the services available
- **From:** Phil: "Changing the carrier service, needs to be a dropdown of services available, rather than being an editable field for the service code."
- **Today:** Carrier and carrier service are plain text inputs (`ui order-form.tsx:25-26,170-180`). The account's service list is only checked when dispatching (`core/dispatch/prepare.go:95-113`), and the list route is admin-only (`openapi.yaml:764`). The first Overview already listed "a carrier-service picker" as not built.
- **Verdict:** gap. **Unit:** O3.

### R07 — Explain "Needs packing"
- **From:** Phil: "An order saying its at the 'Needs Packing' stage. Whats the logic to make an order be at this stage?"
- **Today:** The statuses are invalid, needs packing, ready, dispatched and voided (shown as "Cancelled"). Any problem makes an order invalid; a valid order with no parcels is needs packing; otherwise it is ready (`core/imports/validate.go:188-196`). A row counts as a parcel only if it gives a parcel number, a dimension, a weight or a preset (`core/mapping/orders.go:192-198`).
- **Verdict:** exists, but nothing on screen says so. The answer to give Phil: valid, but the file named no parcel size, weight or preset. **Unit:** O8.

### R08 — One view for a shipment and its order
- **From:** Phil: when you click a shipment, show "the exact view as when you click 'Open the order'"; and on that screen show the recipient's contact details and the weight details.
- **Today:** A shipments row opens `/shipments/{id}` (`ui shipments/shipments-table.tsx:78,93`), which has status, consignment, labels, tracking, void and an "Open the order" link. A dispatched order's page shows a read-only address card and the booking summary (`order-form.tsx:149-162`). Neither page shows contact details or weights, and the Packing panel is hidden once an order is dispatched (`order-form.tsx:101`).
- **Verdict:** gap. **Unit:** O7 (after O1, O2, L1).

### R09 — A Despatch button at the bottom of the order page
- **From:** Phil: so a user who has scrolled down checking or editing doesn't have to scroll back up.
- **Today:** The dispatch card sits near the top and appears only when the order is ready (`order-form.tsx:95-99,146`). The orders list has a batch "Dispatch N ready" button (`ui orders/orders-table.tsx:129-139`). Nothing in the UI is sticky or at the foot of a page.
- **Verdict:** exists, top only. **Unit:** O6. It must be one panel with two triggers; a second copy of the panel under the same key is the doubled-panel bug fixed in C23.

## CSV import (Phil)

### R10 — ConsigneeReference in the CSV and the UI, and searchable
- **From:** Phil. Pete asked whether the Despatch Cloud CSV already has a second reference; Phil: it doesn't.
- **Today:** There is no field called ConsigneeReference. The nearest is Container ID (`ConsRef`, `models/order.go:7-8`), which is one of the nine optional columns the team added, not one of Despatch Cloud's 40. It is searchable together with the order ref (`queries/orders.sql:62`) but isn't shown or editable on the order page (`models/order_record.go:94-99`). Selector's wire format has a `ConsigneeReference` (`adapters/selector/wire.go:85`) that `BuildShipment` never sets (`core/dispatch/request.go:65-72`).
- **Verdict:** partial. **Unit:** I2. **Open:** Q2 (is it the Container ID, or a new reference?).

### R11 — A packaging preset named in the CSV must fill length, width and height
- **From:** Phil: "When importing a CSV file with packaging presets, when going in to the order in the system, the L, W and H are not populated, which is needed to despatch the order."
- **Today:** Confirmed, and it is a bug. Import keeps the preset name as text (`core/mapping/orders.go:202`) and the ingest dependencies have no preset reader (`core/imports/ingest.go:94-104`), so dimensions and weight stay empty. Validation accepts any named preset (`core/imports/validate.go:139`), so the order shows Ready. Dispatch then refuses it: "parcel N has the packaging preset … but no measurements" (`core/dispatch/request.go:145-147`). Saving the Packing panel fills the dimensions (`core/orders/pack.go:103-118`).
- **Verdict:** bug. **Unit:** I1.

### R12 — More than one package on a single CSV line
- **From:** Phil: "the ability to set packages > 1 in the CSV for a single line would be good. Can only be done currently when importing products over multiple lines." Items may be left out of the CSV, but package weight and dimensions are still needed, in the CSV or in the system. "Might need a call." Pete asked whether this is a new CSV format with a shipment row and sub-rows for product lines; Phil's reply describes an extra column, not a new format.
- **Today:** Rows sharing a Parcel Number are one parcel; each row without one is its own parcel (`core/mapping/orders.go:171-186`). There is no package-count column in the layout or the public API. A single row with no parcel fields gives needs packing; with parcel fields it gives one parcel holding the whole quantity. Bulk packing makes one parcel per order (`openapi.yaml:1196`).
- **Verdict:** gap. **Unit:** I3, after G1. **Not checked:** whether an order can be imported with no product lines at all.
- **Open:** Q4.

## Integrator contract (Chris)

### R13 — Which legacy fields Yusen US should ignore
- **From:** Chris: required fields have been updated; before sending to Yusen US, "I can still see we have such things as Panther Options, DeliverySlotDetails and some other not needed legacy fields." Are Yusen US told to ignore them and use the fields in his payload examples?
- **Today:** Native Dispatch has no trace of either name on `origin/main`: not in the wire types, the layout or the public spec, and its built-in layout rejects unlisted columns (`core/imports/format.go:18`). Both exist in Selector2's REST schema (`apps/selector2-api/openapi/rest-v1.yaml`, `docs/rest-v2.md`). Native Dispatch's own integrator contract is `apps/svc/public-openapi.yaml`, whose `OrderInput` requires `shipRef`, `shipTo`, `service.requested` and `lines`.
- **Verdict:** probably not ours. Chris is most likely reading Selector2's spec. **Unit:** X1, after G2.
- **Open:** Q6.

## Carried from the TCA trial

### R14 — Send ShipperId 0
- **From:** Oliver, 12 Nov: "send 0. Every DispatchCloud call on the live TCA box sends 0 (82 of 82), so that's the proven path."
- **Today:** Not possible. The connection check says "shipperId must be above zero" (`core/carriers/connection.go:211-212`) and the table has `CHECK (shipper_id > 0)` (migration 004). The TCA-TEST connection on dev sends 1.
- **Verdict:** gap, code plus a migration. **Unit:** T2.

### R15 — Tracking link `{consignment}`
- **From:** Oliver, 12 Nov: ConsNumber is the CSS consignment number, which for FedEx is also the FedEx tracking number; one link per shipment, as Despatch Cloud does.
- **Today:** The Export tab already supports a link template with `{consignment}`. TCA's is not set. The template to use is `https://tracking.justshoutgfs.com/ConsLink.asp?ConsNumber={consignment}`.
- **Verdict:** exists; configuration only. **Unit:** T5.

### R16 — Allow weight 0 on a packing template, and create TCA's five templates
- **From:** Harry, 13 Nov: "allow weight 0 and make the templates". TCA's five packing templates carry a weight of 0.000.
- **Today:** The service rejects a preset with weight 0 (`core/packaging/presets.go:134`), so the five can't be created.
- **Verdict:** gap, approved. **Units:** T3 (the rule), T4 (the five presets on dev). The rule must keep "a parcel with no weight fails before dispatch".

### R17 — Prove the connection against TCA's live endpoint
- **From:** The catch-up: one proof against TCA's endpoint, then give TCA an account. Oliver asked on 13 Nov at 11:07 UTC whether he could test-print against TCA live; Harry said yes at 11:08.
- **Today:** At 14:06 UTC Oliver wrote that "connection generates a label and test worked with live account". That is his report; nothing in this repo or session confirms what was created at the carrier.
- **Verdict:** in progress. **Unit:** T1.

## Open questions

| # | Who | Question |
| --- | --- | --- |
| Q1 | Oliver | Does the shipment page's "Void shipment" (cancels at Selector, order back to Ready) cover "cancel label / set live again"? If not, which part is missing: void from the order page, deleting the order, or voiding after manifest? Still open from 12 Nov: live or bill-on-scan, and http or https. |
| Q2 | Phil | Is ConsigneeReference the end customer's own reference, and is it different from Container ID? Where must it show, and does Selector need it? |
| Q3 | Phil | Which weight is wanted on a product: a per-item weight Yusen sends in the CSV (not modelled), or the parcel weight (editable in Packing)? |
| Q4 | Phil, on the call | What is the package-count column called, how does it combine with Parcel Number, and can an order be imported with no product lines? |
| Q5 | Phil | Should the total weight be editable, or always the sum of the packages? Proposed: the sum, read-only. |
| Q6 | Chris | Which spec is going to Yusen US: Selector2's REST API or Native Dispatch's `public-openapi.yaml`? The two named fields live only in Selector2's. |
| Q7 | Harry | The API key UI has been hidden since 12 Nov (#131). The catch-up says TCA wants the API as MVP2 with a first test on 30 Nov, and that Oliver set up a connection on it on 12 Nov. Re-enable it? (Re-enabling is a revert.) |
| Q8 | Oliver | Still open: DDP on FIP and for which countries; whether whole-cm rounding of dimensions is acceptable; printer models and Yusen IT's policy on swapping a printer driver; what "VT changes for native dispatch" means in the catch-up. |

## Carried findings with no new requirement

These came from the TCA test session and have no other home. They are units T6 to T12 in the State doc: bench printing on Windows and the QZ Tray option, the red dev smoke test, raw error text on a failed packaging save, DDP on FIP, and customer self-serve for SFTP keys.
