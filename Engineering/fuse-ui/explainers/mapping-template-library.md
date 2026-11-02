---
tags: [waypoint, explainer, fuse-ui]
thesis: "A template stores a MappingConfig verbatim plus a default-marks sidecar in fuse-ui's own Mongo. It is edited in the connector mapping editor and copied, never read, when applied or captured."
confidence: high
updated: 2026-10-19
verified: 2026-10-19
verified_sha: 6f0d67f
verified_paths:
  - code/src/lib/db/template-collections.types.ts
  - code/src/lib/db/template-collections.collection.ts
  - code/src/app/server-functions/templates/templates.func.ts
  - code/src/app/server-functions/templates/templates.action.ts
  - code/src/modules/translator-config-editor/components/translator-config-editor.tsx
  - code/src/modules/translator-config-editor/logic/mapping-config-validity.logic.ts
  - code/src/modules/translator-config-editor/logic/mapping-config.logic.ts
  - code/src/modules/translator-config-editor/logic/required-field-coverage.logic.ts
  - code/src/modules/translator-config-editor/components/simple-required-field-coverage.tsx
  - code/src/modules/translator-config-editor/components/grouped-required-field-coverage.tsx
  - code/src/modules/translator-config-editor/components/simple-translator-defaults.tsx
  - code/src/modules/translator-config-editor/stores/grouped-config-editor/grouped-config-editor-store.ts
  - code/src/modules/translator-config-editor/stores/simple-config-editor/simple-config-editor-store.ts
  - code/src/modules/template-library/logic/template-apply.logic.ts
  - code/src/modules/template-library/logic/default-marks.logic.ts
  - code/src/modules/template-library/logic/ilg-standard-import.logic.ts
  - code/src/modules/template-library/schema/template-collection.schema.ts
  - code/src/modules/template-library/components/template-mapping-editor.tsx
  - code/src/modules/customer-storefront/components/connector-mapping-editor.tsx
  - code/src/modules/customer-storefront/components/add-use-case-modal.tsx
  - code/src/instrumentation.ts
  - code/src/proxy.ts
drifted_evidence: []
drift_checked: 2026-10-19
commits_behind: 0
---
# Mapping Template Library

```orient-bluf
{
  "v": 1,
  "bluf": "A template stores a MappingConfig verbatim plus a default-marks sidecar in fuse-ui's own Mongo. It is edited in the connector mapping editor and copied, never read, when applied or captured.",
  "confidence": "high",
  "action": "none"
}
```

## Mechanism

### Storage

- **CONFIRMED** The `template_collections` collection holds one document per collection. Fields: `name`, `description`, `connectorType`, audit stamps and `templates`. [1][2]
- **CONFIRMED** `templates` is `Partial<Record<UseCase, UseCaseTemplate>>`. Each key is optional, never required-but-nullable, so a new use case cannot invalidate stored documents. [1]
- **CONFIRMED** A `UseCaseTemplate` is `{config, defaultMarks, updated}`. The config is a `MappingConfig`, stored without transformation. [1]
- **CONFIRMED** `DefaultMarks` mirrors the shape of `config.defaults`, keyed by default key. Each value is `preset` or `to_be_advised`. Lined configs split it into `header` and `lines`. [1]
- **CONFIRMED** The marks live beside the config, never inside it. The config still validates against the published mapping schemas. [1][5]
- **CONFIRMED** `template-collections.types.ts` carries pure types and the marks vocabulary. The `.collection.ts` file imports the Mongo connection, so client code imports only the types file. [1][2]
- **CONFIRMED** Two indexes exist, on `connectorType` and `lastUpdated`. Neither is unique. [2]

### Reads and writes

- **CONFIRMED** Only `templates.func.ts` (reads), `templates.action.ts` (writes) and `instrumentation.ts` touch the collection module. [2][3][4][15]
- **CONFIRMED** `instrumentation.ts` creates the indexes once at boot. [15]
- **CONFIRMED** Template reads call no `getSession`. `proxy.ts` resolves the session for every non-auth route. [3][16]
- **CONFIRMED** Every template write calls `getSession` first. It returns "Not authenticated" when no email is present. [4]
- **CONFIRMED** Writes emit audit events against two targets. `template_collection` uses the collection id. `template` uses `${collectionId}:${useCase}`, since a template has no id of its own. [4]
- **CONFIRMED** The write path covers collection create, rename and delete, plus per-use-case template save, delete and `setDefaultMarks`. [4]

### Saving a template

- **CONFIRMED** `persistTemplate` is the single write gate. It runs `validateMappingConfig` against the collection's connector type. [4][6]
- **CONFIRMED** The gate then requires `marksAreComplete`. Every default needs a mark, and no mark may describe a missing default. [4][8]
- **CONFIRMED** `saveUseCaseTemplate` reconciles marks from the saved config. It keeps existing marks and defaults new defaults to `preset`. [4][8]
- **CONFIRMED** `validateMappingConfig` checks the config type against `resolveMappingConfigType`, then the published Zod schema. [6][7]
- **CONFIRMED** It treats a required key as handled when a rule targets it or a default supplies it, on every flow. It calls `computeCoverage` with `defaultsSatisfy` set. A to-be-advised default counts. [6][21]

