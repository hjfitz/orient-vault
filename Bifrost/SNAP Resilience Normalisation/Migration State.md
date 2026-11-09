---
title: SNAP Resilience Normalisation — Migration State
programme: snap-resilience-normalisation
status: active
owner: Harry Fitzgerald
services:
- pkg-node
- snap-adapter
- snap-queue-polling-service
- observability
created: '2026-11-05'
updated: '2026-11-09'
tags:
- bifrost
- migration-state
---
# SNAP Resilience Normalisation — Migration State

## Unit status
Legend: ⬜ not started · 🟨 in progress · ✅ merged · ⛔ blocked · ⏸ deferred · ❌ dropped · 🔄 rescoped

### A — `@gfs-bifrost/resilience` 0.2.0 (pkg-node, one PR, one publish)
| Unit | St | Summary | Deps | Risk | Tier | PR | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **N1** | ✅ | Port timeout semaphore + token bucket | | low | sonnet/medium | pkg-node#302 | Verbatim ports from `apps/snap-adapter/src/shared`: `Semaphore.acquire(timeoutMs?)`, `SemaphoreAcquireTimeoutError` and `TokenBucket`. Port the adapter's 3 timeout specs and 6 token-bucket specs. The 0.1.0 specs stay green. Also ports `normalizeHostKey` from `apps/snap-adapter/src/shared/snap-host-key.ts`, with specs for case, trailing slash, the `/api` path dropped to the origin, and the non-URL fallback. |
| **N2** | ✅ | Breaker options: `halfOpenAfterMs`, `countsAsSuccess` | | med | sonnet/medium | pkg-node#302 | Additive, with defaults unchanged. Verify: the 0.1.0 breaker specs pass unchanged with the options unset, and the default path emits no extra callbacks. A 30s constant blocks at 29.9s and probes at 30s. `countsAsSuccess` resets the consecutive count. |
| **N3** | ✅ | `canAttempt(host)` gate | N2 | high | opus/high | pkg-node#302 | False when isolated, when open inside the cool-off, **or while a half-open probe is in flight**. A pre-slot gate then rejects instead of holding slots behind the probe (R1). Specs: flips true after the cool-off with no `execute()`; a gate built on it never leaves a circuit stuck open; it returns false during the probe. |
| **N4** | ✅ | `state(host)`, `snapshot()`, `onStateChange(from,to)` | N2 | low | sonnet/medium | pkg-node#302 | Readout for periodic gauges. `snapshot()` doesn't create breakers. `onStateChange` carries `from`, so the apps can count an open only on closed→open (R6). |
| **N5** | ✅ | Release resilience 0.2.0 + snap 0.4.2 | N1,N3,N4 | med | sonnet/low | pkg-node#302 | snap 0.4.2 only refreezes its resilience dep. Add a **new** resilience row to pkg-node's root CLAUDE.md table, plus org changelog rows. Smoke-test snap-mcp and snap-mcp-server on 0.4.2. CI: "Code Quality - Resilience" and "Code Quality - Snap" green. Clears G2. |

