---
tags: [snap-maintenance]
date: 2026-10-19
subject: "Snap Version release and patch"
what: "Snap version update and patch (build 2.20.26076)"
impact: downtime
scope: "WebUI, Snap Portal, integrations; DB1 Space/Salfords/Sterling Park 7, DB4 EGA/Gatwick/EG25, DB3 Poland, DB2 BM1, DB5 BM2"
window_start: "2026-10-21T08:30:00Z"
windows:
  - start: "2026-10-21T08:30:00Z"
    label: "DB1 · Space, Salfords, Sterling Park 7"
  - start: "2026-10-22T08:30:00Z"
    label: "DB4 · EGA, Gatwick, EG25"
  - start: "2026-10-27T09:30:00Z"
    label: "DB3 · Poland"
  - start: "2026-10-28T10:00:00Z"
    label: "DB2 · BM1"
  - start: "2026-10-29T10:00:00Z"
    label: "DB5 · BM2"
est_duration_min: 60
sender: "Kavusalya Sivakumar (ILG IT)"
message_id: "<LOEP265MB70526703804F948FE80A2E9DCFCB982@LOEP265MB705267.GBRP265.PROD.OUTLOOK.COM>"
slack_url: "https://gfsdeliver-eng.slack.com/archives/C098LD5PS95/p1792422375799859"
slack_ts: "1792422375.799859"
notified_at: "2026-10-19T11:01:32Z"
posted_at: "2026-10-19T11:30:00Z"
unpinned_at: "2026-11-02T09:26:00Z"
reminded: ["2026-10-21", "2026-10-22", "2026-10-27", "2026-10-29"]
session_id: f72f4f0d-f60f-4c8a-aa19-ffd6c7c6af24
---
# Snap maintenance: version update and patch, Wed 21 – Thu 29 Oct

**BLUF: Snap version update and patch, one DB per day, Wed 21 – Thu 29 Oct. Downtime (est. 60 min per DB). No action required.**

- **WHAT:** Snap version update and patch (build 2.20.26076)
- **WHERE:** WebUI · Snap Portal · integrations · DB1 Wed 21 Oct 09:30 BST (Space, Salfords, Sterling Park 7) · DB4 Thu 22 Oct 09:30 BST (EGA, Gatwick, EG25) · DB3 Tue 27 Oct 09:30 GMT (Poland) · DB2 Wed 28 Oct 10:00 GMT (BM1) · DB5 Thu 29 Oct 10:00 GMT (BM2)
- **IMPACT:** Estimated 60 min downtime per DB. Users logged out 5 min before start. Integrations off for designated sites. Portal unavailable.
- **FUSE:** Snap alerts in #bifrost-notifications during each DB's window: likely this. Persisting past the estimated 60 min: investigate.
- **ACTION:** None for Fuse. Snap users: log out 5 min before each DB's start.
- **NOTICE:** 1d 21h. First email reached the mailbox 19 Oct 12:01 BST.
- **SOURCE:** Kavusalya Sivakumar (ILG IT) → SNAP Downtime, 19 Oct

The email labels every time BST, but clocks go back on 25 Oct, so the 27–29 Oct times are GMT here (taken as London time). The 60 min estimate and the logout, integration and portal notes come from the attached release notes, which give the date and start time as TBC. No end time is stated, so `window_end` is left out and this pin needs a manual unpin after 29 Oct.
