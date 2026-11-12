---
tags:
- waypoint
- selector2
title: selector2 — testing
verified: '2026-11-12'
verified_sha: unknown
verified_paths:
- apps/selector2-api/vitest.config.ts
- compose.yaml
- .github/workflows/ci.yaml
- apps/selector2-api/src/adapters/carriers/__tests__/support
- apps/selector2-api/src/http/soap/__tests__
- apps/selector2-api/src/http/controllers/__tests__/support
---
# selector2 — testing

The real strategy is not obvious from the file list: the tests prove contracts against recorded or spec-derived truth, and prove tenant isolation against a real Postgres. Vitest 3 in both apps. At `6442634` the PR evidence reports about 5,200 api tests (126 files) and 375 ui tests (snapshot 2026-11-12).

## Running it
From the repo root, through mise:
`mise x node@24.7.0 pnpm@10.34.7 -- pnpm run lint | build:check | build:check:tests | build | test`
Run `lint:fix`, both `build:check`s, `test` and `build` before every push; CI runs `lint`, `build:check`, `build:check:tests`, `test`, `build` in that order.

The api's tests run as two Vitest projects: `unit` (everything under `__tests__/` except integration files) and `integration` (`*.integration.test.ts`). Integration files run one at a time in a single fork, because they drop and recreate cluster-wide roles. They skip when `PGHOST` is unset, and CI sets it so they fail instead of skipping. Run them against the throwaway service, never the development database:

`docker compose up -d --wait postgres-test` (port 5433, no volume), then `PGHOST=localhost PGPORT=5433 PGUSER=postgres PGPASSWORD=postgres pnpm --filter @selector2/api test`.

## The layers and what each proves
- **Postgres-backed integration tests** lay the database out as Cloud SQL does (a migrator, an `app_rw` login, default privileges), run the real migrations and exercise repositories and use-cases with real SQL. Two tenants plus a god sit in one database, and tenant B's rows are checked byte for byte unchanged after tenant A acts (`tenant-isolation.integration.test.ts`). The REST v2 and admin integration tests also run every operation with two tenants.
- **Strict fake proxies.** `FakeProxy` is a local HTTP server that records each request and answers from a per-carrier fixture (`royalMailProxy`, `upsProxy`, `inPostProxy`, `vehoProxy` and so on). The fixtures copy carrier-playground's own request validation, in the proxy's check order, using a small JSON-schema checker that throws on a keyword it does not implement. A request the real proxy would refuse is refused by the fake. The real `CarrierHttpClient` and adapter run against it, with `drop`, `delayMs` and arbitrary statuses to force timeouts, dropped sockets, 429s and HTML 503s.
- **Shared adapter contract tests** (`support/adapter-contract-tests.ts`, `shared-carrier-tests.ts`): every adapter gets the same set for Cloud Run failures with no proxy code, no resend after an ambiguous create, and leak checks (a proxy that echoes the key and recipient into its error bodies must not reach `messages` or logs).
- **Golden SOAP replies.** `http/soap/__tests__/golden/` holds 46 request and reply XML files, compared byte for byte. They are the recorded real replies with every value replaced by a synthetic one. For the four operations nobody recorded (ProcessShipments, ValidateShipments, CommitShipGroup, CommitShipments) they are built from the C# source and the 2022 WSDL, so they prove the source reading rather than the real server.
- **Contract tests per spec.** Each OpenAPI document (`openapi/admin.yaml`, `rest-v1.yaml`, `rest-v2.yaml`) has a spec test, and response bodies of every documented status are validated against the spec's schemas with Ajv. A check fails when a route returns a status the spec omits, and the v2 check has its own test that it refuses a renamed field or a missing `ok`. REST v1 also has `rest-v1-proxy-contract.integration.test.ts`, a port of selector-rest-proxy's own smoke suite (26 of 26 pass; the original passes 20 of 28 against selector2, the 6 failures assert Selector sandbox data).
- **Done-when runs against real clients.** Parcel Portal's Selector client was copied unchanged into a scratch Go module and booked against a local selector2, with only endpoint and credentials changed. This lives in a PR body, not in the repo.
- **Mutation-style proofs.** Where a guard or filter is the point, the tests are written so that removing it fails them: tenant-scoped writes are tested directly with the other tenant's scope, and a test of key redaction checks a whole key, not a fragment. PR review rounds fixed tests that could not fail (cursor tests that could not see gaps, a fragment-only key check). There is no mutation-testing tool in the repo. **ASSESSED:** this is a practice, not a gate.
- **UI tests** are plain Vitest over the server hook, gate, session cache, attempt limiter and route load/actions through a route harness with fakes. They do not run a browser.

## Conventions
- Tests sit in `__tests__/` beside the code, one behaviour per test, with hand-written fakes over mocks. Shared setup is in `support/` next to the tests.
- Test names state the one behaviour checked.
- **Live end to end against the real mocks:** the ui's `/scenarios` page books one happy path per carrier and the mocks' failure values, and compares each with what it expects. Locally it needs the synthetic seed (Acme has a route for all twelve carriers); reset the database before re-seeding after the fixtures change, because the seed never rewrites a row. On dev no tenant has carrier contracts yet.
- Never put a real credential, customer or label in a fixture. Fixture keys are published mock keys (`rm-key-acme`, `seedacme01_...`).

## Gaps
- Nothing runs against the deployed dev services in CI, and the last PRs recorded no booking through the public mocks (no network in the build environment).
- No test covers the real 50,000-row CSV export; unit tests run at the default cap.
- The god sign-in on dev has never been checked, because nobody running the agents can read the password.
