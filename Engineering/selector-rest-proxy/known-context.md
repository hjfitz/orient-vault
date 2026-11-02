---
tags:
- waypoint
- selector-rest-proxy
verified: '2026-10-27'
---
# selector-rest-proxy — known context

This is interview truth (Harry, 2026-10-27) plus facts that source can't give you. Claims marked
`(snapshot …)` describe mutable state and age out.

## Intent and ownership

- **Harry owns and operates it.** He built it (Feb 2025 – Mar 2026). Carrier Integrations engineers
  ship changes into it on `CID-*` tickets (Daniel Grzenia, Chris Mulder, John Finney), but they don't own
  it. Escalations come to Harry.
- **It is due for retirement.** The plan is a **Fuse adapter that calls Selector directly**. Tenants move
  onto Fuse, and this repo is then decommissioned. No ticket or epic exists yet (snapshot 2026-10-27: no
  FUSE issue matches "selector"). Until that exists, nothing here should grow beyond what tenants need.
  The shape of the Selector contract (operations, status mapping, print-spec defaults,
  `ResponseDetails` semantics) is what the Fuse adapter will have to reproduce, so this repo is the
  reference for it.
- **Tenant onboarding is ApiKy-only.** Create an ApiKy token whose profile carries `upstream` (the
  tenant's `…/ClientServer/ClientShipService.asmx?wsdl`), `username` and `password`. No deploy is needed.
  The ApiKy profile is the only record of who the tenants are.
- **"Stepping stone"** (the repo's own description) means a REST interface in front of SOAP Selector,
  so that customer WMSes and iPaaS tools don't have to speak SOAP.

## Tenants and traffic (snapshot 2026-10-27, Datadog, 2026-10-12 to 27)

- There are two live tenants, both on their own Selector instance:
  - **YUSENCASIO** (`yusencasio.gfsdeliver.com`): about 200–700 authenticated calls a day.
  - **SMEGUK** (`smegukltd.gfsdeliver.com`): about 40–360 a day.
- That is about 7.3k authenticated calls in 15 days. No meaningful traffic uses the static `BASICAUTH_KEY` or reaches the sandbox.
- The `container-id` header echo (CID-111) exists for Yusen's Manhattan integration.
- Errors over the same window:
  - about 7.3k 404s from scanners hitting the public LB
  - 221 `Unknown operation` 500s on `GET /` and `/liveness`
  - 75 tenant 400s, mostly Selector business rules such as "Chosen date of despatch is earlier than today"
  - 71 `ProcessShipments failed`
  - 45 401s
- Datadog log retention here is about 15 days. Anything older is gone.

## History that explains the code

- **CID-308 EU commodity validation** (2026-10-06). It requires SKU, ManufacturerProductID and
  StandardisedProductID for EU destinations, framed in code as a CSS requirement. It was **disabled on
  2026-10-15** with an early `return []` and `TEMPORARY` comments on the tests. Nobody interviewed knows why,
  or what re-enables it. Daniel Grzenia made both changes.
- **The custom upstream per tenant** (PR #8, March 2026) is what made it multi-tenant. Before that,
  every call went to the env-configured Selector.
- **The sandbox URL moved** from `justshoutgfs` to `gfsdeliver` (PR #9, 2026-07). The
  `.env.production` sandbox fallback dates from then.
- PR #10 is titled "BJS REST API … ExpLicense", but it changed this repo's spec: `E_MAIL` casing, and
  `ExpLicense` is no longer required. Expect CID ticket titles to name the wrong API now and then.

## Fragility and surprises

- **Deploys are ungated by design (known, accepted).** A master merge goes straight to prod with
  auto-approve. The `terraform-destroy-prod` job then sits waiting on every run, for weeks, and shows up
  as a pending deployment review in email. Don't approve it. Harry accepts this; it isn't a TODO.
- **Prod only.** There's no dev environment to try a change in. The PR smoke tests are the nearest
  thing: they run against the real Selector **sandbox** over the network, so a sandbox outage turns PR
  CI red.
- **The WSDL is fetched on every request.** The retry and 2 s timeout cover only that fetch. A slow
  Selector SOAP call is bounded only by the LB's 30 s.
- **A profile with no `upstream`** sends a real tenant's credentials to the sandbox WSDL, with only a
  warn log. A misconfigured ApiKy profile looks like the tenant getting sandbox results.
- **PII lands in logs.** The access log records full request and response bodies, and failed SOAP calls
  log the raw XML.
- **The public LB attracts scanners.** 404 noise dominates error counts, so any error-rate monitor
  needs to exclude 404s. No monitor exists today.
- **Live domain.** `rest-preview.selector.freightops.dev` is the real production domain despite
  "preview". Its DNS is a central core-infra record that the DNS migration deliberately kept.
- **Labels and ownership.** The Terraform labels say `contact = harry-fitzgerald` and
  `team = carrier-integrations-and-hybrid-services`. The repo has no `system:` in Waypoint because no
  system exists for the `gfs-hybrid-services` org.

## Repo conventions

- Biome for lint and format (`pnpm run lint:fix`). A husky pre-commit hook runs lint and unit tests.
- Tests are Vitest **`.js` spec files** next to TS source (`src/**/__test__/*.spec.js`), with
  fixtures under `__fixtures__`. Smoke tests are in `__test__/smoke`.
- The default branch is `master`, PRs are squash-free merge commits, and CID branches are named after
  the ticket summary.

## Unknowns

- Why was EU commodity validation (CID-308) disabled on 2026-10-15, and what has to happen before it's
  re-enabled? (Daniel Grzenia would know.)
- When will the Fuse Selector adapter be ticketed, and will tenants keep their REST contract (a
  compatibility shim) or move to Fuse's canonical API?
- Who creates and rotates the ApiKy tokens and profiles for tenants, and where are the Selector
  credentials in those profiles sourced from?
- Is there any tenant beyond YUSENCASIO and SMEGUK that calls less often than once in 15 days? Log
  retention can't show it. The ApiKy profile list would.
- Does the CommitShipGroup 207-vs-400 comparison (error groups vs consignments) behave as tenants
  expect? It is unverified against a real failure.
