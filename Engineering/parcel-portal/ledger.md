---
tags: [waypoint, ledger]
---
# parcel-portal — work ledger

Agent-facing. Newest first. What meaningful work happened here, and the
context a future agent needs. Not a diary, not release notes, not a diff.

## 2026-11-13 — Make an order's total weight follow its parcels

Make an order's total weight follow its parcels

Native Dispatch unit O2, svc half (R04). One function now gives an order's total weight from its parcels (each converted to kg, rounded to the gram as dispatch does, summed); the export's Shipping Weight and GET /orders/{id} totalWeight use it, so an edited parcel weight reaches the export as well as Selector. When the parcels can't give a total, the file's stated total is used. Dispatch now calls the same conversion. The layout preview still shows the mapped total. No contract change. The export weight is now always kilograms (it used to be the file's unit): not confirmed with Yusen, so it is a gate before prod (G9). The export still reads the order's current parcels, not what a voided shipment booked (O10). The UI display is the next half.

PR: ilg-merak/parcel-portal#144

## 2026-11-13 — Offer a customer the carrier services on its account, and check a service code on edit

Offer a customer the carrier services on its account, and check a service code on edit

Native Dispatch unit O3, svc half (R06). New GET /carrier/services returns the services the acting customer's account offers (code and label; blocked ones left out; a restricted flag tells 'no list' from 'every service blocked'), readable by any signed-in user and tenant-scoped. An order edit that changes the service code is refused if the account doesn't offer it; the code is trimmed and stored in the listed spelling, and a save that leaves the code alone never fails because the list changed. Contract 5.15.0. Known gaps: the edit check and the picker don't follow dispatch's test-carrier exemption (dev only), and a carrier-only edit isn't judged. The UI dropdown is the next half.

PR: ilg-merak/parcel-portal#143

## 2026-11-13 — Order page: contact details, why it needs packing, a foot Dispatch button and void

Order page: contact details, why it needs packing, a foot Dispatch button and void

Native Dispatch units O1, O8, O6 and L1 (R05, R07, R09, R01), one PR. The order page now shows the recipient's email and phone read-only beside the address; says beside the status why an order needs packing; has a second Dispatch button at the foot (one dispatch panel, two triggers, so no stale-panel bug); and a dispatched order with a booked shipment can be voided from its own page, which returns it to Ready. Review fixes: a dispatch error no longer survives a retry, focus moves to the booking summary after a foot dispatch, the address form warns (without blocking) when it has unsaved changes, and the voided notice only shows while the order is Ready. Verified against the production UI build and a local svc with the fake carrier, driven by Playwright, with one panel or one summary after every action. UI only. Known gaps: products and parcels have no unsaved-changes warning (O9), and the badge tooltip is hover-only in lists.

PR: ilg-merak/parcel-portal#142

## 2026-11-13 — Correct the runbook and the svc README

Correct the runbook and the svc README

Native Dispatch unit T15. A 13 Nov doc refresh found claims that were no longer true: the runbook's one SFTP account, one carrier tenant, no list-tenants call and no void (with break-glass SQL), and the README's carrier-services and X-Expected-Tenant claims and its package listing. Each was re-checked against the code and corrected. Docs only. Found, not changed: openapi.yaml lines 28-30 repeat the X-Expected-Tenant claim and need a version bump.

PR: ilg-merak/parcel-portal#141

## 2026-11-13 — Say Native Dispatch in what users and customers see

Say Native Dispatch in what users and customers see

Native Dispatch unit T13 (Harry: rename to native dispatch). Page titles, sign-in card, nav heading, bench test-print title, the gateway docs title, the customer API title (public spec 1.2.1) and the export file's Sales Channel column now read Native Dispatch. Identifiers, Terraform, Datadog names and code comments are unchanged. The export value goes into customers' files, so Oliver is told.

PR: ilg-merak/parcel-portal#139

## 2026-11-13 — Allow a packaging preset's weight to be zero

Allow a packaging preset's weight to be zero

Native Dispatch unit T3 (R16, approved by Harry). A preset is a box; TCA's five boxes weigh 0.000, which the service refused. A preset's weight is now zero or more; size stays above zero; negatives, -0 and non-numbers still fail. No migration (the table only checks weight <> ''). A parcel with a weight of 0 or none is still refused at dispatch, now pinned by tests. Contract 5.14.0.

PR: ilg-merak/parcel-portal#137

## 2026-11-13 — Remove the Trivy ignores the rebuilt runtime images no longer need

Remove the Trivy ignores the rebuilt runtime images no longer need

Native Dispatch unit T14. The three Trivy ignores (CVE-2026-78661, CVE-2026-76844, CVE-2026-85091) expired on 2026-11-16. Harry asked to renew them; the platform has since rebuilt go-runtime and node24-runtime under the same rolling tag, and a scan of the current images finds none of them, so they are removed and the file keeps an empty list. Proven by the PR's own container scans (svc, gateway, sftp, ui all green with the empty list). The svc scan first failed on a Go proxy download error and passed on re-run.

PR: ilg-merak/parcel-portal#138

## 2026-11-13 — Show plain text when a packaging preset fails svc's request check

Show plain text when a packaging preset fails svc's request check

Native Dispatch unit T9. Saving a packaging preset showed svc's raw OpenAPI request-check text, for example 'request body has an error: ... Error at "/name": minimum string length is 1'. The action now maps the field path to the form's own label: 'Name is required.', 'Length can be at most 20 characters.'; anything unrecognised keeps the generic line. Verified through the real form on a local stack, before and after. UI only.

PR: ilg-merak/parcel-portal#140

## 2026-11-12 — Round a shipment's customs value and total weight before sending to Selector

Round a shipment's customs value and total weight before sending to Selector

Found by Check with carrier on TCA's sample orders: the FIP order (3 x 0.95) was rejected with commodity missing Wrong customs amount because the customs value went out as 2.8499999999999996, an unrounded float product, while the Cost block was already rounded to cents. The customs value is now rounded to cents and the total weight to grams, as package weights already are. UnitPrice is left unrounded. svc only; any international order whose price times quantity isn't exactly representable was affected.

Ship: SHIP-1112-tca-portal-setup (orchestrated session, no ticket)
PR: ilg-merak/parcel-portal#136

## 2026-11-12 — Generate an SFTP key pair in the admin's browser

Generate an SFTP key pair in the admin's browser

The Access tab can now make an SFTP key pair in the admin's browser (RSA 4096, WebCrypto only, via packages/ssh-keygen). The admin downloads the private key once as a PEM and only the public line is registered, as source generated, so svc never sees a private key. Pasting a public key is unchanged and sends nothing new. Proven locally: no key material in any request or log, the registered line matches the downloaded file, a heap snapshot after close is clean, and ssh -i authenticates against a local host. Reviewed with review-panel (security, frontend, platform, contract). Third of three changes after svc source on keys (#133) and the package (#132); customer self-serve is not decided.

Ship: SHIP-1112-tca-portal-setup (orchestrated session, no ticket)
PR: ilg-merak/parcel-portal#135

## 2026-11-12 — Submit the packaging preset's size and weight units

Submit the packaging preset's size and weight units

The Add preset form on Settings > Packaging could never save: the toolkit's select doesn't pass its name to the form, so the unit fields were never submitted and every save answered Choose a unit. The units now travel in hidden inputs, and the form submits from onSubmit with startTransition so React's post-action form reset no longer snaps the selects back to inches and pounds. UI only. Found by Harry adding a preset on dev; weight 0 is still rejected by svc (a decision for later).

Ship: SHIP-1112-tca-portal-setup (orchestrated session, no ticket)
PR: ilg-merak/parcel-portal#134

## 2026-11-12 — Record whether an SFTP key was supplied or generated

Record whether an SFTP key was supplied or generated

svc half of browser-side SFTP key generation: sftp_user_key.source (supplied or generated, migration 019), OpenAPI 5.13.0 additive, a same-key retry that returns the existing key and republishes the SFTP snapshot, audit fields keyId, keyType and keySource, and a debug MCP redactor that also catches clipped and base64-wrapped private keys. svc only ever receives the public line. Reviewed with review-panel; mutation-checked.

Ship: SHIP-1112-tca-portal-setup (orchestrated session, no ticket)
PR: ilg-merak/parcel-portal#133

## 2026-11-12 — Add a package that generates an SSH key pair in the browser

Add a package that generates an SSH key pair in the browser

New packages/ssh-keygen: generateSshKeyPair() makes an RSA 4096 pair with crypto.subtle only and returns a PKCS#1 PEM, an ssh-rsa public line and a SHA256 fingerprint. First of three changes so an admin's browser generates the SFTP key and the portal's server never sees a private key. Nothing consumes it yet. Reviewed with review-panel; tests added for provenance, encoding branches and DER failure paths; cross-checked against ssh-keygen and the portal's Go key validator.

Ship: SHIP-1112-tca-portal-setup (orchestrated session, no ticket)
PR: ilg-merak/parcel-portal#132

## 2026-11-12 — Hide the API key section of the customer admin UI

Hide the API key section of the customer admin UI

Removes the API card from a customer's Access tab and the API keys step from the Overview setup list, plus the listApiKeys calls behind them. UI only: the svc API, key tables and existing keys are untouched, so re-enabling is a plain revert. The business isn't ready to use the API yet.

Ship: SHIP-1112-tca-portal-setup (orchestrated session, no ticket)
PR: ilg-merak/parcel-portal#131

## 2026-11-11 — Add a dev-only debug MCP server

Add a dev-only debug MCP server

A stdio MCP at apps/svc/cmd/debug-mcp with 20 tools to read and write dev state, preview the exact Selector request for an order, search dev logs, read deploys and replay requests to Selector's test endpoint. Dev hosts only, no manifesting, no gate approval, secrets redacted.

Ship: SHIP-1110-selector-services
PR: ilg-merak/parcel-portal#128

## 2026-11-11 — Let a named developer call svc directly in dev

Let a named developer call svc directly in dev

svc is private, so nothing run from a developer's machine reached the admin API. A debug_invokers variable grants roles/run.invoker on svc to named members; dev sets one, prod ignores it.

Ship: SHIP-1110-selector-services
PR: ilg-merak/parcel-portal#127

## 2026-11-11 — Send the shipment cost so Selector can book a FedEx shipment

Send the shipment cost so Selector can book a FedEx shipment

Selector's ProcessShipment threw a null reference (0030) after the carrier step for every FedEx booking. Replaying the failed request against the test endpoint one change at a time showed the shipment-level Cost block is what it needs. The portal now sends it: the sum of each item's price times its quantity, in the order's currency, omitted when there is no price or currency.

Ship: SHIP-1110-selector-services
PR: ilg-merak/parcel-portal#126

## 2026-11-10 — Log Selector's fault text when its server fails a call

Log Selector's fault text when its server fails a call

Ship: SHIP-1110-selector-services. Dispatch on dev was refused with a bare 'carrier rejected the request' and logs showed only code 0030. Selector's own fault text (codes 0030 and 0040 only, cut to 200 chars) is now in the logged cause; it showed a null-reference inside ProcessShipment.

PR: ilg-merak/parcel-portal#125

## 2026-11-10 — Send a goods description with every shipment

Send a goods description with every shipment

Shipments now carry Selector's shipment-level Content (each distinct item's customs description, else name, else SKU, joined, cut to 35 characters). FedEx refuses a shipment without it; found by Check with carrier on the dev Beachhead Demo order after the services list was in place.