### B — snap-adapter app
| Unit | St | Summary | Deps | Risk | Tier | PR | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **A1** | ✅ | Swap local primitives for the package | N5 | low | sonnet/medium | snap-adapter#321 | Refactor, no behaviour change. Delete the local copies and specs. `pnpm why @gfs-bifrost/resilience` shows one version, which `instanceof` in `classify-snap-failure` depends on. Dev deploy plus one `mock-send` create. |
| **A2a** | ✅ | Transport wrapper at the axios `adapter` hook, parity | A1 | high | opus/high | snap-adapter#322 | `guardSnapTransport`: `canAttempt` → token → slot → `breaker.execute(base)` → release in `finally`. Parity: `shouldTrip` is undefined or ≥500, **no 429 yet**, and `countsAsSuccess` covers a non-transient 4xx.<br>`onDispatch` **mutates `cfg` in place** (R6). Opens are counted only on closed→open (R5).<br>Behaviour changes for sign-off: single-probe half-open, and the slot released before retry backoff.<br>Specs: 5×503 opens; a 404 resets; probe at 30s; a **hung probe makes waiters reject `circuit_open`, not hold slots**; a retry re-passes the gates; a slot timeout reaches the classifier as `slot_timeout`; the success-path latency value is set. Prod deploy gated on G1. <br>**Shipped (#322) behind `SNAP_TRANSPORT_GUARD` (`interceptors` default, `adapter` new).** The prod deploy is a no-op. Still to do after G1: flip it (a tfvar, alongside A2b's), soak, then delete the interceptor path and `SnapCircuitBreaker`. The live breaker-open check is left to A3's unreachable-host dev test (the simulator only faults writes). |
| **A2b** | ✅ | 429 trips the breaker, behind a switch | A2a | med | sonnet/medium | snap-adapter#323 | `SNAP_CB_TRIP_ON_429` (tfvar, default false), flipped after G1. Ship the monitor 337501612 message update ("also opens on 429") with the flip. Verify: a spec, and after the flip per-host 429 counts vs `snap.circuit_opened` (the decision record's confirmation signal). Also check `circuit_open` nacks against the 30-delivery budget. |
| **A3** | ✅ | Dual-emit unified breaker metrics | A2a,N4 | low | sonnet/medium | snap-adapter#325 | Adds `snap.breaker.opened`, `snap.breaker.state` (per dispatch and on transitions, since adapter CPU throttles between requests) and `snap.breaker.rejected`. The old names stay unchanged. Verify on dev with a business pointed at an unreachable host (a network error trips the breaker). 503/429 coverage is by spec only. |
| **X1** | 🟨 | Flip the switches (Terraform, after G1) | A2a,A2b,Q1,Q2b,Q3a,Q5 | high | opus/high | snap-adapter#331 | One Terraform change per app; share the plan first.<br>**snap-adapter:** `SNAP_TRANSPORT_GUARD=adapter`, `SNAP_CB_TRIP_ON_429=true`, and update monitor 337501612's message ("also opens on 429").<br>**poller:** `SNAP_REQUEST_TIMEOUT_MS=120000` (the 30-day data supports it), `SNAP_BREAKER_SINGLE_PROBE=true` (the config needs the timeout), and `SNAP_NORMALISE_HOST_KEY=true` together with re-pointing the latency monitor groups and the dashboard `$snap_host` (that clears G3).<br>`SNAP_MAX_CONCURRENT_REQUESTS` waits for Q3b. Each switch reverts by its tfvar alone. |
| **X2** | ⬜ | Delete the adapter's interceptor transport path | X1 | med | sonnet/medium | | Once `SNAP_TRANSPORT_GUARD=adapter` has soaked in prod, remove the interceptor gates, `SnapCircuitBreaker` and the switch, leaving one transport path. That's the prerequisite for S2. |

