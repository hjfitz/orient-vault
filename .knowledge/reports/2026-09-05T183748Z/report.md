# orient adoption report -- normalise

- vault: `/home/hjf/Documents/obsidian`
- started: 2026-09-05T18:37:48.860Z (38563 ms)
- tree hash: `60a118e810ecd8b2663d73fe4deec08a61c7e70c27cc38da14f97e7da270581a`

## Acceptance checklist

|  | check | expected | actual |
|---|---|---|---|
| PASS | Every inventoried document is indexed | 334 of 334 | 334 of 334 |
| PASS | No fatal findings | 0 fatal | 0 fatal |
| PASS | Warnings within the adoption budget | at most 40 warn | 0 warn |
| PASS | Every Engineering/<svc>/** document has a service container | 130 of 130 | 130 of 130 |
| PASS | Every plan carries a wp status | 9 of 9 | 9 of 9 |
| PASS | Every programme status maps to the enum | 14 mapped, 0 unmapped | 14 mapped, 0 unmapped |
| PASS | Every parsed wikilink occurrence is classified | 4067 of 4067 | 4067 of 4067, 0 documents short |
| PASS | Ambiguous targets within budget | at most 5 distinct | 0 distinct |
| FAIL | Vault tree hash unchanged | 60a118e810ecd8b2 | c3d893c1f91faf12 |
| PASS | A second reconcile leaves the manifest byte-identical | identical | identical |
| PASS | wp doctor findings unchanged | identical | identical |

## Inventory

334 documents, 27 sidecars, 5 assets, 3,739,418 bytes.

| extension | count |
|---|---|
| .md | 334 |
| .yaml | 27 |
| .png | 3 |
| .draft | 1 |
| .json | 1 |

| skipped | count |
|---|---|
| ignored-dir | 2 |

| folder | count |
|---|---|
| Meetings | 34 |
| People | 31 |
| Digests/2026-07 | 22 |
| Digests/2026-08 | 16 |
| Haude/Relationships | 11 |
| Bifrost | 10 |
| Digests/2026-06 | 9 |
| Haude | 8 |
| Digests/Weekly | 7 |
| Engineering/config-service | 7 |
| Engineering/dedupe-service | 7 |
| Engineering/sftp-connector | 7 |
| Engineering/fuse-mcp | 6 |
| Engineering/fuse-mocker | 6 |
| Engineering/fuse-ui | 6 |
| Engineering/ilg-secure-notes | 6 |
| Engineering/replay-service | 6 |
| Engineering/secops-reporting | 6 |
| Engineering/shopify-connector | 6 |
| Engineering/snap-adapter | 6 |
| Engineering/snap-mcp | 6 |
| Engineering/snap-queue-polling-service | 6 |
| Customers/PURDYFIGG | 5 |
| Digests/Roundups | 5 |
| Engineering/bifrost-pubsub | 5 |
| Engineering/collector | 5 |
| Engineering/core-infra | 5 |
| Engineering/distraction-dashboard | 5 |
| Engineering/fapi | 5 |
| Engineering/fuse-devtools | 5 |
| Engineering/github-actions | 5 |
| Engineering/github-config | 5 |
| Engineering/observability-sdk | 5 |
| Engineering/pkg-node | 5 |
| Engineering/renovate-runner | 5 |
| Engineering/terraform-modules | 5 |
| Engineering/ui-toolkit | 5 |
| Explainers | 5 |
| (root) | 4 |
| Bifrost/HR | 4 |
| Digests/2026-09 | 4 |
| Haude/Channels | 4 |
| Interviews | 4 |
| Bifrost/Fuse MCP Go | 3 |
| Bifrost/Fuse Mocker Go API | 3 |
| Engineering/snap-adapter/plans | 3 |
| _heap | 2 |
| Bifrost/Dedupe NestJS Migration | 2 |
| Bifrost/SecOps API Go | 2 |
| Bifrost/Shopify Connector Rearchitecture | 2 |
| Bifrost/Team | 2 |
| Bifrost/Tech Services IaC Review | 2 |
| Engineering | 2 |
| Growth | 2 |
| Bifrost/Platform Terraform Alignment | 1 |
| Bifrost/Purdy & Figg Testing | 1 |
| Customers | 1 |
| Digests/Sprints | 1 |
| Engineering/fapi/plans | 1 |
| Engineering/fuse-ui/plans | 1 |
| Engineering/secops-reporting/plans | 1 |
| Engineering/sftp-connector/plans | 1 |
| Engineering/shopify-connector/plans | 1 |
| Engineering/snap-adapter/explainers | 1 |
| Engineering/snap-queue-polling-service/plans | 1 |
| Growth/Influence | 1 |

## Documents

23 declare `title:`, 10 are sensitive, 0 failed to parse.

| type | count |
|---|---|
| waypoint | 94 |
| digest | 64 |
| meeting-series | 34 |
| person | 31 |
| ledger | 27 |
| note | 27 |
| persona | 23 |
| programme | 14 |
| plan | 9 |
| explainer | 6 |
| customer | 3 |
| index | 2 |

| area | count |
|---|---|
| engineering | 137 |
| digests | 64 |
| meetings | 34 |
| people | 31 |
| programmes | 30 |
| persona | 23 |
| customers | 5 |
| legacy | 5 |
| growth | 3 |
| inbox | 2 |

| container | count |
|---|---|
| (none) | 186 |
| service | 130 |
| programme | 14 |
| customer | 4 |

| frontmatter | count |
|---|---|
| present | 309 |
| none | 25 |

### Duplicate basenames

| basename | count |
|---|---|
| overview.md | 35 |
| architecture.md | 27 |
| known-context.md | 27 |
| ledger.md | 27 |
| operations.md | 13 |
| migration state.md | 5 |
| 2026-w34.md | 2 |
| 2026-w36.md | 2 |
| index.md | 2 |
| interfaces.md | 2 |
| jack bailey.md | 2 |
| matt shaw.md | 2 |
| nylah klasson.md | 2 |
| wolf clostermann.md | 2 |

## Findings

| severity | count |
|---|---|
| info | 261 |

| code | count | severity |
|---|---|---|
| LINK-UNRESOLVED | 134 | info |
| FM-TAGS-BLOCK | 50 | info |
| FM-DATE-QUOTED | 49 | info |
| FM-NO-BLOCK | 25 | info |
| PLAN-PLURAL-KEY | 3 | info |

## Links

4067 classified of 4067 parsed occurrences, across 5819 relation rows.

| resolution | count |
|---|---|
| basename | 2782 |
| entity | 405 |
| path | 372 |
| unresolved | 303 |
| same-folder | 143 |
| suffix | 51 |
| relative | 10 |
| same-container | 1 |

### Unresolved targets -- 39 distinct

| target | count |
|---|---|
| Manucurist | 144 |
| Fulfil | 53 |
| SportLux | 31 |
| EPERFUM | 25 |
| Accenture | 6 |
| Meetings/DevOps Drop In | 6 |
| project_fuse_mocker_go_api | 2 |
| project_fuse1104_silent_loss_hardening | 2 |
| reference_gfs_bifrost_checkouts | 2 |
| reference_ilg_platform_workflows | 2 |
| STUBBLE | 2 |
| atlassian-confluence-access-loss | 1 |
| CLAUDE | 1 |
| Dock & Bay | 1 |
| Dock &amp; Bay Fulfil.io API collection | 1 |
| F Veal | 1 |
| feedback_comment_density | 1 |
| feedback_metrics_in_service_not_shared_package | 1 |
| Gisou | 1 |
| ICONIC | 1 |
| Meetings/… | 1 |
| Meetings/Bifrost Standup | 1 |
| Pasted image 20260701164457.png | 1 |
| Pasted image 20260701164734.png | 1 |
| Pasted image 20260701170534.png | 1 |
| People/Thomas Dunn | 1 |
| project_dockbay_fulfilio_postman_collection | 1 |
| project_fuse_mcp_go_rewrite | 1 |
| project_fuse_mocker | 1 |
| project_saira_prod_order_intake_outage | 1 |
| project_secops_dep_node_checkout_regression | 1 |
| Purdy and Figg | 1 |
| reference_cloudrun_domain_mapping_region | 1 |
| reference_cross_env_tfstate_read | 1 |
| reference_fuse_dashboards | 1 |
| reference_shopify_retrieval_conditions_traps | 1 |
| Shopify retrieval-conditions full-replace | 1 |
| Sprint 13 | 1 |
| Todo item below | 1 |

### Ambiguous targets -- 0 distinct

| target | count |
|---|---|

## Entities

299 entities, 233 of them stubs.

| kind | count |
|---|---|
| ticket | 180 |
| person | 48 |
| service | 26 |
| channel | 21 |
| pr | 9 |
| programme | 8 |
| incident | 6 |
| customer | 1 |

## Entries

| kind | count |
|---|---|
| digest-todo | 1289 |
| digest-section | 615 |
| together | 303 |
| open-loop | 217 |
| human-slot | 167 |
| programme-unit | 138 |
| meeting-occurrence | 102 |
| programme-decision | 91 |
| persona-log | 88 |
| plan-increment | 48 |
| plan-decision | 46 |
| snapshot-claim | 7 |
| ledger | 3 |
| explainer-update | 2 |

## Index

`/home/hjf/.local/state/orient/index.sqlite` -- 334 documents, 3116 entries, 299 entities, 5819 relations.

## Normalisation preview

306 of 307 eligible files would change; 306 were applied this run.

| rule | count |
|---|---|
| add-title | 283 |
| quote-date | 155 |
| tags-flow | 50 |

| refused | count |
|---|---|
| no-frontmatter | 15 |
| sensitive | 10 |
| generated-index | 2 |

| path | rules | refusal |
|---|---|---|
| Bifrost/Dedupe NestJS Migration/Migration State.md | quote-date | -- |
| Bifrost/Dedupe NestJS Migration/Overview.md | quote-date | -- |
| Bifrost/Epic Structure.md | -- | no-frontmatter |
| Bifrost/Epics Covered.md | -- | no-frontmatter |
| Bifrost/Fuse Collector.md | -- | no-frontmatter |
| Bifrost/Fuse MCP Go/Migration State.md | quote-date | -- |
| Bifrost/Fuse MCP Go/Overview.md | quote-date | -- |
| Bifrost/Fuse Mocker Go API/Migration State.md | quote-date | -- |
| Bifrost/Fuse Mocker Go API/Overview.md | quote-date | -- |
| Bifrost/HR/Ibrahim Investigation - notes.md | -- | sensitive |
| Bifrost/HR/Ibrahim Write-Up - Ben.md | -- | sensitive |
| Bifrost/HR/Ibrahim Write-Up - Kim.md | -- | sensitive |
| Bifrost/HR/Ibrahim Write-up - Ibrahim.md | -- | sensitive |
| Bifrost/James Godsell — Migration Lead Concerns.md | quote-date, add-title | -- |
| Bifrost/Kit Confirmations & Short-Ship (FUSE-785).md | -- | no-frontmatter |
| Bifrost/Leadership notes.md | -- | no-frontmatter |
| Bifrost/Matt Tickets - Config Leadership.md | -- | no-frontmatter |
| Bifrost/Platform Terraform Alignment/Overview.md | quote-date | -- |
| Bifrost/Purdy & Figg Testing/Overview.md | quote-date | -- |
| Bifrost/SRE Terraform Framework — Bifrost Coexistence.md | -- | no-frontmatter |
| Bifrost/SecOps API Go/Migration State.md | quote-date | -- |
| Bifrost/SecOps API Go/Overview.md | quote-date | -- |
| Bifrost/SecOps Workflows 0.2 Plan.md | -- | no-frontmatter |
| Bifrost/Shopify Connector Rearchitecture/Migration State.md | quote-date | -- |
| Bifrost/Shopify Connector Rearchitecture/Overview.md | quote-date | -- |
| Bifrost/Team/Big up the team.md | -- | sensitive |
| Bifrost/Team/Matt Appraisal - 2026.md | -- | sensitive |
| Bifrost/Tech Services IaC Review/Overview.md | quote-date | -- |
| Bifrost/Tech Services IaC Review/Remediation State.md | quote-date | -- |
| Bifrost/Ticket Template.md | -- | no-frontmatter |
| Customers/PURDYFIGG/architecture.md | quote-date, add-title | -- |
| Customers/PURDYFIGG/known-context.md | quote-date, add-title | -- |
| Customers/PURDYFIGG/ledger.md | add-title | -- |
| Customers/PURDYFIGG/overview.md | quote-date, add-title | -- |
| Customers/index.md | -- | generated-index |
| Digests/2026-06/2026-06-17.md | quote-date, add-title | -- |
| Digests/2026-06/2026-06-18.md | quote-date, add-title | -- |
| Digests/2026-06/2026-06-19.md | quote-date, add-title | -- |
| Digests/2026-06/2026-06-23.md | quote-date, add-title | -- |
| Digests/2026-06/2026-06-24.md | quote-date | -- |
| Digests/2026-06/2026-06-25.md | quote-date, add-title | -- |
| Digests/2026-06/2026-06-26.md | quote-date, add-title | -- |
| Digests/2026-06/2026-06-29.md | quote-date, add-title | -- |
| Digests/2026-06/2026-06-30.md | quote-date, add-title | -- |
| Digests/2026-07/2026-07-01.md | quote-date, add-title | -- |
| Digests/2026-07/2026-07-02.md | quote-date, add-title | -- |
| Digests/2026-07/2026-07-03.md | quote-date, add-title | -- |
| Digests/2026-07/2026-07-06.md | quote-date, add-title | -- |
| Digests/2026-07/2026-07-07.md | quote-date, add-title | -- |
| Digests/2026-07/2026-07-09.md | quote-date, add-title | -- |
| Digests/2026-07/2026-07-10.md | quote-date, add-title | -- |
| Digests/2026-07/2026-07-13.md | quote-date, add-title | -- |
| Digests/2026-07/2026-07-14.md | quote-date, add-title | -- |
| Digests/2026-07/2026-07-15.md | quote-date, add-title | -- |
| Digests/2026-07/2026-07-16.md | quote-date, add-title | -- |
| Digests/2026-07/2026-07-17.md | quote-date, add-title | -- |
| Digests/2026-07/2026-07-20.md | quote-date, add-title | -- |
| Digests/2026-07/2026-07-21.md | quote-date, add-title | -- |
| Digests/2026-07/2026-07-22.md | quote-date, add-title | -- |
| Digests/2026-07/2026-07-23.md | quote-date, add-title | -- |
| Digests/2026-07/2026-07-24.md | quote-date, add-title | -- |
| Digests/2026-07/2026-07-27.md | quote-date, add-title | -- |
| Digests/2026-07/2026-07-28.md | quote-date, add-title | -- |
| Digests/2026-07/2026-07-29.md | quote-date, add-title | -- |
| Digests/2026-07/2026-07-30.md | quote-date, add-title | -- |
| Digests/2026-07/2026-07-31.md | quote-date, add-title | -- |
| Digests/2026-08/2026-08-03.md | quote-date, add-title | -- |
| Digests/2026-08/2026-08-04.md | quote-date, add-title | -- |
| Digests/2026-08/2026-08-06.md | quote-date, add-title | -- |
| Digests/2026-08/2026-08-10.md | quote-date, add-title | -- |
| Digests/2026-08/2026-08-11.md | quote-date, add-title | -- |
| Digests/2026-08/2026-08-12.md | quote-date, add-title | -- |
| Digests/2026-08/2026-08-13.md | quote-date, add-title | -- |
| Digests/2026-08/2026-08-17.md | quote-date, add-title | -- |
| Digests/2026-08/2026-08-18.md | quote-date, add-title | -- |
| Digests/2026-08/2026-08-19.md | quote-date, add-title | -- |
| Digests/2026-08/2026-08-20.md | quote-date, add-title | -- |
| Digests/2026-08/2026-08-24.md | quote-date, add-title | -- |
| Digests/2026-08/2026-08-25.md | quote-date, add-title | -- |
| Digests/2026-08/2026-08-26.md | quote-date, add-title | -- |
| Digests/2026-08/2026-08-27.md | quote-date, add-title | -- |
| Digests/2026-08/2026-08-28.md | quote-date, add-title | -- |
| Digests/2026-09/2026-09-01.md | quote-date, add-title | -- |
| Digests/2026-09/2026-09-02.md | quote-date, add-title | -- |
| Digests/2026-09/2026-09-03.md | quote-date, add-title | -- |
| Digests/2026-09/2026-09-04.md | quote-date, add-title | -- |
| Digests/Roundups/2026-W30.md | add-title | -- |
| Digests/Roundups/2026-W32.md | add-title | -- |
| Digests/Roundups/2026-W34.md | add-title | -- |
| Digests/Roundups/2026-W35.md | add-title | -- |
| Digests/Roundups/2026-W36.md | add-title | -- |
| Digests/Sprints/Sprint-14-boundary.md | quote-date, add-title | -- |
| Digests/Weekly/2026-W25.md | add-title | -- |
| Digests/Weekly/2026-W26.md | add-title | -- |
| Digests/Weekly/2026-W27.md | add-title | -- |
| Digests/Weekly/2026-W29.md | add-title | -- |
| Digests/Weekly/2026-W33.md | add-title | -- |
| Digests/Weekly/2026-W34.md | add-title | -- |
| Digests/Weekly/2026-W36.md | add-title | -- |
| Engineering/Waypoint — programme notes.md | quote-date, add-title | -- |
| Engineering/bifrost-pubsub/architecture.md | tags-flow, add-title | -- |
| Engineering/bifrost-pubsub/known-context.md | quote-date, add-title | -- |
| Engineering/bifrost-pubsub/ledger.md | add-title | -- |
| Engineering/bifrost-pubsub/overview.md | tags-flow, add-title | -- |
| Engineering/collector/architecture.md | tags-flow, add-title | -- |
| Engineering/collector/known-context.md | quote-date, add-title | -- |
| Engineering/collector/ledger.md | add-title | -- |
| Engineering/collector/overview.md | tags-flow, add-title | -- |
| Engineering/config-service/architecture.md | quote-date, add-title | -- |
| Engineering/config-service/interfaces.md | quote-date, add-title | -- |
| Engineering/config-service/known-context.md | quote-date, add-title | -- |
| Engineering/config-service/ledger.md | add-title | -- |
| Engineering/config-service/operations.md | quote-date, add-title | -- |
| Engineering/config-service/overview.md | quote-date, add-title | -- |
| Engineering/core-infra/architecture.md | quote-date, add-title | -- |
| Engineering/core-infra/known-context.md | quote-date, add-title | -- |
| Engineering/core-infra/ledger.md | add-title | -- |
| Engineering/core-infra/overview.md | quote-date, add-title | -- |
| Engineering/dedupe-service/architecture.md | tags-flow, add-title | -- |
| Engineering/dedupe-service/known-context.md | add-title | -- |
| Engineering/dedupe-service/ledger.md | add-title | -- |
| Engineering/dedupe-service/operations.md | tags-flow, add-title | -- |
| Engineering/dedupe-service/overview.md | tags-flow, add-title | -- |
| Engineering/dedupe-service/testing.md | tags-flow, add-title | -- |
| Engineering/distraction-dashboard/architecture.md | tags-flow, add-title | -- |
| Engineering/distraction-dashboard/known-context.md | quote-date, add-title | -- |
| Engineering/distraction-dashboard/ledger.md | add-title | -- |
| Engineering/distraction-dashboard/overview.md | quote-date, add-title | -- |
| Engineering/fapi/architecture.md | tags-flow, add-title | -- |
| Engineering/fapi/known-context.md | quote-date, add-title | -- |
| Engineering/fapi/ledger.md | add-title | -- |
| Engineering/fapi/overview.md | tags-flow, add-title | -- |
| Engineering/fapi/plans/FUSE-1056-resolve-confirmation-webhook-target-by-connector.md | tags-flow, quote-date | -- |
| Engineering/fuse-devtools/architecture.md | quote-date, add-title | -- |
| Engineering/fuse-devtools/known-context.md | quote-date, add-title | -- |
| Engineering/fuse-devtools/ledger.md | add-title | -- |
| Engineering/fuse-devtools/overview.md | quote-date, add-title | -- |
| Engineering/fuse-mcp/architecture.md | tags-flow, add-title | -- |
| Engineering/fuse-mcp/known-context.md | quote-date, add-title | -- |
| Engineering/fuse-mcp/ledger.md | add-title | -- |
| Engineering/fuse-mcp/operations.md | tags-flow, add-title | -- |
| Engineering/fuse-mcp/overview.md | tags-flow, add-title | -- |
| Engineering/fuse-mocker/architecture.md | tags-flow, add-title | -- |
| Engineering/fuse-mocker/known-context.md | quote-date, add-title | -- |
| Engineering/fuse-mocker/ledger.md | add-title | -- |
| Engineering/fuse-mocker/operations.md | tags-flow, add-title | -- |
| Engineering/fuse-mocker/overview.md | quote-date, add-title | -- |
| Engineering/fuse-ui/architecture.md | tags-flow, add-title | -- |
| Engineering/fuse-ui/known-context.md | quote-date, add-title | -- |
| Engineering/fuse-ui/ledger.md | add-title | -- |
| Engineering/fuse-ui/operations.md | tags-flow, add-title | -- |
| Engineering/fuse-ui/overview.md | quote-date, add-title | -- |
| Engineering/fuse-ui/plans/FUSE-1070-template-library-storage-browse-and-crud.md | tags-flow | -- |
| Engineering/github-actions/architecture.md | tags-flow, add-title | -- |
| Engineering/github-actions/known-context.md | quote-date, add-title | -- |
| Engineering/github-actions/ledger.md | add-title | -- |
| Engineering/github-actions/overview.md | tags-flow, add-title | -- |
| Engineering/github-config/architecture.md | tags-flow, quote-date, add-title | -- |
| Engineering/github-config/known-context.md | quote-date, add-title | -- |
| Engineering/github-config/ledger.md | add-title | -- |
| Engineering/github-config/overview.md | tags-flow, quote-date, add-title | -- |
| Engineering/ilg-secure-notes/architecture.md | quote-date, add-title | -- |
| Engineering/ilg-secure-notes/known-context.md | quote-date, add-title | -- |
| Engineering/ilg-secure-notes/ledger.md | add-title | -- |
| Engineering/ilg-secure-notes/operations.md | quote-date, add-title | -- |
| Engineering/ilg-secure-notes/overview.md | quote-date, add-title | -- |
| Engineering/index.md | -- | generated-index |
| Engineering/observability-sdk/architecture.md | quote-date, add-title | -- |
| Engineering/observability-sdk/known-context.md | quote-date, add-title | -- |
| Engineering/observability-sdk/ledger.md | add-title | -- |
| Engineering/observability-sdk/overview.md | quote-date, add-title | -- |
| Engineering/pkg-node/architecture.md | tags-flow, add-title | -- |
| Engineering/pkg-node/known-context.md | quote-date, add-title | -- |
| Engineering/pkg-node/ledger.md | add-title | -- |
| Engineering/pkg-node/overview.md | tags-flow, add-title | -- |
| Engineering/renovate-runner/architecture.md | quote-date, add-title | -- |
| Engineering/renovate-runner/known-context.md | quote-date, add-title | -- |
| Engineering/renovate-runner/ledger.md | add-title | -- |
| Engineering/renovate-runner/overview.md | quote-date, add-title | -- |
| Engineering/replay-service/architecture.md | tags-flow, add-title | -- |
| Engineering/replay-service/known-context.md | quote-date, add-title | -- |
| Engineering/replay-service/ledger.md | add-title | -- |
| Engineering/replay-service/operations.md | tags-flow, add-title | -- |
| Engineering/replay-service/overview.md | tags-flow, add-title | -- |
| Engineering/secops-reporting/architecture.md | tags-flow, add-title | -- |
| Engineering/secops-reporting/known-context.md | quote-date, add-title | -- |
| Engineering/secops-reporting/ledger.md | add-title | -- |
| Engineering/secops-reporting/operations.md | tags-flow, add-title | -- |
| Engineering/secops-reporting/overview.md | tags-flow, add-title | -- |
| Engineering/secops-reporting/plans/vulnerability-report-issue-writer.md | quote-date | -- |
| Engineering/sftp-connector/architecture.md | tags-flow, add-title | -- |
| Engineering/sftp-connector/interfaces.md | tags-flow, add-title | -- |
| Engineering/sftp-connector/known-context.md | add-title | -- |
| Engineering/sftp-connector/ledger.md | add-title | -- |
| Engineering/sftp-connector/operations.md | tags-flow, add-title | -- |
| Engineering/sftp-connector/overview.md | tags-flow, add-title | -- |
| Engineering/sftp-connector/plans/FUSE-1010-re-point-prod-goods-out-mappings-before-the-flag.md | tags-flow, quote-date | -- |
| Engineering/shopify-connector/architecture.md | tags-flow, add-title | -- |
| Engineering/shopify-connector/known-context.md | quote-date, add-title | -- |
| Engineering/shopify-connector/ledger.md | add-title | -- |
| Engineering/shopify-connector/operations.md | tags-flow, add-title | -- |
| Engineering/shopify-connector/overview.md | quote-date, add-title | -- |
| Engineering/shopify-connector/plans/FUSE-1057-route-confirmations-to-the-originating-shopify-c.md | tags-flow | -- |
| Engineering/snap-adapter/architecture.md | tags-flow, add-title | -- |
| Engineering/snap-adapter/explainers/work-order-family-confirmations.md | quote-date, add-title | -- |
| Engineering/snap-adapter/known-context.md | quote-date, add-title | -- |
| Engineering/snap-adapter/ledger.md | add-title | -- |
| Engineering/snap-adapter/operations.md | tags-flow, add-title | -- |
| Engineering/snap-adapter/overview.md | tags-flow, add-title | -- |
| Engineering/snap-adapter/plans/FUSE-866-join-woc-lines-by-line-key.md | tags-flow, quote-date | -- |
| Engineering/snap-adapter/plans/routing-metadata-to-firestore-write-side.md | tags-flow | -- |
| Engineering/snap-mcp/architecture.md | quote-date, add-title | -- |
| Engineering/snap-mcp/known-context.md | quote-date, add-title | -- |
| Engineering/snap-mcp/ledger.md | add-title | -- |
| Engineering/snap-mcp/operations.md | quote-date, add-title | -- |
| Engineering/snap-mcp/overview.md | quote-date, add-title | -- |
| Engineering/snap-queue-polling-service/architecture.md | tags-flow, add-title | -- |
| Engineering/snap-queue-polling-service/known-context.md | quote-date, add-title | -- |
| Engineering/snap-queue-polling-service/ledger.md | add-title | -- |
| Engineering/snap-queue-polling-service/operations.md | tags-flow, add-title | -- |
| Engineering/snap-queue-polling-service/overview.md | tags-flow, add-title | -- |
| Engineering/snap-queue-polling-service/plans/routing-metadata-to-firestore-read-side.md | tags-flow | -- |
| Engineering/terraform-modules/architecture.md | quote-date, add-title | -- |
| Engineering/terraform-modules/known-context.md | quote-date, add-title | -- |
| Engineering/terraform-modules/ledger.md | add-title | -- |
| Engineering/terraform-modules/overview.md | quote-date, add-title | -- |
| Engineering/ui-toolkit/architecture.md | tags-flow, add-title | -- |
| Engineering/ui-toolkit/known-context.md | quote-date, add-title | -- |
| Engineering/ui-toolkit/ledger.md | add-title | -- |
| Engineering/ui-toolkit/overview.md | quote-date, add-title | -- |
| Explainers/2026-08-21-explain-skill-built.md | quote-date, add-title | -- |
| Explainers/2026-08-24-work-order-lines-mirrored-across-both-snap-documents.md | quote-date, add-title | -- |
| Explainers/2026-08-25-gadg-bulk-ingest-soak-test-findings.md | quote-date, add-title | -- |
| Explainers/2026-08-26-gcp-config-antipattern-audit.md | quote-date, add-title | -- |
| Explainers/2026-09-01-actioning-a-waypoint-plan.md | quote-date, add-title | -- |
| Growth/Influence/Recommended Tooling etc..md | -- | no-frontmatter |
| Growth/Staff+ Things.md | -- | no-frontmatter |
| Growth/oli-harry career (no images).md | -- | no-frontmatter |
| Haude/Autonomy.md | quote-date, add-title | -- |
| Haude/Channels/Agents-Only.md | quote-date, add-title | -- |
| Haude/Channels/Bifrost-General.md | quote-date, add-title | -- |
| Haude/Channels/Fitz-Nylah-Matt-GroupDM.md | quote-date, add-title | -- |
| Haude/Channels/Guild-AI.md | quote-date, add-title | -- |
| Haude/Decisions.md | quote-date, add-title | -- |
| Haude/Disagreements.md | quote-date, add-title | -- |
| Haude/Haude.md | quote-date, add-title | -- |
| Haude/Lessons.md | quote-date, add-title | -- |
| Haude/Mood.md | quote-date, add-title | -- |
| Haude/Operating Rules.md | quote-date, add-title | -- |
| Haude/Relationships/ChatGPT.md | quote-date, add-title | -- |
| Haude/Relationships/Harry.md | quote-date, add-title | -- |
| Haude/Relationships/Jack Bailey.md | quote-date, add-title | -- |
| Haude/Relationships/Jaude.md | quote-date, add-title | -- |
| Haude/Relationships/Matt Shaw.md | quote-date, add-title | -- |
| Haude/Relationships/Nylah Klasson.md | quote-date, add-title | -- |
| Haude/Relationships/Olliama.md | quote-date, add-title | -- |
| Haude/Relationships/Shannonigans.md | quote-date, add-title | -- |
| Haude/Relationships/Stefthropic.md | quote-date, add-title | -- |
| Haude/Relationships/Thomas Dunn.md | quote-date, add-title | -- |
| Haude/Relationships/Wolf Clostermann.md | quote-date, add-title | -- |
| Haude/User.md | quote-date, add-title | -- |
| Interviews/Azdean interview.md | -- | sensitive |
| Interviews/Feedback for both.md | -- | sensitive |
| Interviews/Harry Humby interview notes.md | -- | sensitive |
| Interviews/Interviews 24-11.md | -- | sensitive |
| Meetings/1-1 Harry Humby.md | add-title | -- |
| Meetings/1-1 Jack Bailey.md | add-title | -- |
| Meetings/1-1 Kyle Chandler.md | add-title | -- |
| Meetings/1-1 Matt Shaw.md | add-title | -- |
| Meetings/1-1 Nylah Klasson.md | add-title | -- |
| Meetings/1-1 Oli Denton.md | add-title | -- |
| Meetings/1-1 Schuster Efigenio.md | add-title | -- |
| Meetings/1-1 Stef Aspin.md | add-title | -- |
| Meetings/API Documentation - Examples.md | add-title | -- |
| Meetings/API Documentation - Mandatory Use Cases.md | add-title | -- |
| Meetings/Bifrost - Operational Readiness.md | add-title | -- |
| Meetings/Bifrost Leadership Catchup.md | add-title | -- |
| Meetings/Bifrost Refinement.md | add-title | -- |
| Meetings/Bifrost SteerCo.md | add-title | -- |
| Meetings/Bruno Scripting.md | add-title | -- |
| Meetings/Charlotte Tilbury SAP - ILG Integration Catch Up.md | add-title | -- |
| Meetings/EDIFACT Interfaces - DESADV RECADV.md | add-title | -- |
| Meetings/EDIFACT Interfaces - INSDES OSTRPT.md | add-title | -- |
| Meetings/EDIFACT Interfaces - INVRPT.md | add-title | -- |
| Meetings/EDIFACT Interfaces - PRICAT.md | add-title | -- |
| Meetings/Escentric Engraving - Solution Design.md | add-title | -- |
| Meetings/FUSE Shopify Load Test Call.md | add-title | -- |
| Meetings/Fuse Support & Operational Ownership.md | add-title | -- |
| Meetings/Fuse Support Catch up.md | add-title | -- |
| Meetings/Fuse-Bifrost Weekly Sync.md | add-title | -- |
| Meetings/ILG - Fulfil Dock and Bay Integration.md | add-title | -- |
| Meetings/ILG Self-Service Feasibility.md | add-title | -- |
| Meetings/Platform Engineering Weekly.md | add-title | -- |
| Meetings/Purdy and Figg Go-Live War Room.md | add-title | -- |
| Meetings/RGA SFTP Ingress Catch-up.md | add-title | -- |
| Meetings/Return-to-work catch-up.md | add-title | -- |
| Meetings/Saira Skin Shopify Migration.md | add-title | -- |
| Meetings/Shopify Bulk - go-no-go.md | add-title | -- |
| Meetings/Shopify Retrieval Conditions - Catch up.md | add-title | -- |
| People/Alex Pickard.md | add-title | -- |
| People/Alex Topea.md | add-title | -- |
| People/Ankit Kansal.md | add-title | -- |
| People/Ashley Quick.md | add-title | -- |
| People/Darren Cobby.md | add-title | -- |
| People/Darren Rielly.md | add-title | -- |
| People/Denis Tomolea.md | add-title | -- |
| People/Harry Humby.md | add-title | -- |
| People/Hayley Prior.md | add-title | -- |
| People/Jack Bailey.md | add-title | -- |
| People/Jacques Dalton-Almeida.md | add-title | -- |
| People/James Godsell.md | add-title | -- |
| People/John Clarke.md | add-title | -- |
| People/John Finney.md | add-title | -- |
| People/Keith Rigg.md | add-title | -- |
| People/Kyle Chandler.md | add-title | -- |
| People/Laura Bockling.md | add-title | -- |
| People/Lee Simmons.md | add-title | -- |
| People/Matt Shaw.md | add-title | -- |
| People/Milosz Fialkowski.md | add-title | -- |
| People/Nylah Klasson.md | add-title | -- |
| People/Oli Denton.md | add-title | -- |
| People/Oliver Wilders.md | add-title | -- |
| People/Patricia Navarro Vaquero.md | add-title | -- |
| People/Peter Liu.md | add-title | -- |
| People/Ryan Ellis.md | add-title | -- |
| People/Sarah Davenport.md | add-title | -- |
| People/Schuster Efigenio.md | add-title | -- |
| People/Stef Aspin.md | add-title | -- |
| People/Tom Dunn.md | add-title | -- |
| People/Wolf Clostermann.md | add-title | -- |
| Untitled.md | -- | no-frontmatter |
| _heap/Inovize Issues.md | -- | no-frontmatter |
| _heap/Sportlux Confirmations @ 1-Jul.md | -- | no-frontmatter |

## wp doctor

wp doctor: 33 findings across 12 sections, exit 2 -- unchanged after adoption.

## Idempotency and rollback

Ids are path-derived, so a second run reconciles to a byte-identical manifest (verified this run) and rebuilds the index from the same files. Re-running is safe at any time.

The whole adoption is undone by:

```sh
rm -r /home/hjf/Documents/obsidian/.knowledge
rm -f /home/hjf/.local/state/orient/index.sqlite /home/hjf/.local/state/orient/index.sqlite-wal /home/hjf/.local/state/orient/index.sqlite-shm
```

No vault file is moved, renamed or rewritten by any mode except `--normalise`.

## Written this run

- `/home/hjf/Documents/obsidian/.knowledge/manifest.json`