PR: ilg-merak/parcel-portal#124

## 2026-11-10 — Shipping-methods editor offers only the account's services

Shipping-methods editor offers only the account's services

On a customer with listed services, a shipping method's service code is a choice of the enabled ones, a stale mapping stays flagged blocked or not offered, and an unrestricted customer keeps free text. Increment 7 of the per-account services plan; draft, stacked.

PR: ilg-merak/parcel-portal#123

## 2026-11-10 — Account services card on the carrier page

Account services card on the carrier page

A GFS admin lists the services installed on a customer's Selector account (code, label, package code, Offered tick that blocks) in a second card on the Selector config tab; empty means no restriction, and a customer with no config is told to save it first. Increment 6 of the per-account services plan; draft, stacked.

PR: ilg-merak/parcel-portal#122

## 2026-11-10 — Shipping methods report where each service stands

Shipping methods report where each service stands

GET and PUT shipping-methods (openapi 5.12.0) add restricted, the enabled services to choose from, and a per-method serviceStatus (available, blocked, unlisted; x-extensible-enum). Increment 5 of the per-account services plan; draft, stacked.

PR: ilg-merak/parcel-portal#121

## 2026-11-10 — Refuse saving a shipping method for a blocked service

Refuse saving a shipping method for a blocked service

With listed services on a tenant's Selector account, PUT shipping-methods refuses a new or changed method for the account's carrier that maps to a blocked or unlisted service (400); unchanged rows and a reset to built-ins still save. Increment 4 of the per-account services plan; draft, stacked.

