---
tags: [waypoint, explainer, fuse-ui]
thesis: "fuse-ui reads runtime flags from config-service once per request, within 1 s, and falls back to the code default. Admins change flags on an audited admin-only page, and every preview shares dev's flags."
confidence: high
updated: 2026-10-19
verified: 2026-10-19
verified_sha: dd6eec7
verified_paths:
  - code/src/lib/feature-flags/is-feature-enabled.ts
  - code/src/observability/events/feature-flag-event.type.ts
  - code/src/lib/api-client/api-client.ts
  - code/src/app/server-functions/feature-flags/assert-admin.ts
  - code/src/app/server-functions/feature-flags/feature-flags.func.ts
  - code/src/app/server-functions/feature-flags/feature-flags.action.ts
  - code/src/app/server-functions/audit/audit-config-change.func.ts
  - code/src/app/user-management/feature-flags/page.tsx
  - code/src/modules/user/components/user-management-sidebar.tsx
  - code/src/proxy.ts
  - code/src/modules/feature-flags/feature-flags.const.ts
  - code/src/modules/feature-flags/components/feature-flags-view.tsx
  - code/src/modules/feature-flags/components/feature-flag-drawer.tsx
  - code/src/modules/feature-flags/components/feature-flag-form.tsx
  - code/src/modules/feature-flags/components/flag-status-control.tsx
  - code/src/modules/feature-flags/components/scheduled-change-control.tsx
  - code/src/modules/feature-flags/components/schedule-change-form.tsx
  - code/src/modules/feature-flags/components/apply-flag-update.ts
  - code/src/modules/feature-flags/logic/feature-flag-history.logic.ts
  - code/src/modules/feature-flags/logic/feature-flag-list.logic.ts
  - code/src/modules/feature-flags/logic/uk-time.logic.ts
  - code/src/lib/audit/audit-writer.ts
  - code/src/lib/audit/audit-reader.ts
  - code/src/lib/gen/config-service.client.d.ts
  - "code/src/app/customer/[customerId]/storefront/[storefrontId]/connector/[connectorId]/[useCase]/page.tsx"
  - "code/src/app/templates/[collectionId]/[useCase]/page.tsx"
  - code/src/config.ts
  - iac/env/dev.tfvars
  - iac/env/prod.tfvars
  - iac/env/feature-branch.tfvars
  - iac/projects/fuse-ui/variables.tf
drifted_evidence: []
drift_checked: 2026-10-19
commits_behind: 0
---
# Runtime feature flags

```orient-bluf
{
  "v": 1,
  "bluf": "fuse-ui reads runtime flags from config-service once per request, within 1 s, and falls back to the code default. Admins change flags on an audited admin-only page, and every preview shares dev's flags.",
  "confidence": "high",
  "action": "none"
}
```

## Mechanism

```orient-flow
{
  "v": 1,
  "title": "Runtime feature flags in fuse-ui",
  "nodes": [
    { "id": "page", "label": "Feature Flags page", "sub": "/user-management/feature-flags", "service": "fuse-ui", "ev": [7, 9] },
    { "id": "act", "label": "Flag server functions", "sub": "assertAdmin on every call", "service": "fuse-ui", "ev": [4, 13, 33] },
    { "id": "cfg", "label": "config-service", "sub": "/api/v1/feature-flags", "kind": "service", "service": "config-service", "tone": "accent", "ev": [29] },
    { "id": "topic", "label": "Audit topic", "sub": "feature_flag/<key>", "kind": "topic", "ev": [18, 19] },
    { "id": "aud", "label": "audit-service", "kind": "service", "service": "audit-service", "ev": [20] },
    { "id": "ed", "label": "Mapping editors", "sub": "connector and template", "service": "fuse-ui", "ev": [21, 22] },
    { "id": "read", "label": "isFeatureEnabled", "sub": "per request, 1 s race", "service": "fuse-ui", "ev": [1] },
    { "id": "def", "label": "Code default", "sub": "env value", "ev": [1, 23] }
  ],
  "edges": [
    { "from": "page", "to": "act", "label": "create, switch, schedule, edit, delete" },
    { "from": "act", "to": "cfg", "label": "write with expectedVersion" },
    { "from": "act", "to": "topic", "label": "before and after, read via GET" },
    { "from": "topic", "to": "aud" },
    { "from": "aud", "to": "page", "label": "History, latest 200 rows" },
    { "from": "ed", "to": "read", "label": "fuse-ui.mapping-dictionaries" },
    { "from": "read", "to": "cfg", "label": "GET whole list" },
    { "from": "read", "to": "def", "label": "unavailable, unknown or invalid", "style": "dashed" }
  ]
}
```

