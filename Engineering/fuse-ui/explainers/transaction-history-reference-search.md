---
tags: [waypoint, explainer, fuse-ui]
thesis: "Transaction History search sends one trimmed reference to collector for every record type in scope, through one server function, and shows only what collector matched. It fails closed when collector cannot have filtered."
confidence: high
updated: 2026-10-12
verified: 2026-10-12
verified_sha: 36e8575
verified_paths:
  - code/src/app/server-functions/customer/transaction-history.func.ts
  - code/src/modules/transaction-history/logic/transaction-history-search.logic.ts
  - code/src/modules/transaction-history/hooks/use-reference-search.ts
  - code/src/modules/transaction-history/components/transaction-history-view.tsx
  - code/src/modules/transaction-history/components/transaction-history-search-form.tsx
  - code/src/modules/transaction-history/components/transaction-history-search-status.tsx
  - code/src/modules/transaction-history/transaction-history.const.ts
  - code/src/modules/transaction-history/logic/transaction-history-rows.logic.ts
  - code/src/const/use-case.const.ts
  - code/src/app/customer/[customerId]/transaction-history/page.tsx
drifted_evidence: []
drift_checked: 2026-10-12
commits_behind: 0
---
# Transaction History reference search

```orient-bluf
{
  "v": 1,
  "bluf": "Transaction History search sends one trimmed reference to collector for every record type in scope, through one server function, and shows only what collector matched. It fails closed when collector cannot have filtered.",
  "confidence": "high",
  "action": "none"
}
```

## Mechanism

**CONFIRMED** One search box takes one exact-match value. The browser calls `searchTransactionChunks` once with every in-scope record type. The server function runs one collector GET per type in parallel. [1][2]

```orient-sequence
{
  "v": 1,
  "title": "One search",
  "actors": [
    { "id": "b", "label": "Browser", "sub": "view + useReferenceSearch" },
    { "id": "f", "label": "fuse-ui server function", "service": "fuse-ui" },
    { "id": "c", "label": "collector", "service": "collector" }
  ],
  "steps": [
    { "from": "b", "to": "f", "label": "targets + reference", "kind": "call", "ev": [1] },
    { "from": "f", "to": "f", "label": "validate targets, trim reference", "kind": "call", "ev": [2] },
    { "from": "f", "to": "c", "label": "GET records/{type}/{businessId}?reference= (per type)", "kind": "call", "ev": [1] },
    { "from": "c", "to": "f", "label": "page {total, data} per type", "kind": "return" },
    { "from": "f", "to": "f", "label": "records but no correlationId: search unavailable", "kind": "call", "tone": "alert", "ev": [2] },
    { "from": "f", "to": "b", "label": "rows and total, or an error, per type", "kind": "return" }
  ]
}
```

**CONFIRMED** Scope is the use-case filter, or all 13 collector-readable record types when the user selects none. The set includes Stock Sync, which sits outside the configurable use-case registry. [3][4][5]

**CONFIRMED** The server function validates before any collector call. Targets must be distinct known record types at whole-number offsets. The server function trims the reference, which must then hold 1 to 256 characters. Anything else fails every type with no call. [2]

**CONFIRMED** The search form applies the same trim and length rule first. It shows an inline error instead of submitting. [6]

**CONFIRMED** Failure of one type never touches another. The fan-out settles each type on its own and maps a thrown fetch to a per-type error. [2]

**CONFIRMED** The server function fails closed. A page with records where none carries a string `correlationId` becomes "Reference search is unavailable for this record type". The rows are never shown as matches. [2]

**CONFIRMED** `useReferenceSearch` caches results per search value and type. Changing scope fetches only the newly added types. Back to an earlier search refetches nothing. [7]

**CONFIRMED** Each type pages in chunks of 100 as the table runs out of rows. `retryFailed` re-runs only the failed types. Refresh re-runs every in-scope type from offset 0. [7][3]

**CONFIRMED** Each request carries a generation stamp. The hook drops a response that a newer request for the same value and type has overtaken. [7]

**CONFIRMED** `searchOutcome` picks exactly one of five page states. [2]

- **CONFIRMED** Loading: a type has not settled and no row is visible.
- **CONFIRMED** Every type failed, with no matches.
- **CONFIRMED** No records found. The page lists the types searched and offers **Search all use cases** when the user narrowed scope.
- **CONFIRMED** Matches exist but the filters hide all of them.
- **CONFIRMED** Results, with a count line noting hidden matches and types still searching.

**CONFIRMED** Per-type failures show in a banner next to whatever matched. The banner offers Retry. [8]

**CONFIRMED** The URL holds the applied search in `?search=`. Submit and clear push a history entry and drop `?record=`. Back and Forward re-read the URL. [4]

