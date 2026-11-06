---
tags:
- waypoint
- tracking-webhooks
verified: '2026-11-06'
---
# tracking-webhooks — known context

From the 2026-11-06 egress deep dive (code, GitHub, Cloud Run, Jira, Datadog). No interview.

## Cutover state (snapshot 2026-11-06)
- **Evri:** moved into the monorepo 15 Oct; deploys on push to `main`. The old repo's workflows are off; it needs archiving. Publish is off in prod.
- **Royal Mail:** PR #3, open. 22 resource moves. It needs a reviewed plan, a check that the Mongo connection points at the same cluster, and a quiet-time merge.
- **InPost:** PR #2, open. Publish off in prod and the deploy job disabled.
- **Next:** Veho tracking webhooks are planned (CID-347). A UniUni spec also exists.

## Evri go-live (CID-315, In Progress, John Finney)
1. Evri enables webhooks for all GFS customers. Today they send about 25% of the volume.
2. Reconcile the account IDs Evri sends.
3. Review the mapping (ETA events, extra event types).
4. Turn publish on.
5. Run alongside the connectors for about 2 hours, then switch off connectors-hermes and connectors-hermesps.

## Unknowns
- Why Evri's signature lookup shows no activity: no events link a signature, or the lookup fails silently.
- The current depth of the dead-letter topics.
- Whether these services' logs reach Datadog. Metrics arrive; log searches returned nothing.