### C — snap-queue-polling-service
| Unit | St | Summary | Deps | Risk | Tier | PR | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **Q1** | ✅ | Per-request SNAP timeout | | med | sonnet/medium | snap-adapter#324 | Add `withTimeout` to the poller's `AxiosBuilder`. Default **in code**, so no terraform. Floor 120s for adapter parity (R7). Record the 30-day `snap.poll.request.latency.max/p95` value in the PR. Stock sync's own 20s timeout still overrides it. A spec shows confirmation and outbound-queue calls carry `timeout`. Check the run still fits the 420s collection deadline given serial vs parallel calls. Behaviour change: hangs now time out. Prod gated on G1. |
| **Q2** | ✅ | Breaker → `PerHostCircuitBreaker` | | med | sonnet/medium | snap-adapter#326 | Adds the `@gfs-bifrost/resilience` dependency; the poller has none today, only cockatiel direct. Keep the breaker at `SnapApiHttpClient.send()`, which counts per logical call; `fetchKits` relies on it. Keep the raw-host key (normalising it is Q5). The exponential half-open is kept for parity. Behaviour change: re-probe on every poll becomes a single probe. Re-point the 14 `circuit-breaker.spec.ts` cases; `fetchKits` specs green. Can use 0.1.0, so no G2. |
| **Q2b** | ✅ | Poller single-probe + late-failure guard, behind a switch | Q2 | med | opus/high | snap-adapter#329 | Rescoped out of Q2 (2026-11-06) so that Q2 ships as pure parity. Add `tryAdmit` single-probe and #322's late-failure guard (a pre-open request's failure must not re-open a half-open circuit) behind one env switch, default off, flipped after G1. Keep per-logical-call counting at `send()`; `fetchKits` relies on it. |
| **Q3a** | ✅ | Per-host concurrency cap, code only | N5,Q2 | med | sonnet/medium | snap-adapter#330 | `guardSnapTransport` with the semaphore only (no breaker; it lives at `send()`). Semaphores are module-level per normalised host. Config defaults are effectively unlimited, so this is a no-op until Q3b. Specs: a bare `axios(err.config)` retry passes the wrapped adapter (peak in flight ≤ cap); the slot is free during backoff. `onDispatch` re-stamps the request start. |
| **Q3b** | ⬜ | Cap values + `max_instance_count` (IaC) | Q3a | high | sonnet/low | | Values come from the poller's per-host concurrency measured after Q3a. Share the terragrunt plan before apply. Watch `confirmation_run.deadline_reached` and run duration after. |
| **Q4** | ✅ | Dual-emit unified breaker metrics | Q2,N4 | low | sonnet/medium | snap-adapter#327 | Same names as A3. `cpu_idle=false`, so a 10s `snapshot()` gauge is reliable here. `snap.breaker.rejected` carries `snap_host` (replacing the untagged `snap.poll.skipped_circuit_open`). |
| **Q5** | ✅ | Normalise the host key: breaker key + `snap_host` tags | Q2 | med | sonnet/medium | snap-adapter#328 | Origin, lowercased, same as the adapter. Behaviour change: businesses on hosts that differ only in case or slash share a breaker. Tag-value churn: the latency monitor's groups (`snap_api_latency_threshold_breached`) and the dashboard's `$snap_host` dropdown (5 poller queries). Verify the poller and adapter tag values match in Datadog. |

### D — Metric cutover (observability, then snap-adapter)
| Unit | St | Summary | Deps | Risk | Tier | PR | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **O1** | ⬜ | New monitors + widgets on `snap.breaker.*` | A3,Q4,Q5 | med | sonnet/medium | | Alongside `snap_host_circuit_opened` and `snap_poller_host_circuit_opened`. Queries filter on `service` (the adapter emits both `snap-adapter` and `snap_adapter`). The plan must show notification routing **identical** to the old monitors. After apply, OK, not No Data. Gated on G3. |
| **O2** | ⬜ | Delete old monitors, widgets and message text | O1 | med | sonnet/low | | Includes old-name prose in `monitors.snap-adapter.tf` messages (~:604, :729). Plan shows only destroys and edits. Gated on G4. |
| **O3** | ⬜ | Stop emitting old metric names | O2 | low | sonnet/low | | snap-adapter repo, both apps. Delete the poller's key→raw-host map, if any. Specs assert the old names are absent. |

