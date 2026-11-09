---
tags: [waypoint]
---
# Engineering

One folder per service. Inside each:

- `waypoint.yaml` — cheap orientation index (not documentation)
- `overview.md` / `architecture.md` / `known-context.md` (+ optional `operations.md`, `testing.md`, `interfaces.md`, `design.md`) — durable context
- `plans/` — what we intend to do, and what is happening now
- `ledger.md` — agent-facing record of meaningful work, newest first
- `explainers/` — human-facing current system truth

Source is implementation truth. Git is forensic truth. Plans describe intended and
current work. The ledger records completed work. Explainers describe the system as
it is now. Regenerate this page with `wp index`; check health with `wp doctor`.

| Service | Type | Docs | Explainers | Active plans | Last work |
| --- | --- | --- | --- | --- | --- |
| [[Engineering/agents/overview\|agents]] | ? | 0 | 0 | 0 | — |
| [[Engineering/amazon-proxy/overview\|amazon-proxy]] | backend | 1 | 0 | 0 | — |
| [[Engineering/api-host-framework/overview\|api-host-framework]] | backend | 0 | 0 | 0 | 2026-10-06 |
| [[Engineering/apiky/overview\|apiky]] | backend | 0 | 0 | 0 | 2026-10-09 |
| [[Engineering/audit-service/overview\|audit-service]] | backend | 4 | 1 | 0 | 2026-10-27 |
| [[Engineering/bifrost-pubsub/overview\|bifrost-pubsub]] | infra | 3 | 0 | 0 | 2026-10-14 |
| [[Engineering/bjs-proxy/overview\|bjs-proxy]] | backend | 1 | 0 | 0 | — |
| [[Engineering/carrier-playground/overview\|carrier-playground]] | backend | 0 | 0 | 0 | 2026-11-05 |
| [[Engineering/carrier-proxies/overview\|carrier-proxies]] | backend | 1 | 0 | 0 | 2026-10-08 |
| [[Engineering/client4/overview\|client4]] | frontend | 3 | 0 | 0 | — |
| [[Engineering/coll8-proxy/overview\|coll8-proxy]] | backend | 1 | 0 | 0 | — |
| [[Engineering/collector/overview\|collector]] | backend | 3 | 1 | 0 | 2026-11-05 |
| [[Engineering/config-service/overview\|config-service]] | backend | 5 | 0 | 1 | 2026-11-05 |
| [[Engineering/connectors-amazon/overview\|connectors-amazon]] | backend | 1 | 0 | 0 | — |
| [[Engineering/connectors-collectplus/overview\|connectors-collectplus]] | backend | 1 | 0 | 0 | — |
| [[Engineering/connectors-dhlexpress/overview\|connectors-dhlexpress]] | backend | 1 | 0 | 0 | — |
| [[Engineering/connectors-dhlparcel/overview\|connectors-dhlparcel]] | backend | 1 | 0 | 0 | — |
| [[Engineering/connectors-dpd/overview\|connectors-dpd]] | backend | 1 | 0 | 0 | — |
| [[Engineering/connectors-fedex/overview\|connectors-fedex]] | backend | 1 | 0 | 0 | — |
| [[Engineering/connectors-hdnl/overview\|connectors-hdnl]] | backend | 1 | 0 | 0 | — |
| [[Engineering/connectors-hermes/overview\|connectors-hermes]] | backend | 1 | 0 | 0 | — |
| [[Engineering/connectors-hermesps/overview\|connectors-hermesps]] | backend | 1 | 0 | 0 | — |
| [[Engineering/connectors-inpost/overview\|connectors-inpost]] | backend | 1 | 0 | 0 | — |
| [[Engineering/connectors-international/overview\|connectors-international]] | backend | 1 | 0 | 0 | — |
| [[Engineering/connectors-panther/overview\|connectors-panther]] | backend | 1 | 0 | 0 | — |
| [[Engineering/connectors-tuffnells/overview\|connectors-tuffnells]] | backend | 1 | 0 | 0 | — |
| [[Engineering/connectors-ups/overview\|connectors-ups]] | backend | 1 | 0 | 0 | — |
| [[Engineering/connectors-yodel/overview\|connectors-yodel]] | backend | 1 | 0 | 0 | — |
| [[Engineering/core-infra/overview\|core-infra]] | infra | 3 | 0 | 0 | 2026-09-21 |
| [[Engineering/css/overview\|css]] | backend | 3 | 0 | 0 | — |
| [[Engineering/cx/overview\|cx]] | backend | 0 | 0 | 0 | 2026-10-12 |
| [[Engineering/dedupe-service/overview\|dedupe-service]] | backend | 5 | 0 | 0 | 2026-11-04 |
| [[Engineering/distraction-dashboard/overview\|distraction-dashboard]] | frontend | 4 | 0 | 0 | 2026-11-05 |
| [[Engineering/dpd-europe-proxy/overview\|dpd-europe-proxy]] | backend | 1 | 0 | 0 | — |
| [[Engineering/evri-auth-facade/overview\|evri-auth-facade]] | backend | 1 | 0 | 0 | — |
| [[Engineering/exelot-proxy/overview\|exelot-proxy]] | backend | 1 | 0 | 0 | — |
| [[Engineering/fapi/overview\|fapi]] | backend | 3 | 0 | 0 | 2026-11-05 |
| [[Engineering/fedex-proxy/overview\|fedex-proxy]] | backend | 1 | 0 | 0 | — |
| [[Engineering/file-ingestion-ftp-proxy/overview\|file-ingestion-ftp-proxy]] | backend | 1 | 0 | 0 | — |
| [[Engineering/fuse-billing/overview\|fuse-billing]] | backend | 0 | 0 | 0 | 2026-11-05 |
| [[Engineering/fuse-devtools/overview\|fuse-devtools]] | backend | 3 | 0 | 0 | 2026-10-31 |
| [[Engineering/fuse-mcp/overview\|fuse-mcp]] | backend | 4 | 0 | 0 | 2026-11-03 |
| [[Engineering/fuse-mcp-server/overview\|fuse-mcp-server]] | backend | 0 | 0 | 0 | 2026-11-05 |
| [[Engineering/fuse-mocker/overview\|fuse-mocker]] | backend | 4 | 0 | 0 | 2026-11-05 |
| [[Engineering/fuse-ui/overview\|fuse-ui]] | frontend | 5 | 3 | 1 | 2026-11-05 |
| [[Engineering/gcp-config/overview\|gcp-config]] | backend | 0 | 0 | 0 | 2026-10-29 |
| [[Engineering/gfs-pod-service/overview\|gfs-pod-service]] | backend | 3 | 0 | 0 | — |
| [[Engineering/github-actions/overview\|github-actions]] | infra | 3 | 0 | 0 | 2026-10-27 |
| [[Engineering/github-config/overview\|github-config]] | infra | 3 | 0 | 0 | 2026-10-27 |
| [[Engineering/ilg-merak/overview\|ilg-merak]] | backend | 0 | 0 | 0 | 2026-10-28 |
| [[Engineering/ilg-platform-core-infra/overview\|ilg-platform-core-infra]] | backend | 0 | 0 | 0 | 2026-10-29 |
| [[Engineering/ilg-secure-notes/overview\|ilg-secure-notes]] | backend | 4 | 0 | 0 | — |
| [[Engineering/images/overview\|images]] | backend | 0 | 0 | 1 | 2026-11-02 |
| [[Engineering/inpost-proxy/overview\|inpost-proxy]] | backend | 1 | 0 | 0 | — |
| [[Engineering/merak-portal/overview\|merak-portal]] | backend | 0 | 0 | 0 | 2026-10-28 |
| [[Engineering/observability/overview\|observability]] | backend | 0 | 0 | 0 | 2026-11-03 |
| [[Engineering/observability-sdk/overview\|observability-sdk]] | library | 3 | 0 | 0 | — |
| [[Engineering/ocs-proxy/overview\|ocs-proxy]] | backend | 1 | 0 | 0 | — |
| [[Engineering/orient/overview\|orient]] | frontend | 1 | 0 | 2 | 2026-11-06 |
| [[Engineering/parcel-portal/overview\|parcel-portal]] | backend | 4 | 0 | 0 | 2026-11-03 |
| [[Engineering/pkg-go/overview\|pkg-go]] | backend | 0 | 0 | 0 | 2026-11-06 |
| [[Engineering/pkg-node/overview\|pkg-node]] | library | 3 | 0 | 1 | 2026-11-06 |
| [[Engineering/remote-compute/overview\|remote-compute]] | backend | 0 | 0 | 2 | 2026-11-03 |
| [[Engineering/renovate-runner/overview\|renovate-runner]] | infra | 3 | 0 | 0 | 2026-11-06 |
| [[Engineering/replay-service/overview\|replay-service]] | backend | 4 | 0 | 0 | 2026-11-05 |
| [[Engineering/repo-template/overview\|repo-template]] | ? | 0 | 0 | 0 | — |
| [[Engineering/royal-mail-proxy/overview\|royal-mail-proxy]] | backend | 3 | 0 | 0 | — |
| [[Engineering/secops-reporting/overview\|secops-reporting]] | backend | 4 | 0 | 1 | 2026-09-14 |
| [[Engineering/secrets-hub/overview\|secrets-hub]] | backend | 0 | 0 | 2 | 2026-11-05 |
| [[Engineering/selector-adapter/overview\|selector-adapter]] | backend | 3 | 0 | 0 | 2026-11-05 |
| [[Engineering/selector-rest-proxy/overview\|selector-rest-proxy]] | backend | 3 | 0 | 0 | — |
| [[Engineering/sftp-connector/overview\|sftp-connector]] | backend | 5 | 1 | 2 | 2026-11-06 |
| [[Engineering/shopify-connector/overview\|shopify-connector]] | backend | 4 | 0 | 1 | 2026-11-05 |
| [[Engineering/snap-adapter/overview\|snap-adapter]] | backend | 4 | 2 | 1 | 2026-11-05 |
| [[Engineering/snap-mcp/overview\|snap-mcp]] | backend | 4 | 0 | 0 | 2026-11-05 |
| [[Engineering/snap-queue-polling-service/overview\|snap-queue-polling-service]] | backend | 4 | 0 | 9 | 2026-10-15 |
| [[Engineering/svc-template/overview\|svc-template]] | backend | 0 | 0 | 0 | 2026-10-28 |
| [[Engineering/tech-services-manager/overview\|tech-services-manager]] | ? | 0 | 0 | 0 | — |
| [[Engineering/terraform-modules/overview\|terraform-modules]] | infra | 3 | 0 | 0 | 2026-10-28 |
| [[Engineering/tracking-core/overview\|tracking-core]] | backend | 3 | 0 | 0 | — |
| [[Engineering/tracking-file-processor/overview\|tracking-file-processor]] | backend | 1 | 0 | 0 | — |
| [[Engineering/tracking-service/overview\|tracking-service]] | backend | 4 | 0 | 2 | 2026-11-06 |
| [[Engineering/tracking-webhook-royal-mail-sapient/overview\|tracking-webhook-royal-mail-sapient]] | backend | 1 | 0 | 0 | — |
| [[Engineering/tracking-webhooks/overview\|tracking-webhooks]] | backend | 3 | 0 | 0 | — |
| [[Engineering/ui-toolkit/overview\|ui-toolkit]] | library | 4 | 0 | 0 | — |
| [[Engineering/ups-proxy/overview\|ups-proxy]] | backend | 3 | 0 | 0 | — |
| [[Engineering/wms-gateway/overview\|wms-gateway]] | backend | 4 | 0 | 0 | 2026-11-05 |
| [[Engineering/workspace-kit/overview\|workspace-kit]] | backend | 0 | 0 | 0 | 2026-10-28 |