PR: ilg-merak/parcel-portal#120

## 2026-11-10 — Refuse a blocked service, send its package code

Refuse a blocked service, send its package code

Dispatch, batch dispatch and Check with carrier refuse an order whose mapped service is blocked or unlisted on the tenant's Selector account (order_not_dispatchable, before any claim or Selector call); the listed package code goes out as PackageCode between ServiceCode and Dropoff. The test carrier and tenants with no list are untouched. Increment 3 of the per-account services plan; draft, gated.

PR: ilg-merak/parcel-portal#118

## 2026-11-10 — Carrier-services API

Carrier-services API

GET and PUT /admin/tenants/{tenantId}/carrier-services (openapi 5.11.0) read and replace a tenant's Selector services; an empty list is unrestricted, the tenant needs a connection first. Increment 2 of the per-account services plan, stacked on the store PR; nothing enforces the list yet.

PR: ilg-merak/parcel-portal#119 (replaces #117, closed when #116's branch was deleted)

## 2026-11-10 — Store a tenant's Selector services

Store a tenant's Selector services

Migration 018 and a tenant-scoped store for the services on a tenant's Selector account: code, label, enabled (false blocks) and optional package code; an empty list is unrestricted. Increment 1 of the per-account services plan; nothing reads it yet.

PR: ilg-merak/parcel-portal#116