### Editing reuses the connector editor

- **CONFIRMED** `TranslatorConfigEditor` takes no connector or customer identity. It takes injected `save`, `remove` and `onRemoved` callbacks plus a `saveSlotId`. [9]
- **CONFIRMED** The template page passes `saveUseCaseTemplate` and `deleteUseCaseTemplate`. The connector page passes `updateConnectorMapping` and `deleteConnectorMapping`. [10][11]
- **CONFIRMED** The two pages portal their Save and Delete actions into different slots: `TemplateHeaderSaveSlot` and `StorefrontHeaderSaveSlot`. [10][11]
- **CONFIRMED** A per-store `calculateIsValid` gates the Save button. It derives `isValid` from `computeCoverage`, and the store seeds it on load and on each prop sync. [12][13][21]
- **CONFIRMED** A default counts as handling a required key on every inbound flow, on the template page and the connector page alike. [21]
- **CONFIRMED** The `defaultsSatisfyRequiredKeys` flag matters only on outbound flows. The template page sets it so a template can defer a value. The connector page leaves it off, so a customer's outbound mapping needs a rule. [21][9][10]
- **ASSESSED** A default on an outbound file emits no column unless a rule reads it. That is why a customer's outbound mapping stays rules-only. [21]
- **CONFIRMED** The Dictionaries tab and `lookup()` appear when `dictionariesEnabled` is true. Both pages pass the feature flag through. [9][10][11]
- **ASSESSED** A template carries dictionaries when its config does. The store keeps the config whole, and `applyTemplate` spreads it. [14]

### The coverage panel

- **CONFIRMED** A panel under the tab pills, on every tab, shows what needs attention. `SimpleRequiredFieldCoverage` and `GroupedRequiredFieldCoverage` build its rows from `computeCoverage`. [21][22]
- **CONFIRMED** A gap is a required field with no rule and no fallback. It blocks Save and offers Add mapping and Add fallback with the field preselected. [21][22]
- **CONFIRMED** A conflict is a fixed rule plus a fallback, so the fallback never applies. A check is a column rule plus a fallback on a required field. Neither blocks Save. [21]
- **CONFIRMED** A conflict offers Remove fallback. A check offers Remove mapping, or Always send with the value. That swaps the column rule for a fixed rule and deletes the fallback. [22]
- **CONFIRMED** The editor calls default values Fallback Values in the tab, the tables and the dialogs. The config keys and types keep the name `defaults`. [23]

### Apply and capture

- **CONFIRMED** Apply runs in the client. The add-use-case modal lists templates via `listApplicableTemplates(connectorType)`, then calls `applyTemplate`. [3][17]
- **CONFIRMED** `applyTemplate` copies the config. It overwrites each `to_be_advised` default with the value the operator typed. Preset defaults pass through. [14]
- **CONFIRMED** The result goes to `addConnectorMapping` as an ordinary create request. A use case with no chosen template starts from `emptyMappingConfig`. [17][7]
- **CONFIRMED** Capture runs the other way. The connector editor passes `saveAsTemplate`, which opens a modal where the operator marks each default. [11][4]
- **CONFIRMED** `captureMappingAsTemplate` accepts a new collection or an existing one. It creates the collection if needed, then calls `persistTemplate`. [4][18]
- **CONFIRMED** The template editor omits `saveAsTemplate`, so the library offers no capture from a template. [9][10]

### ILG Standard import

- **CONFIRMED** `importIlgStandardCollections` seeds one collection named "ILG Standard" per connector type from `ilgStandardTemplates`. It finds an existing one by connector type and name. [4]
- **CONFIRMED** A use case that already has a template reports `already_present` and stays untouched. A config that fails validation reports `rejected`. [4]
- **CONFIRMED** Marks come from a placeholder convention. A default whose value is the literal `TBA` becomes `to_be_advised`. Every other default becomes `preset`. [19]

## Boundaries

- **CONFIRMED** Nothing downstream reads a template. After apply or capture, the template and the connector mapping are independent documents. [14][4]
- **CONFIRMED** Deleting a template or collection never touches a connector mapping already created from it. [4]
- **CONFIRMED** config-service holds no template concept. Templates exist only in fuse-ui. [1][4]
- **CONFIRMED** There is no code-managed default mapping. The ILG Standard data is only an import source for the library. [4][7]
- **CONFIRMED** `emptyMappingConfig` leaves `columnOrder` off the simple arm. The simple stores re-stamp `configType` on save and would drop it. [7]

## Constraints

- **CONFIRMED** `template_collections` is a sanctioned exception to the rule against owning Fuse platform collections. Copy-on-apply keeps a template from becoming a second source of truth. [4][14]
- **CONFIRMED** Collection names carry no uniqueness constraint. Only the ILG Standard import matches on name, together with connector type. [2][4]
- **CONFIRMED** A collection's connector type is immutable. The metadata schema omits `connectorType`, since it fixes which configs and use cases the collection holds. [20]
- **CONFIRMED** A use case with no template yet opens on a blank config. It joins the library only after a save passes the gate. [4]
- **UNKNOWN** Whether a value import of the `.collection.ts` file from a client component fails only at `next build`, not at typecheck. No check ran.

