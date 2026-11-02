---
tags: [person]
role: Integration contact
org: SPS Commerce (external)
relationship: external
title: Ashley Quick
---
# Ashley Quick
> SPS Commerce integration contact for the [[Manucurist]] CSV onboarding.

## Coordinates
- Email: (SPS Commerce — external; not in Slack / GitHub / Jira)

## Open loops
**I owe**
- [ ] Reposition the **Stage column** between TotalWeight and StockPool in the confirmation CSV — her 07-29 reply says "otherwise all good for Next Beauty"; [[Lee Simmons]] handed the reorder to me on-thread; exactly what the [FUSE-954](https://globalfreight.atlassian.net/browse/FUSE-954) columnOrder work exists for — [email](https://outlook.office365.com/owa/?ItemID=AAMkADVhYjUxODIyLWM5NTktNGJmOC1hN2FjLWFjMjllNWUzYmY4MwBGAAAAAAAEXHdKGOMeRLfpaU7ff8ChBwABLsgQpFdPTayXOZTVrraLAAAAAAEMAAABLsgQpFdPTayXOZTVrraLAAGYfh%2BDAAA%3D&exvsurl=1&viewmodel=ReadMessageItem)
- [ ] Fix the SPS/[[Manucurist]] shipment confirmation file not referencing the order number (test order "TEST1") — file did go out, but Order Number is missing from the row entirely; possibly related to the [FUSE-954](https://globalfreight.atlassian.net/browse/FUSE-954) CSV column-ordering change now in QA

**Owed to me**
- [ ] Review her updated `create_sales_order` CSV (sent 01/07) + confirm next steps — [email](https://outlook.office365.com/owa/?ItemID=AAMkADVhYjUxODIyLWM5NTktNGJmOC1hN2FjLWFjMjllNWUzYmY4MwBGAAAAAAAEXHdKGOMeRLfpaU7ff8ChBwABLsgQpFdPTayXOZTVrraLAAAAAAEMAAABLsgQpFdPTayXOZTVrraLAAGEzqX2AAA%3D&exvsurl=1&viewmodel=ReadMessageItem)
- [ ] Verify her test orders to `/to_ilg/create_sales_order` — previously failing (currency `GB`→`GBP` + SKU)
- [ ] Diagnose confirmation-CSV field-order mismatch vs the user guide — reported 07-13 18:38, attachment supplied

## Standing context
- External — [[SPS Commerce]]; runs the [[Manucurist]] CSV → SFTP integration into Fuse
- ✍️ 

## Together (newest first)
- 2026-07-29 — replied on the SPS recap thread: asks only for the Stage column to sit between TotalWeight/StockPool, "otherwise all good for Next Beauty" — the reorder is now with me
- 2026-07-24 — reported the resent [[Manucurist]] shipment confirmation file is missing the Order Number reference entirely (test order TEST1) — a functional bug, not just a delay
- 2026-07-23 — still awaiting confirmation the [[Manucurist]] file went out — not yet verified
- 2026-07-22 — chased the [[Manucurist]] resend directly ("Has a new file been sent?")
- 2026-07-13 — flagged the confirmation CSV's field order doesn't match the user guide (attachment supplied) — on the same thread where Lee confirmed TEST2 landed
- 2026-07-01 — sent an updated `create_sales_order` CSV for [[Manucurist]] onboarding; direct-addressed me to review
- 2026-06-25 — sent test orders to `/to_ilg`; awaiting Fuse-side verification
- 2026-06-23 — confirmed her write to `/to_ilg` is succeeding

## Links
- Project → [[Manucurist]] · [[SPS Commerce]]
