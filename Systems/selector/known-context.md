---
tags:
- system
- selector
verified: '2026-11-05'
title: selector — known context
---
# selector — known context

Interview truth (Harry, 2026-11-05), plus facts that source can't give. Claims marked `(snapshot …)` describe mutable state and age out.

## People and ownership
- **Jez Poppleton owns Selector** and writes nearly every commit to CSS and Client4. Andy Palmer contributes now and then.
- Work runs on **SMXI** Jira tickets: one branch per ticket, merged into a `Release-4.50.x` branch, then into master/main.
- **Chris Cumings** is the Selector contact for manifest semantics (from [[parcel-portal]]).
- Oliver Wilders is due to review the MPK *Legacy Selector* pages (snapshot 2026-11-05).

## Direction
- **Selector is being replaced.** Part of what Merak delivers will replace it.
- No programme folder or Jira epic tracks the replacement yet (snapshot 2026-11-05). The MPK *Legacy Selector* Confluence pages are the survey feeding it.
- Until then, Fuse's [[selector-adapter]], [[parcel-portal]] and [[selector-rest-proxy]] all book through CSS. Whatever replaces Selector has to reproduce the CSS contract they rely on.

## Hosting
- **GFS hosts one Windows box per customer.** It runs CSS under IIS and that customer's `GFS.FDB`, behind `<customer>.gfsdeliver.com`.
- Client4 runs on the customer's own PCs at the site.

## Fragility and surprises
- **CSS-only customers still depend on Client4.** If the upload-station PC is off or Client4 is closed, shipments label fine but never reach GFS or billing. Nothing alerts on this.
- **No duplicate guard.** Selector books a repeated `ProcessShipment` again (proved by the [[selector-adapter]] spike).
- **Carrier logic lives twice.** Client4 (Delphi) and CSS (C#) each carry their own carrier units, so a carrier change usually needs both.
- **No CI and no automated tests** in either repo. The CSS `Test*` projects are manual SOAP harnesses. A release merge into CSS master was reverted on 2026-10-16 (`Release-4.50.7.0`).
- **CSS refuses every call during a database update.** When `clientdb.UPD_START = 1` it returns `0066 Database updating`.
- **No central telemetry.** CSS logs to files on each box. The carrier proxies' Datadog logs (about 15 days' retention) are the only central view of Selector traffic.
- **Security, class-level only.** Committed database admin credentials in CSS config. Plaintext comparison of API user passwords. Recent request and response dumps written to `C:\temp` on the host. Specifics are for the security ticket, not this vault.

## Unknowns
- How a CSS or Client4 build reaches customer boxes and PCs. Is it manual, is there an installer run, does Client4 self-update through `UpdateUtil`?
- Which tables the `CUST_SCRIPTS` registration rows copy. Needs a read of the central DB.
- Whether Manager pushes contract changes to sites that are already registered.
- What `SITE_REG = 2` means.
- How many customer boxes exist, and which run CSS at all versus Client4 only.
- Who creates `web_users` rows for a new CSS customer.
