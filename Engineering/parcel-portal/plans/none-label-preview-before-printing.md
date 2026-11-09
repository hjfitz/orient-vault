---
ticket: none
title: Label preview before printing
service: parcel-portal
status: active
created: '2026-11-06'
updated: '2026-11-06'
repo: ilg-merak/parcel-portal
worktree: /home/harry/code/merak/parcel-portal/.claude/worktrees/label-preview
branch: hjf/label-preview
base: origin/main
base_sha: 82ced5cb1959915e2deafd25254a42be163c80da
pr: '106'
tags:
- waypoint
- plan
programme: Parcel Portal
unit: C22
---
# none — Label preview before printing

<!-- Guidance in this file is written as HTML comments: Obsidian hides them, agents read them,
     and `wp signoff` ignores them. Only <angle spans> are treated as unfilled placeholders, so
     they mark the places a human or agent must actually type something. Leave the comments in
     place — deleting them costs the next reader the guidance and gains nothing at the gate.

     SUPERSEDING A STATEMENT. This file is edited by several sessions over days. When something
     here stops being true, do NOT strike it through, delete it, or bury a correction inside it.
     Put one blockquote immediately ABOVE the stale text and leave the text alone:

         > SUPERSEDED 2026-09-04 — the monitor now lives in `gfs-bifrost/observability`.
         > Everything below is kept as the record of how it was first built here.

     One marker, always above, never inside. `wp decide` writes the dated entry in
     `## Decisions & deviations` that explains why. -->

## Intent
<!-- What we are changing and why. Link the ticket. -->
Harry, 6 Nov: "can we also look at rendering the label on the page or having some means of showing it prior to printing?" Today a label only appears on screen as the print fallback, and only for PDF accounts; a ZPL account gets a download. Users should see a shipment's labels on its page, and preview them from every Print button, without one-click printing or the automatic print after dispatch getting slower. At thermal benches the preview should be the printer's own dots, so it is exactly what prints. No label data leaves the browser.

## Acceptance criteria
<!-- Observable, checkable outcomes — not tasks. Numbered by order: increments cite them as
     (AC 2,4), and sign-off prints which criteria no increment claims. -->
- [ ] 1. The shipment page's Labels card shows the shipment's PDF labels inline; a voided shipment still shows only its note.
- [ ] 2. A Preview button sits next to Print on the order's shipment summary, the Shipments list (ticked rows) and the batch dispatch results, and opens the same labels in a dialog with Print and Download.
- [ ] 3. The dialog's Print never opens a new tab: it prints silently where this browser is set up for it, and otherwise prints the frame on screen.
- [ ] 4. One-click Print buttons and the automatic print after a dispatch behave exactly as before.
- [ ] 5. A ZPL account sees that the label can't be drawn here, with Download, in place of a drawing.
- [ ] 6. At a ZPL/EPL bench or with the demo printer, a PDF label's preview shows the 1-bit dots the printer gets at this browser's DPI, and the dialog's Print sends those same dots.
- [ ] 7. Carrier ZPL reaches the printer byte for byte (no UTF-8 decode and re-encode on the way).

## Affected boundaries
<!-- Components, paths and contracts this touches. Wikilink existing explainers; do not restate
     their contents. If this names a topic, endpoint, canonical type, collection, inter-service
     dependency or shared package, sign-off will prompt for the Fuse MCP data file too. -->
- UI `apps/ui/src/printing/` (print-labels.ts, reasons.ts, demo-print-panel.tsx), `app/(app)/shipments/print/print-frame.tsx`, shipment page Labels card and parcels table, `orders/[id]/dispatch-panel.tsx`, `orders/batch-results.tsx`, `shipments/shipments-table.tsx`.
- `packages/label-print` (increments 3–4): `printBitmaps`, a per-page callback on `renderPdfToBitmaps`, `printZpl` taking bytes. The UI holds a `file:` copy, so `pnpm install` in `apps/ui` after each change.
- No svc or contract change: the preview reads the UI's existing label routes, which proxy `GET /shipments/labels` and `GET /shipments/{id}/parcels/{parcelId}/label`.

