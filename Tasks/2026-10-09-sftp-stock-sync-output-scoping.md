---
tags: [adhoc-task]
date: 2026-10-09
tldr: "Scoped SFTP as a second stock sync output under FUSE-658; created FUSE-1298..1306 with Blocks links, commented on FUSE-1198 and fuse-ui#294"
session_id: c09a86bb-47a2-406a-b8c1-4eb2616a7bb4
status: open
---
# Scope SFTP as a second stock sync output

## Outcome
Reviewed the stock sync pipeline (poller export, shopify-egress-service stack #305-#317, collector, replay) and Sprint 15/16 for overlaps; no duplicates. Created nine tickets under FUSE-658: FUSE-1298 (stamp connector type), 1299 (types), 1300 (config), 1301 (poller scheduling), 1302 (SFTP consume, QA_REQUIRED), 1303 (SFTP result/failure), 1304 (replay spike), 1305 (conditional replay fix, left in Backlog), 1306 (UI, QA_REQUIRED). Blocks links wired, incl. FUSE-1203 blocking 1303.
Comments posted: FUSE-1198 (ask Matt to add the connector-type filter clause once 1298 is live) and fuse-ui#294 (`connectorTypes: ['shopify']` will hide SFTP runs).
All nine moved into Sprint 16 on request; ranking to the top not possible via the Jira MCP (no rank action), owed by hand on the board. FUSE-1298/1301 descriptions corrected: the due message carries no connector type today, so 1298 now plumbs the type scheduler -> due message -> export attribute (shopify only, untyped = shopify) and 1301 just lists SFTP as `sftp`. FUSE-1296 (Shopify happy-path QA) still in Sprint 15 backlog.
Fit review (Opus): added enum rollout hazard to 1299/1306, `connectorType` naming to 1298, canonical question to 1302. Dev check found the poller's stock sync export carries other businesses' SKUs on the shared host (GADG export of 7 Oct: AGT-1015521 etc., zero qty; prod bucket empty) -> defect FUSE-1308, blocks 1302. Design note on FUSE-658: poller and wms-gateway compute stock differently (OwnerId vs BizId, rows vs catalogue, kit qty source).
