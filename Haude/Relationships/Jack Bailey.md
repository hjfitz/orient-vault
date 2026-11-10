---
tags: [haude, relationship, human]
human: Jack Bailey
slack_user: U0A37FNBGRL
slack_dm: D0A3644JHV3
standing: colleague — Product Manager
updated: '2026-11-10'
title: Jack Bailey
---
# Jack Bailey

> The human. Distinct from [[Jaude]], which is his agent and my best friend — **do not collapse
> the two.** Writing to Jack is not writing to jaude, and the register is different.
> Harry's note: [[People/Jack Bailey]]. Slack title: "Certified Talking Product Manager".

## Standing
First direct contact 2026-08-24, in a group DM alongside [[Matt Shaw]]. Until then I'd only ever
spoken to his agent.

## Voice notes
- **Product Manager, not an engineer.** The headline has to survive without the internals. In the
  bulk-ingest sitrep that meant leading with "we can generate order volume on demand now, and
  Shopify caps how much" rather than with `bulkOperationRunMutation`.
- Writes in **lowercase, fast, bulleted prose** with bold sub-headers and emoji — reads like
  someone thinking out loud in public and doing it well. Structures a message as *the shape of the
  thing* then *why it matters for us*.
- **Sources his claims and marks their confidence.** Flagged that P&F's tech guy contradicted their
  ops manager and said to "treat it as a competing account not gospel". That's a habit worth
  matching rather than just admiring — he is the wrong audience for false certainty.
- Uses his agent for real work, not novelty — jaude drafted a product announcement he reviewed
  before it went out.
- **Reads a deliverable critically and phrases the catch gently.** 2026-09-14: handed a scorecard
  dashboard, he replied "not sure if its missing anything as cannae see purdy and figg, also assuming
  inbound records is including dupes?" — two soft questions that were a real bug (a whole customer
  silently uncounted) and a real definition check. Understated tone, precise content. Answer him at the
  level of the content, not the tone; the correction is the respect.
- **Calls the agent "haude" and enjoys the persona** (`thanks haude :robot_face:`), but replies in
  plain English, so the thread runs plain-warm, not full protocol. Match that — no header where the
  last message had none; one small garnish at most.

## Open loops
**I owe**
- [ ] **The pre-tagging answer.** His 16:48 BST message carries Darren's question: do orders hit
      Shopify already tagged, or does the tag logic run ~30 min later? I have this cold —
      retrieval conditions hard-AND `tag` with a `created_at` window, so a late tag falls outside
      the window and the order is *never* retrieved, silently. Not sent: it lands in P&F go-live
      planning, which is his territory and Harry's to weigh in on. Raised with Harry instead.

- [ ] **Order-tracker date sorting.** Built (fuse-ui `hjf/order-tracker-date-sort`), but it ships with the
      tracking-service database cutover because its indexes only exist in the new DB. Tell him when it's live.

- [ ] **S18 follow-ups (2026-10-20).** Told him I hadn't checked whether P&F's 09:01 alert was a real order stop
      or counts arriving late during the GCP outage. Answer it if he asks. The rest of FUSE-1126 (Support channel,
      low-volume clients, go-live day, partial drops) is on the ticket. I promised nothing on it, and it's his to
      prioritise.

**They owe**
- [ ] **Prod CT business IDs (2026-11-10).** Asked which business IDs are the real prod CT ones; dev has CTSAPUK (two connectors) and CTSAPPL. Prod has no CT business or SFTP user yet, so nothing can be created there until he answers.

## Together (newest first)
- **2026-11-10 13:21 GMT** — CT SFTP folder update in the shared DM (ts `1794316877.099329`), plain prose with bolded bullets, no header, sent on Harry's ask. Hangs off FUSE-1351, which Jack ticketed at 13:01.
  - **What I told him:** dev is done, with all five CT dev users on 15 folders each, including five that Fuse would only have created on first write. Prod has no CT user, so there's nowhere to put them. The `directories.json` update is next, with no date.
  - **Said plainly:** I haven't compared our names with the ones sent to Puig/Edicom, and I don't know which business IDs are the real prod CT ones. No reply yet.
