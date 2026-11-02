---
tags: [waypoint, fuse-devtools]
verified: '2026-08-24'
verified_paths: []
title: fuse-devtools — known context
---

# fuse-devtools — known context

`known-context.md` is exempt from staleness checks — this is interview/investigation
truth, not a claim about current source. Re-verify against code before trusting a
specific implementation detail below.

## Ownership

Confirmed 2026-08-24: **Harry's own initiative**, not wider-Fuse-team-owned
like almost every other Fuse service onboarded this session. Not yet
registered in the Fuse MCP's own service catalog either — genuinely new
and personal at this stage.

## The deploy gap closed on 2026-10-28 {#deploy-gap-status}

Superseded: the `iac/` stack and the on-push / manual-deploy workflows the README described
landed on 2026-10-28 (fuse-devtools#3), and pr-sitrep has run in prod since that day. The
choices behind the deploy, all Harry's on 2026-10-28:

- **GitHub identity is the `ilg-platform-ci` app, not his PAT.** That's the PAT-retirement
  direction. The app is owned by the **gfs-dev** account, which is where its permissions are
  changed.
- **Slack identity is the "Bifrost Deployments" app's bot token**, the app Renovate already
  uses for its webhook. That replaced the support bot, whose token can't be copied out of the
  Slack CLI store.
- **The service took over the morning digest's team PR-status post**, which was retired (Step
  4b), along with the own-drafts DM. It covers every gfs-bifrost author except bots.

## The scheduled version deliberately changes the risk posture of a human-invoked skill

The `pr-sitrep` agent skill's authorization model is implicit: a human
invoking it *is* the approval for whatever it then does. A scheduled,
unattended run has no invoker, so this app treats merging and Slack
posting as a categorically different, opt-in-only risk — both default off,
and the config loader actively rejects the dangerous combinations
(`MERGE_ENABLED` with `GITHUB_ALL_AUTHORS`, and since 2026-10-28 `MERGE_ENABLED`
with GitHub App credentials) rather than merely documenting against them.
If this pattern (porting an interactive skill into a scheduled service) recurs for another skill, this is the model to follow: don't
assume a skill's existing safety story survives removing the human from
the loop — it usually needs its own, stricter one.

## Unknowns

- Whether a second app is planned for this monorepo, or `pr-sitrep`
  remains the only one for the foreseeable future.
