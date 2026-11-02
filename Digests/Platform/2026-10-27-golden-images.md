---
tags: [platform-announcement]
date: 2026-10-27
subject: golden images
channel: DM preview (target #ilg-platform C0B95TS1XTM, not yet sent)
confluence_url: https://globalfreight.atlassian.net/wiki/x/DACAF
confluence_status: draft preview page 343932940 (blog not yet published)
slack_dm: https://gfsdeliver-eng.slack.com/archives/D0990E3U2CA/p1793130332445409
status: drafted
---
# Platform announcement: Golden images

## Slack text
:mega: **New in Platform: Golden images** :tada:

Every Cloud Run service picks its own base image, patches its own CVEs and runs Datadog as a `serverless-init:latest` sidecar, and ~23 Go and Node repos across Bifrost and Tech Services wire that up themselves. The platform now ships one curated, centrally patched base per runtime, with the Datadog agent baked in as the entrypoint.

:white_check_mark: `go-runtime` and `node24-runtime`: distroless Debian 13, nonroot, no shell, amd64 + arm64
:white_check_mark: Datadog runs inside your container. No sidecar, no shared log volume: log to stdout and set `CMD`
:white_check_mark: Build `FROM :0.1-affogato`, no digest. Base patches and agent bumps land on your next build; a breaking change gets a new line (`0.2-bonbon`) you opt in to
:white_check_mark: audit-service runs `go-runtime` in prod, logs and metrics dual-shipping to both Datadog orgs, SIGTERM drain intact
:point_right: Go services can move now. Node is published, and dedupe-service is its first canary
:warning: Restate `USER nonroot:nonroot` (Semgrep can't see the base's), never set `ENTRYPOINT`, and Node services on `@gfs-bifrost/observability` need `^2.4.0` or they won't start
:warning: The shared `cloud-run` Terraform module still adds two sidecars, so hold off if you deploy through it

```
FROM europe-west2-docker.pkg.dev/ilg-platform-ec02/images/go-runtime:0.1-affogato
USER nonroot:nonroot
CMD ["/app/api"]
```

Moving a service? audit-service#16 is the worked example, and the full recipe is here :point_down:
:link: [Platform Announcement: Golden images](https://globalfreight.atlassian.net/wiki/x/DACAF)

## Claims and sources (verified 2026-10-27)
- Digests: `gcloud artifacts docker tags list`. go-runtime 0.1-affogato = sha256:7e98f0e1…fac591, node24-runtime = sha256:fcb6935c…b5b0, both -15bd788
- Rolling tag with no digest: images#9 + README "Registry and tags"
- audit-service prod: `gcloud run services describe audit-service-prod`, rev 00013-q78, one container, no volumes; Dockerfile FROM go-runtime:0.1-affogato
- In-container logs in prod: Datadog `service:audit-service @environment:prod`, dd.datadog_init_version:1.11.2, source:go, "shutdown signal received; draining"
- ILG dual-ship: audit-service#16 evidence (checked by Harry in the ILG org)
- fuse.audit.ingest intact: audit-service#16 evidence (dev)
- ~23 eligible repos: code search for serverless-init. gfs-bifrost 17 (5 Go, 12 TS; excludes repo-template and sandbox), ilg-tech-services 6 TS (excludes iac, mcp-template, knowledge-system, C# database-connector)
- cloud-run module sidecars: terraform-modules compute/cloud-run/main.tf, two serverless-init:latest containers
- observability 2.4.0: GitHub Packages, published 2026-10-27
- 45-day freshness: images/check-upstream-freshness.sh MAX_AGE_DAYS default
- Image sizes ~70MB / ~210MB: README

## Withheld
- gfs-sre and ilg-merak: code search returned nothing. Could be SAML-blind or genuinely none, so no count claimed
- No shoutout: every PR is Harry's, with no reviewers recorded
- node24-runtime not described as prod-proven: no consumer yet (dedupe canary not opened)
- audit-service#18 (tag-only FROM) is waiting at the prod gate; prod runs #17's build, same digest


## Update 2026-10-28: Node proven, prior art added

- **Node canary shipped**: gfs-bifrost/dedupe-service#167 merged as `1545e07`; prod revision `dedupe-service-prod-00049-27h` has one container and serves 100% of traffic.
- **Prod verified**:
  - A real duplicate was held at 09:42:59Z, logged with `source:nodejs`.
  - `fuse.dedupe.event.handled` comes from the new version in both dev and prod.
- **Dev verified**: a mock master_data record for HJF was forwarded, a same-correlationId resend was forwarded as a redelivery, and a fresh-correlationId resend was held as a duplicate.
- **New sharp edge (SIGTERM)**: under datadog-init, Node isn't PID 1, so SIGTERM kills it immediately (0.4s locally, against 12s and SIGKILL on node:24-alpine). The fix is Nest `enableShutdownHooks()`; with it, a request held open across SIGTERM still got 200.
- **Compose gotchas**: a bind mount over `/app` hides the built app, and a `CMD-SHELL` healthcheck has no shell to run in.
- **Scans**: Trivy finds no HIGH/CRITICAL in the base, and the 12 npm-CLI `.trivyignore` entries no longer match. The audit fix is gfs-bifrost/dedupe-service#168, open and unmerged.
- **Digests refreshed to `-152da38`**: go sha256:9d4f7599..., node sha256:c1d2aca5....
- **Prior art section added**: our worked examples, the Datadog in-container docs, distroless, the Cloud Run container contract and NestJS lifecycle events.
- **Drafts**:
  - Slack DM v2: https://gfsdeliver-eng.slack.com/archives/D0990E3U2CA/p1793180771819439 (about 1506 characters rendered).
  - Confluence preview: /wiki/x/DACAF, updated and ADF-verified.
- **Withheld**: the ILG-org copy for dedupe wasn't checked (no ILG Datadog access from here). No prod record has been *forwarded* on the new revision yet, only held.

## Published 2026-10-28
- **Approved by Harry.**
- **Confluence**: published as a PLTE page (not a blog; PLTE rejects blog creates), at https://globalfreight.atlassian.net/wiki/x/DACAF (page 343932940). ADF verified.
- **Slack**: draft is in Harry's #ilg-platform composer (draft Dr0CCMV5ALLB). Harry sends it.
- **Also shipped**:
  - dedupe-service#168 (audit fix), prod rev 00050-56s.
  - images#10 (README SIGTERM rule and #ilg-platform channel fix).
- **To delete by hand**: the probe draft blog in Bifrost, /wiki/x/AgCGF.