## Assumptions & uncertainty
<!-- One line each, with how it was established. A genuine product or domain question goes here
     as UNRESOLVED: and is raised with the user, never invented. -->
- A label is PDF or ZPLII per customer carrier connection; demo customers and the Evri sandbox are PDF — source read (`core/carriers/connection.go`, `core/demo/demo.go`).
- A ZPL account's labels can't be drawn by a browser natively; the best open renderer is Labelize (Rust→WASM, MIT, ~3 MB, one main maintainer since March 2026) — research workflow wf_e93d3f55-6f5, read from source and docs only.
- Labelize draws only the first label it's given and honours a fixed size over `^PW`/`^LL`; its text fields don't survive raw non-UTF-8 bytes — critic, read from labelize v1.10.0 source.
- Selector's sandbox PDFs are A6 pages (MediaBox 0 0 297 420) with the 4×6 image overhanging the bottom by 12 pt, so thermal benches print them at about 97% with white bands and may lose the bottom strip — critic, from the PDFs' MediaBox; not printed.
- svc books ZPLII with `LabelStock PAPER_4X6`; FedEx expects a thermal stock for ZPL, so FedEx ZPL bookings may be refused — critic, from FedEx integrator reports; unverified through Selector.
- UNRESOLVED: ZPL drawing. Recommendation: keep ZPL accounts download-only until a ZPL customer exists (TCA's printers are open, G4); then either Labelize in the browser after a render test on sandbox labels (running third-party code locally needs Harry's OK), or keep accounts on PDF labels, which already print on ZPL/EPL benches and get an exact preview.

## Increments
<!-- Each independently implementable AND verifiable. Cite the criteria it discharges as
     (AC n,n). Tick with `wp tick`, which stamps `— done: <sha>` from HEAD; never hand-write it.
     Prefer 3-7 — more usually means the ticket is too big, so say that rather than splitting
     hairs.

     A PRECONDITION THAT IS NOT CODE goes on its own indented `gate:` line, with a confirmation
     box under it. Sign-off blocks on a ticked increment sitting above an unconfirmed gate, and
     `wp brief` shows unmet gates in its NEXT block — so "do not action this yet" stops being
     bold prose a fresh session can miss:

         - [ ] 6. Widen the subscription filter (AC 6) — verify: filter matches in dev
               gate: FUSE-1052 AND FUSE-1053 confirmed in prod
                     [ ] confirmed
-->

- [x] 1. Labels shown as supplied: one label view in `src/printing/` (fetches the label route once; PDF in a frame without print-on-load; ZPL message with Download; errors, including a sign-in page served as HTML), inline in the shipment page's Labels card, and in a Preview dialog beside Print on the order summary, the Shipments list and the batch results. The dialog's Print prints silently where set up and otherwise prints the frame; it never calls the new-tab fallback (AC 1,2,3,5) — verify: dev screenshots of each surface with the demo customer, a voided shipment shows no labels, and a one-click Print still reaches the demo printer with its toast — PR #106 merged as 6798b4e; local e2e screenshots in c22-screens, keyboard focus and mixed-format checks — done: 6fe7544
- [x] 2. Split `printSilently` into decide and send with no behaviour change, the USB lookup still in parallel (AC 4) — verify: tests for PDF and ZPL, USB and demo targets; one-click and automatic print evidence on dev; timing unchanged — PR #108 merged as 09c3377; local: ZPL one-click bytes identical, auto-print toast, not_paired fallback; PDF path pending #109 — done: 472ecf3
- [x] 3. As printed at thermal benches: `printBitmaps` and a per-page callback in label-print (`printPdf` rebuilt on it, bytes unchanged); the dialog shows the bitmaps with a pager and a one-dot-per-pixel zoom; its Print sends those bitmaps (AC 6) — verify: label-print tests prove `printPdf`'s bytes unchanged; on dev with the demo printer, preview bitmaps equal the printed ones — PR #110 merged as 8827b37; label-print 110 tests incl. printPdf bytes pinned from 0.2.1; local e2e on Chromium 141 and 131: shown dots hash-match the printed job, dialog bytes = one-click bytes, fallback prints once after load — done: b1763af
- [x] 4. Carrier ZPL as bytes: `printZpl` accepts bytes and the UI reads ZPL with `arrayBuffer()` (AC 7) — verify: a unit test sends non-UTF-8 bytes unchanged; on dev the demo panel's ZPL equals the label route's bytes — PR #107 merged as dc927c2; unit test fails on a UTF-8 round trip; local demo-printer bytes identical to the label route — done: c0a0311
- [ ] 5. ZPL drawn in the browser, or ZPL accounts kept download-only (AC 5)
      gate: Harry decides between Labelize after a render test and PDF-only, once a ZPL customer is confirmed
            [ ] confirmed

