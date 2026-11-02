---
tags: [adhoc-task]
date: 2026-10-27
tldr: "Built /platform-announcement; shipped the Node golden-image canary; published the golden-images announcement; built the enterprise-wide migration tracker (108 services by team)"
session_id: 35babc79-8119-4c09-9e0e-012248b87d07
status: done
---
# Create the platform-announcement skill

## Outcome
New skill at ~/.claude/skills/platform-announcement/SKILL.md, modelled on Jack's #bifrost-announcements posts.
Drafts a Slack post (Slack draft in #ilg-platform, Harry sends) and a PLTE Confluence blog (saved as draft).
Platform payload: contract/version line, adoption diff, consumer search, canary proof, gotchas. First run: golden images. Slack text DM'd to Harry, long form saved as PLTE draft page /wiki/x/DACAF. Owed: Harry's approval, then publish the blog, swap the link, and draft to #ilg-platform.

## 2026-10-28
- **Node canary shipped**: dedupe-service#167 is live in prod (rev 00049-27h).
  - It found the fleet-wide SIGTERM gotcha (Node is no longer PID 1) and the compose bind-mount and healthcheck breakage.
- **Announcement v2 DM'd**: the Confluence preview is updated with Node evidence, today's digests and a Prior art section.
- **Owed**:
  - Harry's OK on dedupe-service#168, the audit and image-scan fix that was already red on master.
  - Harry's approval of the announcement, then publish the PLTE blog and draft it in #ilg-platform.
  - Add the SIGTERM rule to the images README.
- **Done**:
  - #168 merged and live in prod.
  - images#10 merged.
  - Announcement published as a PLTE page, with the Slack draft in #ilg-platform.
- **Harry**: send the draft; delete the Bifrost probe blog draft at /wiki/x/AgCGF.
- **Migration tracker**: https://globalfreight.atlassian.net/wiki/x/AYCLF lists 108 services by team, with status and next step.
