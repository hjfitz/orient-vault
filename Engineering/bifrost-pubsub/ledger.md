---
tags: [waypoint, ledger]
title: bifrost-pubsub — work ledger
---
# bifrost-pubsub — work ledger

Agent-facing. Newest first. What meaningful work happened here, and the
context a future agent needs. Not a diary, not release notes, not a diff.

## 2026-11-04 — Let other projects subscribe to topics via a subscribers input

Let other projects subscribe to topics via a subscribers input

Topic module gains a subscribers input (topic-scoped roles/pubsub.subscriber), fed per env from topic_subscribers in tfvars. Grants CX orders-service deploy SAs on create_record, create_acknowledge, create_data_failure, confirmation_ready. Leaner replacement for Darren's closed #18.

PR: gfs-bifrost/bifrost-pubsub#19

## 2026-10-14 — Add the feature_flag_revision topic

Add the feature_flag_revision topic

bifrost.{env}.feature_flag_revision.v1 (+ .dlt) next to config_revision, with outputs feature_flag_revision_topic_{name,id,dlt_name,dlt_id} for config-service's remote state. It's the refetch signal for remote-config feature-flag readers. Dedicated rather than a config_revision fragment because of the closed fragment union. Both env applies are gated.

PR: gfs-bifrost/bifrost-pubsub#17

## 2026-10-13 — Add audit.<env>.secrets.v1 topic

Add audit.<env>.secrets.v1 topic

Secrets Hub programme H2 part 1: topic + dlt + outputs for the secrets audit system. Draft.

PR: gfs-bifrost/bifrost-pubsub#16

## 2026-10-12 — Add audit.<env>.fuse.v1 topic for Fuse audit messages

Add audit.<env>.fuse.v1 topic for Fuse audit messages

Audit Service unit UD. A new 'audit' domain with one topic per reporting system (audit.<env>.<system>.v1, plus the module .dlt), so publisher IAM enforces system. audit-service subscribes and dead-letters to the module .dlt. Applied in dev and prod (run 38230065185).

PR: gfs-bifrost/bifrost-pubsub#15

## 2026-07-13 — FUSE-901

Add confirmation_data_failure topic

New topic `bifrost.{env}.confirmation_data_failure.v1` (+ DLT) — egress-side counterpart to `create_data_failure`, split by direction: `create_data_failure` is ingress/create-side, `confirmation_data_failure` is egress/confirmation-side.

`recordType`-discriminated, mirroring the `create_data_failure` / `confirmation_ready` / `confirmation_made` pattern — no application-level branching, subscribers filter via a Terraform subscription filter.

No publisher or subscriber wired yet — foundation topic only. Gates the connector confirmation-egress failure publish (Pick/Pack FUSE-888/890/892; WO/FGR FUSE-866/868/871/873) and replay's consumption (FUSE-906/902/903/904), both follow-up work.

fuse-mcp-server updated separately (pushed straight to its master per the repo-exception rule) — pubsub-topology.json and event-contracts.json now document the topic, its recordType taxonomy (pick_confirmation, pack_confirmation), and the provisional failure-envelope shape pending refinement.

PR: gfs-bifrost/bifrost-pubsub#11

## 2025-09-10 — FUSE-163

Create topics for errors

Created the initial Pub/Sub error topics for the platform.

PR: gfs-bifrost/bifrost-pubsub#2
