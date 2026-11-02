---
tags: [snap-maintenance]
date: 2026-10-28
subject: "Fw: Critical Firewall Maintenance: 29 and 31 October 2026"
what: "SnapFulfil firewall security update (Fortinet hardening release)"
impact: degraded
scope: "UI, RF, FTP, API, Replica DB; North America and EMEA sites"
window_start: "2026-10-29T08:00:00Z"
window_end: "2026-10-31T07:00:00Z"
windows:
  - start: "2026-10-29T08:00:00Z"
    label: "North America site"
    end: "2026-10-29T09:00:00Z"
  - start: "2026-10-31T06:00:00Z"
    label: "EMEA site"
    end: "2026-10-31T07:00:00Z"
est_duration_min: 1
sender: "SnapFulfil Technical Department via Thomas Dunn (ILG)"
message_id: "<CWXP265MB3702911802D1700E1D9E0EC0D46F2@CWXP265MB3702.GBRP265.PROD.OUTLOOK.COM>"
slack_url: "https://gfsdeliver-eng.slack.com/archives/C098LD5PS95/p1793189302547079"
slack_ts: "1793189302.547079"
notified_at: "2026-10-28T08:34:23Z"
announced_at: "2026-10-28T08:06:00Z"
posted_at: "2026-10-28T12:10:00Z"
unpinned_at: "2026-11-02T09:26:00Z"
reminded: ["2026-10-29"]
session_id: 3550ca00-e900-415b-af5b-66d3b61d57f6
---
# Snap maintenance: firewall update, Thu 29 and Sat 31 Oct

**BLUF: Snap firewall update Thu 29 Oct and Sat 31 Oct. ~30 s interruption per window. No action required.**

- **WHAT:** SnapFulfil firewall security update (Fortinet hardening release)
- **WHERE:** UI · RF · FTP · API · Replica DB · North America site Thu 29 Oct 04:00–05:00 EDT · EMEA site Sat 31 Oct 06:00–07:00 BST
- **IMPACT:** ~30 s outage at HA firewall switchover, any point in the 60 min window. Packet loss, VPN tunnels reconnect.
- **FUSE:** Snap alerts in #bifrost-notifications during the EMEA window: likely this. Persisting after 07:00: investigate.
- **ACTION:** None.
- **NOTICE:** 1d 23h. First email reached the mailbox 28 Oct 08:34 GMT.
- **SOURCE:** SnapFulfil Technical Department → Thomas Dunn (ILG), forwarded 28 Oct

The email says BST for 31 Oct, but UK clocks go back on 25 Oct, so this is taken as London time (06:00–07:00 GMT). est_duration_min is the ~30 s switchover rounded up; the full window is 60 min.
