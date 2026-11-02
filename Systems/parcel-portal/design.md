---
tags:
- system
- parcel-portal
verified: '2026-10-29'
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
