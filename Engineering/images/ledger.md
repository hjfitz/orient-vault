---
tags: [waypoint, ledger]
---
# images — work ledger

Agent-facing. Newest first. What meaningful work happened here, and the
context a future agent needs. Not a diary, not release notes, not a diff.

## 2026-11-02 — Build the remote-compute VM image in CI, weekly, and prune old images

Build the remote-compute VM image in CI, weekly, and prune old images

PRs get a full KVM build and smoke test (no import); main, Mondays 05:00 UTC and manual runs import via the main-pinned WIF grant, skip a sha already imported that day, then prune (keeps newest 4, any disk's source image, anything no older than the newest in-use image, and anything under 30 days). Follow-up #18: fail-fast preflight off main, strict skip check, build pinned to ubuntu-24.04. First CI import: remote-compute-arch-20261102-f8a7311.

Ship: SHIP-1029-remote-compute-workstations
PR: ilg-platform/images#17
PR: ilg-platform/images#18

## 2026-11-02 — Make zsh with syntax highlighting and starship the default shell on remote-compute workstations

Make zsh with syntax highlighting and starship the default shell on remote-compute workstations

Image logs every account in to zsh: /etc/zsh/zshrc sets history, completion, mise, starship and zsh-syntax-highlighting; no first-run wizard; smoke test proves an interactive zsh with no dotfiles. Image remote-compute-arch-20261102-e555081.

Ship: SHIP-1029-remote-compute-workstations
PR: ilg-platform/images#16

## 2026-11-02 — Add the remote-compute Arch VM image (Packer)

Add the remote-compute Arch VM image (Packer)

First VM image in ilg-platform/images: Arch Linux cloud image (signature-verified), customised with Packer qemu and imported to family remote-compute-arch. It provides key-only SSH from rc-users metadata, a /home disk with a blank-only format guard, host keys persisted and self-healing, fail-closed without /home, sshd decoupled from first-boot pacman-init, a toolchain with editors, rg/fd, kubectl/helm and LSPs, opt-in idle and nightly shutdown, rc-setup/rc-upgrade, fail2ban, and the Applied Computing login banner. Built locally (CI build is the next increment); image remote-compute-arch-20261102-fcbcd58. Ship: SHIP-1029-remote-compute-workstations

PR: ilg-platform/images#13
PR: ilg-platform/images#15

## 2026-10-28 — Rebuild and scan both images nightly

Rebuild and scan both images nightly

Nightly schedule (05:00/05:20 UTC) rebuilds each golden image from pinned digests, contract-tests and Trivy-scans it; never publishes.

PR: ilg-platform/images#11

## 2026-10-28 — Document SIGTERM handling for Node consumers

Document SIGTERM handling for Node consumers

README: Node consumers must handle SIGTERM under datadog-init (not PID 1); compose bind-mount/healthcheck notes; #platform-engineering -> #ilg-platform.

PR: ilg-platform/images#10

## 2026-10-27 — Consumers use the rolling tag, not a digest pin

Consumers use the rolling tag, not a digest pin

Consumers build FROM :0.1-affogato with no digest, so compatible rebuilds reach them on their next build (nothing bumps consumer digests; Renovate is npm-only). README, publish summary and CLAUDE.md updated; upstream bases stay digest-pinned for Dependabot.

PR: ilg-platform/images#9

## 2026-10-27 — Tag images with the platform release line (0.1-affogato)

Tag images with the platform release line (0.1-affogato)

Rolling :0.1-affogato (per image) + immutable :0.1-affogato-<sha7> replace :1 / :1-<sha7>, matching ilg-platform/github-actions. Both images republished under it (go-runtime sha256:7e98f0e1…, node24-runtime sha256:fcb6935c…). Legacy :1 tags to delete once audit-service re-pins.

PR: ilg-platform/images#8

## 2026-10-27 — PLTE-4

Add node24-runtime and share the image pipeline

Node 24 golden image on distroless nodejs24-debian13 (glibc, native modules) with datadog-init entrypoint and node on PATH. Shared reusable golden-image workflow + contract test, weekly upstream-freshness check (catches deprecated bases Dependabot can't), Dependabot groups serverless-init across images. Draft, stacked on #5.

PR: ilg-platform/images#6

## 2026-10-27 — fix(go-runtime): move off the deprecated distroless Debian 12 base

fix(go-runtime): move off the deprecated distroless Debian 12 base

Distroless stopped rebuilding Debian 12 (base-nossl-debian12:nonroot frozen 2026-08-21, deprecated-public-image-* tags); go-runtime moves to base-nossl-debian13. Contract unchanged, ships as :1.

PR: ilg-platform/images#5

## 2026-10-27 — docs: tell go-runtime consumers to restate USER nonroot

docs: tell go-runtime consumers to restate USER nonroot

Semgrep missing-user can't see the base image's USER, so consumers restate USER nonroot:nonroot. Found on audit-service#16. Draft.

PR: ilg-platform/images#4

## 2026-10-27 — Add go-runtime, the first golden image

Add go-runtime, the first golden image

Go runtime base on distroless base-nossl with Datadog serverless-init as entrypoint (in-container agent, no sidecar); contract test, secops scan, multi-arch publish as :1 / :1-<sha7>, Dependabot digest pins. Draft; merges after core-infra#15.

PR: ilg-platform/images#1
