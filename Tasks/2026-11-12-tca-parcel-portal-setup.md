---
tags: [adhoc-task]
date: 2026-11-12
tldr: "TCA is set up and validating on dev (version-test); Oliver reports a live test print worked on 13 Nov. Shipped #131-#136 (API key UI hidden, browser SFTP keygen, packaging units, customs rounding). 13 Nov: Phil, Pete, Chris and Oliver's feedback broken into 17 requirements and a new programme, Native Dispatch (the portal's new name). Weight 0 and TCA's templates approved, not started. Prod held at D1"
session_id: 3daf16d6-87bb-438d-944f-828764dcae71
status: open
---
# Set up TCA in the dev Parcel Portal and test it

## Outcome
A TCA customer very probably exists already in dev (tenant 012cf127, set to Selector on version-test since 10 Nov); the debug MCP has no tenant create/list tool. Four sample order CSVs and a README are in the session scratchpad `tca-samples/` (portal dc-layout, headers match the repo's own TCA sample), not uploaded.
Owed: restore `~/parcel-portal-dev-admin.txt` (every parcel-debug call fails without it), then list tenants, set the six services, shipping methods and packing templates. Oliver (11:00 GMT): OK to test against https://tca.gfsdeliver.com/ClientServer/ClientShipService.asmx; confirm in the DM once we have so he can review on the server; no Commit calls. Still open with him: does TCA need DDP on FIP (portal hardcodes DDU), and which countries. The debug MCP guard only allows version-test and sandbox, so reaching tca from the portal needs the guard widened (Harry's call) or the endpoint typed into the UI by a human. Nothing sent to tca yet; no Commit, manifest or dispatch calls. A 15-minute DM watch cron runs in the session (expires after 7 days).
Admin sign-in: the password in ~/parcel-portal-creds is rejected for admin@parcel-portal.invalid (wrong_password for an existing user); Harry's account cannot read the bootstrap secret in Secret Manager. Owed: which account that password belongs to.

## SFTP key generation (design only, nothing built)
Draft design in the session scratchpad `sftp-keygen-design.md`: keep BYOK (already exists, admin-only), add browser-side RSA 4096 PKCS#1 PEM generation so svc never sees the private key; migration 019 `source` column, OpenAPI 5.13.0, new `packages/ssh-keygen`, 3 PRs (self-serve a 4th). Reverses the 2026-11-03 "never generate or hold private keys" decision, so it needs Harry's yes and a Migration State entry. Dev only; prod held at D1.

## Shipped this session
- ilg-merak/parcel-portal#131 (36266dc, merged 13:19 UTC): hides the API key section of the customer admin UI (Access card + Overview step); svc API, keys and Swagger unchanged. review-panel (inline, 78 lines): looks good. Evidence is a local run with before/after screenshots; the shared dev portal wasn't used (no admin sign-in). The ui deploy run was still pushing to dev; no prod gate approved (programme holds prod at D1). Decision logged in Migration State; ledger entry written.
- CSV export vs DispatchCloud: layout already matches (17 identical columns); no code change. Waiting on Oliver's FedEx sample rows and Harry's "which difference?".
- ilg-merak/parcel-portal#132 (f9a1d46) packages/ssh-keygen; #133 (10e2963) svc key `source`, audit, redactor; #134 (c170632) packaging preset unit fields (real bug: toolkit select name not submitted); #135 (8dabeb2) Access-tab key generation. Each reviewed with review-panel, fixes verified, CI green before merge; ledger entries written; no prod gate approved. #132 needed a squash and force-push of my own branch to clear a gitleaks false positive (PEM header literals in a test), no allowlist.
- Findings handed to Harry, not built: weight 0 is rejected by svc (TCA's five templates are 0.000); failed saves show the raw OpenAPI error text; dev smoke test (`smoke-test@parcel-portal.invalid`) has failed on every deploy since at least 6 Nov and needs the dev admin to re-provision; toolkit `GSelectField` doesn't submit its name (ilg-platform).
- Open with Oliver: US call (his 15:05 question to Harry), printer models and Yusen IT driver-swap policy, whether ConsNumber is the consignment or tracking number, whole-cm rounding of dimensions, FedEx export rows, DDP on FIP. Cron DM watcher cancelled at Harry's request.
- Open with Harry: weight-of-0 decision (blocks TCA's five 0.000-weight packing templates); customer self-serve for keys; go-ahead to point TCA at tca.gfsdeliver.com (a human must enter the endpoint in the customer's settings; the debug MCP only allows version-test); the QZ Tray yes/no below.

## Later in the session (after Harry supplied working dev admin creds)
- Dev sign-in solved: Harry gave the dev admin password; written to ~/parcel-portal-dev-admin.txt (mode 600). The ~/parcel-portal-creds password is rejected by dev (probably another environment's).
- Created dev customer "TCA" (id c87d3c0e-b162-49c9-9741-f8f7711c33bd, slug tca-n4g7); Beachhead Demo, GFS, Smoke Test Customer untouched; soft-deleted "TCA Demo" not restored. Configured on version-test with TCA-TEST (shipperId 1, packageCode YOUR, PDF labels, testCarrier false), six FedEx services and shipping methods named as TCA's files send them. Account check: accepted.
- The four sample CSVs imported (13 ready, 4 invalid at import, as predicted). Check with carrier (validation only): all six services and both multi-pack orders accept; no phone and 200 lb rejected; ZIP/state mismatch and a PO box on Home Delivery are accepted by the mock; FIP was rejected with "missing Wrong customs amount".
- Root cause: a portal bug, customs value sent as 2.8499999999999996 (unrounded float). Fixed in #136 (621357e, customs value to cents, total weight to grams); verified on dev after deploy: the FIP order now validates. Ledger written.
- QZ Tray per-bench option designed (not built): design says unsigned QZ prompts on every print (confirmed in QZ's GatewayDialog.java: Allow is disabled when Remember is ticked on an unverified request), so silent printing needs signing (cert about $749/yr or own root, plus a svc signing route and a Secret Manager key). Waiting on Harry's yes/no for three unsigned dev-only PRs (transport field, label-print adapter, UI) and the LGPL qz-tray dependency.
- WebUSB on Windows: not solved; recommendation is Zadig on the benches for TCA, or the browser dialog for the trial; Oliver has not answered the printer-model and Yusen IT questions.
- Dev smoke test still red on every deploy (its smoke-test@ account is refused by dev); now fixable since we have the dev admin.