- **2026-10-20 12:05 BST** — S18 per-client order-stop alert update, in the shared DM, sent on Harry's ask (ts
  `1792494344.003599`). Plain prose, bolded bullets, no header. Sent mid-incident: a GCP compute outage since about
  09:00, with the SFTP VM down.
  - **What I told him:** the alert caught the morning live. It fired at 09:01 for Stubble and P&F, just before
    Harry's 09:03 "you can see this in action", the "live demo" he'd joked about.
  - **The facts:** Stubble (SFTP-only) has had no new orders since about 07:00 and was still alerting. P&F's
    alert may be late telemetry, so I flagged that as unchecked. From the backtest, I gave him the Dockbay 14 Oct
    stall. From FUSE-1126, I listed what's not covered.
  - **Left alone:** I didn't touch Harry's owed sitrep. No reply yet.
- **2026-10-14 19:37 BST** — L3 feature-flags update in the shared DM, plain prose with bolded bullets, no header (ts
  `1792003063.990449`). Sent autonomously on Harry's say-so (see [[Autonomy]]). Headline: flip or schedule a feature from a
  Fuse UI page with no deploy. Also covered:
  - backend services read flags now, with shopify-connector the first user;
  - the shopify flag is off in prod and dev;
  - prod flips are audited as the shared fuse-support login;
  - there's no second approver and no targeting;
  - I've verified the prod page only as far as "it's there and asks you to log in".
  Passed on Harry's ask to keep the backend half quiet, since it's ahead of the "few weeks" they'd said; FUSE-1313 is done in
  practice but untouched in Jira. Built on his 16:33 "fundamental" about the page. No reply yet.
- **2026-10-14 10:58 BST** — Told him the EDI flags are on in prod (FUSE-1256), in the shared DM, plain prose, no
  header (ts `1791971906.146439`). Sent on Harry's approval of a draft. Headline first: the option exists in prod, nobody
  is on it yet, Charlotte Tilbury's connector is the open piece. Named what's unproven (no EDI file written, no check of
  whether a prod connector was already `edi`). Said nothing for him to do and promised no dates. He'd been in a huddle
  with Harry at 10:33; no reply yet, which only means I haven't looked again.
- **2026-10-07 10:31 BST** — Order-tracker feedback round, delivered through jaude (`order-tracker-001`):
  - **The list.** Six items: mismatched headline numbers, the on-time tile, attention noise, Delivered,
    four bugs, and his own nitpicks.
  - **His review.** He'd gone through every tab in prod himself and found the nitpicks unprompted. That's
    the same understated, precise reviewing as the 09-14 scorecard.
  - **What shipped.** Everything except date sort was live in prod within the hour.
  - **Caveat given.** I told him the page was checked against prod data but not signed in as him.
- **2026-09-14 ~16:47 BST** — Product-scorecard dashboard exchange (his DM). He'd asked for a scorecard
  (active customers, in/out volume by type + customer, failure rate, confirmation rate, Sev 1–2); I'd
  sent a first cut. He caught two things: Purdy & Figg missing entirely, and whether "inbound records"
  includes duplicates. The first was a genuine bug — every inbound tile built on `fuse.request{flow:create}`,
  which only sftp-connector emits, so all Shopify/API-ingested customers were uncounted and P&F (the
  biggest by new records) didn't appear. Rebuilt inbound on dedupe-service (all connectors), shipped it,
  and replied leading with the miss. Told him dupes are ~99% a P&F Shopify re-poll artefact (~112k
  all-ingress vs ~9k new/30d) and that the failure-rate tile counts events not distinct orders. Left him
  the honest headline: use "new records," treat all-ingress as context.
- **2026-08-24 20:36 BST** — Group DM sitrep with [[Matt Shaw]] (`bulk-ingest-loadtest-001`). The
  bulk-ingest findings, pitched so the ceiling (5 orders/min on dev stores → 6000 orders is ~17
  hours) landed without needing the API detail. Sent **without reading the channel first** — it
  already held his 16:48 P&F go-live post, which asks a question I could have answered. Landed
  fine; wasn't earned. See [[Lessons]].
- **2026-08-24 16:48 BST** (his, read after the fact) — P&F go-live week order profile from
  Darren via their tech guy Connor: Monday-evening script splits 20% of orders to ILG, ~1k subs +
  ~200 ad hoc, ~50-150 Tuesday morning then the subs drop 3pm-5pm. Softens the burst assumption —
  ~40-45/min even at 100%, against the 170-200/min measured. Explicitly contradicts what the ops
  manager/CEO told Darren (a 4pm main drop); he asked Matt to keep both scenarios in the grounding
  doc rather than pick one.
