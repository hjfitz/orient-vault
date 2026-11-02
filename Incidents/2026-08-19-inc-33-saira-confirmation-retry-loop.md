---
tags: [incident]
reference: INC-33
date: 2026-08-19
service: shopify-connector
business_id: SAIRA
severity: P3
is_us: true
declared_by: agent
declared_at: "2026-08-19T10:26:25Z"
resolved_at: "2026-08-19T11:02:09Z"
minutes_to_resolve: 36
incident_url: "https://app.incident.io/gfsdeliver-eng/incidents/01M0CRXMGV7TPZSH2HNZPP83ZG"
slack_channel_url: "https://gfsdeliver-eng.slack.com/archives/C0BRBLU1BB6"
follow_up_count: 4
ticket: FUSE-1118
session_id: 26786e07-db97-44ac-aff4-911f6cd52eca
status: resolved
---
# shopify-connector: SAIRA order confirmation stuck in retry loop (no fulfillment ID)

## Impact
SAIRA (Saira Skin) order #36044 / Shopify order 14347930861943, shipment SAIRE73AC8C7AFE, was
despatched in SNAP (stage 90) but stuck in an infinite Shopify confirmation re-announce loop
between 09:50–10:50 UTC.

## Root cause
`SalesOrderConfirmationHandler.getLineItemsFromMappings` threw `ConfirmationException` ("Unable to
confirm order: Line item has no fulfillment ID") on every poll cycle, because all 3 shipment lines
were missing their SNAP SHL attachment (the carrier for `extensions.shopify.fulfillmentId`) —
collateral damage from the prior day's token-refresh-wedge outage degrading this order's original
Shopify ingestion. Not a vendor issue: Shopify itself was healthy throughout.

## Resolution
Fixed by manually backfilling the 3 missing SNAP attachments (Shopify `FulfillmentOrderLineItem`
GIDs pulled live via Admin GraphQL, `LineId` computed via snap-adapter's own deterministic-hash
algorithm) since SAIRA is not configured in `snap-mcp-server`. Verified fixed at 11:02:09 UTC:
shopify-connector logged a successful confirmation (Shopify Fulfillment
`gid://shopify/Fulfillment/8472963875191`, status SUCCESS) and snap_adapter logged the outbound-queue
entry (SIOB000003) cleared down. No recurrence since.

Durable fix: [FUSE-1118](https://globalfreight.atlassian.net/browse/FUSE-1118) — shopify-connector
should skip an unmappable line instead of hard-throwing and aborting the whole confirmation.

## Follow-ups
- shopify-connector: unmappable line item aborts entire confirmation instead of being skipped
  (FUSE-1118).
- Harden `attachLineExtensions` against index/count mismatch under degraded Shopify API retries.
- Add SAIRA (+ prod host) to `snap-mcp-server` config.
- shopify-connector: `attachLineExtensions` silently drops all line extensions on a
  raw/translated line-count mismatch.

## Links
- Incident: https://app.incident.io/gfsdeliver-eng/incidents/01M0CRXMGV7TPZSH2HNZPP83ZG
- Slack channel: https://gfsdeliver-eng.slack.com/archives/C0BRBLU1BB6
- Ticket: https://globalfreight.atlassian.net/browse/FUSE-1118