## Verification
<!-- The single authority for evidence. Increment lines carry `— done: <sha>` and nothing else.
     Check-selection order lives in verification-menu.md — do not restate it here. -->

### Evidence
<!-- Newest first, dated. One bullet per check actually run, opening with what it discharges.
     "Suite green" alone is not evidence. Sign-off requires at least one dated bullet here. -->
- 2026-11-06 [inc 3] **As printed at thermal benches (#110), local end to end on Chromium 141 and 131.** Ran against the branch's built UI, svc with the fake carrier, and a two-parcel PDF shipment (PREVIEW-8) previewed from the Shipments list:
  - **Demo printer at a ZPL bench:** the description reads "As Bench 1's demo printer will print them, at 203 dpi."
  - **Pager:** 1 of 2, then 2 of 2.
  - **Zoom:** 812 × 1218 px for an 812 × 1218-dot label.
  - **Tabs:** As printed keeps its label across a trip to As supplied.
  - **Print:** the demo printer's job has the same dots as the dialog showed (SHA-256 per label). The dialog's bytes equal a one-click Print's: 42,810 B on 141, 43,209 B on 131. No frame print. Screens `c22-screens/inc3-1…4`.
  - **Regressions:** a ZPL shipment shows the ZPL note, and its bytes are identical to the label route's. Not set up gives the PDF, and Print prints the frame once.
  - **Paired device that isn't a printer:** the toast gives the reason, the dialog switches to As supplied and prints the frame once (`inc3-5`).
  - **Review fixes, with the frame's `load` held back 1.5 s by a test shim, every click confirmed to beat the load:**
    - Not set up, Print before the load: 1 print, after the load.
    - Two failed sends during the load: 1 print.
    - Leaving As supplied before the load: 0 prints.
  - **Demo panel scaling fix:** "Ref PREVIEW-8" reads correctly at 320 px (`inc3-6`). Before the fix, the same job read "PRF…" (`inc3-4`).
  - Logs: `c22-screens/inc3-e2e-chromium141.txt`, `…131.txt`.
- 2026-11-06 [inc 3] **label-print 0.3.0: 110 tests.**
  - `printPdf`'s ZPL (2,554 B) and EPL (248,526 B) bytes for a fixed two-page PDF are pinned by SHA-256. The hashes were taken by running 0.2.1 from `main`, so the bytes are unchanged.
  - `printBitmaps` has tests for ZPL, EPL, the count, the bitmaps and the DPI on the job, and the default DPI.
  - `onPage` has tests for streaming order, identity, page and count, and errors passed on unchanged that stop the drawing.
  - The signal has tests for stopping before the next page and rejecting with its reason.
  - UI `lint`, `build:check` and `next build` are clean. All of #110's CI checks are green.
- 2026-11-06 [inc 2] **Split (#108) checked on main** (with #109's legacy pdf.js), Chromium 131, demo printer at a ZPL bench:
  - PDF one-click prints 2 labels (812 × 1218 dots, ZPL).
  - ZPL one-click sends bytes identical to the label route's (493 B).
  - The automatic print after Dispatch toasts "Demo printer: 1 label for Bench 1".
  - With no bench set up, Print opens `/shipments/print?…&reason=not_paired`.
- 2026-11-06 [inc 4] **ZPL as bytes (#107).** label-print 0.2.0's `printZpl` takes a `Uint8Array` or `ArrayBuffer`, and the UI passes `res.arrayBuffer()`.
  - The new test sends 0xE9 and 0xFF inside `^FD`. It fails against a UTF-8 round trip and passes with the fix; label-print has 95 tests passing.
  - Locally, with a ZPL bench and the demo printer, a one-click Print toasts "Demo printer: 1 label for Bench 1". The job's bytes are identical to the label route's (493 B, `^XA^CI0^PW812^LL1218…`).
  - That also covers inc 1's open check, a one-click Print through the demo printer.
- 2026-11-06 [inc 1] **Review fix, keyboard focus:** Preview is now the dialog's trigger. Enter opens it (`aria-expanded=true`), and Escape returns focus to Preview (`focused after Escape: preview-selected`).
- 2026-11-06 [inc 1] **Mixed PDF and ZPL batch:** the dialog shows svc's "different formats … smaller batches" message with Print disabled (`c22-screens/0-…`).
- 2026-11-06 [inc 1] **Local end to end.** svc ran on a fresh local database with the fake carrier, and the built UI (`next start`) pointed at it. The data: a demo customer, orders PREVIEW-1 (1 parcel) and PREVIEW-2 (2 parcels) put in through `POST /v1/orders` and dispatched. Then PREVIEW-1 voided, the carrier account switched to ZPL, and PREVIEW-3 dispatched. Playwright 1.49.1 (the official container, full Chromium) produced the screenshots in `c22-screens/`:
  - **Shipments, both ticked:** Preview (2) opens "Labels for 2 shipments" with all 3 labels (`2-…`).
  - **PREVIEW-2's page:** shows its 2 labels inline (`3-…`).
  - **Order page:** Preview sits beside "Print the label" (`4-…`), and its dialog shows the label (`5-…`).
  - **Voided PREVIEW-1:** only the note, with 0 label frames (`6-…`).
  - **ZPL PREVIEW-3:** the inline view shows the thermal-printer message with no duplicate Download. The dialog shows the message, Print disabled (no silent printing) and Download to `/shipments/labels?shipmentId=…&download=1` (`8-…`).
  - **Print-to-screen page:** frame shown, Print enabled, reason alert shown (`9-…`).
- 2026-11-06 [inc 1] **Headless Chromium's PDF viewer lays the label out wider than its frame,** so the 768 px dialog clipped it. Neither `#view=Fit` nor a resize corrected it. The dialog is now `sm:max-w-6xl`, which shows the whole label at 100% (`5-…`). Not checked in headed Chrome: the headed run under xvfb hung.
- 2026-11-06 [inc 1] **Gates:** `pnpm run lint` and `build:check` clean, `next build` compiles.

### Not verified
<!-- Stated, not papered over. "(none)" is a deliberate claim, and a fine one. -->
- [inc 1] Dev: this machine can't sign in to dev (no dev admin credentials), so the surfaces were checked on a local svc and UI, not dev. A look at a shipment's Preview on dev, in real Chrome, would also confirm the wide dialog shows the whole label outside headless.
> SUPERSEDED 2026-11-06 — exercised under inc 4: a one-click Print of a ZPL shipment through the demo printer, bytes identical to the label route.
- [inc 1] A one-click Print through the demo printer after the change. The code path is unchanged (`printLabels` without options), but it wasn't exercised.
- The A6 overhang and the FedEx ZPL stock problem: both read from files and reports, neither printed nor booked.
- [inc 3] **Dev:** the increment's "on dev with the demo printer" check ran locally instead, because this machine has no dev sign-in. Dev runs #110: `ui-parcel-dev-00054-rm9` on image `parcel-ui:dev-8827b37…`, with sign-in returning 200. That is confirmed by the image and sign-in only. The first dev apply failed reading state (GCS credentials 504) before planning, and passed on a re-run of the failed job.
- [inc 3] **Aborting a long batch on close:** covered by label-print's signal tests, but no e2e closed the dialog mid-draw.
- [inc 3] **Selector's A6 sandbox PDFs** haven't been drawn through As printed. That view would show whether they lose the bottom strip.

## Handback
<!-- Append-only, newest first. Written by `wp handback`, never by hand.
     Sign-off never clears this section — a refuted approach is exactly what a
     later session needs and what ## Learnings would have deleted. -->

### 2026-11-06 13:01
- **stopped:** Increments 1-4 merged (#106, #108, #107, #110). Inc 5 (ZPL drawn in the browser, or ZPL accounts kept download-only) waits on Harry's decision; the recommendation stands in Assumptions.
- **tried and abandoned:** Tuning label-print's 1-bit threshold for thin strokes at 203 dpi: refuted. 'PREVIEW' reading 'PRFVIFW' was the demo panel's 320 px nearest-neighbour downscale, not the rasteriser; the same job's dots at one pixel per dot read 'Ref PREVIEW-8' (c22-screens/inc3-2, inc3-4 vs inc3-6).
- **turn:** me

## Decisions & deviations
<!-- Date-stamped, newest first — written by `wp decide`, and by hand when that is easier.
     Where implementation departed from this plan, and why. Source wins over the plan: correct
     the plan in the same increment and record the correction here. Legitimately empty at plan
     time. A decision worth defending in a review six months out belongs in a durable record
     instead — `wp decide --record`. -->

- **2026-11-06** — Inc 3 review (frontend + tests panel): the print-dialog fallback prints a frame only once its PDF has loaded, and once; leaving As supplied drops a waiting print. renderPdfToBitmaps gained a signal (the dialog aborts drawing on close) and passes onPage errors on unwrapped. printPdf's bytes are pinned by SHA-256 taken from 0.2.1 instead of a test comparing printPdf with itself. The demo panel's nearest-neighbour downscale was fixed in the same PR because it had misled the rasteriser diagnosis.
- 2026-11-06 — Inline on the shipment page plus a Preview dialog by each Print, not a preview step before every print: benches print in one click and dispatch prints with none (Harry asked for "on the page or some means of showing it prior to printing"). No external renderer: labels carry names and addresses. Plan drafted from a five-agent read-only research workflow (surface map, ZPL renderer assessment, PDF options, synthesis, critic) rather than waypoint-plan's own agents.

## Learnings
<!-- Durable facts about the service surfaced while planning, working or testing that are not
     already written anywhere in the vault — a gotcha, a constraint, a fragile edge, a confirmed
     or refuted hypothesis. Not restated doc content. Sign-off promotes each confirmed one into
     the matching durable doc, then clears it from here; a refuted one moves to ## Handback
     rather than being deleted. Legitimately empty. -->
- **pdfjs-dist 6.x's modern build needs a very recent Chrome.** It calls `Uint8Array.prototype.toHex` and `Map.prototype.getOrInsertComputed`, so on Chromium 131 and 141 a PDF label couldn't be rasterised for a thermal bench (`render_failed`, so the print dialog). label-print now loads the legacy build (#109). Local headless checks on Playwright 1.49's Chromium 131 hit the same wall. Confirmed on both versions.
- **e2e: a blob PDF in a frame loads before Playwright's next click,** so a "click before the PDF loads" race can't be hit as-is. Holding the frame's load listeners back in the test page works. The late load must be a fresh `load` event dispatched at the frame: Chrome clears a dispatched event's `target`, so replaying the original event never reaches React's `onLoad`.
- The UI's ZPL print path decodes the carrier's bytes as UTF-8 (`res.text()`) and re-encodes them, so non-UTF-8 bytes reach the printer as U+FFFD (print-labels.ts, label-print print.ts) — read from source, increment 4 fixes it.