### E — Phase 2: `@gfs-bifrost/snap` (planned when Phase 1 lands)
| Unit | St | Summary | Deps | Risk | Tier | PR | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **S1** | ⬜ | Client helpers | A3 | med | sonnet/medium | | `SNAP_ENDPOINTS`, `isTransientSnapStatus`, `assertSnapWriteOk`. **First**, add a classifier branch running `collectSnapFieldErrors` on `SnapWriteRejectedError.body`, so field errors aren't lost (G5). |
| **S2** | ⏸ | Lift the transport into `@gfs-bifrost/snap/http` | S1,X2 | med | sonnet/medium | | `AxiosBuilder.withResilience(...)`. Retry options must cover the poller (408, PATCH with no response, jitter) before it can switch. |
| **S3** | ⏸ | Types per entity + parsing breakglass | S2 | high | opus/high | | `SNAP_RESPONSE_PARSE_MODE=strict\|tolerant` (app config, Cloud Run env; the package takes it as an option). **Strict applies only to 2xx success bodies, never error envelopes.** Shadow parse first (`snap.response.parse_failed`). Adapter write-path reads default to tolerant. A strict failure on the create path is never permanent without checking the deduper. One entity per PR, live-verified via the snap MCP. |
| **S4** | ⏸ | Delete `@gfs-bifrost/types`' legacy `snap/` | S3 | med | sonnet/low | | A `types` major. Check fleet consumers first. |

## Gates
- [ ] **G1 — Purdy & Figg peak over** — blocks X1, Q3b. Flipping the behaviour switches in prod (A2a, A2b, Q1, Q2b, Q3a, Q5) happens in X1. Clears when P&F daily orders are back near baseline (forecast ~12k by 2026-11-12) or on Harry's call. Code may deploy to prod with every switch at today's behaviour.
- [x] **G2 — resilience 0.2.0 and snap 0.4.2 published** — blocks A1 and Q3a. Clears when `npm view @gfs-bifrost/resilience@0.2.0 version` and `@gfs-bifrost/snap@0.4.2 version` both resolve.
> SUPERSEDED 2026-11-06 — Q5 shipped behind `SNAP_NORMALISE_HOST_KEY` (off). G3 clears only once that switch is **on** in prod (X1), not merely once Q5 is deployed.
- [ ] **G3 — dual-emit live in prod** — blocks O1. Clears when A3, Q4 and Q5 are all deployed to prod. Q5 must be in, or the old and new series differ on tags alone.
- [ ] **G4 — parity soak** — blocks O2. Clears after at least 7 days of O1 monitors firing in step with the old ones, **with at least one real breaker open per service**, or a notebook backtest of the new queries over the 19/21 Oct opens.

## Risks
- **R1 ★ Half-open probe starves slots** — If waiters held slots behind a hung 120s probe, everything else would slot-time out and spend delivery attempts (the FUSE-1147 failure mode). Mitigation: `canAttempt` is false while a probe is in flight, and the gate sits before the slot. Covered by the A2a hung-probe spec — open.
- **R2 ★ 429 opens the breaker under throttling** — A 429 storm opens the circuit and nacks a healthy backlog. Mitigation: A2b ships behind a switch defaulting off, flipped after G1, then 429s are compared with opens per host — open.
- **R3 ★ Combined per-host SNAP load** — Adapter 15 per host, plus the uncapped poller, plus snap-mcp, against a comfortable ~10–20 fleet-wide. Mitigation: Q3a ships as a no-op, the poller's real per-host concurrency is measured, then Q3b sets the cap and `max_instance_count` from data — open.
- **R4 Monitor blindness during the rename** — Mitigation: dual-emit, identical routing checked in O1's plan, and the G4 soak before any delete — open.
- **R5 Inflated open count** — cockatiel's `onBreak` may re-fire on a failed half-open probe. Today's adapter counts once per open, and monitor 337501612 alerts on any open. Mitigation: count only closed→open (N4 `onStateChange`), with an A2a spec — open.
- **R6 Request latency silently reads ~0** — In the adapter hook, `response.config` is the same object handed in, so a stamp written to a copy is lost. Mitigation: mutate in place, plus a latency spec (A2a) — open.
- **R7 Poller timeout re-sends to a degraded SNAP** — A short timeout with 2 retries re-sends slow `$top=1000` reads to a struggling SNAP. Mitigation: 120s floor (Q1) — open.
- **R8 Phase 2 strict parsing discards real errors** — Mitigation: the breakglass env var, strict only on 2xx bodies, the classifier branch first, shadow mode — standing.

