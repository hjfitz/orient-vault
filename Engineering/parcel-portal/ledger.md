---
tags: [waypoint, ledger]
---
# parcel-portal — work ledger

Agent-facing. Newest first. What meaningful work happened here, and the
context a future agent needs. Not a diary, not release notes, not a diff.

## 2026-11-04 — Type a layout's column names, put its fields in tabs, rename Carrier account to Selector config

Type a layout's column names, put its fields in tabs, rename Carrier account to Selector config

Harry, 4 Nov feedback on the layout editor after #84: drop the 'Your file's columns' section (column names typed, with suggestions), keep group-by, Order / Each product line as tabs with to-do counts, sample fill as one button; the customer's Carrier account tab is Selector config.

PR: ilg-merak/parcel-portal#85

## 2026-11-03 — Match a layout's columns by name and say what's still to map (C18)

Match a layout's columns by name and say what's still to map (C18)

C18, Harry 3 Nov ('lets give it a whirl') after asking whether the CSV mapping/defaults/formatting UX was now good. svc: POST /admin/mapping/suggest matches a file's columns to fields by name (word-based, family words rule fields out, tested against DC's 49 columns and a non-DC header set); MappingField.neededFor (us_address, cross_border, parcel) kept equal to stage 2 by test; contract 5.1.0. UI: reading a sample matches columns and marks them 'Matched: check it' with undo; required fields unmapped are an amber to-do rather than red; US/cross-border fields listed with badges; If blank and Translate values are direct links; a parcels note.

PR: ilg-merak/parcel-portal#84

## 2026-11-03 — Take orders as JSON over the customer API (C15 P6)

Take orders as JSON over the customer API (C15 P6)

C15 P6. POST /v1/orders (customer API 1.2.0): up to 100 JSON orders; one request = one import file (source api, object never written); service.requested mapped via the layout's carrier/carrierService lookups (miss = unmapped_service); then the import's own plan + ApplyImport, so validation, statuses, replace-if-undispatched by shipRef, refuse-if-dispatched and duplicates behave as a file's. Per-order created/replaced/refused with status and problems (no file column). Harry, 3 Nov evening: 'P6, breaking changes, deployments: all fine'; the design calls (one request one file, resend replaces, no Idempotency-Key) were made here.

PR: ilg-merak/parcel-portal#83

## 2026-11-03 — Log an API key's revocation once (C15 P2 follow-up)

Log an API key's revocation once (C15 P2 follow-up)

RevokeAPIKey reports found and newly (the query reads the previous revoked_at FOR UPDATE), so revoking a revoked key stays a 204 with its first time but no longer logs 'API key revoked' again. UploadPanel's tenantId/tenantName props were left: they still choose the admin upload route.

PR: ilg-merak/parcel-portal#82

## 2026-11-03 — Put the customer API behind a public gateway (C15 P5)

Put the customer API behind a public gateway (C15 P5)

