---
tags: [waypoint, ideas]
---
# observability — ideas log

Every idea waypoint-ideate has surfaced, kept or discarded, newest first.
Read in full before generating new ideas — don't resurface a discarded idea
without new evidence that changed the picture.

## 2026-11-12 — kept — Stop the tracking-service push 5xx composite flapping at hold edges
source: techdebt
plan: stop-the-tracking-service-push-5xx-composite-fla

The push 5xx composite subtracts the app's `push.held` from Cloud Run's 5xx count, but the GCP metric arrives minutes later, so the two don't line up at the start and end of a hold. It only matters during a hold, which is a cutover-only step.
