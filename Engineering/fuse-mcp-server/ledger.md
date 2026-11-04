---
tags: [waypoint, ledger]
---
# fuse-mcp-server — work ledger

Agent-facing. Newest first. What meaningful work happened here, and the
context a future agent needs. Not a diary, not release notes, not a diff.

## 2026-11-04 — Clear the high findings failing the MCP dependency audit and image scan

Clear the high findings failing the MCP dependency audit and image scan

Cleared the secops dependency_audit and image_scan checks, red on master since at least 2026-11-02, in their own PR off master as the red-check rule requires. zod went to 4.6.6 and body-parser to 2.4.0. multer GHSA-q7qp-rjg7-q26m is allowlisted until 2026-11-11, because the fix only comes with Nest 12 and the server has no multipart route. Three undici CVEs in the npm CLI bundled in node:24 were trivyignored, since npm@latest still bundles 6.29.0. Follow-up owed: the Nest 12 upgrade before the multer allowlist expires.

PR: gfs-bifrost/fuse-mcp#63

## 2026-11-04 — Add shopify-test-order tools to the MCP

Add shopify-test-order tools to the MCP

Three dev-only Go MCP tools, shopify-test-order-create, -get (read-only) and -delete, over shopify-connector's new /api/v1/test-orders routes. Agents can now create, read and delete a real paid order on GADG's ILG Test Store without a human in the Shopify admin. They use a staging-only SHOPIFY_CONNECTOR client, with URL and key from the connector's dev remote state behind try(). The data files gain shopify-connector's consumer API and the fuse-mcp-server -> shopify-connector dependency. The parity baseline gains the Go-only declarations and the refreshed payloads.

PR: gfs-bifrost/fuse-mcp#62

## 2026-10-05 — Say how to reach consumers with a mocked goods-out

Say how to reach consumers with a mocked goods-out

Out-of-ticket. mock-generate/mock-send descriptions now name dispatch/receipt as a zero-side-effect sink and say to send a goods-out/goods-in as goods_out_confirmation/goods_in_confirmation to reach consumers. Also: baseline accepted for the shared-packages remote-config 2.3.0 data change (d142b59, which had redded master's Code Quality Go).

PR: gfs-bifrost/fuse-mcp#49

## 2026-09-29 — Point the MCP's mocker tools at fuse-mocker's Go API

Point the MCP's mocker tools at fuse-mocker's Go API

remotes.tf mocker_staging_url: fuse-mocker output service_url (Next.js UI, no /api/v1 since the Go API split) → api_service_url (fuse-mocker-api-dev). Every mock-* tool had been returning the UI's 404 page. Also refreshed the Go parity baseline (59330cb) after the FUSE-1258/FUSE-1088 canonical-types.json data commits left Code Quality Go red on master. Smoke-tested mock-generate + mock-activity after the prod apply.

PR: gfs-bifrost/fuse-mcp#47
