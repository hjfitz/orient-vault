---
tags: [adhoc-task]
date: 2026-11-03
tldr: "SFTP prod cut day: S2→S3 done, host at 100%, watch moved to rc-hjf at 13:57Z; host dashboard tab shipped (observability#82, #83). Carry-overs listed."
session_id: c483ad99-3b6e-42ca-94f7-5ad17f5f895d
status: open
---
# Run the SFTP prod cut and carry over what's owed

## Outcome
- **The cut:** S2, the ramp and S3 shipped (sftp-connector#390–#392), and prod has been 100% on the Go host since 09:46Z. The watch moved to the workstation at 13:57Z: see [[Soaks/sftp-prod-cutover-s3]].
- **The dashboard:** the host tab on the SFTP dashboard shipped in observability#82, with the formula fix in #83.

**Owed, unrelated to the watch:**
- The undici and zod `audit-ci` allowlists expire **2026-11-09**, and the zod `^4.6.6` follow-up is still to do.
- The observability#77 revert.
- The no-review window ends **2026-11-06**: delete the agents.md section and the skill notes then.
- Dev test connectors.
- The post-migration ownership revisit, and the scoped-key ideate.
- Build a skill from this watch: start from `soak-watch`, and add authority to roll back and milestone DMs, using `~/sftp-cutover/HANDOVER.md` and the soak record as the source.