### Reading a flag

- **CONFIRMED** `isFeatureEnabled(key, default)` is server-only. Each caller passes the key and its own code default. [1]
- **CONFIRMED** React `cache()` memoises one GET of the whole flag list per request. Nothing caches across requests. [1]
- **CONFIRMED** A 1 s timer races that fetch. When the timer wins, the reader treats config-service as unavailable. [1]
- **ASSESSED** The race uses a timer, not an AbortSignal. `configServiceClient` retries a thrown fetch three times with jitter, so an abort would not bound the wait. [2]
- **CONFIRMED** The reader parses each flag with `FeatureFlagSchema`. A flag that fails logs `InvalidFlagSkipped` and drops out of the list. [1][3]
- **CONFIRMED** It evaluates with `evaluateFeatureFlag(flag, new Date())` from `@gfs-bifrost/types`. A due scheduled change applies on read, and nothing writes it back. [1][28]
- **CONFIRMED** Two outcomes return the default and log `FellBackToDefault`. The reason is `unavailable` for a failed or slow list, or `unknown_key` for a missing or skipped flag. [1][3]

### Managing flags

- **CONFIRMED** The user-management sidebar links the page under Platform. `proxy.ts` and the page both send non-admins to `/`. [5][6][7]
- **CONFIRMED** Every flag server function calls `assertAdmin` first. A server action is callable from any page, so the page check is not enough. [4][13][33]
- **CONFIRMED** The page loads all flags and the latest 200 `feature_flag` audit rows in parallel. [7][8]
- **CONFIRMED** A drawer holds Status, Scheduled change and History for one flag. A dialog form creates a flag or edits its details. [9][12]
- **CONFIRMED** Switch, schedule, cancel and edit send the flag's `version` as `expectedVersion`. config-service answers 409 when the flag has moved on. [10][11][34][12][24]
- **CONFIRMED** Each action revalidates the page before it checks the result. After a 409 the drawer re-renders on the latest version, and a toast asks for a retry. [13][14][15]
- **CONFIRMED** Schedule and "Remove by" inputs take UK wall-clock time and convert it to a UTC instant. The page shows every time in `Europe/London`. [11][12][16]
- **CONFIRMED** "Remove by" (`expiresAt`) is a cleanup reminder. Nothing acts on that date; the list only marks the flag expired. [12][35]

### Audit and history

- **CONFIRMED** A successful create, update or delete writes one row: target `feature_flag`, id the flag key. [13]
- **CONFIRMED** Snapshots come from config-service via GET. Update and delete read `before` first, and create and update read `after` back. [13][18]
- **CONFIRMED** An error from config-service skips the audit call, so a refused write leaves no row. [13]
- **CONFIRMED** Rows leave through `writeSessionAuditLog` to the audit topic. The History section reads them back through audit-service. [19][20][7]
- **CONFIRMED** The drawer filters the 200 rows by key. It names each change from the before and after snapshots. [15][17]

### First reader

- **CONFIRMED** `fuse-ui.mapping-dictionaries` gates the Dictionaries tab in both mapping editors: connector mappings and templates. [21][22]
- **CONFIRMED** Its default is `config.featureFlags.mappingDictionaries`, from `FEATURE_FLAG_MAPPING_DICTIONARIES`. That env value reads false unless it says `true`. [23]
- **CONFIRMED** Both `dev.tfvars` and `prod.tfvars` set the env value to `true`. [25][26]
- **CONFIRMED** Dev config-service holds the flag, switched on. Prod holds no flags, so prod falls back to `true` and logs `unknown_key` per editor load (snapshot 2026-10-19). [30][31]

## Boundaries

- **CONFIRMED** Flags live in config-service, never in fuse-ui's Mongo. fuse-ui reads and writes them over HTTP only. [1][13][29]
- **CONFIRMED** config-service serves each flag with any due scheduled change already folded in. The page and the reader see the same state. [29]
- **CONFIRMED** The page lists every flag in config-service, other services' keys included. Dev also holds a `shopify-connector.*` flag. [7][30]
- **CONFIRMED** fuse-ui subscribes to no flag revision topic. A change reaches it on the next request. [32]
- **CONFIRMED** Other `FEATURE_FLAG_*` env values, such as EDI egress and the order tracker, stay deploy-time switches. [23]
- **CONFIRMED** Previews read dev config-service: `feature-branch.tfvars` adds only `is_preview_env` on top of `dev.tfvars`. A flag change made in a preview changes dev and every preview. [25][27]
- **CONFIRMED** Previews have no audit topic and no audit-service URL. A flag write there records no row, and History stays empty. [36][19][20]
- **CONFIRMED** There is no per-customer targeting. The status control always shows "Who gets it: Everyone", and no form sends `targets`. [10][11][12]

