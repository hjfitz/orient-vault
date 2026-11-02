---
tags: [meeting]
series: DataDog data centre migration
title: DataDog data centre migration
---
# DataDog data centre migration

## 2026-09-07
_11:00–11:30 · Teams · organiser [[John Clarke]] · first occurrence_

### Context

**Attendees**
- [[John Clarke]] (organiser, accepted)
- [[Wolf Clostermann]] (accepted)
- [[Oli Denton]] (accepted)
- Peter Liu (declined)

**Agenda (from invite)** — none, Teams join block only

**⚠️ Clashes with [[Meetings/Bifrost Leadership Catchup]]** (11:15–12:00) by 15 minutes

**Why this matters to Fuse**
- Fuse's dashboards and monitors are Terraform-managed in the `observability` repo, not in the Datadog UI — a DC migration touches state, provider endpoints and API/app keys, so it is a change to code we own rather than a vendor-side event we merely observe.
- The estate is 65 monitors on `domain:fuse` plus 8 curated dashboards. A move that re-issues resource ids would force a re-import rather than a plan-clean apply.
- The 09-04 Terraform pass modified 53 monitors and deleted 4. Anything mid-migration will plan dirty against that.
- [[Sean Defraine]] asked in `#ilg-platform` whether the monitor review can cover the full 175-monitor org estate (106 legacy, 31 receiving no data) — relevant if the migration is the moment legacy monitors get culled.

### What a US1 → EU1 move actually costs us

**Where we are today** — verified locally, not assumed
- Fuse is on **US1** (`app.datadoghq.com`).
- `providers.tf` sets `api_key` and `app_key` but **no `api_url`**, so the provider is *implicitly* US-pinned. EU needs `api_url = "https://api.datadoghq.eu/"` stated explicitly.
- The estate under Terraform is **65 monitors + 20 dashboards + 46 catalog entities** = 131 resources.
- `DD_SITE = "datadoghq.com"` is **hardcoded inline, twice, in the shared `terraform-modules/compute/cloud-run/main.tf`, with no variable backing it** — and hardcoded again in each service's own `cloud-run.tf` (~15 live services).
- **40 distinct Datadog monitor/dashboard links across 53 vault notes** point at US ids.

**Why this is a rebuild, not a migration** — vendor behaviour, confirm with [[John Clarke]] in the room
- Datadog sites are **independent installations**. There is no cross-site migration path and no data transfer between US1 and EU1.
- API and app keys are **site-scoped** — all keys re-issue, including the `DATADOG_APP_KEY` CI secret.
- **Resource ids are not preserved.** Every monitor and dashboard id changes, so the existing Terraform state is worthless against the new org — it is an apply into an empty org, not a `terraform state mv`.
- **Historical telemetry does not come with us.** Whatever retention we need for the old window has to be exported or accepted as lost.
- The **GCP integration must be re-authorised** against the EU org.
- Log indexes, retention filters and custom-metric allowances all reset to defaults.

**What that means for the work, in order**
- Add a `dd_site` variable to the shared cloud-run module rather than editing 15 services — but note `terraform-modules` uses **rolling tags**, so force-moving the tag propagates to every consumer on their next apply. That is the fast path *and* the blast radius.
- Sequencing matters: the agent side (`DD_SITE`) and the provider side (`api_url`) must flip together, or metrics land in one org while monitors watch the other.
- An apply freeze on `observability` during the cutover, since a mid-migration apply plans dirty against whichever org it reaches.
- 53 vault notes and any Confluence runbook carrying a monitor id need re-pointing afterwards — cheap but easy to forget, and it is how a runbook silently rots.

**Questions to raise**
- Does the migration change the Datadog site/API endpoint the Terraform provider targets?
- Do monitor and dashboard resource ids survive, or is a re-import needed?
- Is there a freeze window where applies from `observability` should be held?
- Who owns re-issuing `DATADOG_API_KEY` / `DATADOG_APP_KEY` if they rotate?

### Carried from last time
- none — first occurrence

### Notes
- ✍️ 
