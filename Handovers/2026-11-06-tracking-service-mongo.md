---
tags: [handover]
status: resumed
workstream: tracking-service Firestore → MongoDB Atlas (Tracking Service programme, group D)
programme: Tracking Service
repo: gfs-bifrost/tracking-service
from: laptop
to: hjf.shell.platform.ilg.software
session_id: c36659b6-edee-4035-ab29-ffd89416a0e8
resumed_by: "3aa25172-6c08-47b7-801e-82d3744ffce2"
updated: 2026-11-06T15:22Z
---
# Handover: tracking-service Firestore → MongoDB (group D)

## Where things stand

- **Why this started.** On 2026-11-06 at 09:10–09:16Z, prod Firestore throttled 536 commits with `RESOURCE_EXHAUSTED` during PURDYFIGG's 5-minute reap bursts. They surfaced as `InvalidArgument: transaction has expired`, because the gapic Commit retry reuses the dead transaction id. Pub/Sub redelivery healed it and nothing was dead-lettered. Harry decided to move persistence to MongoDB Atlas. That supersedes his 2026-10-19 "stay on Firestore" decision, and it's recorded in [[Bifrost/Tracking Service/Migration State]].
- **`main` is `a97baca`.** It carries D1 (#18), D2 (#22, #23), D3 (#20), D4 (#21) and D6 (#19).
- **Prod and dev both serve image `44734ac` (D1).** D1's prod Terraform apply (Deploy run 42226342798) is still running its field operations: 6 of 9 were exempt at 15:19Z, at about 6 min each.
- **One Deploy run, 42239748734 for `a97baca`, is pending behind it.** It ships D2–D4 code (inert in prod: `STORE` defaults to `firestore`, Firestore ignores marks) **and creates the Atlas clusters** (D6).

| Unit | Delivered | PR | State |
|---|---|---|---|
| D1 | 9 unqueried fields exempt from Firestore indexing (stopgap; tests the index-hotspot hypothesis) | #18 | dev done and verified; prod apply running |
| D2 | `store.Marks` on every write; the memory store serves stats by summing marks (recompute-equivalent, G5) | #22, #23 | merged, deploy pending |
| D3 | store tests run against every backend (`eachBackend`, `liveCounters` gate) | #20 | merged, deploy pending |
| D4 | `internal/storeopen`, `STORE`/`MONGODB_URI`/`MONGODB_DATABASE`, a Mongo 8.0.13 replica-set harness (`make test-mongo`), non-required `api-mongo` CI | #21 | merged, deploy pending |
| D6 | Atlas M10 per env (backup and PIT on, termination protection in prod), `readWrite` user, connection string as a Terraform local (not wired to the service yet) | #19 | merged; dev plan agreed by Harry; prod plan to be checked in run 42239748734 |

## In flight
| Work | PR / branch | State | To close it |
|---|---|---|---|
| D1 prod apply | run 42226342798 (`44734ac`) | `terraform-apply-prod` in progress, field operations running | Wait for success, then run `gcloud firestore indexes fields describe <field> --collection-group=<c> --database=tracking-service --project=bifrost-prod-global1` for all 9 fields: each should show 0 indexes. Write the evidence into plan `tracking-service/plans/exempt-unqueried-fields-from-firestore-indexing` (inc 3), then `wp tick` inc 3 after the soak. |
| D1 soak (G3) | — | starts when the prod apply completes | 48 h of reap bursts. **Bar (agreed): zero `resource_exhausted`** on `gcp.firestore.api.request_count{database_id:tracking-service}` in burst minutes. Baseline: 536 at 09:10–09:16Z on 2026-11-06. Record the result on G3 in the Migration State, then sign off the D1 plan (`waypoint-work`, Step 5). |
| Batch deploy | run 42239748734 (`a97baca`) | pending behind D1 | When it reaches `terraform-prod`, read the `terraform-plan-prod` log. It must show **only** `mongodbatlas_advanced_cluster.tracking` (`tracking-service-prod`, `termination_protection_enabled = true`), `mongodbatlas_database_user.tracking`, `random_password.mongodb_user_password`, and the Cloud Run image bump; **0 destroy**. Then approve through `gh api -X POST repos/gfs-bifrost/tracking-service/actions/runs/<id>/pending_deployments -F "environment_ids[]=23493256883" -f state=approved`. Harry agreed this chain on 2026-11-06. If the plan differs, stop and ask. Afterwards tick D6 done (`wp programme tick "Tracking Service" --unit D6 --status done --pr "tracking-service#19"`) and D1 too once its soak passes. |

Stale local worktrees on the laptop (nothing unpushed matters): `agent-*`, `exempt-unqueried-firestore-fields`, `skip-identical-republishes`, `tracking-service-mongo`. All branches are merged or unused, so they're safe to remove later.

## Waiting on Harry
- **Nothing blocking.** Already decided: Mongo, not Postgres; G4 (import the frozen `duplicates` history as a frozen collection); G5 (served stats recompute-equivalent); G6 (two M10s, connection string as a Terraform env var); G7 (`internal/storeopen`, `cmd/import-mongo`, `cmd/parity` approved); a **hard-cut** cutover; and a **`seen` collection**.
- **Give Harry the dedupe answer** (already verified, see Closed). Bottom line: the businessId + customer ref rule holds today. **Prod: 89,156 shipments, all keyed by customer ref, 0 duplicate groups, 0 fallback docs; dev: 34,294, same.** Prod has **no returns collection at all**. The latent split paths are in R14, and the Mongo must-haves are in the D5 row.
- **Owed by a human, not blocking:** a prod `recompute-stats -dry-run` to size G5's drift (G5 policy: a human runs prod tools).
- **Before D7:** confirm the shared Atlas project allows Cloud Run egress. No Fuse Atlas stack declares an access list or PrivateLink.

## Next up
1. **D5 Mongo store.** Its own Waypoint plan (`waypoint-programme`, plan D5); opus/high.
   - Design: the D5 row in the Migration State plus `Handovers/2026-11-06-tracking-service-mongo.draft-design.md`. It is the planner's draft; where they differ, the Migration State wins.
   - Must have:
     - each write is a transaction over one record's docs only;
     - a `seen` collection (every messageId including copies and bulk `-i`, unique, 8-day TTL);
     - `ErrNoMarks` on a non-noop write without marks;
     - marks aggregation copied **exactly** from the memory store (`store/memory_marks.go`, `store/marks.go` `CapReasons`/`Tally`);
     - implement `storeopen.Backend`: `Store` plus `Maintenance` (`ShipmentIDs`, `ReturnIDs`, `ReadCounters`, `ReplaceCounters`);
     - add a Mongo entry to `store/backend_test.go`;
     - **the 7 must-haves in the D5 row** (the `seen` key is the per-item event id; the insert goes in the transaction; skip it for an empty eventID; composite events `_id`; retry on DuplicateKey; return transactions patch linked shipments with `upsert:false`; no shared docs), plus `_id` = `{BIZ}__base64url(key)` and a partial unique `{businessId, customerRefNorm}`;
     - read the evidence in `Handovers/2026-11-06-tracking-service-mongo.dedupe-findings.md`.
   - Sub-increments a–e are in the D5 row.
2. **D7 rollback stack plus hard-cut runbook.** It can start in parallel once D6 is in prod.
3. **D8 `cmd/import-mongo`, D9 `cmd/parity`** (after D5).
4. **D10 dev rehearsal of the hard cut.**
5. **D11 prod hard cut.** Gated on G9: a human runs the prod import and parity.

## How work is done here
- **Programme:** `Bifrost/Tracking Service/Migration State.md`, group D (units, gates G3–G11, risks R7–R12, decision log). Drive it with `waypoint-programme`. Service docs are at `Engineering/tracking-service/`; the ledger needs an entry per PR, `--programme "Tracking Service"`.
- **Repo rules:** `tracking-service/CLAUDE.md`, `apps/api/CLAUDE.md`, `iac/CLAUDE.md`, `~/code/CLAUDE.md` (worktrees, branch `hjf/<desc>` with no ticket, PR template, `#bifrost-forge` bundled post per merge batch).
- **Gates:**
  - `make fmt-check vet lint test-race test-emulator` and `make test-mongo` in `apps/api`, and `terraform fmt -check -recursive iac`.
  - Parallel worktrees need `EMULATOR_PORT`, `PUBSUB_EMULATOR_PORT`, `EMULATOR_NAME` and `PUBSUB_EMULATOR_NAME` overridden. `make test-mongo` already picks a free port and project name.
  - Set `MISE_TRUSTED_CONFIG_PATHS=<worktree>`, or mise falls back to go 1.25 and lint fails.
- **Merging:** Harry said "merge them up and deploy them" for this batch. Each new merge still needs the normal bar: CI green including the required `add-tf-plan-output`, a `review-panel` review, and **a local check of the combination with current main** (branch protection is `strict=false`, so GitHub won't catch a semantic conflict). The no-review window in `~/code/CLAUDE.md` expired 2026-11-06.
- **Terraform:** plan-then-proceed. Share the plan, and once Harry agrees, merge and approve `terraform-prod` without re-asking for that change. Always read the prod plan in the Deploy run before approving.
- **Prod tools** (`recompute-stats`, backfills, import, parity against prod) are run by **a human**, never an agent (G5).
- **Background agents can't merge** (auto-mode classifier denial, a memory). Merge in the foreground.

## On the target
Checked 2026-11-06 ~15:15Z on `hjf.shell.platform.ilg.software` (kernel 7.2.14):
- **Tools:** claude 2.1.319, gh, gcloud, git, go, node, docker, python3, jq and mise are present. pnpm isn't, and isn't needed. terraform 1.9.0 and go 1.26.9 come through `mise install` in the repo.
- **Accounts:** `gh` is logged in as `harry-fitzgerald_gfsdev` and sees the merged PRs #18–#23 and pending run 42239748734. `gcloud` is `harry.fitzgerald@gfsdeliver.com` and can read `bifrost-prod-global1`.
- **Repo:** `~/code/fuse/tracking-service` was **cloned during the handover** (at `a97baca`), with `mise.toml` trusted.
- **Unattended running:** `~/.claude/.credentials.json` is present and `defaultMode` is `auto`.
- **Sync:** the vault, skills and memories were synced, and this record, the Migration State, the ledger and session-handover match by hash. The draft-design, the dedupe script and the D1 plan match after the sync's `/home/harry` → `/home/harry` rewrite.
- **MCP:** the `fuse` and `ado-local-mcp` servers were kept with the VM's own config. OAuth servers (Atlassian, datadog, slack, ado-remote-mcp) need `/mcp` once there if they aren't already signed in. **Restart Claude on the VM** to load them.
- **Not there:** the laptop's worktrees and background agents. All their work is pushed and merged; nothing is unpushed.

## Gotchas
- **`tf-plan` PR checks fail on the dev state lock** whenever a Deploy dev apply or another `tf-plan` is running. Re-run them **one at a time** (`gh run rerun <id> --failed`).
- **The Deploy workflow is `concurrency: cancel-in-progress: false`.** A merge while a run is in flight queues, and a newer pending run replaces the older pending one. Merging several PRs back to back yields one deploy of HEAD, which is fine.
- **Firestore field exemptions on populated collections take about 6 min per field**, one at a time. The Deploy run stays open about an hour; don't push to `main` meanwhile.
- **`mongo:8.0` latest won't start on Linux ≥6.19** (SERVER-121912; runners and both machines are on 7.0). Pin `mongo:8.0.13`. The laptop's local `mongo:8.0` tag now points at the broken image, which affects `oms-mongodb` on its next recreate.
- **Compose projects in a directory named `api` collide across repos.** Every compose file needs an explicit `name:` (fixed in #21; it once clobbered mangaverse's `api-mongo-1`, since restored).
- **Datadog logs carry `env:serverless`.** Filter on `configuration_name`. `fuse.tracking.*` undercounts, so verify with `gcp.*` metrics.
- **A record remembers only its last 64 copy ids** (`CountedIDs`). That's why the cutover is a hard cut and Mongo gets `seen`.

## Closed since handover
| When (UTC) | Work | Result |
|---|---|---|
| 2026-11-06 15:15 | Dedupe verification (workflow wf_f7a34f8a-8de, 11 agents, every claim challenged by a skeptic) | **Live data:** 0 duplicate businessId + customerRef groups, 0 fallback-keyed docs and 0 businessId case variants, in dev and prod. **Code:** the doc id is a pure function of the normalised businessId + key, and nothing re-keys. **Latent:** splits via a missing ref, the Shopify raw `name` or replay edits (R14), and redrive's new messageId (R13). **Mongo:** 7 must-haves added to the D5 row, and hard-cut must-haves added to G9. Findings: `Handovers/2026-11-06-tracking-service-mongo.dedupe-findings.md`. |
