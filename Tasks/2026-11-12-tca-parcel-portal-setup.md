---
tags: [adhoc-task]
date: 2026-11-12
tldr: "TCA test setup in the dev Parcel Portal still blocked on dev admin sign-in (creds file rejected on dev). Meanwhile shipped to main: browser-side SFTP key generation (#132, #133, #135), packaging unit-select fix (#134), API key UI hidden (#131). Prod held at D1 throughout"
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
- Open with Harry: which address he signed in at (dev or prod) for the creds in ~/parcel-portal-creds; weight-of-0 decision; customer self-serve for keys.
