---
tags: [adhoc-task]
date: 2026-10-12
tldr: "SPORTLUX private key viewed+copied by james@ilguk.com 13:35Z; VM auth.log shows no login from his IP, all later sessions from the customer's own IP; Sep 16-19 logins from 3 other IPs with no view/copy audit trail"
session_id: e6889067-3a55-44f8-9430-54f8b325b5b3
status: open
---
# Investigate SportLux SFTP key copy in prod fuse-ui

## Outcome
Method (reusable for the planned skill): (1) fuse-ui prod `audit_log` read-only `find` by connector `targetId`, using the `MONGODB_CONNECTION_STRING` env on Cloud Run `fuse-ui-app-prod` (not in Secret Manager; it is the app's read-write user); (2) `/var/log/auth.log*` on `sftp-connector-prod-sftp` via IAP ssh, `sudo -n`, grep `Accepted|Failed` for the SFTP user, group by IP and key fingerprint. Cloud Logging has only systemd session lines, no IP.
Private key viewed then copied 2026-10-12 13:35:58/13:36:00Z by james@ilguk.com from 109.149.149.126. That IP appears nowhere in the VM auth log since 09-14; every login after the copy (13:43 to 14:59) is the customer's poller, 86.98.154.68, same key fingerprint (SHA256:n7Zdqx0D...). Harry Humby viewed the private key 10-09 14:44Z (no IP recorded).
Owed: ask James why he copied it. Open anomaly: 9 logins 09-16 to 09-19 with the same key from 92.97.178.117, 86.181.165.177 and 2.49.21.208 (some on a Saturday), and no view/copy/link audit rows on the connector at that time (only james@ilguk.com config updates, incl. 09-18 14:51Z). Check against Support/2026-09-18-sportlux-192-orders-dispatch-confirmations.
