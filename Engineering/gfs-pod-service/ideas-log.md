---
tags: [waypoint, ideas]
---
# gfs-pod-service — ideas log

Every idea waypoint-ideate has surfaced, kept or discarded, newest first.
Read in full before generating new ideas — don't resurface a discarded idea
without new evidence that changed the picture.

## 2026-11-06 — kept — Capture PODs at ingress and serve them from a store
source: user
plan: capture-pods-at-ingress-and-serve-them-from-a-st

Harry's design: connectors and webhooks fetch the POD and images on delivery, store them in a central bucket, emit a pod.v1 pointer, and gfs-pod-service becomes a read model. Kept as an idea only: the carriers team owns the service, and Harry doesn't own that team yet.
