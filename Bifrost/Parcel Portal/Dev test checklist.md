---
title: "Parcel Portal — dev test checklist"
date: 2026-10-29
tags: [bifrost, merak, parcel-portal]
---
# Parcel Portal — dev test checklist (for 29 Oct)

Everything below is built and merged to `main` in `ilg-merak/parcel-portal`. svc, ui and sftp are deployed to dev, and the svc revision from 20:31 on 28 Oct started cleanly in Datadog: database connected, migrations applied, bootstrap admin created. **Prod hasn't been applied.** Every prod deploy waits at the `terraform-prod` gate.

The ops reference is `docs/runbook.md` in the repo. This page is the short path.

## 0. Access you need
- Only the bootstrap admin's password (below). Once C10 (MKP-34) is on dev, setting up a customer needs no API access or secrets: it's all in **Settings → Customers**. `roles/run.invoker` on `svc-parcel-dev` is only for calling the admin API directly.

## 1. Sign in as the GFS admin
- UI: https://parcel.delivery.freightops.dev once D2 (MKP-35) is applied and its certificate is active. Until then, and as a fallback, https://ui-parcel-dev-qbs2p3wu5a-uc.a.run.app
- SFTP by name: `sftp.parcel.delivery.freightops.dev` (same host as the static IP, once D2 is applied)
- Email: `admin@parcel-portal.invalid`
- Password: `gcloud secrets versions access latest --secret=svc-parcel-bootstrap-admin-password --project=ilg-merak-dev-b5e3`

## 2. Set up the TCA customer (Settings → Customers, as the GFS admin)
1. **New customer:** name `TCA`, folder `tca`. The SFTP host writes to `tca/inbound/`, and files dropped onto Orders go there too.
2. **File layout:** nothing to do. A new customer starts on Despatch Cloud's layout. A custom layout is still API only.
   - **Shipping methods** (same page): the list of `Shipping Method Requested` values and the carrier and service each books as. The FedEx rows are marked *unconfirmed* guesses. Try adding `TCA Ground` → `FEDEX` / `FEDEX_GROUND`, save, and drop a file that asks for it. Orders already imported don't change; drop their file again.
3. **Users:** add a customer user with an initial password of at least 12 characters, and keep it: it isn't shown again.
4. **Carrier account: Settings → Customers → TCA → Carrier account.** Set carrier `FEDEX`, ships from `US`, label format `PDF`, and any https endpoint, username, contract and shipper id (e.g. the sandbox URL, `TEST`, `123456`, `12345`). **No password is needed on dev:** dev books with svc's **fake carrier** (`carrier_mode = "fake"` in `iac/env/dev.tfvars`), which reads none. Every label says **TEST, NOT A REAL LABEL**, and Shipments and the order page say so. Manifest works with it. **Check connection** answers that dev uses the test carrier.
   - **To test against the real Selector sandbox instead:** set `carrier_mode = "selector"` in `iac/env/dev.tfvars` and deploy, then give TCA the sandbox account on the Customers page: carrier `HERMES`, ships from `GB`, user and password `TEST`, contract `123456`. svc stores the password encrypted on TCA's account (the key is the `svc-parcel-carrier-key` secret, which must never be destroyed). The sandbox books GB addresses only, and **Manifest is off against it** (svc refuses and the button says why), because a commit closes out the shared TEST account.
5. Under Settings → Packaging, add two presets.

## 3. Drop a file
- Run `sftp -i ~/.ssh/parcel-sftp-dev-tca tca@34.123.66.172`, then `cd inbound`, then `put <file>.csv`.
  - The key was generated for dev. Only its public half is in the repo.
- **Or drag the file onto Orders** (or use **Upload file**) as the customer. As the GFS admin, pick the customer first. Within a few seconds the page says how the import went. Uploading a file under a name already there replaces it and imports it again, as SFTP does.
- **TCA-shaped sample:** `apps/svc/internal/core/imports/testdata/tca-us-ca-sample.csv` in the repo: three US and Canada FedEx orders, with parcels, that import **ready** and book with the fake carrier (an e2e test pins this).
- Phil's `CSV Example.csv` (Slack file F0CCUG9UQ9Y) imports TEST006 and TEST007 as **needs packing**. Its orders ask for DPD (carrier GFS), so they won't dispatch against dev's FedEx account; use the TCA sample to dispatch.
- Add one bad row, e.g. a missing postcode, to see partial import.

## 4. Walk the screens as the customer
1. **Orders.** The bad row shows its reason. Fix the postcode, and the order flips.
   - **Recent files** flags the file with problems. Open it: problems are grouped by spreadsheet row, with the CSV column to fix highlighted, and the orders it wrote are listed.
2. **Pack TEST006** into two presets and assign its items. It becomes **ready**.
   - **Products and customs** on the order page: blank a Canadian order's HS code in the CSV, import it, then fill it in on the order page. It flips to ready. Edits stay in the portal; Manhattan keeps the original.
3. **Dispatch.** You should get a consignment number and labels that open to print.
4. **Shipments.** The page says the carrier is a test one. Search, view, reprint and download a label, and batch-print several as one merged PDF. **Void** one: the order goes back to `ready`. **Manifest** marks the open ones manifested (with the fake; it's disabled against the shared sandbox). **Refresh status** changes nothing with the fake.
5. **Settings → Printing.** Record bench printers. Silent printing isn't live; check that auto-print fires in real Chrome and Edge.
6. **Export.** Today's CSV in DC's 17 columns, with tracking codes kept as text.

## 5. Printers (office)
1. As admin, set the test customer's bench to ZPL (and EPL if there's an LP2844). Sign in as the customer in Chrome on the bench PC.
2. Settings → Printing: pick the bench, set DPI (203/300), **Pair**, then **Check connection**. On Windows, if you see "the printer driver is using this printer", swap it to WinUSB with Zadig (`docs/printing.md`) and replug.
3. **Test print** should show a box just inside the label edge. **Graphic test print** should show a box, a black square and 8 bars. A cut-off or small box means the DPI or calibration is wrong.
4. Dispatch an order. Labels should print by themselves with "Printed N labels". Then reprint, batch print from Shipments and from the batch-dispatch results, and scan a barcode.
5. Unplug the printer and print, then try Firefox. Both should fall back with a reason. **Demo printer** in Settings shows the expected dots with no device. If anything misbehaves, use Copy diagnostics.

## Known gaps (also in the ledger)
- **Real FedEx is untested** until the TCA FedEx account exists (MKP-10). Dev's fake carrier proves the portal's side end to end; the sandbox is GB HERMES only.
- **Custom file layouts** are still API only; everything else about a customer is in Settings → Customers.
- **Carrier service is free text** in the order form. There's no list of services yet.
- **Monitors are off** until a `DATADOG_APP_KEY` secret exists and `datadog_monitors_enabled = true`.
- **The SFTP canary** deploys with sftp. Its first `SFTP canary PASS` is still to be confirmed in Datadog.
- **Gates still open:**
  - MKP-5 row grain
  - MKP-6 export layout
  - MKP-7 US sample
  - MKP-8 printers
  - MKP-9 manifest semantics
  - MKP-10 FedEx account
  - MKP-11 Oli Denton
  - MKP-29 MVP cut
