---
tags: [waypoint, ledger]
---
# remote-compute — work ledger

Agent-facing. Newest first. What meaningful work happened here, and the
context a future agent needs. Not a diary, not release notes, not a diff.

## 2026-11-02 — Add a skill for logging in from another laptop

Add a skill for logging in from another laptop

Ship: SHIP-1102-add-laptop. New add-laptop skill, run on the new laptop: finds or makes its key, checks it against keys on main and in open PRs (refuses one that's someone else's), adds it only where missing, checks the plan is an in-place rc-users metadata update, sets up ssh; covers removing a lost laptop's key and its other logins. Two variable checks: no key twice on one owner, no key under two emails (type + key data, comment and spacing ignored; errors name owner not key). README, create-workstation, prod.tfvars comment and Confluence (v3) point to it. Prod plan No changes. Open: terraform-prod allows self-review.

PR: ilg-platform/remote-compute#12

## 2026-11-02 — Keep IAP access across a workstation rebuild

Keep IAP access across a workstation rebuild

Root cause proven by a throwaway Terraform probe: an instance-level IAP binding is unreliable after a same-name replace (lost for good on 1 of 3, matching both prod rebuilds). Fix: reserved internal IP per workstation and a project-level IAP grant conditioned on that IP and port 22; probe reached sshd 23-30 s after each of 3 replaces. rc-hjf's IP promoted to static and imported, no VM change. Applied: 1 imported, 1 added, 1 changed, 1 destroyed; IAP SSH confirmed.

Ship: SHIP-1029-remote-compute-workstations
PR: ilg-platform/remote-compute#11

## 2026-11-02 — Copy chosen folders and run the workstation sync every weekday evening

Copy chosen folders and run the workstation sync every weekday evening

--folder copies whole folders (the Obsidian vault) with notes-aware filtering; reviewed scan findings recorded by rule, file and sha256 of the flagged text; skill step 7 installs a weekday 17:30 systemd user timer; an unreachable workstation exits 75 (quiet skip). Installed for Harry: vault (1,780 files) on rc-hjf, timer live.

Ship: SHIP-1029-remote-compute-workstations
PR: ilg-platform/remote-compute#10

## 2026-11-02 — Lead with the skills, move the how-to to Confluence, copy MCP servers

Lead with the skills, move the how-to to Confluence, copy MCP servers

README is a skill-led front door plus a maintainer reference; the how-to is on Confluence (PLTE 348356619, under Agentic Engineering Practices); prod.tfvars points at create-workstation, which hands off to sync-claude-to-workstation. The sync now copies the user's MCP servers (user and local scope, tokens included) into the workstation's ~/.claude.json at mode 600, names only in output. Verified on rc-hjf: 12 servers, github/terraform/snap connected with copied tokens.

Ship: SHIP-1029-remote-compute-workstations
PR: ilg-platform/remote-compute#9

## 2026-11-02 — Move hjf onto the zsh image

Move hjf onto the zsh image

Pinned remote-compute-arch-20261102-e555081 and rebuilt rc-hjf (image_generation 3). /home, IP and host key kept. The apply lost the IAP binding again (provider inconsistent result); restored with a manual-deploy apply, IAP SSH confirmed. Root-cause evidence in the day-2 plan.

Ship: SHIP-1029-remote-compute-workstations
PR: ilg-platform/remote-compute#8

## 2026-11-02 — Add sync-claude-config and a skill to copy Claude Code setup to a workstation

Add sync-claude-config and a skill to copy Claude Code setup to a workstation

Copies a fixed set of a user's Claude Code setup (CLAUDE.md, settings, skills, agents, commands, hooks, memory notes, project roots' CLAUDE.md/AGENTS.md/skills) to their remote-compute workstation. It follows no symlinks except ~/.agents skill links, leaves secret-named files behind, is gated by gitleaks, keeps newer workstation files and checks every file by sha256. Two self-review rounds (security, ops-script). Verified live against rc-hjf: 548 files, 0 errors.

Ship: SHIP-1029-remote-compute-workstations
PR: ilg-platform/remote-compute#5

## 2026-11-02 — Run the PR plan on every PR

Run the PR plan on every PR

main requires the plan check, but the workflow only ran for Terraform paths, so docs-only PRs stayed BLOCKED. That came from my own branch protection on 2026-10-29. Every PR now plans. Ship: SHIP-1029-remote-compute-workstations

PR: ilg-platform/remote-compute#7

## 2026-11-02 — Add a create-workstation skill

Add a create-workstation skill

Self-serve path for an engineer to create their own workstation: values worked out from their git email and the existing entries, public key only, the entry added in a worktree, a PR, a plan check that it's only that entry's adds, and a person approving the prod gate. Rehearsed with a second engineer's entry: 9 to add, 0 to change, 0 to destroy. Also caught that subdomains need 3+ characters. Ship: SHIP-1029-remote-compute-workstations

PR: ilg-platform/remote-compute#6

## 2026-11-02 — Move the hjf workstation onto the remote-compute image

Move the hjf workstation onto the remote-compute image

image_generation 1->2 replaced rc-hjf onto the Arch image; home disk, IP and DNS kept, owner IAM re-bound. harry logs in by hostname with the banner. Ship: SHIP-1029-remote-compute-workstations

PR: ilg-platform/remote-compute#4

## 2026-11-02 — Pin the remote-compute image and make idle and nightly shutdown opt-in

Pin the remote-compute image and make idle and nightly shutdown opt-in

default_image moves to remote-compute-arch-20261102-fcbcd58 (no instance changed: in-place metadata only). idle_minutes defaults to 0 and nightly_stop to off. Adds rc-shell-domain metadata for the login banner. Ship: SHIP-1029-remote-compute-workstations

PR: ilg-platform/remote-compute#3

## 2026-10-29 — Add the workstation module and the first workstation

Add the workstation module and the first workstation

Workstation module: per-engineer Arch VM (n2 tier map), separate home disk and static IP with prevent_destroy, image swap only through image_generation, owners' keys in rc-users metadata (no OS Login on Arch), instance-level owner role + IAP access re-bound on replace, A record under shell.platform.ilg.software. Stack: egress deny to RFC1918 for tag remote-compute, input validation (tiers, DNS labels, Arch-reserved usernames, uid consistency, key format, company emails, no image families), serialised prod applies, lock timeouts, trivy.yaml so the scan evaluates the module. First VM rc-hjf live at hjf.shell.platform.ilg.software. Ship: SHIP-1029-remote-compute-workstations

PR: ilg-platform/remote-compute#2

## 2026-10-29 — Create the repo: Terragrunt skeleton, prod-only CI and the remote-compute network

Create the repo: Terragrunt skeleton, prod-only CI and the remote-compute network

First PR in ilg-platform/remote-compute (per-engineer Claude Code workstations on GCP). Prod-only Terragrunt stack on ilg-platform-tfstate-prod/remote-compute; subnet remote-compute (europe-west2, 10.20.0.0/24) and firewall remote-compute-ssh (tcp/22 from anywhere to tag remote-compute) on the shared ilg-platform VPC, applied locally before CI was admitted; workflows copied from core-infra (PR plan, gated deploy, manual deploy with a main-ancestor check, secops @0.2-bonbon). First CI apply was a no-op. Ship: SHIP-1029-remote-compute-workstations

PR: ilg-platform/remote-compute#1
