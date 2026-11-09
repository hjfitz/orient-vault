---
tags:
- waypoint
- tracking-core
verified: '2026-11-06'
---
# tracking-core — known context

From the 2026-11-06 tracking (ingress) deep dive (code, prod manifests, Datadog). No interview. Shared context is in `Systems/carrier-integrations/known-context.md`.

- **Owner is inferred:** the ECM / fenghuang side. Nobody has confirmed it.
- **Polling cost** (snapshot 2026-11-06, 15 days): about 142M carrier calls produced 5.44M new events, roughly 26 calls per event. About 7M calls failed.
- **.NET Core 3.1 is out of support.** Most connector repos were last changed in early 2025.
- **Delivered parcels keep being polled** wherever a connector's DELIVERED key is on. Amazon re-polled 2.6M of them.

## Unknowns
- The prod etcd values: `TargetPollingMinutes`, `BatchLimit` and which states each connector polls.
- What's on the `untracked` list.
- The `fenghuang-tracking-core-config` ConfigMap (topic and subscription names) isn't in the cluster repo.