## 2026-11-10 — Let each dev customer choose the test carrier or its own Selector account

Let each dev customer choose the test carrier or its own Selector account

Dev's stand-in carrier is now a per-customer choice: carrier_connection.test_carrier (migration 017, default true so existing dev customers keep it), set from a 'Book with the test carrier' box on the Selector config card. Where CARRIER_MODE=fake, bootstrap wires fakecarrier.Router + PasswordRouter, routing every carrier call and the password read by the customer's connection; elsewhere the plain Selector client is wired and the column is never read (prod rows read true until saved, which is harmless). A switch is refused (422 carrier_switch_blocked) while the customer has booked shipments or in_flight/outcome_unknown attempts, since nothing records which backend booked a shipment; the guard is a check, not a lock (documented). Gotchas: the booking log's testCarrier must come from carrier.Test(conn), not the column; a local svc has no carrier key, so own-account saves 503 locally (dev or WithCarrierKey); the dev smoke's admin login is broken, so the authenticated dev drive (plan increment 6) is gated on a login. openapi 5.10.0. Ship: SHIP-1110-dev-carrier-optin

PR: ilg-merak/parcel-portal#115

## 2026-11-09 — Patch golang.org/x/net; ignore the runtime images' copies until they're rebuilt

Patch golang.org/x/net; ignore the runtime images' copies until they're rebuilt

Container scans (every PR, and the nightly DevSecOps run on main since 7 Nov) failed on new HIGHs: CVE-2026-78661 in golang.org/x/net v0.61.0 and CVE-2026-76844/85091 in zlib1g. apps/svc's indirect x/net is now v0.62.0, which fixes this repo's binaries (app/svc, app/sftp, app/canary, app/gateway). The remaining copies are in the platform runtime images (opt/datadog/datadog-init in go-runtime and node24-runtime 0.1-affogato; zlib1g in node24-runtime), excluded via .trivyignore.yaml (trivy YAML format: x/net by path, statements, expired_at 2026-11-16) passed to every container_scan job through the shared workflow's trivyignores input. Owed upstream: rebuild go-runtime and node24-runtime (patched datadog-init, zlib1g +deb13u1), then drop the entries; on expiry the scans fail again by design. Gotcha: a PR whose opened event triggers no runs (seen on #113) needs close/reopen to fire 'reopened'.

PR: ilg-merak/parcel-portal#114

## 2026-11-09 — Clear the previous customer's results and print state on a customer switch

Clear the previous customer's results and print state on a customer switch

