---
tags: [adhoc-task]
date: 2026-10-19
tldr: "Mined #bifrost-general (15 Jul to 19 Oct) for what ILG support keeps asking, then published a DRAFT support set in Confluence under 6. Support & Operations: index, 4 runbooks, 3 FAQs; 5 of 6 TO CONFIRMs closed."
session_id: fb6c0db7-958a-4ae8-9129-5f64a1ac1699
status: open
---
# Write support runbooks for ILG Support L1/L2

## Outcome
Index "Support Runbooks (ILG Support L1/L2)" (Bifrost page 334757891, child of 109511066). Runbooks: Order or record isn't in SNAP (334856194), Confirmation hasn't reached the customer (335020034), Replaying failed records (334856221), Is it an outage? (334725130). FAQs: Credentials and connection failures (334856249), Fuse accounts and access (335085572), How Fuse works (334757933). All DRAFT, UI-first, same spine as the engineering Scenario Runbooks, all ADF/storage-verified.
Closed: support can Edit record in the Retry Queue; Shopify Datadog pattern verified (`@flow:create @recordId:"#<n>"`); Datadog retention is 15 days (oldest indexed log); Test conditions is on the Shopify connector page; escalation is #bifrost-general plus @fusedevelopers.
Restructured for 3am (same day): each runbook is Do this first, What did you find? table, Hand over when plus copy-paste Slack message, then Detail and Why we know this. About 520 words above the Detail divider (R1 2,002 to 1,501 total); index rewritten as a "which page do I open?" entry page; page names hyperlinked. Not yet dry-run: have Denis or Milosz work the 11 Sep Stubble case cold from R2.
All TO CONFIRMs closed (same day): record store has no automatic expiry (no TTL in code or infra; oldest Byoma PO on 19 Oct was 3 Feb 2026); Datadog invites come from engineering (Harry invited the team Oct 2025); ILG is the channel to SnapFulfil (INC-36, INC-39). New rule from INC-39: if a Fuse incident is open, support waits for the go-ahead before replaying. Owed: dry-run with Denis or Milosz; check INC-39 post-mortem's claim that the Retry Queue UI has no dismiss path against the Discard the runbooks rely on (fuse-ui main has bulk Discard).