---
tags: [adhoc-task]
date: 2026-11-06
tldr: "orient /usage now splits Claude spend by machine (local laptop vs remote vm) via per-host usage folds in the vault; committed + deployed on vm, push and laptop deploy owed"
session_id: 480cdd7c-228b-4e61-baff-1e7e44ddde4a
status: open
---
# Split orient's Claude usage into local vs remote compute

## Outcome
Each orient publishes its transcript fold per date to `records/<host>/usage-fold-<date>.json` and merges the other machines'. Every view built on the fold (ticket, programme, task and triage costs) now includes sessions run on either machine. `/usage` gains a Compute lens, a Remote tile and host tags; Today shows remote spend. Commit `567df31` is deployed on the vm, but **not pushed**: the vm's orient deploy key is read-only. Owed: push from the laptop (or give the vm write access), then pull and redeploy orient on the laptop, after which laptop spend appears.