C25. A GFS admin's customer switch refreshes the page in place, so client state survived it. Keyed by the acting customer: UploadPanel (Orders), ManifestBar (Shipments), PrintFrame (print-to-screen tab: it printed the old customer's labels again), ThisBench (Settings > Printing test outcome), DemoPrintPanel (old customer's demo labels and recipients). Toasts can't be cleared by a key (sonner 2.0.8's subscribe replays active toasts to a remounted Toaster), so CustomerSwitcher calls toast.dismiss() when actingId changes. Gotcha, caught by the local e2e: keys among siblings must differ, so each key is prefixed with its component (upload-/orders-/manifest-/print-/bench-/demo-printer-); UploadPanel and OrdersTable sharing the bare customer id left the old upload panel on screen. Not here: the stale-tab write guard (C19 incs 7-8) and the (app) error boundary outliving a switch (C33).

PR: ilg-merak/parcel-portal#113

## 2026-11-06 — Keep a batch's results on screen when it empties the orders list

Keep a batch's results on screen when it empties the orders list

C24. orders/page.tsx rendered 'No orders match' in OrdersTable's place when the list was empty, so dispatching every order on a filtered page (all of Ready) unmounted the table on the refresh and lost its batch results, the only way to print a batch's labels (batch dispatch doesn't auto-print). OrdersTable is now always rendered with the empty message inside, one return with stable child slots (bar, cancel dialog, results, table|empty) so the results card isn't remounted (an early return remounted it, re-enabling an in-flight Print: duplicate labels risk), and keyed by the acting customer so its longer-lived state never crosses customers (fixes C25's batch half). Smoke test dispatches from the Ready list and expects the results to survive. Gotcha: React matches unkeyed children by index; a conditional early return that reorders siblings remounts the ones that moved.

PR: ilg-merak/parcel-portal#112

## 2026-11-06 — Show each panel once on an order's page: unique keys, one dispatch summary

Show each panel once on an order's page: unique keys, one dispatch summary

C23, wider than reported. PackingPanel and LinesPanel were sibling elements keyed by the same order id; React's keyed reconciliation (mapRemainingChildren keeps one fiber per key) never matched or deleted the earlier one, so every OrderForm re-render on the keyed path left a stale panel on screen: one products card per keystroke in an address field, doubled packing forms after packing, a live Save products on a dispatched order, 'Saved' never shown. Fixed with per-panel keys; the problems alert and file problem rows had the same class (svc repeats row/field/code) and now include the index. The dispatch summary had two owners (page.tsx after revalidatePath's refresh, DispatchPanel's own result): OrderForm now holds the dispatched shipment and shows one ShipmentSummary for it or the server's copy. Smoke test asserts one products card after editing City (fails on main, passes now). Gotcha: production React prints no duplicate-key warning; only the dev build does. Follow-ups from the sweep are in Migration State.

PR: ilg-merak/parcel-portal#111

## 2026-11-06 — Show labels as a thermal bench will print them before printing

Show labels as a thermal bench will print them before printing

C22 increment 3. At a ZPL/EPL bench (or the demo printer) the Preview dialog draws each PDF page in the 1-bit dots the printer gets at the browser's DPI (pager, one-pixel-per-dot zoom, As supplied tab), and its Print sends exactly those bitmaps (label-print 0.3.0 printBitmaps; printPdf = render + printBitmaps, bytes pinned by SHA-256 from 0.2.1). renderPdfToBitmaps gained onPage (errors pass through unwrapped) and signal (the dialog aborts drawing on close). Review fixes: the print-dialog fallback prints a frame only once its PDF has loaded and only once; leaving the PDF drops a waiting print. Demo panel no longer downscales nearest-neighbour, which had dropped thin strokes ('PRFVIFW') and wrongly implicated the rasteriser: no threshold tuning needed. Gotcha for e2e: a blob PDF loads before Playwright's next click, so load-order races need a test-page shim that re-dispatches a fresh load event (Chrome clears a dispatched event's target).

PR: ilg-merak/parcel-portal#110

## 2026-11-06 — Rasterise PDF labels with pdf.js's legacy build, which runs on older Chrome

Rasterise PDF labels with pdf.js's legacy build, which runs on older Chrome

label-print 0.2.1: loadPdfjs imports pdfjs-dist/legacy/build/pdf.mjs + legacy worker. pdfjs-dist 6.4.299's modern build needs Uint8Array.prototype.toHex and Map.prototype.getOrInsertComputed; without them (Chromium 131 and 141) a PDF label at a thermal bench couldn't be rasterised and silent printing fell back with render_failed. Verified locally on both Chromium versions: 2 labels to the demo printer. Separate finding: 1-bit rendering at 203 dpi drops thin strokes in small text (threshold may need tuning).

PR: ilg-merak/parcel-portal#109

## 2026-11-06 — Split silent printing into finding the bench printer and sending

Split silent printing into finding the bench printer and sending

C22 increment 2, no behaviour change. print-labels.ts: silentPrinter() (bench, narrowed PrinterLanguage, target, demo, dpi — or the fallback reason, fetching nothing) + sendLabels(). Same check order, same parallel bench+USB lookups. Verified locally: ZPL one-click bytes identical, auto-print after dispatch toast, not_paired fallback tab. Found: pdfjs-dist 6.4.299's modern build needs Uint8Array.prototype.toHex and Map.prototype.getOrInsertComputed, so PDF rasterising fails (render_failed → dialog) on Chromium 131/141; fix via the legacy build in a separate PR.

PR: ilg-merak/parcel-portal#108

## 2026-11-06 — Send the carrier's ZPL to the printer as bytes, not text

Send the carrier's ZPL to the printer as bytes, not text

C22 increment 4. The UI's silent ZPL print read res.text() (UTF-8) and printZpl re-encoded it, so non-UTF-8 bytes under a carrier's ^CI (accents, ^GFB graphics) reached the printer as U+FFFD. label-print 0.2.0: printZpl takes Uint8Array/ArrayBuffer and sends bytes as given, counting labels via Latin-1; UI passes res.arrayBuffer(). Local e2e: demo printer job bytes identical to the label route (493 B). apps/ui lockfile doesn't pin the file: label-print version, so bumping it needs no lockfile commit.

PR: ilg-merak/parcel-portal#107

## 2026-11-06 — Show labels before printing: on the shipment page, and Preview beside each Print

Show labels before printing: on the shipment page, and Preview beside each Print

C22 increment 1. Shipment page shows its labels inline (PDF in an iframe); Preview (src/printing/label-preview.tsx) beside the order summary, Shipments and batch-results print buttons opens a shadcn Dialog with Print/Download; nothing fetched until opened; one-click print and post-dispatch auto-print untouched. printLabels gains a fallback option so the dialog never opens a tab. print-frame.tsx moved to src/printing and split into useLabels/LabelFrame/PrintFrame (also: a non-PDF 200 such as a sign-in page is now an error). Gotcha: headless Chromium's PDF viewer lays a label out wider than a narrow iframe, so the dialog is sm:max-w-6xl. Local e2e (fake carrier, Playwright container) screenshots in plans/c22-screens.

PR: ilg-merak/parcel-portal#106

## 2026-11-06 — Forward only the customer API's declared routes, not all of /v1

Forward only the customer API's declared routes, not all of /v1

Harry: be declarative about gateway routes, not a /v1 wildcard. internal/gateway/gateway.go now has an unexported routes list (POST /v1/order-files, GET /v1/order-files/{orderFileId}, POST /v1/orders) registered by method+path on the mux; any other /v1 path or method is the gateway's JSON 404. TestTheRoutesAreThePublicContractsOperations holds routes equal to public-openapi.yaml's operations (via publicapi.GetSpec), so a new customer API operation must be added to both. forwardable() stays as a second guard (an encoded .. in {orderFileId}). svc's APIKey group is unchanged.

PR: ilg-merak/parcel-portal#105

## 2026-11-05 — Fix what the dev check of the Parcel dashboard and monitors found

Fix what the dev check of the Parcel dashboard and monitors found

Follow-up to #102 after a verification workflow plus critic on dev. SFTP statsd series now carry instance: (two hosts overwrote one untagged series). Dashboard: instances sum instance_count, p95 tile aggregator percentile, canary bars .rollup(sum) (gcp.logging.user.* metrics are untyped in Datadog, so .as_count() is a no-op), 5xx tiles read gcp.run.request_count, admin list +4 events, canary _canary/ lines excluded. Monitors: SFTP unhealthy counts previous_state:healthy only; new stuck-rollout monitor on !previous_state:healthy > 4/30m; canary message points at Cloud Logging (the job has no agent). Logs: Import finished uses importSource (a second source key overrode source:go). A gateway hang-up reclassification was tried and reverted in review: callers timing out on a slow svc are the forward-failed monitor's only slowness signal; its message now explains `context canceled` instead. Also removes ILG dual-shipping (third commit; Harry 6 Nov: "we don't need the ilg api key for datadog"): DATADOG_API_KEY_ILG held a GFS-org key, so every log line landed twice in the GFS org. Parcel ships to the GFS org only now.

PR: ilg-merak/parcel-portal#104

## 2026-11-05 — Let the UI write Next's prerender cache

Let the UI write Next's prerender cache

The UI runtime stage copied .next as root and ran as nonroot, so Next logged an EACCES error on every prerender cache write (28 in dev over 3 days). It now copies with --chown=nonroot:nonroot. Found via the observability work (#102).

PR: ilg-merak/parcel-portal#103

## 2026-11-05 — Observability in Terraform: tabbed dashboard, log metrics, GCP integration, monitors on in dev

Observability in Terraform: tabbed dashboard, log metrics, GCP integration, monitors on in dev

Adds a [Parcel <env>] dashboard with 7 tabs (dashboard.json.tftpl, validated against Datadog's API), 13 parcel.<env>.* log-based metrics, the GCP integration registration, and datadog_monitors_enabled in dev. The Datadog provider moves to ~> 4.4 for tabs.
Found: the shared ilg-platform cloud-run module hardcodes DD_ENV=serverless, so env:dev log queries (monitors, runbook) matched nothing. Switched to @env. A platform fix is owed.
Needs the DATADOG_APP_KEY org secret, and gcp-config#9 applied first.

PR: ilg-merak/parcel-portal#102

## 2026-11-05 — Error pages instead of Application error; sign-out survives svc failing

Error pages instead of Application error; sign-out survives svc failing

C19 PR 2 (UI, plan increment 5).
- A shared ErrorPanel backs app/(app)/error.tsx (page errors) and app/error.tsx (errors in the signed-in layout, e.g. /me failing for a stale acting cookie). It offers Try again (router.refresh and reset), Back to GFS (only while acting, via isActingAction since the cookie is httpOnly: clears acting, then a hard load of /orders) and Sign out, and shows the error digest as a support reference.
- signOutAction retries svc once after 1 s, then clears both cookies anyway.
- On /sign-in the panel offers only Try again.
- The dev browser check (stale cookie in DevTools) is still owed: no credentials on rc-hjf.

PR: ilg-merak/parcel-portal#101

## 2026-11-05 — Acting-as safety in svc: session-only acting, sign-out, actorId, stale-tab guard

Acting-as safety in svc: session-only acting, sign-out, actorId, stale-tab guard

C19 PR 1 (svc, plan increments 1–4).
- X-Acting-Tenant is read on session routes only, and /auth/* ignores it. A gone customer is 404 acting_tenant_not_found.
- Logout revokes in the session's own tenant (it silently revoked nothing while acting).
- actorId is on every signed-in log line via a per-request slot (TrackActor in Correlation, SetActor in Authorize), Request completed included. User events name the subject targetUserId.
- Optional X-Expected-Tenant: 409 tenant_changed is checked in Authorize after scope resolution, documented on 15 operations, and the acting line is logged only after it. Contract 5.9.0.
- e2e: the stale-tab table refuses all 15 and changes nothing, and fails with the guard disabled.
The UI halves are PRs 2–4.

PR: ilg-merak/parcel-portal#100

## 2026-11-05 — Report a refused smoke sign-in at once, with its reason

Report a refused smoke sign-in at once, with its reason

The dev smoke test waited 30 s for the URL to leave /sign-in and failed with a URL mismatch. It now polls for either outcome and fails at once when the sign-in form shows its error, naming the account and the message. The login itself still needs DEV_SMOKE_ADMIN_EMAIL or the password fixed (Harry).

PR: ilg-merak/parcel-portal#99

## 2026-11-05 — Export a range of days, up to 31

Export a range of days, up to 31

GET /exports/shipments and /exports/shipments.csv take an optional to: the export covers the site-local days date to to, inclusive, at most 31 (to needs date and can't be before it; 400 otherwise). The summary returns to, the file is shipments-<date>-to-<to>.csv, and the contract is 5.8.0. The Export page replaces the toolkit dd/mm picker with native First day and Last day inputs in a GET form with Show, and the CSV fetch allows 60 s. Stack 3/3 of the Wilders DC-parity build (C21).

PR: ilg-merak/parcel-portal#98

## 2026-11-05 — Link tracking from the Shipments pages, with a link per consignment

Link tracking from the Shipments pages, with a link per consignment

Tracking link templates take {consignment} as well as {tracking}. With {tracking} there's one link per parcel; a template with only {consignment} gives one per shipment, which is DC's GFS ConsLink.asp shape. The export column follows the same rule. GET /shipments and GET /shipments/{id} return trackingUrl (contract 5.7.0), the Shipments list and detail link out, and the Export tab has a one-click GFS preset. There's no default template. Stack 2/3 of the Wilders DC-parity build (C21).

PR: ilg-merak/parcel-portal#97

## 2026-11-05 — Let a GFS admin set a customer's export settings

Let a GFS admin set a customer's export settings

Wilders' DC-parity item 1 (tracking link), step 1/3. GET/PUT /admin/tenants/{id}/export-settings (IANA time zone, https tracking-link template with {tracking}, Excel-formula flag) + customer Export tab with preview. Nothing on by default. Contract 5.6.0.

PR: ilg-merak/parcel-portal#96

## 2026-11-04 — Smoke-test dev in a browser after every deploy

Smoke-test dev in a browser after every deploy

Harry, 4 Nov: browser smoke test. e2e/ Playwright package; dev-smoke.yaml (reusable, nightly, manual) in the Playwright image signs in as a dedicated GFS admin (DEV_SMOKE_ADMIN_PASSWORD secret), makes a demo customer, uploads the sample, fixes, packs, dispatches 5, checks Shipments, always deletes the demo. Called after svc and ui dev applies; report-only.

PR: ilg-merak/parcel-portal#91

## 2026-11-04 — Add a demo customer and a sample order file for trying the portal on dev

Add a demo customer and a sample order file for trying the portal on dev

Harry, 4 Nov: make upload → pack → label easy to test. Dev/local only (fake carrier): POST /admin/demo-customer sets up a ready customer (DC layout, fake Selector, presets, demo printer); GET /sample-orders.csv gives ready/needs-packing/flagged orders with fresh refs. UI: Try the portal card (acts for it, opens Orders) and Download a sample file. Contract 5.5.0. Checklist rewritten.

PR: ilg-merak/parcel-portal#90

## 2026-11-04 — Make a customer's SFTP folder from its name instead of asking for one

Make a customer's SFTP folder from its name instead of asking for one

Harry, 4 Nov: SFTP users are locked to /inbound, so the folder (slug) should be generated. svc makes it on create from the name + 4 random chars (retry on clash); migration 016 backfills; New customer asks name only; Overview folder read-only. Contract 5.4.0. Stack 3/3 on #88.

PR: ilg-merak/parcel-portal#89

## 2026-11-04 — Let a GFS admin soft-delete a customer and restore it

Let a GFS admin soft-delete a customer and restore it

Harry, 4 Nov: (soft-) delete customers. tenant.deleted_at (migration 015); while deleted: sign-in, sessions, API keys, SFTP snapshot, slug lookup and admin upload all refuse; restore undoes it. Customers page splits deleted with Restore; Overview Delete customer; switcher skips deleted. Contract 5.3.0. Stack 2/2 on #87.

PR: ilg-merak/parcel-portal#88

## 2026-11-04 — Let a GFS admin edit, re-enable and set the password of a user

Let a GFS admin edit, re-enable and set the password of a user

Harry, 4 Nov: GFS admins manage users. Edit name/email, enable, set password (revokes sessions); disable now revokes sessions; no self-disable in svc. Contract 5.2.0. Stack 1/2 with customer soft-delete.

PR: ilg-merak/parcel-portal#87

## 2026-11-04 — Put a customer's users, SFTP logins and API keys on one Access tab

Put a customer's users, SFTP logins and API keys on one Access tab

Harry, 4 Nov: merge Users, SFTP users and API keys, make them intuitive, link the Swagger viewer and share the SFTP host. Access tab with Portal users / SFTP (host, port, /inbound, key-only) / API (address, docs link, bearer key) cards; old tab URLs redirect; stale 'not live yet' notes removed. ui Terraform: SFTP_HOST and CUSTOMER_API_URL env vars from dns_domain (plan to Harry before merge).

PR: ilg-merak/parcel-portal#86

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