## Evidence

```orient-evidence
{
  "v": 1,
  "items": [
    { "id": 1, "kind": "code", "ref": "code/src/lib/db/template-collections.types.ts@36e8575", "note": "document shape, marks vocabulary, optional per-use-case key" },
    { "id": 2, "kind": "code", "ref": "code/src/lib/db/template-collections.collection.ts@36e8575", "note": "Mongo access, non-unique indexes" },
    { "id": 3, "kind": "code", "ref": "code/src/app/server-functions/templates/templates.func.ts@36e8575", "note": "reads, no session check, listApplicableTemplates" },
    { "id": 4, "kind": "code", "ref": "code/src/app/server-functions/templates/templates.action.ts@6f0d67f", "note": "writes, persistTemplate gate, capture, ILG import, audit targets" },
    { "id": 5, "kind": "code", "ref": "code/src/modules/translator-config-editor/logic/mapping-config-validity.logic.ts@6f0d67f:L51-78", "note": "config schema check" },
    { "id": 6, "kind": "code", "ref": "code/src/modules/translator-config-editor/logic/mapping-config-validity.logic.ts@6f0d67f:L29-49", "note": "rule or default handles a required key, via computeCoverage" },
    { "id": 7, "kind": "code", "ref": "code/src/modules/translator-config-editor/logic/mapping-config.logic.ts@36e8575", "note": "resolveMappingConfigType, emptyMappingConfig" },
    { "id": 8, "kind": "code", "ref": "code/src/modules/template-library/logic/default-marks.logic.ts@36e8575", "note": "reconcileDefaultMarks, marksAreComplete" },
    { "id": 9, "kind": "code", "ref": "code/src/modules/translator-config-editor/components/translator-config-editor.tsx@36e8575", "note": "editor props, optional saveAsTemplate, dictionariesEnabled" },
    { "id": 10, "kind": "code", "ref": "code/src/modules/template-library/components/template-mapping-editor.tsx@36e8575", "note": "template page wiring" },
    { "id": 11, "kind": "code", "ref": "code/src/modules/customer-storefront/components/connector-mapping-editor.tsx@36e8575", "note": "connector page wiring, saveAsTemplate modal" },
    { "id": 12, "kind": "code", "ref": "code/src/modules/translator-config-editor/stores/grouped-config-editor/grouped-config-editor-store.ts@6f0d67f:L266-290", "note": "grouped calculateIsValid" },
    { "id": 13, "kind": "code", "ref": "code/src/modules/translator-config-editor/stores/simple-config-editor/simple-config-editor-store.ts@6f0d67f:L98-115", "note": "simple calculateIsValid" },
    { "id": 14, "kind": "code", "ref": "code/src/modules/template-library/logic/template-apply.logic.ts@36e8575", "note": "applyTemplate copies config, fills to-be-advised values" },
    { "id": 15, "kind": "code", "ref": "code/src/instrumentation.ts@6f0d67f", "note": "index creation at boot" },
    { "id": 16, "kind": "code", "ref": "code/src/proxy.ts@36e8575:L15-60", "note": "session resolved for every non-auth route" },
    { "id": 17, "kind": "code", "ref": "code/src/modules/customer-storefront/components/add-use-case-modal.tsx@36e8575:L111-141", "note": "client-side apply, addConnectorMapping" },
    { "id": 18, "kind": "code", "ref": "code/src/modules/template-library/schema/template-collection.schema.ts@36e8575", "note": "capture target, meta schema omits connectorType" },
    { "id": 19, "kind": "code", "ref": "code/src/modules/template-library/logic/ilg-standard-import.logic.ts@36e8575", "note": "TBA convention to marks" },
    { "id": 20, "kind": "code", "ref": "code/src/modules/template-library/schema/template-collection.schema.ts@36e8575:L10-16", "note": "connectorType immutable" },
    { "id": 21, "kind": "code", "ref": "code/src/modules/translator-config-editor/logic/required-field-coverage.logic.ts@6f0d67f", "note": "computeCoverage, defaultsSatisfy, gap / conflict / check" },
    { "id": 22, "kind": "code", "ref": "code/src/modules/translator-config-editor/components/simple-required-field-coverage.tsx@6f0d67f", "note": "panel rows, Add / Remove / Always send actions; the grouped twin mirrors it" },
    { "id": 23, "kind": "code", "ref": "code/src/modules/translator-config-editor/components/simple-translator-defaults.tsx@6f0d67f", "note": "Fallback Values table, required marker, shadowed pill" }
  ]
}
```

## Related

- [[../architecture#bff-not-data-plane]]: the own-Mongo, everything-else-over-HTTP rule this collection is an exception to.
- [[../architecture#Guardrails]]: the load-bearing traps this area shares with the mapping-editor stack.
- [[../plans/FUSE-1070-template-library-storage-browse-and-crud]]: the plan that built storage, browse and CRUD.
