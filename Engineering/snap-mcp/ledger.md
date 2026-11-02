---
tags: [waypoint, ledger]
title: snap-mcp — work ledger
---
# snap-mcp — work ledger

Agent-facing. Newest first. What meaningful work happened here, and the
context a future agent needs. Not a diary, not release notes, not a diff.

## 2026-11-02 — Clear the advisories failing the dependency audit and image scan

Clear the advisories failing the dependency audit and image scan

MCP SDK 1.27.1 to 1.32.2, zod to 4.6.7, raised override floors for body-parser, multer, follow-redirects and proxy-addr, and path-scoped trivy ignores for the npm-bundled undici in the base image. Main and the Renovate bump were both red.

PR: gfs-bifrost/snap-mcp#25

## 2026-10-02 — Cache SNAP clients per connection, not per host

Cache SNAP clients per connection, not per host

The snap MCP's client cache was keyed on SNAP host alone, so every read and snap-write to a shared host (ilg001/003/004/005) ran as whichever business called first. That was live on the hosted server: a STUBBLE call returned PURDYFIGG's outbound queue. The key is now host + credentials, and the circuit breaker stays per host. Verified locally over stdio and HTTP against real ilg005, main vs branch.

PR: gfs-bifrost/snap-mcp#23

## 2026-10-02 — Clear snap-mcp's nightly DevSecOps failure: axios 1.20 and base-image CVE ignores

Clear snap-mcp's nightly DevSecOps failure: axios 1.20 and base-image CVE ignores

Bumps axios 1.18.1 → 1.20.0 to clear six HIGH advisories (dependency_audit), and adds .trivyignore entries for brace-expansion and undici CVEs that ship in the base image's bundled npm CLI, not in our app deps (image_scan). axios 1.20 declares a unique symbol in index.d.cts, so ts-jest saw two incompatible AxiosInstance types. SnapApiService now derives its client type from SnapClient.create().build() (12c149c). Verified: jest 40/40, tsc and biome clean, and a live read of products and kits from the dev SNAP simulator on axios 1.20, including the 401 and 404 paths. snap-mcp has no dev environment, so there was no deploy. Open, awaiting review.

PR: gfs-bifrost/snap-mcp#22
