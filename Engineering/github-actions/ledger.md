---
tags: [waypoint, ledger]
title: github-actions — work ledger
---
# github-actions — work ledger

Agent-facing. Newest first. What meaningful work happened here, and the
context a future agent needs. Not a diary, not release notes, not a diff.

## 2026-10-27 — Make terragrunt's Datadog API key secrets optional

Make terragrunt's Datadog API key secrets optional

datadog_api_key / datadog_api_key_ilg on terragrunt.yaml go from required to optional, so stacks without a Datadog sidecar/provider don't have to pass them. Omitted keys still export as empty TF_VARs, so absorb-only variable declarations keep working. Backward compatible; tags move after a canary.

PR: ilg-platform/github-actions#38
PR: ilg-platform/github-actions#39

## 2026-10-13 — terragrunt: optional Secrets Hub references

terragrunt: optional Secrets Hub references

secrets_hub_url input -> TF_VAR_secret_refs (refs only, fail closed with fix-naming errors). Canaried via secrets-hub#11 (ok / 401 audience hint / id-token hint). Both lines; 0.1-affogato and 0.2-bonbon force-moved after diff-stat check.

PR: ilg-platform/github-actions#36, ilg-platform/github-actions#37

## 2026-10-05 — Deploy notification change merged; 0.1-affogato and 0.2-bonbon rolled

Deploy notification change merged; 0.1-affogato and 0.2-bonbon rolled

#34 (main) and #35 (0-1-affogato) merged after a replay-service dev canary. 0.1-affogato -> d52202b, 0.2-bonbon -> af46124; each differs from its old commit by exactly this change (3 files). Post-roll run on the real tag posted the new format. Prod header live-verified only by the next prod deploy.

PR: ilg-platform/github-actions#34
PR: ilg-platform/github-actions#35

## 2026-10-05 — Make prod deploy Slack messages stand out, show branch

Make prod deploy Slack messages stand out, show branch

Prod gets a distinct 🚀/🚨 [PROD] header in docker-build-push and terragrunt notifications; the branch now shows on the Triggered-by line. Human-facing text only, backward compatible. Two PRs because the 0.1 line lives on the 0-1-affogato branch and is not an ancestor of main. Drafts until canaried; tags not moved.

PR: ilg-platform/github-actions#34
PR: ilg-platform/github-actions#35
