# SNAP outbound queue: PATCH processed behaviour (G2)

Tested 2026-09-30 on dev business HJF, whose SNAP host is fuse-mocker's snap-api **simulator**, not real SnapFulfil.
Route: `PATCH /v2/snapoutbound/{XDoc}/processed` via the snap MCP (`snap-write`, `snapOutbound`, `markProcessed`).

| Case | Result |
| --- | --- |
| First PATCH on an unprocessed row | `Status: Success`; `DateProcessed` set (13:54:48Z). Row drops out of the unprocessed queue. |
| Second PATCH on the same, already-processed row | `Status: Success`, row returned, **`DateProcessed` overwritten** (13:54:52Z). No error. |
| PATCH on an id that does not exist | `Status: Success`, `Message: OK`, **`Results: []`**. A silent no-op, not a 404 and not `Status: Error`. |

## What it means
- On the simulator, a double clear (poller then snap-adapter) is harmless: no error, so no false clear-down failure.
- **C2 must check `Results` is non-empty, not only that `Status` is not `Error`.** A clear against a wrong or absent id looks like success.
- `DateProcessed` moves on a repeat PATCH. Anything reading it as "when it was first cleared" (soak evidence, G3's re-presentation analysis) must not assume it is stable.

## Real SnapFulfil (GADG dev, ilg001testapi) — 2026-09-30
| Case | Result |
| --- | --- |
| PATCH `/processed` on an id that does not exist (`GAOBNOSUCH0001`) | **HTTP 200** with body `{"Status":"Error","Message":"Entity does not exist"}` (no `Results`). Captured with `curl -i`. So it is the 2xx-with-`Status:Error` quirk, **not** a 404: a client that only checks the HTTP status treats it as success. |
| First PATCH on an unprocessed row (`GAOB001448`, a 15 Sep despatch row nothing had consumed) | `Success`; `DateProcessed` 15:04:30.97Z; the row's `Stage` field changed `00` to `90`. |
| **Second PATCH on that already-processed row** | **`Status: Success`, no error.** Row returned with `DateProcessed` **overwritten** (15:04:35.79Z). A `GET` afterwards shows the later timestamp. |
| Listing | Processed rows do not appear in the queue listing (only unprocessed ones do), so a processed row can only be reached by id. |

Consequence: **C2 must read the response body** (`Status === "Error"`), because the HTTP status is 200 for a wrong id. The simulator's `Stage` field is not modelled on processing (real rows go `00` to `90`); the poller reads the stage from `Key`, so nothing depends on it.

## Simulator fixed (fuse-mocker `30f391f`, deployed to dev 2026-09-30)
The simulator now answers an unknown XDoc with HTTP 200 and `{"Status":"Error","Message":"Entity does not exist"}`, matching real SNAP; a repeat clear still succeeds and restamps `DateProcessed`. Re-run on HJF after deploy: rejected as expected. Tests pin all three cases. Not modelled: the top-level `Stage` change on processing, and the success `Message` (real says `Success`, simulator `OK`). Real SNAP errors, so a clear against a wrong id surfaces as a failure (still check `Results`, since a 2xx `Status:"Error"` is a known SNAP quirk).

## Not established
- **G2 is cleared** on real SNAP: a repeat clear does not error, so snap-adapter's clear-down running after a poller clear cannot publish a false clear-down failure. Still open under G3: whether SNAP can *re-present* a row after a successful processed PATCH (the SPORTLUX report).

## Side finding: snap-adapter clear-down failing in prod
Datadog, `service:snap_adapter @environment:prod`, 2026-09-29 18:50Z to 21:30Z (34 lines in a 3-day window): `Confirmation clear-down failed | Timed out after 30000ms waiting for a concurrency slot`. Rows whose clear-down times out stay on the OBQ and re-announce. Not yet investigated: which businesses, whether they recover, and whether the concurrency limit is shared with other SNAP calls.