## Constraints

- **CONFIRMED** A slow or failed config-service never breaks a page. It costs at most 1 s per request, then the default applies. [1]
- **CONFIRMED** Pick the code default as the safe value, since every failure path returns it. Deleting a flag sends every reader back to its default. [1][9]
- **CONFIRMED** fuse-ui evaluates with no context. A flag carrying non-null `targets`, set outside this page, reads false here. [1][28]
- **CONFIRMED** Create and delete send no `expectedVersion`. A delete removes the flag even if someone changed it since the drawer opened. [12][13]
- **CONFIRMED** A scheduled change that takes effect writes no audit row. History shows when someone scheduled it, not when it fired. [1][13]
- **CONFIRMED** History covers the latest 200 flag rows across all keys. An older change can drop out of the drawer; the Audit Log link reaches the rest. [8][9][15]
- **ASSESSED** The losing fetch keeps running after the 1 s timeout, retries included. No code aborts it or reads its result. [1][2]

## Evidence

```orient-evidence
{
  "v": 1,
  "items": [
    { "id": 1, "kind": "code", "ref": "code/src/lib/feature-flags/is-feature-enabled.ts@dd6eec7", "note": "cache(), 1 s race, schema parse, evaluateFeatureFlag, fallbacks" },
    { "id": 2, "kind": "code", "ref": "code/src/lib/api-client/api-client.ts@dd6eec7:L149-164", "note": "retry: three jittered retries on a thrown fetch" },
    { "id": 3, "kind": "code", "ref": "code/src/observability/events/feature-flag-event.type.ts@dd6eec7", "note": "FellBackToDefault reasons, InvalidFlagSkipped" },
    { "id": 4, "kind": "code", "ref": "code/src/app/server-functions/feature-flags/assert-admin.ts@dd6eec7", "note": "session role must be admin" },
    { "id": 5, "kind": "code", "ref": "code/src/modules/user/components/user-management-sidebar.tsx@dd6eec7:L41-54", "note": "Platform > Feature Flags link" },
    { "id": 6, "kind": "code", "ref": "code/src/proxy.ts@dd6eec7:L49-55", "note": "/user-management redirects non-admins" },
    { "id": 7, "kind": "code", "ref": "code/src/app/user-management/feature-flags/page.tsx@dd6eec7", "note": "admin check, parallel flag list and audit history load" },
    { "id": 8, "kind": "code", "ref": "code/src/modules/feature-flags/feature-flags.const.ts@dd6eec7", "note": "HISTORY_LIMIT 200, Everyone labels" },
    { "id": 9, "kind": "code", "ref": "code/src/modules/feature-flags/components/feature-flag-drawer.tsx@dd6eec7", "note": "drawer sections, delete copy, Audit Log link" },
    { "id": 10, "kind": "code", "ref": "code/src/modules/feature-flags/components/flag-status-control.tsx@dd6eec7", "note": "switch sends expectedVersion; Who gets it: Everyone" },
    { "id": 11, "kind": "code", "ref": "code/src/modules/feature-flags/components/schedule-change-form.tsx@dd6eec7", "note": "UK date and time to ISO, expectedVersion" },
    { "id": 12, "kind": "code", "ref": "code/src/modules/feature-flags/components/feature-flag-form.tsx@dd6eec7", "note": "create without expectedVersion, edit with it, Remove by hint" },
    { "id": 13, "kind": "code", "ref": "code/src/app/server-functions/feature-flags/feature-flags.action.ts@dd6eec7", "note": "writes, revalidatePath, audit only on success, GET read-backs" },
    { "id": 14, "kind": "code", "ref": "code/src/modules/feature-flags/components/apply-flag-update.ts@dd6eec7", "note": "409 conflict toast" },
    { "id": 15, "kind": "code", "ref": "code/src/modules/feature-flags/components/feature-flags-view.tsx@dd6eec7:L49-50", "note": "drawer flag and history found by key" },
    { "id": 16, "kind": "code", "ref": "code/src/modules/feature-flags/logic/uk-time.logic.ts@dd6eec7", "note": "Europe/London conversion and formats" },
    { "id": 17, "kind": "code", "ref": "code/src/modules/feature-flags/logic/feature-flag-history.logic.ts@dd6eec7", "note": "describeFlagChange from before and after" },
    { "id": 18, "kind": "code", "ref": "code/src/app/server-functions/audit/audit-config-change.func.ts@dd6eec7", "note": "before, after, changedPaths" },
    { "id": 19, "kind": "code", "ref": "code/src/lib/audit/audit-writer.ts@dd6eec7:L32-85", "note": "no topic, no row; publish to audit topic" },
    { "id": 20, "kind": "code", "ref": "code/src/lib/audit/audit-reader.ts@dd6eec7:L16-28", "note": "no audit-service URL, empty log" },
    { "id": 21, "kind": "code", "ref": "code/src/app/customer/[customerId]/storefront/[storefrontId]/connector/[connectorId]/[useCase]/page.tsx@dd6eec7:L40-45", "note": "connector mapping editor reads the flag" },
    { "id": 22, "kind": "code", "ref": "code/src/app/templates/[collectionId]/[useCase]/page.tsx@dd6eec7:L58-63", "note": "template mapping editor reads the flag" },
    { "id": 23, "kind": "code", "ref": "code/src/config.ts@dd6eec7:L103-113", "note": "FEATURE_FLAG_* env values" },
    { "id": 24, "kind": "code", "ref": "code/src/lib/gen/config-service.client.d.ts@dd6eec7:L3437-3450", "note": "expectedVersion: 409 unless the flag is at this version" },
    { "id": 25, "kind": "code", "ref": "iac/env/dev.tfvars@dd6eec7", "note": "dev config-service URI; mapping dictionaries env true" },
    { "id": 26, "kind": "code", "ref": "iac/env/prod.tfvars@dd6eec7", "note": "mapping dictionaries env true" },
    { "id": 27, "kind": "code", "ref": "iac/env/feature-branch.tfvars@dd6eec7", "note": "previews override only is_preview_env" },
    { "id": 28, "kind": "url", "ref": "https://github.com/gfs-bifrost/pkg-node/blob/63d441b/pkg/types/src/config/utilities/feature-flag-state.ts", "note": "resolveFeatureFlag, evaluateFeatureFlag; no context means targeted flags read false" },
    { "id": 29, "kind": "url", "ref": "https://github.com/gfs-bifrost/config-service/blob/de3e3c0/code/src/core/feature-flags/feature-flags.service.ts", "note": "list and get return resolved flags" },
    { "id": 30, "kind": "log", "ref": "GET /api/v1/feature-flags on dev config-service, 2026-10-19: fuse-ui.mapping-dictionaries enabled v3, shopify-connector.api-cache-per-connector disabled v4" },
    { "id": 31, "kind": "log", "ref": "GET /api/v1/feature-flags on prod config-service, 2026-10-19: {\"flags\": []}" },
    { "id": 32, "kind": "log", "ref": "git grep -i 'feature_flag_revision|remote-config' origin/main -- code/src code/package.json iac at dd6eec7: no match" },
    { "id": 33, "kind": "code", "ref": "code/src/app/server-functions/feature-flags/feature-flags.func.ts@dd6eec7", "note": "list and get, both assertAdmin" },
    { "id": 34, "kind": "code", "ref": "code/src/modules/feature-flags/components/scheduled-change-control.tsx@dd6eec7", "note": "cancel sends scheduledChange null with expectedVersion" },
    { "id": 35, "kind": "code", "ref": "code/src/modules/feature-flags/logic/feature-flag-list.logic.ts@dd6eec7:L49-51", "note": "isExpired" },
    { "id": 36, "kind": "code", "ref": "iac/projects/fuse-ui/variables.tf@dd6eec7:L4-6", "note": "previews get empty audit topic and audit-service URL" }
  ]
}
```

## Related

- [[../architecture#Feature flags]]: the short summary this page expands.
- [[../architecture#Audit trail]]: the audit writer and reader the flag page relies on.
- [[../operations]]: preview environments and the throwaway-key smoke test.
- [[mapping-template-library]]: the template editor, which shares the Dictionaries tab gate.
- [[../plans/runtime-feature-flags-audited-flag-page]]: the plan that built the page.
- [[../../audit-service/explainers/audit-event-flow]]: where the audit rows go next.
