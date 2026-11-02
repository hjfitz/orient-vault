---
title: G3 — SPORTLUX re-presentation explained
date: 2026-10-02
gate: G3
verdict: explained — a manual re-push, not SNAP behaviour
---
# G3 — SPORTLUX re-presentation (2026-09-22) explained

**Verdict:** the 09-22 re-presentation was an **operator re-push** of SportLux's uncollected dispatch confirmations onto the SNAP outbound queue. SNAP did not reopen processed rows on its own. A clear is consume-once unless a person re-pushes the row in SNAP.

## Evidence
- **The re-pushed range is exactly the customer's missing window.**
  - The first re-presented row, `SPLU003836`, was created 2026-09-11 15:43:04Z.
  - SportLux's uncollected confirmation files start at 09-11 15:44Z ([[2026-09-18-sportlux-192-orders-dispatch-confirmations]]).
  - The row before it, `SPLU003835` (created 09-10, processed 27 s later, 09-10), was not re-presented.
- **The intent is on record.** On 09-21 09:48 BST, James Godsell wrote in the group DM with Harry and Thomas Dunn: *"I will need to go through and re-push those confirmations to the queue. Hoping they're all still in Snap…"*
- **Repeat clears form contiguous XDoc blocks, which is what overlapping manual batches look like.** In the 09-22 14:16–14:38Z burst, 279 rows were cleared 395 times:
  - `SPLU003837–3840`: 3 clears each
  - `SPLU003836–3948`: 2 clears each (110 rows)
  - `SPLU003949–4333`: 1 clear each (166 rows)

  Random SNAP failure would not split along XDoc ranges.
- **Rows already processed came back.**
  - `SPLU004066–4098` were cleared once on 09-18 and not touched again until 14:32–14:36 on 09-22, all inside the burst.
  - If their 09-18 PATCH had silently failed, the poller would have re-listed them 10 minutes later the same day.
- **No business event re-opened them.** The traced shipment `SPOR6E6CB9B3310` (`SPLU003840`) has not changed since it closed (09-14 11:54 local).
- **Poll cycles don't overlap.** They take 10–20 s each (14:16:03–:12, 14:26:03–:20, 14:38:03–:11). The 14:26 cycle listed `SPLU003840` a full 10 minutes after its 2xx PATCH, so this is not a stale snapshot inside the poller.
- **There has been none since.** From 09-23 to 10-02, 7 rows fleet-wide were cleared more than once, all STUBBLE. In every case the first attempt logged `Confirmation clear-down failed`, then the row was re-announced and cleared: the normal rescue path. **Zero** rows were re-listed after a logged-successful clear.

## What did not cause it
- **The 2xx `Status:"Error"` body.** snap-adapter's `clearFromOutboundQueue` does discard the PATCH response body (scar tissue, and still true), but the contiguous re-push blocks and the 4-day gap rule it out here. C2's body check still stands.
- **The `e6726fa` snap-adapter deploy** (09-18 08:48Z). It only renamed log events; the clear-down logic is unchanged.
- **The 09-19/20 gap in clears.** That was the weekend (no SportLux activity at all).

## Consequences
- **G3 cleared.**
- **Re-pushing rows in SNAP is a live ops replay path.** Under C2 it still works: a re-pushed row is re-listed, re-announced and cleared again. It bypasses replay-service, though, and overlapping passes double-delivered 113 confirmations to SportLux's SFTP on 09-22. That's worth raising with CS/James as hygiene, not a programme blocker.

## Method notes
- **Datadog `env` tag:** since the sidecar consolidation, prod logs carry `env:serverless` in SQL. Filter on `@environment:prod` (the older 09-22 logs still match `env:prod`).
- **Flex tier retention:** it only reaches back to about 09-17 (roughly 15 days). The absence of a log before that date proves nothing; the SPLU003840 "never cleared before 09-22" claim only holds from 09-17.
- **correlationId is per poll cycle, not per confirmation.** One correlationId covers every business in a cycle.
- **Queries used:** `analyze_datadog_logs` over `service:snap_adapter @businessId:SPORTLUX @record.identifiers.queueId:*` (flex). SNAP reads used `snap-get snapOutbound` / `shipments` against SPORTLUX prod, read-only.
