---
tags:
- waypoint
- css
verified: '2026-11-05'
---
# css — known context

Interview truth (Harry, 2026-11-05) and facts source can't give. System-wide context (ownership, hosting, direction, unknowns) is in the `selector` system's known-context. This file holds what is specific to CSS.

## History that explains the code
- **This repo, not CSS-Enterprise, carries the live line.** `CSS` has about 700 commits from 2022-08 to 2026-10, including the SMXI 4.50.7.0 tasks (for example 607). `CSS-Enterprise` has 9 commits (2023-02 to 2025-08), ending in an unfinished refactor whose batch path is no-ops. The Tech Services vault still names CSS-Enterprise as the source. **ASSESSED** from history. Confirm with Jez which repo the shipped 4.50.7.0 DLL was built from.
- **`AssemblyFileVersion` in this repo is stale** (4.0.482.2). The deployed DLL's version can't be matched to a commit from the repo alone.
- **Two generations of carrier code.** The older carriers are static `InternalProcedures/<Carrier>Procedures.cs` files. Carriers that moved behind GFS's own proxies (BJS, Coll8, Exelot, FedEx, InPost, OCS, Royal Mail, DPD NL/DE) are `ICarrier` classes in `Carriers/`. Some carriers have both, for example `FedexProcedures.cs` and `FedexApiProcedures.cs`, and `InPostProcedures_old.cs` is still in the tree.
- **`LocalSwagger/` holds several copies of each proxy spec**, such as `fedex-integration-api (3).yaml` and `NEW.yaml`. Nothing marks which one the generated client was built from.
- **The SMXI-Release-4.50.7.0 merge to master was reverted on 2026-10-16.** The FedEx URL commit on 2026-10-20 followed it. Check master against the release branch before assuming a 4.50.7.0 fix is live.

## Fragility and surprises
- **The procedure files are huge.** `ValidateProcedures.cs` is about 10k lines and `LabelProcedures.cs` about 6k. Search by method name. Don't read them end to end.
- **Committed environment config.** `Web.config` in the repo carries a working connection string with the Firebird admin login. Treat the repo copy as one developer's box, not a template (class-level; specifics belong in the security ticket).
- **API users live in two tables.** API version 5.1.3 checks `web_users`. Every other version checks `gfs_users` with role 3 ("Web user"), set up in Client4 under Defaults → Users. Both store and compare passwords in plaintext (class-level).
- **Recent debugging writes payloads to disk.** Since October 2026, carrier calls dump the last request and response under `C:\temp` on the host (class-level).
- **The `Test*` projects aren't tests.** Each is a console app that sends one SOAP call to a configured endpoint. They have no assertions and no runner.

## Releases
- Only `vzClientSoapServer.dll` ships. It is copied by hand into the `ClientServer` IIS app on each VM, as a "GFS Enterprise" release from GFSIT SharePoint, and only to the sites that need it. Some releases also need hand edits to the production `Web.config`, such as the 4.50.7.0 carrier-logging keys.
- `SetupCSS`/`MainSetupCSS` are an old MSI and bootstrapper (IIS6 compatibility, Firebird 1.5, .NET 2.0), last touched 2022. They aren't the delivery path.
- `CheckUpdates` doesn't update CSS. It checks the site DB's version status and can fire `UPD_FOUND`, which makes Client4 pull Selector updates.

## Logging
- `Logging:Sinks` = `File,Http`. The repo's endpoint is a dev address. Production pointed at SMXI's LoggingServer (`logging.gfsdeliver.com`: public, no auth, source not in any repo). 4.50.7.0 moves sites to [[carrier-logging]] on Cloud Run.

## Unknowns
- Which CSS build each VM runs. Releases go only to sites that need them, so versions drift. `VersionId` is the API contract version (5.0.0 or 5.1.x), not the build. Read the DLL's file version on the VM.
- Which `LocalSwagger` copy each `Service References` client came from.
- Each VM's production `Web.config` logging values, and whether the carrier-logging Datadog copy is on.
