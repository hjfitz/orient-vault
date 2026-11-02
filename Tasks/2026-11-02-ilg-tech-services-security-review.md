---
tags: [adhoc-task]
date: 2026-11-02
tldr: "Read-only security + technical-choices review of all 13 ilg-tech-services repos and org settings; ~8 urgent issues found, nothing changed"
session_id: 1504bf95-34fe-411d-b609-9fc62adf2cf0
status: open
---
# Review ilg-tech-services org security posture

## Outcome
Reviewed all 13 repos plus the org settings, read-only; no changes made. The code itself is careful. The trust boundaries are drawn too wide. Most urgent:
- Org-wide WIF to `deploy-sa`, which can read every project secret.
- Default write access for all members, and no branch protection on most repos.
- A CSS `GetCustRoutes` auth bypass plus SQL injection in the CSS sign-in.
- Public route-check prod.
- SYSDBA used everywhere, and carrier credentials returned in clear.
- A shared customer-VM service account that can read every VM's admin password and the wildcard TLS key.
- Bifrost Atlas open to 0.0.0.0/0.

Owed: a decision on who gets the findings, and the org-setting fixes (Harry is an org owner).
