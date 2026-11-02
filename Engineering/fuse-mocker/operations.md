---
tags:
- waypoint
- fuse-mocker
verified: '2026-10-01'
verified_sha: 15477b0
verified_paths:
- apps/api/internal/observability
- apps/api/Makefile
- apps/api/.golangci.yml
- .github/workflows
- iac
title: fuse-mocker — operations
---
# fuse-mocker — operations

## Deploy

**No PR flow — direct commits to `main` auto-deploy to dev.** `deploy.yaml`
triggers on push and now builds and deploys all three services (`apps/api`,
`apps/snap-api`, `apps/ui`); `code-quality` (per app) and `secops` trigger on
`pull_request` plus a nightly cron, `tf-plan` on `pull_request` only — so a
direct push ships with no CI gate having run against it (see [[known-context]]
— a known, tracked gap, not fixed as of this pass). Run the local gates
yourself before pushing:

```
cd apps/api      && make fmt-check && go build ./... && go vet ./... && TZ=UTC go test ./... && make lint
cd apps/snap-api && make fmt-check && go build ./... && go vet ./... && go test ./... && make lint
cd apps/ui       && pnpm lint:fix && pnpm lint && pnpm test && pnpm build
```

Cloud Run: three services behind one global HTTPS load balancer, own Mongo
Atlas cluster (shared by both Go services), own `api_key` Terraform output
(also in `~/.secrets`). No prod environment exists anywhere in this repo.
Of the ten confirmation-capture subscriptions, nine filter `confirmation_ready`
by recordType and `stock_adjustment_ready` is unfiltered (`pubsub-capture.tf`);
the PO/SO ready ones no longer have topics of their own. Both cutover flags are on (`api_serves_traffic`, `api_owns_background_loops`,
`iac/env/dev.tfvars`), so the Go API serves `/api/*` and `/events/*` and owns
the loops.

The **snap-api simulator rides the same load balancer and static IP** on its
own custom domain, `crackle.devtools.fuse.freightops.dev`: a serverless NEG +
backend service for snap-api, a host rule routing the whole host to it, a
**separate** managed cert attached to the shared HTTPS proxy via SNI (kept
apart from the mocker's own cert so adding it never force-replaces the
immutable-domains cert), and an A record to the LB IP.

Go dependency vulnerabilities are scanned by `secops.yaml` — a
`dependency_audit_api` job and a matching `dependency_audit_snap_api` job
(both `secops-dep-go.yaml@0.2-bonbon`), plus per-app Go SAST
(`code_scan_*`) and container-scan (`container_scan_*`) jobs. The dep audit is
deliberately its own job rather than a step in `api-code-quality.yaml`: a step
there is skipped when an earlier step in the same job fails, which is how a
HIGH `golang.org/x/text` advisory sat unreported for three days behind a
broken lint step. Keep it separate. `apps/snap-api` has its own
`snap-api-code-quality.yaml` (hand-rolled Go gates, path-filtered), mirroring
`api-code-quality.yaml`.

## Observability

Datadog, dashboard `r2r-76f-65i`. The Go API's log shape is a **contract**
with Datadog (`internal/observability/handler_test.go` is a
characterization test against it — a rename there is a silent production
regression no other test would catch): flat JSON, no `requestor` nesting,
`source: "go"` (the runtime, stated honestly — a message's *business*
origin rides under `messageSource`, never `source`). Logs must reach the
sidecar via `/shared-volume/logs/app.log` — a bare
`slog.NewJSONHandler(os.Stdout, …)` ships nothing to Datadog; `ResolveSink`
is what actually tees to the shared volume and must not be bypassed.

Metrics: dogstatsd, namespace `fuse`, unchanged names from the TS original
so the dashboard and any monitors kept working through the rewrite —
`fuse.mocker.publish{target,recordType,outcome}`,
`fuse.mocker.schedule_tick`, `fuse.mocker.load_run_message{mode,outcome}`.

`apps/snap-api` mirrors the same log-shape contract (flat JSON slog handler,
`source: "go"`, tee to `/shared-volume/logs/app.log` via its own `ResolveSink`)
and emits its own dogstatsd metrics under the same `fuse.` namespace —
`fuse.snapapi.request`, `fuse.snapapi.confirmation.emitted`,
`fuse.snapapi.queue.cleared`.

## Real failure modes

- **A `@gfs-bifrost/types` bump lands without regenerating the canonical
  layer**: nothing catches it. `make gen-check` detects it but no workflow
  runs it, and deploy doesn't wait on CI anyway, so a push ships stale
  generated Go structs silently. Run `make gen`/`make gen-check` yourself
  after any types bump that touches a canonical schema the mocker generates
  from. UNRESOLVED: whether gen-check's absence from CI is deliberate
  (`tools/canonschema` needs pnpm plus a GH Packages token for
  `@gfs-bifrost/types`) or just never wired up.
- **Two Cloud Run instances both running the scheduler/load engine**: fires
  every schedule twice. The API service owns them, so it is capped at
  `min=max=1` with `cpu_idle=false` while `api_owns_background_loops` is on —
  don't raise `max_instance_count` there, and don't restart the loops from
  `apps/ui`'s instrumentation hook.
- **A simulator row missing a column the poller's schema requires**: the
  poller's page parse fails and the confirmation (or its batch/expiry) goes out
  wrong or not at all, for any business whose SNAP host is the simulator.
  Check the poller's `Snap*Schema` against `apps/snap-api/internal/models/snap`
  before assuming the poller is at fault.
- **A response-shape change on any of the 14 `fuse-mcp`-facing endpoints**:
  breaks that consumer silently, with no signal on this side until the next
  time an agent calls the affected tool and gets something unexpected back.
- **`golangci-lint-action` pinned below v9**: v6 caps `version: latest`
  inside golangci-lint's v1 line (1.64.8), which can't parse `go 1.25.1`, so
  lint fails on every run *and* masks whatever the job would have run after
  it. `.golangci.yml` declares `version: "2"` — the action major has to
  match.
- **A generator constraint "simplified" without checking why it exists**:
  several (SNAP reference lengths, order-class namespacing, mandatory RGA
  fields) encode a real prior incident, not a guess — see
  [[known-context#snap-field-lore]].

## Verification oracles (dev)

- SNAP dev via the `snap` MCP: shipments by `SalesOrder eq '<MOCK-ref>'` or
  `CustomerRef`; receipts by `PurchaseOrder eq`.
- Dedupe holds via the `fuse` MCP's `dedupe-list`.
- Failures via replay-service's `/api/v1/failures?businessId=&recordType=`.
- Datadog: full-text search the `mock-` correlation id.
- **A zero-side-effect load sink exists on purpose**: publishing
  `confirmation_ready` with a reserved recordType (`dispatch` or `receipt`)
  matches no subscription filter, so messages publish for real (proving the
  publish path works) but are delivered to nobody — safe to use for load
  testing without polluting any real downstream queue.
