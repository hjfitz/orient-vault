---
tags:
- waypoint
- client4
verified: '2026-11-05'
---
# client4 — known context

Interview truth (Harry, 2026-11-05) and facts source can't give. System-wide context (ownership, hosting, direction, unknowns) is in the `selector` system's known-context. This file holds what is specific to Client4.

## History that explains the code
- **The repo is called V4 but holds only the client.** The central server projects moved to their own `V4-Server-*` repos on 2023-10-11. `Server/*` here are README stubs saying so.
- **`Client.Alpha` is the live app**, despite the name. `GFSClient4 4.0.532.4.zip` at `Client/` is an old build artefact committed to the repo.
- **Release branches are `Release-4.50.x`**, for example `Release-4.50.6.6`, merged to `main` on 2026-08-27. Tickets are SMXI. Client4 and CSS release separately, on separate branch lines.
- **Alternative services are dormant.** They have been off since 2026-08-18 ("until the database is updated").

## Fragility and surprises
- **The upload station is a single point of failure per site.** If that PC is off or Client4 is closed, labels still print but nothing reaches GFS. CSS customers are affected too.
- **Delphi 7 only.** The project is a `.dof`, not a `.dproj`, so it needs the Delphi 7 IDE plus the same third-party component packs (DevExpress, IBX) installed. Nobody outside the current developers is known to have a working build machine.
- **Very large units.** `fmMain.pas` is about 9.6k lines and `dmClient.pas` about 5.7k. Search by handler or dataset name.
- **Carrier code duplicates CSS.** `Carriers/*.pas` mirrors the CSS `Carriers/*.cs` for the same carriers. A fix in one rarely lands in the other at the same time.

- **A blank `FEDEX_URL` falls back to FedEx's test gateway** (`gatewaybeta.fedex.com`, `uFedex.pas:96`). A site set up without the column would ship to FedEx's beta environment.
- **Re-registration wipes the site.** The registration script deletes shipments, routes, ranges and contracts before reloading. The menu only appears when the local `SITE_REG = 0`.

## Unknowns
- Who uploads new Client4 exes through Manager's Versions screen today, and how many sites have `AUTO_UPDATE` on.
- Who holds a working Delphi 7 build environment, and whether it is reproducible.
- How many sites run Client4 without any CSS use, and how many CSS customers have a live upload station.