C15 P5. cmd/gateway forwards /v1 to private svc signed with an ID token for svc as its own SA (X-Serverless-Authorization; caller's dropped), passes x-request-id, serves Swagger UI at /docs over the embedded public spec (/openapi.json); anything else JSON 404, unclean paths not forwarded. iac/projects/gateway: Cloud Run (LB-only ingress, allUsers invoker), run.invoker on svc for its SA (as the UI has), own HTTPS LB + managed cert, A record api.parcel.delivery.<domain>. gateway-on-push/manual-deploy; plan matrix and scans include it. Harry OK'd P5 dev Terraform overnight in-session (3 Nov) on a purely additive plan.

PR: ilg-merak/parcel-portal#81

## 2026-11-03 — Take order files over the customer API, idempotently (C15 P4b, draft)

Take order files over the customer API, idempotently (C15 P4b, draft)

C15 P4b. POST /v1/order-files (customer API 1.1.0): CSV stored as <slug>/inbound/api-<token>-<name> with metadata source=api, api-key, import-file-id, content-sha256; recorded as received and answered 202 with its id before the import runs, which keeps the id. Idempotency-Key: token = hash(tenant, key), conditional GCS create; same file replays, different file 409. A clashing import-file-id falls back to a new id. Portal contract 5.0.0: ImportFile.source x-extensible-enum [sftp, browser, api] (oasdiff calls both enum-add and enum->x-extensible-enum breaking; no 4.x was ever released). Held as a draft for Harry's yes on 5.0.0.

PR: ilg-merak/parcel-portal#80

## 2026-11-03 — Serve the customer API's first route behind API keys (C15 P4a)

Serve the customer API's first route behind API keys (C15 P4a)

C15 P4a. public-openapi.yaml 1.0.0 is the customer API's own contract, generated into internal/http/publicapi and served on svc's router beside the portal routes, each with its own validator. middleware.APIKey (Bearer ppk_...) runs in a chi group before path binding, so a keyless request is always 401; it scopes to the key's tenant and ignores X-Acting-Tenant. GET /v1/order-files/{id} reads one of the customer's files (no bucket path or uploader ids). make public-contract-check in CI. P4b (CSV upload, source=api) waits on Harry's internal ImportFile.source enum call. svc stays private until P5's gateway (Terraform).

PR: ilg-merak/parcel-portal#79

## 2026-11-03 — Pack and cancel ticked orders from the Orders page (C16 G, UI)

Pack and cancel ticked orders from the Orders page (C16 G, UI)

Any pending order can be ticked. Dispatch and Check take the ready ones, Pack N in this box (preset picker) takes those that need packing, and Cancel N takes any of them, with a confirmation. With no presets, the action links an acting admin to the Packaging tab or tells a customer to ask GFS. Cancelled orders show as Cancelled.

PR: ilg-merak/parcel-portal#77

## 2026-11-03 — Cancel pending orders and pack them into a preset in bulk (C16 G, svc)

Cancel pending orders and pack them into a preset in bulk (C16 G, svc)

Harry asked to bulk-change the status of pending orders (3 Nov) and agreed two actions. POST /orders/cancel voids pending orders that no dispatch holds, recorded under the user and audited; a later file with the same reference imports the order afresh. POST /orders/pack gives each needs_packing order one preset parcel holding all its lines, through the single-order pack. Both return per-order results and work for an acting admin. Contract 4.9.0 (renumbered after #68 took 4.8.0); no migration. Verified locally as a customer and as an acting admin. Pre-merge review fixes: portal-side per-order faults are logged ('Bulk order action failed'), a held order (dispatch running or outcome unknown) says to dispatch it again to settle it, stale-read is order_changed. Merged with #77 as 6b12b7d via the async stack merge API.

PR: ilg-merak/parcel-portal#76

## 2026-11-03 — Rework the file layout editor around columns, grouping and portal fields (C17 2/2)

Rework the file layout editor around columns, grouping and portal fields (C17 2/2)

C17, Harry 3 Nov: the file layout editor was 'extremely confusing'. UI: one File layout card — start from Despatch Cloud's layout, file columns first (read from a sample), a grouping column picker, portal-field dropdowns grouped Order / Each product line with required fields always listed, column / fixed value / advanced expression sources, translate values and if-blank, derived required/optional columns, check at the bottom. DC template round-trips to identical rules.

PR: ilg-merak/parcel-portal#74

## 2026-11-03 — Let a customer's own layout ignore extra columns and carry its shipping methods (C17 1/2)

Let a customer's own layout ignore extra columns and carry its shipping methods (C17 1/2)

C17, Harry 3 Nov: the file layout editor was 'extremely confusing'. svc: a customer's own layout ignores extra columns (missing required ones still refused; DC built-in stays strict); shipping methods read and write a custom layout's carrier/carrierService lookups; mapping fields gain plain labels; contract 4.6.0.

PR: ilg-merak/parcel-portal#73

## 2026-11-03 — Manage a customer's API keys in Settings (C15 P2 UI)

Manage a customer's API keys in Settings (C15 P2 UI)

C15 P2 UI. API keys tab on the customer: list, make with a label (secret shown once with copy), and revoke behind a confirm; an optional Overview checklist step; a note that the customer API isn't open yet.

PR: ilg-merak/parcel-portal#71

## 2026-11-03 — Let GFS admins make and revoke API keys (C15 P2)

Let GFS admins make and revoke API keys (C15 P2)

C15 P2. core/apikeys creates ppk_<env>_<keyId>_<secret> keys (shown once, SHA-256 stored), lists, revokes, and authenticates a token to its tenant with a throttled last-used. Admin routes under /admin/tenants/{tenantId}/api-keys (contract 4.6.0, additive). Audit by key id only.

PR: ilg-merak/parcel-portal#70

## 2026-11-03 — Store each customer's API keys (C15 P1)

Store each customer's API keys (C15 P1)

C15 P1. Migration 014: api_key (SHA-256 of the secret only, unique key id, revocable, last used) and import_file.api_key_id, with source api allowed. A tenant-scoped store plus one unscoped by-hash lookup for authentication. The import keeps an api-key from object metadata only for its own tenant. The contract enum for ImportFile.source is left for P4 (adding a response enum value is breaking).

PR: ilg-merak/parcel-portal#69

## 2026-11-03 — Show every date in the site's time zone (C16 F)

Show every date in the site's time zone (C16 F)

C16 part F, UX review item 9. /me gains timezone: the zone of the tenant the request reads, so it's the customer's when a GFS admin is acting (contract 4.6.0). The UI shows every time as 'Nov 3, 2026, 10:05 AM EST' rather than en-GB UTC, and the export spells out its day. Follow-up: the toolkit GDatePicker hardcodes en-GB.

PR: ilg-merak/parcel-portal#68

## 2026-11-03 — Let a GFS admin acting for a customer dispatch its orders (C16)

Let a GFS admin acting for a customer dispatch its orders (C16)

Harry said to proceed (3 Nov). Migration 013 points dispatch_attempt.started_by and shipment.booked_by at app_user(id), the same shape as voided_by and manifested_by. The acting-dispatch 403 is removed (contract 4.5.1). Verified locally: an acting gfs_admin booked a customer's order, recorded under the admin.

PR: ilg-merak/parcel-portal#67

## 2026-11-03 — Give the SFTP host its users bucket's real name (C14 U4 fix)

Give the SFTP host its users bucket's real name (C14 U4 fix)

Dev's apply of #59 failed with the provider's 'inconsistent final plan' on the host instance template, which read SFTP_USERS_BUCKET from the IAM member ('b/<name>', only known after apply; it would also have been unreadable). Switched to the bucket data source's name. Applied on dev: the new hosts loaded 2 SFTP users and the canary passes as _canary. Verified live: unknown usernames and key mismatches are refused; tca-verify is confined to its own /inbound; disabling it refused the login 27 s later.

PR: ilg-merak/parcel-portal#66

## 2026-11-03 — Let GFS admins act for a customer (C16 C)

Let GFS admins act for a customer (C16 C)

C16 part C (Harry: a customer switcher is necessary for support). svc: a gfs_admin's X-Acting-Tenant header scopes session routes to a customer, with each request logged; others get 403, unknown tenants 404. Dispatch is refused while acting, because dispatch_attempt.started_by and shipment.booked_by are FK'd to a user of the same tenant; this is a decision for Harry. UI: an Acting as switcher (httpOnly cookie, cleared on sign-in and sign-out), a banner on every page, and a pick-a-customer state for admins on Orders, Shipments and Export. Contract 4.4.0, additive.

PR: ilg-merak/parcel-portal#65

## 2026-11-03 — Allow the demo printer per customer (C16 D)

Allow the demo printer per customer (C16 D)

C16 part D, from Harry: the demo printer is per-customer config. Migration 012 adds tenant.demo_printer (off by default). Admins toggle it on the customer's Bench printers tab via PUT /admin/tenants/{id}/demo-printer (audited), and both bench reads carry demoPrinter (contract 4.4.0, additive). Customers only see the demo option when it's allowed. A browser still using it after it's turned off is warned and prints with the dialog, with a reason.

PR: ilg-merak/parcel-portal#64

## 2026-11-03 — Read svc's SFTP users bucket from the bucket, not its grant (C14 U2 fix)

Read svc's SFTP users bucket from the bucket, not its grant (C14 U2 fix)

Dev's first apply of #57 failed with the Google provider's 'inconsistent final plan' on Cloud Run env, because SFTP_USERS_BUCKET was read from the IAM member's bucket, which is known only after apply. A rerun got dev through; this reads the bucket's own name so prod's first apply won't fail the same way.

PR: ilg-merak/parcel-portal#63

## 2026-11-03 — Let GFS admins add other GFS admins (C16)

Let GFS admins add other GFS admins (C16)

Per Harry (3 Nov), the GFS staff page's add form creates GFS admins. svc now enforces where roles live: a gfs_admin only in GFS's own tenant, and a customer only in a customer tenant (400 otherwise).

PR: ilg-merak/parcel-portal#62

## 2026-11-03 — Lead each order with its next step (C16 B)

Lead each order with its next step (C16 B)

C16 part B, from the UX review. A ready order shows Dispatch first and one needing packing shows Packing first. Problems are marked on their field. Dispatched and voided orders show a read-only summary. One back control throughout; visible row links; single-parcel shipments without a duplicate per-parcel print button.

PR: ilg-merak/parcel-portal#61

## 2026-11-03 — Set a customer up from one place, and keep GFS staff apart (C16 A)

Set a customer up from one place, and keep GFS staff apart (C16 A)

C16 part A, from the UX review. Customers get an Overview tab (folder plus a setup checklist), and Packaging and Bench printers become customer tabs, replacing the admin pages that took a pasted UUID. GFS's own tenant is shown as staff with a Users tab only, and nobody can disable their own sign-in. Primary buttons get variants; headings, failure messages and the shipping-methods empty state are fixed. Five frontend review findings fixed, plus a swallowed redirect.

PR: ilg-merak/parcel-portal#60

## 2026-11-03 — Sign SFTP logins in only against svc's SFTP users (C14 U4)

Sign SFTP logins in only against svc's SFTP users (C14 U4)

C14 U4. The SFTP host polls svc's sftp-users.json and signs logins in against its last good copy. Anyone not in it can't log in: there is no shared account, and nobody can until a first snapshot loads. A key logs in only its own user, into that user's business's folder, and uploads carry sftp-user. Adds a per-user session cap. The canary moves to its own _canary login and prefix. Terraform: the host gets objectViewer on svc's SFTP users bucket only; the single-user vars and the authorized-keys secret are removed; adds a refresh-failure monitor. Merge after #57, and run the dev cutover first (create SFTP user tca in TCA Demo with the dev test key). Not merged: carries Terraform and IAM, so the plan goes to Harry once it retargets to main.

PR: ilg-merak/parcel-portal#59

## 2026-11-03 — Manage a customer's SFTP users in Settings (C14 U3)

Manage a customer's SFTP users in Settings (C14 U3)

C14 U3. A new SFTP users tab under Settings → Customers. It lists logins with their keys, adds a user with an optional first key, adds a key, and revokes a key or disables a user behind confirmations. svc's reasons are shown as they are. On a 503 from revoke or disable, the tab says the key may still sign in. A banner says the SFTP server doesn't use these logins until U4. Five frontend review findings fixed: accessible names, the SSR date, 503-only wording, the dialog close, and a stale add-key form. Evidence: screenshots from a local run against svc.

PR: ilg-merak/parcel-portal#58

## 2026-11-03 — Publish the live SFTP logins for the SFTP host (C14 U2)

Publish the live SFTP logins for the SFTP host (C14 U2)

C14 U2. svc writes every enabled SFTP user's live keys and its tenant's slug to sftp-users.json in a new svc-owned bucket. It writes at startup, after each SFTP user or key change, and after a slug change, with a generation precondition read before the database read. Publishes are detached from the request and retried in the background until they succeed. Revoke and disable answer 503 when their write fails. Terraform: the bucket, svc's objectUser on it only, SFTP_USERS_BUCKET, and a monitor. Review-panel fixes: request cancellation, a deadline on the lock, and a reconciler so a stale snapshot never waits for the next change. The plan was shared with Harry before merging.

PR: ilg-merak/parcel-portal#57

## 2026-11-03 — Store and manage per-customer SFTP users and keys (C14 U1)

Store and manage per-customer SFTP users and keys (C14 U1)

C14 U1, a three-PR stack. Adds migration 011: sftp_user and sftp_user_key, keys only. Usernames are never reused, and a live key belongs to one user across all tenants. Disabling a user revokes its keys. import_file.sftp_user_id is read from the host's sftp-user metadata and is tenant-bound. The core use-case and ssh key parser refuse options, private keys, short RSA and types the host doesn't accept. GFS admins get the API under /admin/tenants/{id}/sftp-users (contract 4.3.0, additive). The review panel's data findings were fixed before opening: the add-key/disable race, the composite FK on import_file, indexes, and constraint-specific error mapping. Not yet live for logins: the snapshot (U2) and the host (U4) follow.

PR: ilg-merak/parcel-portal#53
PR: ilg-merak/parcel-portal#54
PR: ilg-merak/parcel-portal#55

## 2026-11-03 — Say so when Try a file can't read the picked file

Say so when Try a file can't read the picked file

Unit C13 follow-up, found while verifying #51 on dev. When the browser can't read the picked file, file.text() rejects. That rejection went unhandled and nothing showed; Try a file now asks for the file again.

PR: ilg-merak/parcel-portal#52

## 2026-11-03 — Edit a customer's file layout in Settings, with a dry-run preview

Edit a customer's file layout in Settings, with a dry-run preview

Unit C13, the mapping editor. svc (#48, #49; contract 4.1.0 then 4.2.0, additive):
- the tenant's layout in editable form, with a built-in expanded and its shipping-method overrides baked into its dictionaries;
- built-in layouts by name, and the fields a rule can fill;
- a save-time check that every rule parses, uses known functions and looks up a declared dictionary, with errors naming the rule;
- POST mapping/preview, a write-nothing dry run that shares one parse, map and plan path with the real import. It caps orders at 100 and problems at 200, the body at 3 MiB and the file at 2 MiB.

UI (#51): an editor on Settings → Customers → <customer> → File layout, with tabs for Columns, Order fields, Line fields, Defaults, Dictionaries and Try a file. Saving gives the customer its own layout, and the Shipping methods tab points such a customer at its dictionaries.

Review panels: svc (backend, contract/security, tests) found 2 contract defects and 5 test gaps, all fixed. UI (frontend) found 5 defects, all fixed: number defaults, keeping unshown config keys, stale groupBy, preview state across tabs, the server-action body limit. Verified locally end to end against svc. Follow-up: there's no cost bound on DSL evaluation in preview (admin-only).

PR: ilg-merak/parcel-portal#48
PR: ilg-merak/parcel-portal#49
PR: ilg-merak/parcel-portal#51

## 2026-11-03 — Tab the settings pages, with a tabbed page per customer

Tab the settings pages, with a tabbed page per customer

Unit C13, first part. Settings is tabbed: Customers (GFS admins only), Packaging and Printing. Customers is a list, and each customer opens on its own page with Folder, File layout, Shipping methods, Carrier account and Users tabs, each with its own URL. Old ?tenant= links redirect. The tabs are links with aria-current. Review (frontend and security, panel of 2) found 3 issues, all fixed before merge: the Radix tablist semantics, a missing header on the error state, and the non-admin redirect. Merged as 861674a. Base for the mapping editor in the File layout tab.

PR: ilg-merak/parcel-portal#47

## 2026-11-02 — Set each customer's carrier account in the admin UI

Set each customer's carrier account in the admin UI

Unit C12. Each tenant has its own Selector account, set from a Carrier card on Settings → Customers with a write-only password. svc seals the password into carrier_connection.password_ciphertext (AES-256-GCM, tenant-bound AAD) with a Terraform-generated key (svc-parcel-carrier-key, prevent_destroy), pinned by CARRIER_KEY_VERSION. The password must be re-entered when the endpoint changes. Migration 010 and contract 4.0.0 drop passwordSecret. The env-var carrier config from #25 is removed. No IAM change. Live on dev at 8205627 (migrations applied, svc ready, fake carrier mode). Prod is held at D1. Follow-up: when two admins save the same carrier card at once, a password-less save can restore the old password.

PR: ilg-merak/parcel-portal#43
PR: ilg-merak/parcel-portal#44

## 2026-10-29 — Edit an order's products and customs before dispatch

Edit an order's products and customs before dispatch

C11 part 2 (MKP-36). The order page edits currency and, per line, quantity (1–100000), unit price, HS code, customs description and origin, before dispatch only. Stage 2 re-runs; a quantity change re-checks packing; edits and packs that lose a race with another write get 409 order_changed; every edit logs 'Order edited' with field names only. Three review rounds (the third with Harry's go-ahead). Live on dev f3b7bbd. Follow-up: scope the quantity-edit packing re-check to the edited SKUs (a qty edit on a partly-packed import also flags untouched lines), treat an unchanged quantity as no change, move the misplaced packed() doc comment.

PR: ilg-merak/parcel-portal#41

## 2026-10-29 — Add the file page, a shipping-methods editor and setup-flow fixes

Add the file page, a shipping-methods editor and setup-flow fixes

C11 part 1 (MKP-36). A new customer starts on Despatch Cloud's layout; uploads for a customer with no layout are refused; the admin picker offers only customers that take files. Each customer has its own shipping method → carrier/service list (import_mapping.shipping_methods, cleared on a layout change). A page per order file shows problems by row with the CSV column highlighted, paged 200 at a time. Two review rounds. Live on dev a0283de. Line and customs editing (#41) is held for one narrow fix.

PR: ilg-merak/parcel-portal#38
PR: ilg-merak/parcel-portal#39
PR: ilg-merak/parcel-portal#40

## 2026-10-29 — Add the admin Customers page, a dev-only fake carrier and a sandbox Manifest guard

Add the admin Customers page, a dev-only fake carrier and a sandbox Manifest guard

C10 (MKP-34). A gfs_admin creates customers, folders, layouts and users in the UI, so a dev end-to-end test needs no API access. Dev books with a fake carrier (CARRIER_MODE=fake, refused outside dev at boot and at plan time) that labels US/CA FedEx orders as TEST and derives its daily query from the portal's own shipments. Manifest is refused against the shared Selector sandbox. Independent review: nothing blocking; one round of hardening, delta re-review clean. Live on dev c0b34e1; startup warning logged.

PR: ilg-merak/parcel-portal#33
PR: ilg-merak/parcel-portal#34
PR: ilg-merak/parcel-portal#35

## 2026-10-29 — Serve the UI only through its load balancer

Serve the UI only through its load balancer

D2 follow-up (MKP-35). With the dev certificate ACTIVE, the UI's Cloud Run ingress defaults to internal-load-balancer: https://parcel.delivery.freightops.dev → 200, the run.app URL → 404. A new env's UI is unreachable until its cert is active (runbook).

PR: ilg-merak/parcel-portal#37

## 2026-10-29 — Put the Parcel Portal at parcel.delivery.<domain>

Put the Parcel Portal at parcel.delivery.<domain>

D2 (MKP-35). ilg-merak claims delivery.<domain> (core-infra#16: dnsRecordWriter for each env's merak runner, merged and applied by Harry). The UI sits behind the platform serverless load balancer at parcel.delivery.freightops.dev with a managed cert; sftp.parcel.delivery.freightops.dev points at the SFTP static IP. Follow-up: switch UI ingress to internal-LB once the cert is ACTIVE.

PR: ilg-merak/parcel-portal#32
PR: ilg-platform/core-infra#16

## 2026-10-29 — Fix the sftp dev deploy: plan-time key count, canary memory, Cloud Scheduler API

Fix the sftp dev deploy: plan-time key count, canary memory, Cloud Scheduler API

Every sftp dev apply had failed since the canary landed (#18), which is what #merak-notifications was reporting. Three stacked causes: authorized-keys count depended on an apply-time key; the canary job asked for 256 MiB (Cloud Run jobs need 512); Cloud Scheduler API was off. Dev sftp applies green; canary PASS on dev at 10:27.

PR: ilg-merak/parcel-portal#26
PR: ilg-merak/parcel-portal#27
PR: ilg-merak/parcel-portal#28

## 2026-10-29 — Upload order files from the browser alongside SFTP

Upload order files from the browser alongside SFTP

C9 (MKP-33). Orders gets a drop zone and an Upload button. svc writes the CSV to <slug>/inbound/<name> in the inbound bucket so the SFTP import pipeline imports it unchanged; a re-upload replaces the file. import_file records source and uploader (an admin uploading for a customer is recorded). The bucket notification now covers every tenant, request bodies are capped before validation, and sign-in retries once on a cold start. Independent review: 3 blockers found and fixed, delta re-review clean.

PR: ilg-merak/parcel-portal#29
PR: ilg-merak/parcel-portal#30

## 2026-10-29 — Read the carrier account from deploy-time config

Read the carrier account from deploy-time config

While the portal serves one customer, svc's Selector account is CARRIER_ env vars set from `carrier` in iac/env/<env>.tfvars (dev: sandbox for tca; prod: none until MKP-10). Only the named tenant can dispatch; the password stays a hand-made svc-parcel-carrier-<slug> secret read at booking time. PUT /admin/tenants/{id}/carrier-connection removed (contract 3.0.0), GET read-only; carrier_connection table kept for the multi-customer future. Deployed to dev and verified in Datadog.

PR: ilg-merak/parcel-portal#25

## 2026-10-28 — MKP-31

Add WebUSB bench printing as @ilg-merak/label-print

Standalone package (pairing, ZPL/EPL/PDF send, pdf.js raster to ZPL ^GFA / EPL GW, typed errors, DemoPrinter), 93 vitest tests, own CI; apps/ui wires Settings → Printing, printLabels everywhere incl. C7 batch results, auto-print after dispatch on a paired browser, print-to-screen fallback. ui image now builds from repo root. Real printers untested until 29 Oct office test.

PR: ilg-merak/parcel-portal#23

## 2026-10-28 — MKP-30

Dispatch and check selected orders in one go

C7. svc contract 2.10.0: POST /orders/dispatch runs B5's per-order dispatch sequentially (own claim/reconcile each, never ProcessShipments), per-order booked/not_booked with the single dispatch's codes plus carrier_unavailable/not_found/not_attempted; 3-minute budget, cap 100 (sandbox ~0.6 s/order). POST /orders/validate = portal checks + ValidateShipment, books nothing. B5's read-and-build moved into a shared preparer. UI: ready-only checkboxes, Dispatch selected / Check with carrier, results panel, print all booked as one PDF. Sandbox run: 18 booked and all voided, no commit.

PR: ilg-merak/parcel-portal#21

## 2026-10-28 — MKP-23

Shipments date filter in the site's timezone

bookedFrom/bookedTo are site-local days via the export's day bounds; DST-tested.

PR: ilg-merak/parcel-portal#20

## 2026-10-28 — MKP-23

Add the Shipments screen: search, labels, void, manifest, and printing settings

C2 + C3 (MKP-23, MKP-24) in one PR. svc contract 2.8.0, migration 007: GET /shipments search (shipref, consref, tracking, carrier, status, booked days), GET /shipments/{id}, GET /shipments/labels (one merged PDF via pdfcpu, or joined ZPL), void via DeleteShipments recorded only on Selector's confirmation (DailyShipQuery decides a refused delete) releasing the order to ready, manifest via CommitShipments + DailyShipQuery marking, refresh-status for auto-commits (manifested_by empty), bench_printer per tenant (recorded only), GET /admin/tenants. UI: /shipments, detail, print page (browser dialog), Settings > Printing. Gate assumptions: MKP-9 explicit Manifest button + auto-commit backstop, manifested can't be voided; MKP-8 print-to-screen floor, silent printing not built. Sandbox DailyShipQuery statuses seen: PRINTED, MANIFESTED, DELETED, MANIFESTED_DELETED; CommitShipments never called on sandbox.

PR: ilg-merak/parcel-portal#19

## 2026-10-28 — MKP-28

Add the ops runbook, Datadog monitors and the SFTP canary

docs/runbook.md, 10 Datadog monitors as Terraform (off until DATADOG_APP_KEY exists, no paging by default), SFTP canary as a scheduled Cloud Run job uploading an import-ignored dotfile. Plus the svc system variable fix (#16) that had broken the svc dev apply since #11.

PR: ilg-merak/parcel-portal#18

## 2026-10-28 — MKP-27

Add packaging presets and package contents

Per-tenant presets (admin CRUD, customer list, Settings → Packaging), PUT /orders/{id}/parcels to pack with a picked preset or manual dims and assign items (re-validated, never defaulted), contents per parcel on dispatched orders.

PR: ilg-merak/parcel-portal#17

## 2026-10-28 — MKP-21

Take the despatch date from the site's timezone

Dispatch and reconcile use the tenant timezone (default America/New_York) instead of the UTC day; invalid zones fall back with a tenant-ID-only log line.

PR: ilg-merak/parcel-portal#15

## 2026-10-28 — MKP-26

Build the Manhattan SCALE export

DC's 17-column layout, consref in Channel Alt ID, multi-parcel tracking comma-joined and quoted, voided as Cancelled=Yes, days bounded by a new tenant timezone, optional Excel-proof formula cells (off by default), Export page with row count and download.

PR: ilg-merak/parcel-portal#14

## 2026-10-28 — MKP-21

Book and label: dispatch through Selector

Ledger already written by the B5 agent; this records the merge to main.

PR: ilg-merak/parcel-portal#13

## 2026-10-28 — MKP-21

Dispatch a ready order through Selector, at most once, and keep its labels

POST /orders/{id}/dispatch books a ready order on the tenant's Selector account (carrier_connection names a Secret Manager secret svc-parcel-carrier-*, 5-min cache), stores labels in the labels bucket (<tenant>/labels/<shipment>/<parcel>.pdf|zpl), marks the order dispatched. At-most-once: dispatch_attempt claimed in one tx that locks and holds the order (orders.dispatch_attempt_id; B4 ReplaceOrder now skips held orders), in_flight unique per order with a 5-min lease; outcome_unknown (retryable+RequestSent, labels not stored, or expired lease) is reconciled via DailyShipQuery and any unrecorded live consignment voided before booking again (lost bookings are voided, not adopted: no label reprint op). 422 carrier_rejected keeps the order ready. New tables carrier_connection/dispatch_attempt/shipment/shipment_parcel (migration 004), GET /orders/{id}/shipment ({shipment} envelope), label stream route, admin carrier-connection routes, contract 2.3.0, Terraform labels bucket + prefix-conditioned secretAccessor. 1064 integration tests pass; live sandbox 2-parcel HERMES 2DAY booked, both PDF labels served, voided. FedEx/US/CA untested (MKP-10). On merge with C1 (#12): UpdateEditedOrder needs AND dispatch_attempt_id IS NULL; both bump the contract to 2.3.0.

PR: ilg-merak/parcel-portal#13

## 2026-10-28 — MKP-22

Build the Orders screen

Orders grid with status, plain failure reasons, search by shipref/consref, rejected-files list; order page edits address/service before dispatch via PATCH /orders/{id} reusing B4's stage-2 rules; dispatch button against B5's contract with labels opened to print.

PR: ilg-merak/parcel-portal#12

## 2026-10-28 — MKP-20

Import uploaded order files into orders, with two-stage validation

POST /events/inbound-files (Pub/Sub push, OIDC as svc-parcel-<env>-push) imports <slug>/inbound/<file>: claim import_file per bucket/object/generation, stage 1 header vs the tenant's layout (rejects the file with a reason), B2 mapper, stage 2 per-row problems {row, field, column, code, message} (mandatory fields, US state from County + ZIP, CA customs per line, unmeasured parcels), then orders + finished file in one transaction. New tables orders/order_line/parcel/parcel_item/import_mapping and tenant.slug, composite (id, tenant_id) FKs, one live order per shipref. Admin slug/mapping routes (dc-layout built in), customer read API for import files and orders. Terraform push subscription with dead-letter. Assumes MKP-5 per-product rows (no parcels -> needs_packing), MKP-7 state from County, MKP-29 fix by re-drop. 950 integration tests pass; local SFTP -> fake-gcs -> Pub/Sub emulator -> svc run verified; nothing deployed.

PR: ilg-merak/parcel-portal#11

## 2026-10-28 — MKP-15

Add tenants, per-person sign-in and tenant-scoped data access

Opaque hashed sessions, argon2id login with identical failures and throttling, context-scoped stores that refuse to run without a tenant (static test), admin cross-tenant only via path and logged, bootstrap admin from Secret Manager, UI sign-in with svc reachable only from the UI SA. 168 integration tests pass.

PR: ilg-merak/parcel-portal#10

## 2026-10-28 — MKP-19

Add the single-user Go SFTP host

cmd/sftp copied from sftp-connector's Go host, one user with keys in Secret Manager, GCS inbound bucket + finalize notification, MIG/LB IaC with its own VPC. Dev apply partial: needs terraform-runner compute.instanceAdmin.v1 (ilg-merak/gcp-config#7).

PR: ilg-merak/parcel-portal#7

## 2026-10-28 — MKP-14

Add Cloud SQL with IAM-only auth, startup migrations and the first tables

Cloud SQL PostgreSQL 17 (svc-parcel-<env>, dev db-f1-micro ZONAL, prod db-custom-1-3840 REGIONAL) in iac/projects/svc: connector-only public IP, IAM database user for the runtime SA (cloudsqlsuperuser via google-beta database_roles), no password users. svc connects through cloudsqlconn with IAM auth, applies embedded tern migrations at startup under an advisory lock, and the startup probe is /health/readiness (DB reachable and migrated). Migration 001: tenant, app_user, import_file. Removes the template notes example; contract 2.0.0. Draft; not yet deployed (deploy dispatch and CI trigger blocked by the permission guard).

PR: ilg-merak/parcel-portal#8

## 2026-10-28 — MKP-18

Port the rules-engine mapper and add the DC-layout mapping

Mapper engine ported to Go (111 conformance fixtures from rules-engine 2.1.1 pass), order model, LinedConfig + MapOrders with per-row problems, embedded DC 40-column mapping with placeholder FedEx services and assumed parcel columns pending gates MKP-5/MKP-7.

PR: ilg-merak/parcel-portal#9

## 2026-10-28 — MKP-17

Port the Fuse mapping DSL to Go

Lexer, parser, interpreter, lookup and runner; 298 conformance cases generated from rules-engine 2.1.1 all pass.

PR: ilg-merak/parcel-portal#6

## 2026-10-28 — MKP-16

Add the Go Selector client

Validate, book (multi-package, PDF/ZPL), void, commit and daily query; typed errors with plain user messages; sandbox-recorded fixtures.

PR: ilg-merak/parcel-portal#5

## 2026-10-28 — MKP-13

Scaffold the parcel portal repo from svc-template

Repo, names, GFS-branded UI shell (Orders/Shipments/Export/Settings), Basic-auth stub, dev deploy.

PR: ilg-merak/parcel-portal#4
