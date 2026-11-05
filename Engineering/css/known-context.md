---
tags: [waypoint, css]
verified: 2026-11-05
---
# css — known context

Interview truth (Harry, 2026-11-05) and facts source can't give. System-wide context (ownership, hosting, direction, unknowns) is in the `selector` system's known-context. This file holds what is specific to CSS.

## History that explains the code
- **Two generations of carrier code.** The older carriers are static `InternalProcedures/<Carrier>Procedures.cs` files. Carriers that moved behind GFS's own proxies (BJS, Coll8, Exelot, FedEx, InPost, OCS, Royal Mail, DPD NL/DE) are `ICarrier` classes in `Carriers/`. Some carriers have both, for example `FedexProcedures.cs` and `FedexApiProcedures.cs`, and `InPostProcedures_old.cs` is still in the tree.
- **`LocalSwagger/` holds several copies of each proxy spec**, such as `fedex-integration-api (3).yaml` and `NEW.yaml`. Nothing marks which one the generated client was built from.
- **The SMXI-Release-4.50.7.0 merge to master was reverted on 2026-10-16.** The FedEx URL commit on 2026-10-20 followed it. Check master against the release branch before assuming a 4.50.7.0 fix is live.

## Fragility and surprises
- **The procedure files are huge.** `ValidateProcedures.cs` is about 10k lines and `LabelProcedures.cs` about 6k. Search by method name. Don't read them end to end.
- **Committed environment config.** `Web.config` in the repo carries a working connection string with the Firebird admin login. Treat the repo copy as one developer's box, not a template (class-level; specifics belong in the security ticket).
- **API user passwords are compared in plaintext** against `web_users.user_psw` (class-level).
- **Recent debugging writes payloads to disk.** Since October 2026, carrier calls dump the last request and response under `C:\temp` on the host (class-level).
- **The `Test*` projects aren't tests.** Each is a console app that sends one SOAP call to a configured endpoint. They have no assertions and no runner.

## Unknowns
- Whether every customer box runs the same CSS build, or versions drift per site. `CheckUpdates` and `VersionId` suggest a version check, but the release path is unknown.
- Which `LocalSwagger` copy each `Service References` client came from.
- Where the HTTP log sink (`Logging:HttpEndpoint`) points in prod, and whether anyone reads it.