## Decision log
- **2026-11-09** — **snap-adapter attachment-completion fix handed over to hjf.shell.platform.ilg.software** (out-of-programme-unit follow-up to tonight's ilg005 incident: orders acked as `already_in_wms` skip their post-create attachments; 30 of 35 affected shipments backfilled in Snap, 5 despatched left). Record: [[Handovers/2026-11-09-snap-adapter-attachment-completion]]. Not an X1 step; X1 stays PR #331.
- **2026-11-06** — **Phase 1 code is complete** (A2a–A3 and Q1–Q5, including Q2b and Q3a, all in prod with every switch at today's behaviour). What's left of phase 1 is the X1 flip after G1, then X2, O1–O3 and Q3b. Both poller switches that can wedge a host (`SNAP_BREAKER_SINGLE_PROBE`, `SNAP_MAX_CONCURRENT_REQUESTS`) **refuse to start without `SNAP_REQUEST_TIMEOUT_MS`**. That's a config-schema rule, proved on dev (the revision failed its startup probe with the reason, and traffic stayed put).
- **2026-11-06** — **Phase 2 resequenced on real dependencies** (Harry: "a switch flip is a good breakglass"). **S1 no longer waits for O3**: the client helpers have nothing to do with the metric cutover. It depends only on A3 and can start now, following the same discipline (parity, or behind a switch). **S2 waits for X2**, so only one adapter transport path gets lifted. S3's `SNAP_RESPONSE_PARSE_MODE=strict|tolerant` (default tolerant) is the breakglass Harry asked for, the same switch pattern as phase 1.
- **2026-11-06** — **Q2 rescoped to a pure parity swap** (snap-adapter#326). The single-probe change and the late-failure guard moved to a new unit, Q2b, behind a switch. Q2 shipped to prod on the day of the P&F peak with no behaviour change. The 14 existing breaker specs passed unchanged against `PerHostCircuitBreaker`.
- **2026-11-06** — Observation (dev, old and new implementations alike): the `tests.com` dev business fails every poll with network errors, yet its poller breaker **never opens** (264 failures in 3 h, no `circuit_breaker.state` points). The likely cause is low per-instance volume (about one logical call per tick, 2 instances) plus instance churn resetting in-memory state. Check this before relying on the poller half of A3/Q4's "unreachable host" dev verification. In prod, with warm instances, it may not hold.
- **2026-11-06** — **`snap.breaker.state` encoding is a cross-service contract: closed 0, half-open 0.5, open or isolated 1**, per `snap_host`, emitted on every request and every transition (A3). It extends the poller's existing `circuit_breaker.state` 0/1, so a `>= 1` monitor means "refusing requests" in both services. Q4 must use the same values. `snap.breaker.opened` counts closed→open only, and `snap.breaker.rejected` counts each request an open circuit turns away.
- **2026-11-06** — The Q1 flip value comes from data. Prod `snap.poll.request.latency` over 30 days had a p95 averaging 1.35 s and a max of 127–140 s per host. At hourly resolution the only hour over 100 s was the 2026-10-19 15:00 SNAP outage (151 network failures). **120 s is safe at the flip**: only outage-time calls exceed it.
- **2026-11-06** — The poller prod deploy of Q1 (snap-adapter#324) also carried **FUSE-1329 (ba382a8), ahead of its QA, on Harry's explicit waiver**. It had been parked at the poller gate in Ready for QA. The 8-minute prod smoke was clean, but no FGR flowed in that window.
- **2026-11-06** — A2b (#323) makes the 429 rule apply in **both** transport modes, so `SNAP_CB_TRIP_ON_429` is never silently a no-op if flipped before `SNAP_TRANSPORT_GUARD`. The live breaker-open was produced on dev with `SNAP_CB_CONSECUTIVE_FAILURES=2` plus a simulator 429 fault (a PUT and its retry give two consecutive failures). That's the reusable recipe while the simulator can only fault writes.
- **2026-11-06** — A2a puts the **whole** new transport path behind one switch, `SNAP_TRANSPORT_GUARD` (default `interceptors`), not only its behaviour changes. A parity refactor of the write path's gates can't be flagged piecemeal, and it shipped on P&F's first peak day. The flip and the legacy deletion come after G1 (snap-adapter#322).
- **2026-11-06** — A2a guard: a request dispatched while closed that fails after the circuit opened is kept out of cockatiel's accounting. Otherwise cockatiel's Closed branch calls `open()` and clobbers a half-open probe, leaving the circuit open after SNAP recovers. Queued callers re-check the state in-slot and never wait on a probe.
- **2026-11-06** — Observation (dev, both modes): **a write-only SNAP outage never opens the adapter's breaker.** Each delivery's successful read resets the consecutive count. It's parity with today's breaker, not a regression; whether reads should reset it is a question for A2b or later.
- **2026-11-05** — N3 shipped as `tryAdmit(host)`, not `canAttempt`. The gate hands out one probe ticket per cool-off, which lapses after another cool-off. A pure check let every caller arriving between the gate and `execute()` through to wait on cockatiel's probe holding a slot (R1). `normalizeHostKey` also falls back for opaque `"null"` origins (scheme-less `host:port`). Published 15:57Z (pkg-node#302).
- **2026-11-05** — Phase 1 and the eventual `@gfs-bifrost/snap` target. Resilience goes through `@gfs-bifrost/resilience`, and a 429 trips the breaker. `@gfs-bifrost/snap` is the eventual target, behind a response-parsing breakglass env var (Harry). See the decision record linked in the Overview.
- **2026-11-05** — A programme, not one plan. Four services and about 20 units. Each unit gets its own plan when it's picked up.
- **2026-11-05** — Wrap at axios's `adapter` hook rather than add an interceptor gate API to the package. That keeps cockatiel's real `execute()`, makes slot release automatic in `finally`, catches bare-axios retries, and keeps the package axios-free.
- **2026-11-05** — Each app keeps its breaker counting level: the adapter per attempt, the poller per logical call. `fetchKits` stops at `consecutiveFailures − 1` kit failures and relies on per-call counting.
- **2026-11-05** — **Every behaviour change ships behind an env-var switch defaulting to today's behaviour. Code may go to prod before the peak is over; switches flip after G1** (Harry). This covers single-probe half-open (A2a, Q2), the poller timeout (Q1), the cap (Q3b), host-key merging (Q5) and 429 tripping (A2b).
- **2026-11-05** — `normalizeHostKey` moves into `@gfs-bifrost/resilience` (N1), since it is the per-host budget key and two copies would drift. This amends the decision record, which had it app-local. It was my recommendation and Harry didn't object; revisit if he does.
- **2026-11-05** — The poller's concurrency budget is set from measurement, not up front. Q3a ships as a no-op, and Q3b's values come from the poller's measured per-host concurrency.
- **2026-11-05** — Doc staleness found by review, to fix when the first poller unit signs off: poller `architecture.md` G2 (the Redis claim was removed by #308) and `operations.md` ("trips only on 5xx/network"; it also trips on 429).

## Scar tissue
- **cockatiel records an outcome against the state the call started in.** A pre-open request failing during half-open re-opens it unless it's kept out (A2a guard). Any wrapper around `PerHostCircuitBreaker` with long-running calls needs the same care (the poller, Q2).
- **Never match a SNAP error body by fixed shape** (snap-adapter G5). A schema-matched parser has discarded the real error twice (FUSE-599).
- **Breaker → rate limit → slot, with caps far below SNAP's ~50-concurrent meltdown** (snap-adapter G6, May 2026 incidents).
- **A slot timeout is transient and never happens inside `breaker.execute()`.** cockatiel closes a half-open circuit on a non-tripping failure, so a slot timeout during a probe would close it.
- **The poller's breaker counts per logical call.** `fetchKits` is built on that.
- **`snap.circuit_opened` and `snap.circuit_breaker.state` are read by live monitors.** Never rename without dual-emit first.