**CONFIRMED** The drawer finds a record across search rows and browse rows. It reports the record missing only once no search is pending. [4][9]

## Boundaries

**CONFIRMED** Collector owns matching. It decides which fields count per type, the index, the `#` rule and the 400 for a bad value. fuse-ui never filters rows by reference itself. [2]

**CONFIRMED** Collector matches the value against a type's reference fields and `metadata.correlationId`. It tries the value with and without a leading `#`. A 24-hex value also matches `_id`. Matching is exact. [10]

**CONFIRMED** Browse is a separate path. With no search, the page shows 13 server-seeded first pages of 100 and pages them client-side. [4][11]

**CONFIRMED** Search results replace browse rows while a search runs. Direction, range and status filters still apply to matches. [4][9]

**CONFIRMED** One business per search. The page binds `businessId` on the client, and the user never chooses it. [4]

**ASSESSED** The matching half lives in [[../../collector/explainers/reference-search|collector reference search]]. This page rests on collector's behaviour only through the sources above.

## Constraints

**CONFIRMED** The displayed Record ID chain per type is `refPaths` in the entity table. Collector's search fields for that type must include those paths. Change the two repos together. [5]

**CONFIRMED** The chain contract runs one way. Stock Sync displays `identifiers.runId`. Collector also indexes `identifiers.connectorId` for that type, so a connector ID finds runs that no Record ID shows. [5][10]

**ASSESSED** One server function serves all types because Next runs browser-invoked server functions through a router action queue. Per-type browser calls would run back to back. The code comment states the one-call design; the queue behaviour comes from the architecture doc.

**ASSESSED** The server function rejects a blank reference instead of dropping it, because openapi-fetch sends an empty string and drops only `undefined`. Mapping blank to "no param" would return the full list. [2]

**ASSESSED** The correlation-ID check exists because an older collector ignores `?reference=` and returns the unfiltered list. Absence of `correlationId` is then the only signal. [2]

**UNKNOWN** Whether every Stock Sync run record carries a top-level `correlationId`. A non-empty Stock Sync page with none reports "search unavailable". This pass did not confirm collector's response shape for that type.

**CONFIRMED** Correlation-ID search matches the latest ingest's ID only. Collector stores one `metadata.correlationId` per record, so an older log line's ID can find nothing. Search the order reference instead. [10]

## Evidence

```orient-evidence
{
  "v": 1,
  "items": [
    { "id": 1, "kind": "code", "ref": "code/src/app/server-functions/customer/transaction-history.func.ts@36e8575:L31-79", "note": "listRecords, searchRecords, searchTransactionChunks" },
    { "id": 2, "kind": "code", "ref": "code/src/modules/transaction-history/logic/transaction-history-search.logic.ts@36e8575", "note": "validation, fanOut, fail-closed toSearchChunk, searchOutcome" },
    { "id": 3, "kind": "code", "ref": "code/src/modules/transaction-history/transaction-history.const.ts@36e8575:L12", "note": "TRANSACTION_FETCH_COUNT = 100" },
    { "id": 4, "kind": "code", "ref": "code/src/modules/transaction-history/components/transaction-history-view.tsx@36e8575", "note": "scope, ?search= sync, selected record, browse versus search rows" },
    { "id": 5, "kind": "code", "ref": "code/src/modules/transaction-history/transaction-history.const.ts@36e8575:L55-185", "note": "refPaths per type, AVAILABLE_USE_CASES" },
    { "id": 6, "kind": "code", "ref": "code/src/modules/transaction-history/components/transaction-history-search-form.tsx@36e8575:L23-51", "note": "same trim rule before submit" },
    { "id": 7, "kind": "code", "ref": "code/src/modules/transaction-history/hooks/use-reference-search.ts@36e8575", "note": "cache per value and type, generations, retryFailed, refresh" },
    { "id": 8, "kind": "code", "ref": "code/src/modules/transaction-history/components/transaction-history-search-status.tsx@36e8575", "note": "failure banner and per-state copy" },
    { "id": 9, "kind": "code", "ref": "code/src/modules/transaction-history/logic/transaction-history-rows.logic.ts@36e8575", "note": "toVisibleRows, findSelected" },
    { "id": 10, "kind": "doc", "ref": "Engineering/collector/explainers/reference-search", "note": "collector origin/master 9c4d56d: core/reference-search.ts and use-case-registry.service.ts read directly" },
    { "id": 11, "kind": "code", "ref": "code/src/app/customer/[customerId]/transaction-history/page.tsx@36e8575:L35-80", "note": "13 first-page loaders, count 100" }
  ]
}
```

## Related

- [[architecture]] covers the server-function calling model and the `refPaths` guardrail.
- [[known-context]] holds search semantics and browse defects.
- [[../../collector/explainers/reference-search|collector reference search]] covers the matching side.
