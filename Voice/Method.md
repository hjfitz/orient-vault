---
tags: [voice, style-guide, method]
title: Voice method
updated: '2026-09-30'
---
# How the Voice guide was built, and what it cannot tell you

Part of [[Voice]]. Built 2026-09-30.

## Pipeline

1. **Sample.** 52 random weekdays across 2025-08-05 to 2026-09-28 (seeded, weighted to the last six months:
   5 days a month Apr to Sep 2026, 3 a month Oct 2025 to Mar 2026, 2 each in Aug and Sep 2025). For each day,
   every message Harry sent, in any channel, DM or group DM, via Slack search `from:me on:<day>`. Capped at
   120 messages a day, so heavy days are cut after the first 120 (busy mornings are over-represented).
2. **Collect.** Six agents transcribed the messages verbatim into JSONL (date, time, channel, thread flag, ts,
   text), redacting secrets, and tagged messages that looked machine-written. 4,322 rows. A spot-check of
   5 random rows against live Slack matched exactly on text and timestamp.
3. **Filter.** 380 rows were flagged machine-written and removed (templated deploy and PR posts, PR-status
   digests, haude and agent-room posts, self-DM reports, long polished analysis). Plus `#real-agent-only`,
   `#agents-only` and DMs to himself. **3,941 human rows remain.** The flagged rows carry an em or en dash 81%
   of the time, the human rows 0.05%, which is why "no em dash" is rule 1. Machine-written posts under his
   account rise from about 0% of his output in Jan to Jun 2026 to about 30% in Sep 2026.
4. **Cluster** by reader into six groups (Jack, Oli and John, Darren, reports, wider DMs, channels).
5. **Profile.** One agent per cluster read the whole slice, fetched context for about 10 to 30 of his replies
   to see what he was answering, and wrote a profile: register in numbers, openers, moves with counts and
   verbatim examples, lexicon, anti-patterns, drift, gaps. Every number came from a script.
6. **Verify.** The orchestrator re-ran the headline numbers independently for all six profiles (they
   reproduced, with under 1 point of difference in denominators) and machine-checked quoted examples against
   the corpus (Darren 158, Jack 120, Oli 112, reports 203, wider 174, channels 220 exact matches; the misses were
   descriptive phrases, not fabricated quotes). Corrections made in this guide: `:pray:` and `:heart:` are
   rare, not banned; chasing is near-absent (a handful of timing questions), not literally zero.
7. **Distil** into this folder. Every quoted exemplar in `Voice.md`, `Audiences.md` and `Registers/` was
   re-checked: 364 of 393 quoted strings are exact in the human corpus. The other 29 are the "never says"
   lists (kudos, kindly, hope you're well) and prose fragments, not exemplars.

## What the data supports

Strong: the terse-versus-warm split by reader, the hard rules (no em dash, no closing full stop, shortcode
emoji, "in to", "anybody", "ok"), the per-person numbers for Jack, Darren, Oli, Matt, Nylah, Thomas, Stef and
Kyle, bursts, and the delegation, pushback and reassurance moves for reports.

## What it cannot tell you

- **Email, PR comments, Jira, Confluence.** Not mined.
- **Hard conversations.** Corrective feedback, performance, difficult news and formal escalation mostly
  happen in person, in 1:1s, or were skipped as sensitive. The guide's only evidence is that he moves them out
  of DM.
- **Up the hierarchy.** About 80 rows to or with John Clarke and about five examples per move. Thin.
- **Incidents and go-live.** 31 incident rows from one episode, 14 go-live rows. Weak.
- **Late-2026 ILG-facing messages.** Some that survived the filter may be agent-drafted or agent-edited.
- **Thin people.** Schuster (28), Harry Humby (54), Wolf (19), John Finney (12), Oliver Wilders (22),
  Chris Mulder (18), Harrison Beckley (31), Robert Fletcher (10).
- **Early data.** Jack-cluster rows start on 2026-01-13, Darren on 2025-10-29, wider DMs are 89% Apr to Sep
  2026. Sampled days with no messages: 2025-08-21, 2025-08-25, 2025-09-10, 2025-09-29, 2025-12-25,
  2026-04-03, 2026-05-04, 2026-05-12, 2026-05-15.
- **Per-day case.** Some days are capitalised end to end and nothing in the data predicts which.
- **Causation.** Drift since Apr 2026 (more capitalised, more emoji shift) may be partly audience mix, partly
  a real change, partly tool use. The guide uses the recent figures.

## Privacy

The raw corpus (private DMs, other people's context) is **not** stored in the vault. It lived in the session's
scratch directory. The guide holds only Harry's own words, chosen to avoid colleagues' personal details,
hiring, HR, health, family, money and credentials. Rows skipped as sensitive were roughly 18 to 23% of the
warm-register clusters. To refresh, re-run the pipeline above.

## Refresh

Re-mine when the terse or warm numbers drift by more than about 10 points, when a new direct report or a new
close peer appears, or roughly each quarter. Steps: new seeded day sample, collect, filter, cluster, profile,
verify, diff the register tables. Do not merge the new corpus into the old without re-checking the
machine-written filter: the flagged share is rising.

## Validation

See the held-out blind test in [[Validation]] (if present).
