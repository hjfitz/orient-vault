---
tags:
- system
- parcel-portal
verified: '2026-11-03'
title: parcel-portal — design language
---
# parcel-portal — design language

The system has one rendered surface, the [[parcel-portal]] ui (`apps/ui`), built on `@ilg-platform/ui-toolkit` with GFS branding.

## The stance
- **The reader is a pack-station operator at a bench**, often standing, scanning and printing, not an engineer. Say why an order can't go in plain words ("ZIP must be 12345 or 12345-6789"), never a code.
- **One obvious next action per state:** fix, pack, dispatch, print. Batch actions only on orders that can take them (only `ready` rows can be ticked).
- **Printing never dead-ends.** Every print path falls back to the browser's print dialog and says why.
- **Destructive carrier actions confirm first:** void and manifest.

## Conventions
- Toolkit components wherever one exists; frontend structure decisions wait for Darren Rielly's principles (`AGENTS.md`, *Frontend*).
- Light theme only; dark mode isn't built (snapshot 2026-10-29).
- Dates and the export day are the site's local day, shown as such.

## From the UX review (2026-11-03)
- **`GButton` defaults to `ghost`**, which reads as plain text. Every primary action sets `variant="default"`, and secondary ones `outline`.
- **The order page leads with the state's next step:** Dispatch first when ready, Packing first when it needs packing. A problem is shown on the field it's about. Dispatched and voided orders are a read-only summary, never a greyed-out form.
- **One back control:** `GHeaderContent backHref`, never an in-page "Back" button or link.
- **Configuration lives on the customer.** Everything an admin sets for one customer is a tab under Settings → Customers → that customer: Overview (folder plus setup checklist), File layout, Shipping methods, Carrier account, Packaging, Bench printers, Users, SFTP users. Never a top-level page with a customer picker. GFS's own tenant is "GFS staff", with Users only.
- **A failure names what failed** ("SFTP users can't be loaded…"), and svc's lower-case reasons are turned into sentences before they're shown.
- **Dates still show UTC** until the tenant's time zone reaches the UI (`/me`), even though the stance above is the site's local day. That's the open gap.
- **Phones aren't a target:** the reader is at a bench computer, and the wide tables don't reflow at 390px. That's deliberate.
