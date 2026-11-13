---
tags: [adhoc-task]
date: 2026-11-13
tldr: "Onboarded remote-compute into Waypoint properly and joined it to the ilg-platform system; orient now shows it as a member with overview, architecture and known-context."
session_id: c442cdeb-5451-4a5e-ab55-47215f284cac
status: open
---
# Onboard remote-compute into Waypoint and the ilg-platform system

## Outcome
The stub folder became a full onboarding. `waypoint.yaml` is filled in (system: ilg-platform, type: infra, commands anchored on mise.toml), and `overview.md` and `architecture.md` are written and anchored at 8498e18. `known-context.md` is written and the public-tcp/22 decision record is filled in. Systems/ilg-platform overview and architecture now name it as the sixth member.
Open: the startup_script half of PR #15, the second adopter, disk-side offboarding, a cost gate for m/l, and upstreaming to terraform-modules. These are listed under known-context `## Unknowns`.
