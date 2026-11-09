---
title: "Parcel Portal — dev test checklist"
date: 2026-11-04
tags: [bifrost, merak, parcel-portal]
---
# Parcel Portal — dev test checklist

Rewritten 4 Nov 2026, after the demo customer and the sample file landed. It replaces the 29 Oct version.

Dev books with svc's **fake carrier** (`carrier_mode = "fake"` in `iac/env/dev.tfvars`). Every label says **TEST, NOT A REAL LABEL**, and nothing reaches FedEx or Selector. **Prod hasn't been applied**: every prod deploy waits at the `terraform-prod` gate. The ops reference is `docs/runbook.md` in the repo.

## 0. Sign in as the GFS admin
- UI: https://parcel.delivery.freightops.dev
- The bootstrap admin is `admin@parcel-portal.invalid`. Its password: `gcloud secrets versions access latest --secret=svc-parcel-bootstrap-admin-password --project=ilg-merak-dev-b5e3`
- Or use your own GFS admin login if one has been made for you (Settings → Customers → GFS staff).

## 1. Upload to a label in two minutes
1. **Settings → Customers → Try the portal → Create a demo customer.** It's named `Demo <day> <time>` and set up completely:
   - Despatch Cloud's layout;
   - a test Selector config;
   - two packaging presets;
   - the on-screen demo printer.

   You're switched to acting for it and taken to **Orders**.
2. **Download a sample file** (under the upload box), then drag it onto Orders. It has new order numbers each time, and it says how the import went within a few seconds:
   - `…-1`, `…-2` (two parcels) and `…-3` (Canada, with customs data) arrive **Ready**;
   - `…-4` has no parcels, so it arrives **Needs packing**;
   - `…-5` is missing its city, so it's **flagged** and the rest still import.
3. **Fix `…-5`**: open it, type a city and save. It flips to Ready.
4. **Pack `…-4`**: open it and pack it into a preset. It becomes Ready.
5. **Dispatch.** Tick the Ready orders and dispatch them together. Each gets a consignment number, and the label shows on screen (the demo printer).
6. **Shipments.** The page says the carrier is a test one.
   - Search, reprint, download a label, and batch-print several as one PDF.
   - **Void** one: its order goes back to Ready.
   - **Manifest** marks the rest manifested.
7. **Export.** Today's CSV is in Despatch Cloud's 17 columns, with tracking numbers as text.
8. **Clean up:** the demo customer's **Overview → Delete customer**, then stop acting for it with the switcher at the top.

## 2. The other ways in (same demo customer)
- **SFTP.**
  1. Go to **Access → SFTP**. It shows the host and port, and that the login uploads to `/inbound`.
  2. Add an SFTP login with your public key.
  3. Run `sftp -i <your key> <login>@sftp.parcel.delivery.freightops.dev`, then `cd inbound`, then `put sample-orders.csv`.
  4. The orders appear on Orders.
- **API.**
  1. Go to **Access → API**, make a key and open the API docs (Swagger).
  2. Send the sample file with `POST /v1/order-files`, or JSON with `POST /v1/orders`, using `Authorization: Bearer <key>`.
- **Portal users.**
  1. On Access → Portal users, add a user.
  2. Sign in as them in a private window. They see only their own orders.
  3. Try Edit, Set password (it signs them out) and Disable / Enable.

## 3. Setting up a real customer's file
On **File layout**, start from Despatch Cloud's layout, or use **Fill fields from a sample file** with the customer's own file:
- check each field marked **Matched**;
- type any column the matcher missed;
- run **Check with a sample file**;
- then save.

**Shipping methods** maps each method the file asks for to a carrier service.

## 4. Printers (office)
1. As admin, set a bench to ZPL (and EPL if there's an LP2844) on the customer's **Bench printers** tab, and turn the demo printer off.
2. Sign in as the customer in Chrome on the bench PC. In Settings → Printing, pick the bench, set the DPI (203 or 300), **Pair**, then **Check connection**. On Windows, if you see "the printer driver is using this printer", swap it to WinUSB with Zadig (`docs/printing.md`).
3. **Test print** should show a box just inside the label edge. **Graphic test print** should show a box, a black square and 8 bars.
4. Dispatch an order: the labels should print by themselves. Unplug the printer, or use Firefox: both should fall back with a reason.

## Known gaps
- **Real FedEx is untested** until TCA's FedEx account exists (MKP-10). The Selector sandbox books GB HERMES only.
- **TCA's real US file** hasn't arrived (MKP-7). We don't know yet whether it carries parcels (Ready) or every order needs packing.
- **The UI has no automated end-to-end test yet.** A browser smoke test of upload → pack → dispatch in CI is next.
- **Monitors are off** until a `DATADOG_APP_KEY` secret exists and `datadog_monitors_enabled = true`.
- **Gates still open:**
  - MKP-5 row grain
  - MKP-6 export layout
  - MKP-7 US sample
  - MKP-8 printers
  - MKP-9 manifest semantics
  - MKP-10 FedEx account
  - MKP-11 Oli Denton
  - MKP-29 MVP cut
