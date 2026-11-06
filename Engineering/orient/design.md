---
tags:
- waypoint
- orient
verified: '2026-11-03'
verified_sha: 11aaab0
verified_paths:
- app/globals.css
- src/components/ui-lang
- src/components/shell/Sidebar.tsx
- src/components/sprint
- src/components/team/TeamRail.tsx
- app/sprint
- src/components/slack
- app/slack
- app/runs
- src/components/jira/JiraIssueView.tsx
- src/components/usage
- app/usage
- src/lib/service-colors.ts
- src/lib/model-colors.ts
- app/recordings
- src/components/recordings
- src/lib/recordings.ts
- src/components/shell/nav-status-store.ts
- src/domain/nav-status.ts
- src/lib/nav-status.ts
- src/components/shell/nav-controls.tsx
- src/components/shell/NavLink.tsx
- app/focus
- app/layout.tsx
- src/components/focus
- src/lib/focus-timer.ts
- src/lib/focus-log.ts
- src/lib/focus-ambient.ts
- src/lib/focus-music.ts
- src/lib/focus-suggest.ts
- src/lib/focus-ideate.ts
- src/lib/focus-context.ts
- src/lib/ambient-noise.ts
- src/domain/focus.ts
- src/domain/focus-suggest-run.ts
- src/domain/focus-ideate-run.ts
- src/domain/focus-context.ts
- src/adapters/focus-log.ts
- src/actions/focus.ts
- src/actions/focus-suggest.ts
- src/actions/focus-ideate.ts
- src/actions/focus-log.ts
- src/components/CommandPalette.tsx
- src/lib/palette.ts
- src/domain/palette-ticket.ts
- app/api/palette
- scripts/puzzle-pieces.mjs
- app/not-found.tsx
- src/domain/navigation.ts
- src/lib/entity-href.ts
- src/lib/mentions.ts
- src/domain/overviews.ts
- app/customer
- app/service
- src/components/DocumentList.tsx
- src/components/mentions
- src/components/shell/QuickView.tsx
- src/lib/quick-view.ts
- src/components/render/WikiLink.tsx
- src/lib/recording-ask.ts
- src/domain/recording-ask.ts
title: orient — design language
---
# orient — design language

`~/projects/orient` · personal local-first knowledge workspace over Harry's Obsidian vault.
Its own `CLAUDE.md` governs; the Fuse org contract does **not** apply here. Part of the
[[orient]] system.

## Identity

An **engineering console**, read at 07:00 and after hours by one expert user who already
knows the domain. Every pixel carries information or an affordance. It is the calibration
reference *for itself*: if a change would make orient feel less like orient, it is wrong.

**Read on an ultrawide.** The reader's display is 21:9 (3440×1440), so a layout is judged there
as well as at 1440 and on a phone. See *Wide displays* below.

**Density stance: maximum.** Dense tabular readouts, 11–13px monospace, no hero whitespace,
no cards where a rule and a label will do. Sitting closest to the Oxide / tactical-HUD end
of the rubric's anchors — taken for hierarchy and restraint, never chrome.

## Theme

**Dark only, deliberately.** `app/globals.css` sets `:root { color-scheme: dark }` and
defines exactly one palette — there is no `prefers-color-scheme` block and no toggle. Its
own comment gives the reason: one theme halves contrast work across ~4,800 vault table rows,
and Obsidian is a keystroke away when light reading is wanted.

**For capture:** light and dark shots come back byte-identical. That is correct, not a bug.
Shoot dark, and discharge the rubric's both-themes rule explicitly as "dark-only by design"
rather than silently skipping it.

## Tokens

All in `app/globals.css` under `@theme`. Never a raw hex in a component.

| Token | Value | Use |
| --- | --- | --- |
| `bg-0` | `#0b0c0e` | page |
| `bg-1` | `#12141a` | raised surface, code blocks |
| `bg-2` | `#1a1d24` | row hover |
| `line` | `#2a2e36` | every rule and border |
| `fg` | `#e9e4d8` | primary text (warm off-white) |
| `fg-2` | `#9b9890` | secondary; `/70`, `/60`, `/30` for further steps |
| `accent` | `#e0a526` | amber — **the one all-purpose colour** |
| `accent-ink` | `#0b0c0e` | text on a filled accent |
| `alert` | `#c4534b` | red — a real problem only |
| `done` | `#74a35a` | green — complete |

Three semantic colours total. Opacity suffixes on `fg-2` do the rest of the hierarchy work;
reach for those before inventing a token.

**Categorical colour is identity, never status.** Service, business, model and epic colours come
from fixed hue sets (`src/lib/model-colors.ts`, `service-colors.ts`) and mean *which one*, not *how
it is going*. The epic set (`epicColors`) is cool hues only — blue, cyan, violet, magenta, aqua,
orchid, purple, pink — because amber, red and green already mean accent, alert and done, and a
warm or green epic would read as a status on the sprint board. Assignment is a stable hash that
bumps a collision to the next free slot, so no two epics on one board share a colour.
On a sprint card the epic is a 3px left stripe plus its key in the same colour pulled toward `fg`
(`color-mix(in oklab, <hue> 70%, var(--color-fg))`, so the darker hues stay legible at 11px), with a
legend row above the columns; the key text still names the epic, so the colour never carries it alone.

Radius `--radius-sm: 3px`, `--radius-md: 5px`. Spacing `--spacing-row: 1.75rem`,
`--spacing-trow: 2rem`, `--spacing-gutter: 1.5rem`.

## Type

IBM Plex Mono / IBM Plex Sans, **listed first but not bundled** — no build-time font fetch,
no binary assets in the repo; the fallbacks are faces installed on this machine.

**Mono is the default voice** (377 `font-mono` uses vs 20 `font-sans`). Sans is reserved for
long-form rendered prose in the reader.

Measured scale, by frequency:

| Size | Role |
| --- | --- |
| `text-[11px]` | chips, meta, counts, table sub-rows — the workhorse |
| `text-[13px]` | body, a page's purpose line, prose |
| `text-[12px]` | dense table rows |
| `text-[15px]` | page `h1` |
| `text-[10px]` | micro labels |
| `text-[22px]` | reader article title (`font-sans`) |

A page `h1` at 15px is deliberate — hierarchy comes from weight, colour and position, not
size. Do not introduce a 24px+ heading outside the reader.

## Components (`src/components/ui-lang/` + friends)

- **`Section`** — a top rule, an uppercase 12px `tracking-wider` label, an optional count,
  optional right-aligned actions. *"Sections are a rule and a label, never a card: cards
  would flatten the hierarchy."* Use this, never a bordered box.
- **`FoldSection`** (same file) — a `Section` that starts closed: the same rule, label and
  count, a one-line `summary` gist, and an `href` to the page that owns the content. For an
  aggregating page (`/today`) where a board is worth reaching but not worth its full height.
  A fragment link to something *inside* a closed fold opens it — the browser's ancestor-details
  reveal — so in-page anchors keep working with no client JS.
- **`JiraStatusChip`** (`components/work/`) — **the only** renderer for a live Jira status:
  Jira's category tone, **filled** for a status parked on a human (Code Review, Ready for QA,
  In QA…), `unknown` when the lookup had nothing. A page-local status mapping is a bug —
  one sent "Ready for QA" to the done-green tone on `/today` while `/ledger` showed it waiting.
- **`InlineMarkdown` voices** — `prose` (15px sans, the default: sentences meant to be read, a
  needs-me item, a todo) and `meta` (12px mono, a digest summary in an instrument panel, where
  sans beside mono tables reads as a size jump).
- **`Chip`** — `h-5 rounded-sm border px-1.5 text-[11px]`. Tones: `neutral` `accent` `alert`
  `muted` `dashed` `done`; `filled` for a state that needs to pull the eye (e.g. a ticket
  parked on a human). Its contract, and the app's rule generally:
  **"Status is text first. A chip carries a word, not a colour that has to be learned, so a
  screenshot or a colour-blind reader loses nothing."**
- **`StateSwatch`** (`components/programme/`) — an 11px `rounded-[2px]` token-coloured
  square per programme unit state, with a `StateLegend`. **Emoji are not used as status
  glyphs** anywhere; they come from a different font with their own advance width and
  baseline and carry no word.
- **`StatePill`** (`components/programme/`) — the programme page's state, as a tinted 18px lozenge
  carrying the word (`IN PROGRESS`, `NOT STARTED`, `DEFERRED`; a gate's `OPEN`/`MET`, a risk's
  `STANDING`). It replaced the coloured squares on that page, so the page needs no key; solid tint
  for a state that is someone's problem now, outlined for a parked one. `StateSwatch` and its
  `StateLegend` remain on the Programmes list, which is dense enough to want the square.
- **Programme page layout** — row 1: "What this is" (under the same small uppercase label as its
  neighbour, 14px, flowing into `34rem` columns on a wide display) beside Progress, from 1200px; both
  are short, so neither leaves a hole. Row 2: Gates and Risks as tables, full width, side by side from
  2200px. Then the unit board — each row carries its risk and opens (native `<details>`, closed, with
  a show/hide-notes `ExpandAllToggle`) to the ledger's Notes; the body's Unit status tables are dropped once
  the board draws units, so they are not shown twice — and the decision log / scar tissue as 12px mono lists
  flowed into `34rem` columns (`.prose-log`), so the log is never one narrow column. Pill-first in every
  list (board, Gates, Risks). Ledger tables size known columns by header (`remarkTableColumns`: Summary
  `min-w-[22ch]`, Unit/Deps nowrap) so a wide Notes column cannot squeeze Summary to a word per line.
  A gate that names another programme's units resolves them from that ledger.
- **Plan page layout** — the same shape as the programme page. Head row from 1200px: Intent (14px,
  flowed) beside a Status section (turn chip, progress bar, AC met/open, gates, PR, idle, the next
  increment's *lead*, the note as text with "edit note", service/model/branch, and a `CopyPrompt`
  fast path). Then Increments as pill-first rows (`DONE` / `NEXT` / `GATE BREACHED` / `NOT
  STARTED`), each with its AC refs and stamped sha, the verify/outcome text behind a caret
  (`splitIncrement`: the lead is the text before the first " — "). Then Acceptance criteria as a
  table (met/open, covering increments from "(AC n)"). The `PromptBuilder` lives in a closed
  `FoldSection` ("Work on this plan"), so its sticky phone bar only exists once opened. The rest
  of the plan renders in the `.prose-log` style with one strip of section anchors. The Intent,
  Acceptance criteria and Increments sections leave the body only when the page drew rows for them.
- **`ProgressBar`**, **`CopyPrompt`**, **`SendToTerminal`** — a send button and a state label
  must not share a shape; a terminal state renders as plain text, never a bordered chip.
- Identity dots: `serviceColor()` / `businessColor()` (`src/lib/service-colors.ts`) —
  stable hash into a fixed palette, rendered `h-2 w-2 rounded-[1px]`.

## Usage page (`/usage`)

- **Charts show money, not tokens.** 97% of tokens are cache reads priced at a tenth of input, so a
  token chart is a picture of cache reads and says nothing about spend. The Spend chart is cost per
  day, stacked **reads / writes / output**: neutral `fg-2` steps for the two cache parts, the one
  accent for output. Quiet days stay on the axis as gaps; Mondays carry a faint rule; days that are
  estimates (`estimatedThrough`) are faded and the legend says so.
- **A cost the data cannot split exactly is the remainder, not a guess.** Reads and output are tokens
  times the published rate; writes are what is left of the folded cost, because the folded totals merge
  the 5-minute and 1-hour write tiers (`costComponents`).
- **Count a request once.** Claude Code writes a transcript line per content block, each repeating the
  request's usage; the fold charges only what grew since the previous line of the same request
  (`newSinceTail`). Any new transcript-derived figure must go through the same fold.
- **Biggest sessions** answers where the money concentrates: cost, requests, per-request cost, peak
  context and span, with amber on a peak over 500K (every request re-reads it) and its key printed under
  the table. Names come from the status-line snapshots, never from transcripts, which only `/history`
  may read; the row links to `/history/<id>`.
- **Estimated history is labelled where it is shown**, not only in the code: a one-line note under the
  tiles says which days are scaled estimates and why.

## Wide displays

A single column of full-width rows is the failure on 3440px: a label and its value end up a
thousand pixels apart and the eye cannot track across. Two moves, both on `/monitors`:

- **Two panes from 2200px** (`grid min-[2200px]:grid-cols-2`, arbitrary variant — Tailwind's
  own `2xl` is too low). A page with a *live* panel and a *history* set puts live state and
  the record list in the left pane and the aggregates (leaderboard, breakdowns, chart) in
  the right, the right pane `min-[2200px]:row-span-2`. Below 2200px it is one column in
  reading order. The breakpoint is set by the **widest table in a pane**: the record list
  needs ~950px, so a pane must be ≥ 950px, i.e. (2200 − sidebar 176 − gutters) / 2. Lower and
  the table scrolls sideways, which is worse than one column.
- **A long flat list, grouped and flowed.** `NormalMonitors` groups by service and lays the
  groups out with CSS `columns-[26rem]` + `break-inside-avoid`, so 64 rows become three
  columns on the wide display, two at 1440, one on a phone, with no breakpoint of its own.
  Use this when the items are short and the grouping key is meaningful; use a table when the
  reader compares columns of values.

Capture with `capture.mjs --viewports mobile,desktop,ultrawide --themes dark`.

## Tabs and live panels

- **In-page tabs are server-rendered links**, `<a href="/<page>?tab=<slug>">`, the same markup
  as the nav-view tabs in `app/[view]/page.tsx` (`-mb-px border-b`, `border-accent` when
  active, `aria-current="page"`). Use the shared `PageTabs` (`components/ui-lang/`); `/monitors`
  and `/incidents` both do. No client state, so `AutoRefresh` and the back button both
  keep working. Put the count in each tab's label, and make the tabs **partition** the set
  (alerting / normal / recently alerted: every monitor in exactly one) so the counts add up
  to a total the reader can check.
- **A panel fed by an external API** (Datadog on `/monitors`, `/health`) reads through an
  `AdapterResult`, states its freshness ("as of HH:MM:SS UTC"), degrades to an explicit
  "unavailable — <detail>" rather than an empty zero, and re-renders with
  `<AutoRefresh seconds={60} />` matched to the adapter's 60s cache TTL.
- **Count what is resting, do not list it.** A state that is the normal resting condition of
  the thing (a `No Data` event-driven monitor) is a count and lives under Normal; it is never
  in the alerting list.
- **A status chip must not cry wolf.** It goes red only for something that is actually urgent
  now. `/incidents` treats a live incident older than 7 days as *stale* (amber, "2 stale
  live"), not on fire: a P2 left in Monitoring for seven months is a forgotten status, and a
  chip that is red every day teaches the eye to skip it. The rule is `headlineStatus` in
  `domain/live-incidents.ts`, tested.
- **Join the sparse source onto the complete one.** incident.io has every incident; the vault
  has only those `incident-closeout` mirrored (2 of 31). The page lists incident.io's set and
  links a row to its vault record where one exists, then says the coverage out loud ("2 of 31")
  rather than letting the sparse source stand in for the whole. The vault-only view is the
  fallback when the API is unreachable, so the page is never worse than before.
- **Prefer the median where one outlier can dominate.** incident duration includes time an
  incident was left open (70 days on one), so severity tables show median *and* worst rather
  than a mean.
- **A filter scopes the whole page, and says what it hides.** `/incidents` opens on Bifrost
  (`DEFAULT_TEAM`, overridden by `?team=`) and *every* section is derived from the filtered rows
  — tabs, list, chart, severity, leads, and the vault leaderboard — never one table filtered
  beside five that are not. The chips are plain links carrying the tab, each with its count,
  then `All`, then a dashed `Unplaced`. A default filter must never silently drop what it
  cannot classify: the scope note gives the number that could not be placed, and the Unplaced
  view names the leads to fix. A team is the lead's team in People (joined on the email
  local-part) **or** incident.io's Affected-teams tag, or both; the Team column's tooltip says
  which.
- **Quiet the past.** A fact that is urgent when live (`untriaged` on an alerting monitor) is
  plain `text-fg-2` once the thing has recovered.

## What a page is for

Each surface answers exactly one question, and the nav groups say which:

| | Question | Surface |
| --- | --- | --- |
| **truth** | how is it built, and why | Systems → Services → Customers |
| **intent** | what are we doing | Work (programmes → plans → tickets), Programmes |
| **history** | what happened | Ledger, Digests |

**Content that answers a different question belongs on the other page, not duplicated here.**
`/work` listing 40 shipped tickets was history on the intent page; it shows open ones and
links the count to `/ledger`. A page that shows the same rows as another page is the tell.

**A count in a section label must mean what a reader assumes.** "23 in flight" counted
`waypoint-ideate`'s draft stubs because wp's `OPEN_STATUSES` includes `draft` — correct for
`wp status`, wrong for a human asking what is being worked. Drafts collapse into a `<details>`
labelled as ideas.

**An aggregating page leads with its own question and folds the rest.** `/today` answers
"what needs me this morning": needs, sprint, people owed, meetings, todos. Work, health, deploy
skew, nightlies, stale docs, PRs, recent changes and spend are each another page's subject, so
each is a `FoldSection` with its first sentence as the gist and a link out — not a full
re-render. It went from 6,810px to 2,802px with nothing removed.

**Finished is history.** A programme with every unit done, a shipped ticket, a settled plan:
each collapses or moves to the page for history, rather than sitting among live work.

**A ticked item must look done.** The mark is `CheckMark` (`components/ui-lang/CheckMark.tsx`): an
outline box when open, a `done`-filled box with a tick when done. A completed row's content takes
`DONE_TEXT` (`line-through` plus `opacity-50`), never a text colour: links, chips and code inside a row
set their own colour, so a colour on the row left a finished item looking open. Done items sink under a
`done N` divider on Needs me today; in lists that drop a ticked item on refresh (Todos, You owe) the row
is held done-styled until then. The button's hit area is `p-1.5` with a matching negative margin, so a
14px box stays 26px to tap without moving the layout.

**Name the thing, then link it.** A service named on a row links to its Waypoint docs
(`ServiceCell`); a ticket links to its own page; a plan links up to its programme unit.

## Conventions

- **Monitor names**: the constant `[FUSE]` tag is dropped and the remaining `[Group]` prefix
  dimmed to `text-fg-2` (`splitMonitorName`), so the part that differs between rows is the part
  that is read.
- **Tables**: `table-fixed`, proportional `<col>` widths, `tabular-nums`, numerics
  right-aligned, `border-t border-line/50` per row, `hover:bg-bg-2`. Sticky header goes on
  the `<th>`s with a `shadow-[0_1px_0_var(--color-line)]` standing in for the collapsed
  bottom border.
- **Below 640px, drop low-value columns — `<col>` and cells both.** Under `table-fixed` a
  hidden cell's `<col>` still reserves its width, so hide the `<col>` with
  `hidden sm:table-column` as well as its `th`/`td` with `hidden sm:table-cell`. A status chip
  wider than any phone column moves under the row's title (`sm:hidden`). A seven-column table
  that can't lose enough columns (`/ledger`) becomes stacked cards instead.
- **"Fits" is not the phone check; cells not spilling is.** Count `td`/`th` whose
  `scrollWidth > clientWidth` at 390px. Rendered vault markdown tables are exempt — they are
  designed to scroll inside their own bordered `.table-scroll` box.
- **Expand/collapse is native `<details>`**, closed by default — no client JS, no open state
  to manage. The caret is `▸` with `group-open:rotate-90`.
- **Keyboard-first**: every nav view has a `g <chord>`; chords live in
  `src/domain/navigation.ts`, and the sidebar grouping is *user config* in
  `<vault>/.knowledge/config.yaml`, not the in-repo default.
- Counts next to a `Section` label must be the **true** total, not a truncated list's length.
- **Everything with a name has an address, and every mention of it links there.** One readable,
  stable URL per thing, keyed on its real name, never an internal id: `/jira/KEY` (a ticket's overview;
  `/tickets/KEY` is its delivery work, reached from the overview and the tickets board), `/pr/o/r/n`,
  `/customer/<ID>`, `/service/<repo>`, documents by `docHref`. `src/lib/entity-href.ts` builds every one.
  Mentions link wherever text is shown: the markdown pipeline (ticket keys, PR refs, and customers and
  services from the index's terms, `remarkMentionLink`), plain text (`<Mentions>`, first in recording
  write-ups and transcripts), Slack (context cards, which open the overview beside the conversation). A
  customer id matches only as written (STUBBLE, not "stubble"); services, multi-word friendly names and
  incident keys ignore case. Code, text already inside a link, and the page's own subject (`subjectOfPath`)
  stay plain. A note's header links what it is about (`SubjectLinks`: its folder grouping or a declared
  `business_id`). An outside link orient has a page for opens that page (`orientHref` in the markdown `a`),
  the source one click away, never instead of it. A link is underlined in the text's own colour, never
  accent, which marks state; a mention's underline is dotted, as in Slack (`MENTION`, and
  `a[data-opens-beside]` inside `prose-orient`, whose own `a` rule would otherwise make it solid), going accent
  on hover. A wikilink to a customer's overview note (`Customers/<ID>/overview.md`) is a mention of the customer
  and opens `/customer/<ID>`.
- **Every mention has Slack's hover card and quick view.** A plain click on a `MentionLink` opens the thing
  beside the current page (the page itself stays the link's address, so a new-tab or modified click still goes
  there), and it opens a card after 300ms of hover or on focus (`HoverCard`; Escape or leaving closes it): the context
  card for a customer or service, Jira's summary, status chip and owner for a ticket (the quick switcher's lookup),
  and just the ways on for a PR. Every card ends "open beside" (accent, a `SideLink`) and "go to page". The card
  is inline spans (`w-80`, `bg-bg-1`, hairline border), so it sits inside a sentence. Nothing is fetched until it
  opens, and each thing once per page load.
- **The quick view** (`components/shell/QuickView.tsx`, in the root layout): `?side=<target>` opens that page
  embedded in a panel on the right (`min(44rem, 55vw)`, full width on a phone), above the terminal dock, with the
  name, "go to page" and "close ✕" (Esc). Clicking off it closes it too, except on something that opens beside
  (`data-opens-beside`, which switches the panel instead), a card, or the terminal dock. The page underneath stays
  put and the panel is in the URL. A Slack context card's customer or service opens its overview beside on a
  click; an incident still opens its card. `/slack` keeps
  its own split pane for the same targets, and an embedded page never opens a panel of its own: its "open beside"
  posts a same-origin message and the page around it switches its panel instead.
- **Customer and service overviews** (`/customer/[id]`, `/service/[name]`, `domain/overviews.ts`): the facts
  line, the overview note's excerpt with "read the overview", then two columns from 1400px: the thing's own
  notes (its folder only) and docs or plans, and "Mentioned in" (records filed under it or naming it,
  outside its folder). A service's open PRs stream in under `Suspense`, since GitHub is slow. Both take
  `?embed=1` for Slack's side panel (`side=customer:ID`, `side=service:name`).
- **Every view state lives in the URL** (tab, side panel, query, selection, transcript position), so any
  screen can be reopened or pasted.
- **`DocumentList` drops a Status column that every row leaves empty**: it took the titles' width in a
  narrow panel and said nothing.
- **Every page names itself in the tab**, most specific first, because a narrow tab keeps only the start:
  the root layout's template is `%s · orient`. A list page exports `metadata = { title: viewTitle(slug) }`, the
  rail label, so tab and rail agree. A detail page's `generateMetadata` names the thing: its title, `repo#n
  <title>`, `KEY <summary>`, `<run> · repo#n`, `Search: <q>`. A page whose data comes from GitHub, Jira or the
  scribe loads it through a module-level `cache()` that the page and its title share, keyed on plain values
  (`cache` compares arguments by identity), so the title costs no second fetch. The not-found page (`app/not-found.tsx`)
  sets its title with React's own `<title>`, because not-found takes no metadata. Anything that adds live state to
  the tab (the Focus clock) prefixes the page's title and strips only its own prefix, never saves and restores one.

## People (`/people`)

A directory read three ways (Directory / Teams / Org), all from `People/` frontmatter: `team:`,
`reports_to: "[[Name]]"` (`none` = a deliberate top of the chart), `role:` (the title). Internal
vs external comes from the note's email domain, not a hand-set flag.

- **Team is an identity, so it is a colour.** `distinctColors()` (`lib/service-colors.ts`) gives
  each team its own slot: the hash picks it, a collision moves to the next free one. Plain
  `serviceColor` would collide across ~11 teams in a 16-slot palette. The dot (`TeamDot`) is
  never the only carrier; the team's name is always beside it.
- **`TeamKey` is legend and filter in one.** A row of dot + name + count above the Directory and
  the Org chart. A click sets `?team=`: the Directory filters to it, the Org chart dims every
  other node to 40% and keeps the structure. On a phone it folds into a native `<details>`
  ("Teams 11") so the list starts on the first screen.
- **Say a repeated fact once.** The tree prints a node's team only where it differs from its
  parent's; 30 bordered chips on a 31-node tree was the failure this replaced.
- **Every control is a link built by `peopleHref()`** (`lib/people-href.ts`), so a filter set by
  one control survives a click on another. Sort (`?sort=`), gap (`?gap=`) and audience are all
  server-rendered links; no client state.
- **Gaps are scoped to who they apply to.** An external contact has no team or manager, so
  `hasGap` never counts one; only non-zero gaps print, and each is a filter link.
- **`~` marks a guess.** Audience decided by `relationship` (no email on file) reads `~ internal`
  / `~ external`, with a one-line caption under the table.
- **The Org chart is a route, not a dump.** Every manager is a native `<details>`; the default
  opens only the chain of command down to the reader's own team (`people.me` in
  `.knowledge/config.yaml`, names their People note; marked `you`), everything else closed at
  ~15 rows. `?team=` re-routes to another team, `?expand=all` opens everything. `routeTo()` (pure,
  tested) opens a node iff anyone beneath it is a target. Managers are `font-medium`, individual
  contributors regular, and children hang off elbow connectors (`before:`/`after:` borders).
- **Teams tab flows in CSS columns** (`columns-[24rem]`, `break-inside-avoid`) and lists a team's
  lead first: short groups of different sizes leave ragged voids in a grid.
- **Tab counts are people, not tabs-of-things** (Directory 37, Teams 31, Org 31): each matches
  its own Section count. The tab is labelled **Org** because four labelled tabs with counts do
  not fit 390px; the Section heading still reads "Org chart".

## Meetings (`/meetings`)

Its own nav view (`g l`, People group), no longer a People tab; `/people?tab=meetings` redirects.
One row per meeting series, from the same `meeting-series` docs the reader (`/meeting/<slug>`) uses.

- **Group by what a meeting is, derived from the data:** held once → one-off; else a counterpart →
  **1:1s**; else **Recurring**. `groupMeetings()` is pure and tested; the two listed groups flow in
  CSS `columns-[34rem]`. **One-offs are not listed** (21 of 37): the section's count is the 16 shown,
  and a line under it says how many are left out and where to find them (search).
  A count must equal the rows beneath it, so the label says "Meeting series 16", not 37.
- **Sort and dim on the real field.** `updated` is null for every series, so a sort on it is
  arbitrary; the list sorts on `lastOccurrence` and dims a date older than 14 days
  (`STALE_DAYS`, `text-fg-2/60`). A subtitle that promises "most recently held first" must be true.
- **No excerpt.** A series' excerpt is one occurrence's logistics or a bare heading ("Attendees"),
  not a description of the series; it made a series look defective from one occurrence's warning.
- **Owed is a join, not new data:** a 1:1 row shows `N you owe · N owed` from the counterpart's
  People note counts (`openLoopsMine`/`openLoopsTheirs`), the same figures the reader header shows.
  `you owe` is `text-accent`; there is no red in a list.
- **Today is a day view, not a second list.** `/today` already lists today's meetings; here the
  same rows (`todaysMeetings`, from the morning digest's schedule) sit on a vertical time axis:
  hours down the left, a block per meeting sized by its length (`PX_PER_MIN` = 72/60), overlaps
  drawn side by side in lanes and marked `clash`, a live `now` line in `text-accent` refreshed by
  `<AutoRefresh seconds={60} />`, past blocks at 60% opacity. `layoutDay()` is pure and tested.
  It only draws when the digest is *today's*; otherwise it says so rather than showing another
  day's schedule as today's. The axis is 09:00-18:00 and widens for a meeting outside it.
- **Now / Next replaces the old Past meetings week log.** Beside the day view, one `Section` per
  schedule row marked `now` or `next` (`MeetingNotes`), rendering that series' occurrence dated today,
  else the last one before it with an amber line saying so (`occurrenceFor`, pure). Held meetings are
  reached through search and each series page. A "no meeting today" note (`notHeld()`) is still not an
  occurrence: it is left out of `Held` and `Last held`. The card, top to bottom:
  - **Prep** — `PrepDraft`: a click runs Sonnet headless with **no tools, no MCP servers, no skills**
    (`toolLessArgs`, the PR review draft's lockdown) over the prompt builder's own context; ~10s, ~$0.05.
    Kept per series per day in the state dir (`meeting-preps/`). Its suggested To raise items can be added
    to today's occurrence (a guarded `raise` capture); `[id]` citations are stripped from the text.
  - **Context** — a `**Owed by you**` line inside it is a quiet 11px `fg-2/70` label (`splitLabelled`), never
    15px bold under an 11px label. When the live loops are shown the digest's frozen Owed copy is dropped.
  - **To raise** — a checklist (`RaiseList`, `LoopToggle asTask`): ticking writes `- [x]`, and a plain bullet
    from before the digest wrote checkboxes is promoted. The morning digest drops ticked items and carries
    unticked ones.
  - **Open loops with <counterpart>** — the People note's live loops (`OpenLoops`), tickable here.
  - **Notes** — the `- ✍️` seed reads "No notes yet." (no emoji glyph).
  - **Earlier** — the last four occurrences as closed `<details>`, with `all N →` beside the label.
  The meeting's time prints once (section actions); the subtitle drops it (`subtitleWithoutTime`). From
  2200px the sections flow in `columns-[34rem]`. On a phone the card comes before the day view
  (`max-lg:order-first` on an explicitly placed grid).
- **Prompt context rows** (`PromptBuilder`, shared) show the date when there is one and never the index id
  (it is the tooltip); titles wrap to two lines at 12px rather than truncating to "I owe — …".
- **Search is a GET form** (`?q=`), no client state: every word must appear, in any order, in a
  series' title or counterpart, or an occurrence's title, place, date or warning
  (`searchSeries`/`searchPast`, pure). It reaches the one-offs the list leaves out. Results replace
  the Now/Next and series sections (Series, then Held, capped at 60 with a count), and on a phone the
  day view hides while a query is set so the results start on the first screen.
- **Reader:** an occurrence row is marked only when it *has* notes (`notes` chip), and the section
  header says "N of M written up"; a dashed "no notes" chip on 107 of 134 occurrences told nothing.

## Quick switch (`ctrl k`, `CommandPalette`)

A jump box, so the thing most often wanted is first: **pages, then everything else.** Group order is Pages, Ticket (only for a ticket), Documents, Create,
Copy command, App, Search. Before this, documents sat above the pages, so typing `plans` selected whichever document mentioned plans and Enter went there
rather than to `/plans`.

- **Pages are ranked, not just filtered** (`rankPages`, `lib/palette.ts`): a name or short name that *starts with* what was typed, then one where a later
  word does, then one that merely contains it, and the rail's order within a tier. With nothing typed they keep the rail's order, which is what `g`
  chords already teach. Documents still come from `/api/palette` (titles and aliases first, body matches top the list up).
- **A group with nothing in it draws no heading.** cmdk is run with `shouldFilter={false}`, which makes it draw every group's heading regardless, so each group
  is rendered only when it has rows.
- **A ticket-shaped query brings the ticket up from Jira.** The *whole* term must be a key (`ticketKeyOnly`: `fuse-1232` in any case, spaces ignored), so a
  phrase that mentions a ticket is an ordinary search and `UTF-8` is not a ticket. The Ticket row is there at once, on the key alone, saying
  `Looking up in Jira…`; the details arrive from their own request (`/api/palette/ticket`) once typing has settled for 300ms, so a slow Jira never holds up
  the pages and documents, and a keystroke per digit asks Jira once, not four times (the adapter also caches for 60s). The row shows the status as every
  status is drawn (`JiraStatusChip`), the summary on its own line (it wraps to two), and a details line of what Jira said: who has it (or `unassigned`),
  priority, type, points, what it sits under, how long ago it changed, and how many PRs orient's ledger shows shipped for it. Enter opens orient's own
  `/jira/KEY` page; a second row opens the ticket in Jira in a new tab. Both say so honestly when Jira cannot answer (`not configured`, `did not answer in
  time`, `could not be reached`) without quoting the adapter's text, and a ticket Jira has never heard of reads `Not found in Jira` and offers no link to it.
- A lookup is never shown against a different key than the one now typed.

## Sidebar statuses (`domain/nav-status.ts`)

Small live facts in the rail, so something running or broken is visible from every page.

- **A provider per source.** It is a `() => Promise<NavStatus | null>` listed in `PROVIDERS`. A `NavStatus`
  carries an optional `badge` (a few characters beside its nav item, `tone` accent / alert / muted, with the
  full sentence as `title`) and an optional `control`. Each provider gets a 1.5s budget, so a slow or failing
  one drops out of the rail rather than holding it up. `/api/nav-status` serves them all.
- **One poller for the app** (`components/shell/nav-status-store.ts`). It is a module-level store read with
  `useSyncExternalStore`, so the mobile drawer and the desktop rail share it, and the last answer survives
  navigation (every page renders its own `Sidebar`). It polls every 5s while subscribed and the tab is visible,
  refetches on becoming visible, and `refreshNavStatus()` refetches straight after an action.
- **A control lives on its own nav item.** `NavLink` finds the status for its slug: the badge renders inside
  the link, and a `control` hands the whole row to `components/shell/nav-controls.tsx`, one case per `kind`. A
  kind with no case renders a plain row, and there is nothing above the nav groups.
  - Each kind gets the row's classes (hover and active fill), the link with and without its `g` chord, and lays
    out a trailing slot on the row plus an optional panel beneath it (`pl-6 pr-3`, 11px). Buttons sit beside the
    link, never inside it. Controls take `linkWithoutHint`, so the button or clock takes the chord's place and
    the chord moves into the link's tooltip.
  - The panel shows only when the kind has something worth showing. An idle control is a single row.
- **Say it once.** A badge is for what the row does not already show. A live or paused recording has
  no badge, because the clock is on the row. Work in progress reads `busy`/`busy 2`, never a bare number, and red
  is only a failure: `failed` (in the last 24 hours) or `down` (the recorder is unreachable).
- **Recording control** (`components/recordings/RecordingNav.tsx`):
  - Idle, the row has a small accent `rec` button. With a meeting on now or about to start, the panel shows its
    start time and title, and one click records it linked to its notes. Otherwise it starts an untitled recording.
  - Live, the row has a dot and the clock (time actually recorded). The panel holds the title, linked to the
    recording, then `pause`/`resume` and `stop` as two equal buttons.
  - Paused, the dot and clock dim and stand still, and the title reads `paused · <title>`.
  - A clock re-reads the time the moment it runs again, or a resume shows the time from before the pause.
- **Focus control** (`FocusNav`): see Focus below.

## Recordings (`/recordings`, `/recordings/<id>`)

Meetings recorded and summarised by the `scribe/` sidecar (`orient-scribe.service`), read only through
`src/adapters/scribe.ts`. Now group, `g w`. Answers *what did that meeting settle, and what do I owe?*

- **The default is the meeting you are in.** The title input starts as the meeting on now, or the next one
  when it starts within 10 minutes (`suggestedChoice`, `SOON_MINUTES`). A line under the input says "on now"
  or "about to start", with the time and whether it records against the meeting's notes. Typing a title unlinks
  it, and until a title is typed the default follows the clock as the page refreshes. That meeting is not
  listed again among the other choices.
- **Save to meeting notes is a button, then a link.** On a recording linked to a meeting, `SaveToNotes`
  appends the write-up to that day's occurrence `### Notes` through the guarded, append-only `notes-block`
  capture. The block has the template's shape: a `**Recording**` line linking back with an absolute
  `orientUrl` (so it opens from Obsidian), the tl;dr, then `**Decisions**`, `**Actions**` as `- [ ]` (so the
  digest carries open ones) and `**Left open**`. A named speaker with a People note becomes a wiki link.
  "Saved" is read from the note (the recording's link is in its Notes), so the vault stays the record; once
  saved, the button becomes a plain `in <series> notes` link. An unlinked recording shows nothing, and a
  missing occurrence shows its reason in muted text.
- **Reminders are the service's job, not the page's.** orient-scribe polls `GET /api/recordings/upcoming`
  every 30s and nudges through libnotify once per meeting, so the page never needs to be open for it.
- **A live recording is amber, never red.** Red is a failure only. The live marker is a drawn
  `h-2 w-2 rounded-full bg-accent motion-safe:animate-pulse` dot beside the word `recording`. It is not a
  `●` glyph, which comes from a fallback font with its own baseline. The record button takes `PrepDraft`'s
  accent idiom.
- **Status chips only where a look is needed.** In-flight states get an accent chip and `failed` a red one;
  `done` is plain `fg-2` text in the list and absent from the detail header (`StatusMark`).
- **The list is capped at `max-w-[1400px]`.** At 3440 its figures sat about 2,900px from the title. The
  table follows the conventions: numerics right-aligned, `border-t` rows, and the series after a `·` as an
  `fg-2` link.
- **Detail: summary beside transcript from 1800px**, with the summary pane `sticky top-5` and scrolling
  inside itself, so the actions stay in view along a 100-line transcript. Below that it is one column, in
  reading order.
- **Actions: owner, then the action.** A spoken due date ("next meeting…") is an 11px `fg-2` line under
  the action, not a column; it ran four lines deep in a 112px column. Harry's own actions sort first with
  the owner in `accent`, and others are `fg-2`, matching Meetings' `you owe`. Owners wrap; they never
  truncate.
- **Labels are voices, not people.** The scribe names one voice on the mic `Harry` and several `Room 1`,
  `Room 2`… (people in the room with the mic, Harry among them; the one who talks most is not assumed to be
  him), and voices the laptop played `Speaker N`. So in a room Harry's own voice is a row in the speaker
  list until he names it, with Claude's guess beside it. "Mine" (accent owner, sorted first, the digest's
  own-actions) is judged on the shown name (`isMine`), so a `Room 2` named Harry counts as him. Two labels
  given the same name read as one person. **Merging is explicit**: a row's "same person as…" folds that voice
  into another (Harry's own included, for far-end bleed that is him), stored in the scribe as its own `merged`
  map, one level deep. Its lines speak as the target, its actions take the target's owner, and the target's row
  lists it under "merged in:" with `split` to undo. One helper (`withMerges`) applies it for the page and save to
  notes; the summary prompt, the MCP tool and the digest resolve merges the same way.
- **Copy for Slack** sits first among the summary's actions. It copies rich text (Slack's composer keeps the bold
  labels and bullet lists) with plain mrkdwn alongside, Harry's names applied and his own actions first. There
  is no link back, because orient is only reachable on this machine.
- **The transcript is time · who · what** (`[3.5rem_7rem_1fr]`). The name is printed only when the
  speaker changes, so it never reads as the start of the sentence. Other speakers take `epicColors`
  mixed 70% toward `fg`, and Harry's lines are plain. The sticky audio bar must be `bg-bg-0`: `bg-bg` is
  not a token and was transparent. On a phone the name sits above the text.
- **The player is orient's own, not the browser's** (`AudioBar`, over a hidden `<audio>` that `TranscriptPlayer` owns).
  One mono row: a `play`/`pause` button, the time heard (`fg`), a 2px hairline scrubber that fills `accent` with a small
  `fg` square to drag (`input.scrub` in `globals.css`, a real range input so the keyboard and screen readers work), the
  length (`fg-2`), `−10` `+10` and the speed (`1×` to `2×`, cycling). Under it, `TrimBar` ("trim at 03:10", `cut before`,
  `cut after`, confirmed with what goes; the cut is permanent). The bar is sticky and `bg-bg-0`; on a phone it keeps
  `pr-12` clear of the floating menu button, the length and the jumps are hidden, and the buttons are `h-10`. The
  audio's metadata can arrive before hydration, so the component reads `readyState` on mount; relying on the
  `loadedmetadata` event alone left the length at 0 and the trim bar hidden.
- **Ask Claude about it** (`AskRecording`, an `Ask` section above Summary on a finished recording). A mono textarea
  (Enter asks, Shift+Enter breaks the line), three starter questions until the first answer, and each exchange as a
  `> question` in `fg-2` over the answer in `fg`. Times the answer cites (`[12:40]`) are amber buttons that fire
  `orient:seek`; the player listens, plays from there and scrolls itself into view. A failed run keeps the question in
  the field. The run is tool-less (`domain/recording-ask.ts`, `toolLessArgs`, `sonnet`, medium) over the notes and the
  enhanced transcript with Harry's names; nothing is saved and the conversation is gone when the page is left.
- **The transcript leaves the page as text** (`TranscriptExport`, `copy` and `export` in the Transcript header beside `enhance again`): whichever tab is showing, one `[mm:ss] Name: text` line per utterance under the title and when, hesitations left out. Export saves `<title>-<day>-<enhanced|raw>.txt`.
- **Enhanced and raw are tabs** (`PageTabs`, `?tab=enhanced|raw`, each with its line count). Enhanced is the
  default once it exists and raw until then. Enhanced is Claude's reading of the transcript, line for line, so
  the times, voices, names and merges are the raw transcript's (`withMerges` runs on both), and a line that was
  only hesitation is left out. Under the tabs an 11px `fg-2` note says it is a correction (misheard words and
  names put right, hesitations dropped, nothing reworded; check raw or the audio where it matters), because a
  clean transcript otherwise reads as verbatim. While a run is queued or going the page auto-refreshes, and the
  tab says so. A failed run shows its error in `alert` above the last good one. "enhance again" sits in the
  Transcript section's actions and shows only when it can act.
- **Empty states say where the recording is** (`transcriptNote`/`summaryNote`): queued, transcribing
  ("usually 10–20% of the call's length"), or failed, never "no speech" for a failure. An error prints the
  recording's files path under it, and the buttons show only when they can act. A failed recording can
  be deleted.
- **A meta line wraps inline, not flex.** Each `·` is joined to the item before it by a no-break space, so
  a wrapped line never starts with a separator.
- **Fixtures for review:** dense, failed and in-flight states are seeded as store dirs under
  `~/.local/state/orient/scribe/` (`meta.json` + `transcript.json` + `audio.ogg`), with
  `POST /api/recordings/<id>/summarise` for a real summary. Delete them afterwards.

## Desk (GNOME top bar, `desk/`)

orient's widgets outside the browser: `orient-desk` puts `/api/desk` on the session bus and the `orient@hjfitz.github.io`
extension draws it. Answers *is anything running, and what is next?* without opening orient.

- **The bar carries one thing, text first.** The first live widget, in a fixed order (recording, Focus, a meeting within
  `SOON_MINUTES`), shows its label and clock (`rec 12:39`, `focus 18:20`, `1:1 with Matt Shaw 4:59`). Accent is
  `#e0a526` while something runs and alert `#c4534b` on a failure; muted is the panel's own colour. With nothing live
  the bar is the `◎` mark alone. While orient-desk or orient is not answering it is `◎ –` at reduced opacity, and the
  menu says which.
- **The menu is every widget, in the same order:** the title (in the widget's tone) with its clock on the right, an
  optional detail line, then one item per button, separated by a rule; `Open orient` last. Labels are sentences in
  Harry's terms ("Stop and transcribe", "Start 25 minutes of focus", "Open its notes"), never ids.
- **Clocks tick in the desk, not by polling.** Each is anchored to a fixed instant, so the desk JSON only changes when
  the state does, and a ticker runs only while a moving clock is on the bar or in an open menu.
- **A refused press is a notification** (`Main.notify`), because the menu has closed by then.
- **Titles read wiki links as names** (`plainNames`): the schedule's `1:1 with [[Matt Shaw]]` shows as `1:1 with Matt Shaw`.

## Focus (`/focus`, chord `g F`)

A pomodoro timer that logs what it finishes, and a smart nav item: it runs from the rail on any page. 25 min focus, 5 short break,
15 long break after every fourth block; the lengths are editable (1 to 180 whole minutes).

- **The timer lives on the server**, as one file for the machine: `<vault>/.knowledge/focus/state.json` (phase, `endsAt`, task,
  lengths, the last phase to end). A `focus` provider in `domain/nav-status.ts` serves it through `/api/nav-status`, so the rail, the
  page and every open tab read one clock; the client computes the countdown from `endsAt`, never a tick count. It changes only
  through `focusCommand` (start, pause, reset, skip, phase, task, minutes). Start and pause are separate commands, not a toggle,
  so a second tab or a double click cannot undo the first.
- **A phase ends on the server.** Whoever reads the timer first after `endsAt` (`settledSession`) ends it at the moment it was
  due, appends the finished focus block to the log, and saves the next phase idle. The block's end time is its id, so settling twice
  writes one line. A timer nobody looked at settles at the next poll, with the true end time.
- **The log** is append-only JSONL, `<vault>/.knowledge/focus/YYYY-MM.jsonl` (`adapters/focus-log.ts`). `.knowledge` is outside the
  index, so nothing here enters search or prompt context. Skip and a finished break log nothing. Today and Last 7 days are server
  components over it.
- **The rail.** Untouched, the Focus row has a `start` button (like Recordings' `rec`) and a `N today` badge. Going, the clock is on
  the row and the task, pause and skip sit beneath. A phase that just ended keeps its panel for 30 minutes (`focusInStrip`), so the
  next one is a click from any page. `FocusNav` is the control; `FocusEffects` is mounted once in the layout.
- **`FocusEffects`** does what no rail component can: the tab title carries the clock, a timeout at `endsAt` reads the timer back
  the moment it ends (the rail only polls while a tab is visible, which would hold a hidden tab's alert), and the end is announced
  once per browser (chime, plus a notification when opted in) via a `localStorage` marker shared by tabs. It also refreshes each
  tab's server-rendered Today.
- **Per browser:** only whether to notify (`orient.focus.notify`). Notifications are opt-in from Settings, because the permission
  prompt needs a click. The chime needs a click on the page in this load, so after a reload with a running timer the end is silent but
  visible, which is what the notification is for. With no tab open at all nothing can alert.
- **"Working on"** is free text with a datalist of plans in flight and recently shipped tickets (from the work graph, never Jira).
  Text that names a ticket groups under the ticket and links to `/tickets/<KEY>`; untagged time is its own row. It is saved after a
  pause in typing and belongs to whichever block ends next.
- **Music** is a list of mixes in the vault config (`focus.music`: a title and a YouTube link each, in `.knowledge/config.yaml`), played by
  YouTube's own no-cookie embed (`FocusMusic`, `lib/focus-music.ts`). Click-to-load: nothing is requested from YouTube until a mix is
  chosen, and the player autoplays on that click. A link is parsed strictly (https, a YouTube host, an 11-character video id, a
  playlist id of the right shape); an entry that does not parse is dropped, not an error. It plays the chosen video and then carries on
  through its playlist. Config is read at boot: a changed list needs an orient-web restart. See *Sound outlives the page* below.
- **Ambient** layers (rain, wind, waves, brown noise; `FocusAmbient`, `ambient-engine.ts`) are synthesised in the browser with Web Audio from
  generated noise (`lib/ambient-noise.ts`), so nothing is downloaded and the repo ships no audio. They are independent of the music:
  each layer has its own on/off and volume and they add together, so any layer plays alone, over a mix, or stacked. Rain is a pink
  body, a band-passed hiss and sparse drops; wind and waves are pink noise swept by slow LFOs at unrelated rates, so they never loop
  audibly. Loops are 10s with an equal-power crossfade at the seam (`seamless`), so there is no click. The audio device is created on the
  first click, never on load (browsers will not start one without a gesture), and `Stop all` closes it (leaving the page does not). Per-layer
  trims in the engine put every sound within 1 dB at the same slider position, measured at the output with an analyser; re-measure when a
  recipe changes. Only the volumes are remembered (`orient.focus.ambient`); which layers are playing never is.
- **Sound outlives the page.** Music and ambient keep playing as you move around orient. The root layout never unmounts on a soft
  navigation, so what is playing lives there: `sound-store.ts` (a module-level store: the chosen mix, the layers, their volumes and the
  one audio engine) and `SoundHost`, mounted in `app/layout.tsx`. The Focus page's Music and Ambient sections are only controls over
  that store. A full page load still ends the sound; a soft navigation (a rail link, a chord, the phone drawer) does not.
- **One YouTube player that never moves in the tree.** Moving an iframe reloads it, which would restart the mix, so `SoundHost` owns the
  only iframe and positions it instead. On `/focus` the Music section reserves a box (`data-player-slot`, registered in the store) and the
  host lays the iframe over it with `position: absolute` from the box's page coordinates, re-measured by a `ResizeObserver` on the box and
  the body, so it scrolls with the page. Anywhere else it docks bottom-right (above the terminal bar, `z-30`, 22.5rem wide so it is
  at least YouTube's 200px minimum height; on a phone it spans the width). The dock carries the mix's name, a link back to `/focus` and `stop`.
  Test with `iframe.__marker` and the request count, not by eye: the same element must survive `/focus`, other pages and back, with
  one embed request in total.
- **The rail says what is playing.** The Focus row's panel gains `Halo mix · rain  stop` (the mix, then the layers, wrapped to two lines
  in the 176px rail) whenever anything plays, even with the timer idle, so ambient sound with no player can be stopped from any page.
  Its `stop` ends the mix and the layers together; the dock's `stop` ends only the mix; the Ambient section's `Stop all` ends only the layers.
- **Music follows the timer, and each mix is a row.** The mixes are full-width rows with a word at the right (`play`, `playing`, `paused`), not
  tabs: a tab reads as a filter, a row reads as a thing to press. The player is built with `enablejsapi=1` and the page origin, `SoundHost` asks it
  for its messages (`listening`), and the player's own state comes back into the store, so a row and the rail can say `paused`. With
  *Follows the timer* on (the default, `orient.focus.follow`), a focus block starting plays the music and anything else (pause, break, skip,
  finish) pauses it. **Only changes act**, so picking a mix during a break still plays it. A command sent before the player is listening is
  held and released by its first message; readiness is kept per mix (`ready === mixNow`) so a stale one is never trusted; messages are accepted
  only from `youtube-nocookie.com` and only from the iframe's own window. Ambient layers do not follow the timer.
- **Pick a task** (`FocusSuggest`, `domain/focus-suggest-run.ts`, `lib/focus-suggest.ts`) turns the open items of the morning digest's *Needs me*
  into focus-block tasks, one card at a time. It is the meeting-prep pattern: a click starts one headless, **tool-less** Sonnet run (about $0.05 and
  10 to 20 seconds), kept as `<state>/focus-suggestions/<date>.json`, polled while it runs. The run sees only the open `needs` (links reduced to their
  words by `plainNeed`) and may only propose: each suggestion has a title, a one-line *why*, 3 to 6 steps, a worth in 25-minute blocks, an optional
  ticket and the ids it rests on. The system prompt tells it to **sweep several quick replies into one task** and to skip items that need only waiting.
  `clean` trims what the card can hold and drops a suggestion with no steps. The deck is **take (right / →) or skip (left / ←)**, by drag, arrow keys on
  the card, or the two buttons; a drag past a quarter of the card (at least 90px) decides, a shorter one springs back, and the stamp (`TAKE IT` / `SKIP`)
  is text so the direction never rests on colour. What was decided is stored with the record, so a reload resumes where you were, and
  `Go through them again` costs nothing. Taking one sets the timer's task (the ticket key is put in the text, so the block is logged against it) and
  its steps in one command (`plan`); the steps are a checklist under *Working on* (`CheckMark`, `DONE_TEXT`), kept in the session so every tab sees them.
- **Do not `revalidatePath('/focus')` from the timer or suggestion actions.** It makes the server re-render the whole page (work graph included) before the
  action can answer: a take took 3.7s that way and 0.2s without. Nothing server-rendered on the page changes when a command runs; the timer reaches the
  client by the nav-status poll, and a finished block refreshes Today through `FocusEffects`.
- **Done finishes a task before the time is up** (`complete` in `lib/focus-timer.ts`, the `done` command, `completeSession` in `domain/focus.ts`). It is
  offered on the page and in the rail while a *focus* block is running or paused (never idle, never on a break). It logs the time **actually worked**
  (`minutes`) with the planned length beside it (`planned`) and `done: true`, then starts the break exactly as a block that ran out would, counting toward
  the long break. It clears the task and its steps, because the next block must not be logged against something finished; a block that merely runs
  out leaves them, since the work goes on. Under 30 seconds in is refused so a slip cannot log an empty block. A block that had already run out is settled
  first, so it is logged once as the full block it was and the click finds nothing to finish. Today and Last 7 days show a `done` chip on the block and on
  the task, and a count (`1h 13m focused · 2 done`). A click is its own announcement, so `lastFinished.manual` suppresses the chime and the notification.
  **`manual` must be in the stored-session schema**: without it the flag is written but stripped on every read, and the chime sounds anyway.
- **Ideate steps** (`FocusIdeate`, `domain/focus-ideate-run.ts`, `lib/focus-ideate.ts`) turns the title in *Working on* into steps. One headless, **tool-less**
  Sonnet run (about $0.03 to $0.05 and 8 to 15 seconds), one record at a time in `<state>/focus-ideas/latest.json`, polled while it runs; starting another title
  stops the old run and its answer is discarded. The run has no tools, so **orient looks for context first and hands it over numbered** (`domain/focus-context.ts`
  finds, `lib/focus-context.ts` chooses): the ticket the title names from Jira (facts, description, parent and links, last three comments), vault notes about
  that ticket, notes matching the words of the title (at most 4 of those, since they are the noisy kind), what the ledger shows shipped for the ticket, its open
  PRs and the morning digest's lines about it. At most 12 sources. Each source is best-effort and bounded (3.5s, Jira 6s): one that is slow or down is simply
  absent, never an error. **What may be sent is decided in one place**: a note is used only if the index calls it `normal`, its path is not under the vault's
  `sensitive` or `contextExcluded` globs, and it is not a digest or ledger (excluded in the query itself, because a digest outranks everything for any query
  and fills the pool). The record's `phase` goes `context` then `thinking`, and the panel says which.
  **Each step cites the sources it rests on** (`cites: ["c1","c3"]`, at most 3). Ids are checked against what was actually shown to the run, so an invented id
  is dropped. The panel shows numbered chips on each step (link to the page, or a plain chip for the digest, listed in source order) under the step text, never beside it, since beside it a long step is squeezed to a word a line on a phone; chips are 28px tall on a phone) and a `Sources · N looked at, M cited` fold listing
  everything, with the uncited dimmed, so a thin answer reads as "looked at 8, used 2" rather than hiding the rest. When a proposal is used, the pages each
  step cites travel with it as `refs` (at most 3, only `/path` or `https://`, labels clipped to 40) and appear as small links on the step in the timer.
  A source Jira cannot give is not an error and the run works from what it has. The system prompt turns anything it cannot know into a check ("Find out which...")
  and forbids inventing names, numbers, files or ids. The result is a **proposal, not a change**: steps can be unticked, then *Use these steps* (sets the task and
  replaces the steps in one `plan` command), *Add to my steps* (`add-steps`, which skips repeats and stops at 12) or *Discard*. Steps already on the list are sent with
  the request so new ones fill gaps. A record written before citations (plain-string steps) is read as steps that cite nothing.
- **Entries can be edited and deleted** (`FocusEntries`, `editBlock`/`removeBlock` in `adapters/focus-log.ts`, `actions/focus-log.ts`). Each row in Today has `edit`, which
  opens the entry in place: task, minutes (1 to 180) and *Task finished*, with Save, Cancel (or Escape) and a **two-step Delete** (`Delete`, then `Delete this
  entry? Yes, delete / Keep it`). An *Earlier this week* fold under Today lists the other days' entries, grouped by day, with the same controls, so a mistake
  from yesterday is reachable; the by-day and by-task tables are aggregates and are not edited. **The time an entry ended, and so its id and its day, cannot be
  changed**: an entry never moves between files. The log was written append-only, so a change **rewrites only that entry's month file, atomically, touching nothing
  but its line**: every other line, a damaged one and the trailing newline are kept byte for byte (checked against a real file with a torn line in it). An entry
  is found by its id (an id is the time it ended, so its month file is tried first, then the rest, in case an id is not a time). The change shows at once from a
  local overlay; the page is then asked to refresh (`router.refresh()`, not `revalidatePath`, for the reason above) so the totals follow, and the overlay is dropped when
  the new list arrives. Deleting an entry that is already gone counts as done. Not built: adding an entry by hand, or changing when one ended.
- The readout is 72px, the one numeral in the app above the 15px h1, because it is an instrument, not a heading. Paused dims it
  to `fg-2`. `F` because every lowercase chord is taken.
- **Layout is three tiers on one grid** (`app/focus/page.tsx`): one column below 1280px (Timer, Today, Music, Ambient, Week, which puts
  what a phone needs first); from 1280px two columns, Timer + Today beside Music + Ambient, with the week full width underneath as two
  side-by-side tables; from 2200px three columns (34rem, 34rem, 44rem) with the week as its own column. Before this the page was one
  34rem column at every width, which at 3440px left the right 60% empty and pushed Today and the week below the fold at 1440.
- **One clock on the screen.** Every readout (the rail, the page, the tab title) reads one shared 250ms ticker (`useNow` in
  `focus-client.ts`). With a ticker each they sat a second apart for part of every second, which reads as a bug when two clocks share a
  screen. Recency (`focusInStrip`) uses the poll's own clock, never the ticker.
- **State is a word, not a colour.** A playing ambient layer reads its percentage in accent and an idle one reads `off`; the tint on the
  button is the second cue, never the only one. Both week tables carry headers and the same Time, Blocks and Share column widths.
  Truncated task text carries its full text as a `title`.

## Puzzles (`/puzzles`, chord `g C`)

Harry's Lichess puzzles, solved in orient and counted on Lichess (`adapters/lichess.ts`, his own `LICHESS_TOKEN`
with `puzzle:read` and `puzzle:write`). Answers *what should I practise today, and is it working?*

- **Lichess holds the rating, orient keeps the record.** Every result Lichess counts is a JSON line in
  `.knowledge/puzzles/YYYY-MM.jsonl` (puzzle, themes, its rating, win, time, rating after and the change). A
  result Lichess cannot take is held in `~/.local/state/orient/puzzles/pending.json`, sent with the next one,
  and only logged once counted. Orient never runs its own rating maths, so there is one number, not two.
- **The plan is a day's ten slots** (`planDay`), made once from the 90-day theme dashboard and kept in the
  state dir: missed puzzles come back first, then the weak themes in turn (trainable, 10+ puzzles, performing
  50+ below the rating), two stretch puzzles at `harder`, the rest at the rating. A plan made while Lichess
  could not say where the weak spots are is used but not kept. Past ten, puzzles keep coming at the rating.
- **The board is orient's, the engine Lichess's** (`@lichess-org/chessground`, chess.js for the rules). Squares
  are two dark tones one step apart (`#191c22`/`#262a32`) in a `line` hairline frame; amber marks only the last
  move and the piece picked up, the alert red only check (`components/puzzles/board.css`). Pieces are cburnett's
  shapes repainted: White solid cream, Black ink with cream lines, so both read in one colour on a dark board.
  `scripts/puzzle-pieces.mjs` writes `pieces.css` from chessground's file, because a data-URI SVG cannot read a
  token: change `fg` or `bg-0` and rerun it. Coordinates are a mono `fg-2` axis outside the frame, in a gutter
  the trainer leaves. Themes stay hidden until the puzzle is done, as on Lichess; a weak-spot slot names its
  theme, because choosing it was the point.
- **The trainer panel is a console column** beside the board (`31rem` board, `24rem` panel from 900px): the
  slot as a small uppercase label with why beneath, one status line, the moves as numbered notation as they are
  played (the latest in amber, like its squares), then the result and the next action.
- **Lichess's rules for a result:** any wrong move or a look at the solution is a miss, a mate the solution
  did not list still solves, and an expected under-promotion is taken from the solution.
- **Solved is the `done` green, missed is plain text.** A miss is a result, not a failure, so it is never red.
- **90 days, not Lichess's suggested 30.** At a few hundred puzzles a quarter, 30 days left 3 themes worth
  judging. Rating history is fetched with the token: a private profile returns `[]` to anyone else.
- The nav row's badge is today's count against the plan (`4/10`), from local files only, so the rail never
  waits on Lichess.

- **Three tabs: chess, queens, tango** (`PageTabs`, `?tab=`), each counting what was done today (chess puzzles, daily
  boards solved). Queens and Tango take `?level=easy|medium|hard` (default medium) and `?seed=` for another board; no
  seed is the day's board for that game and level (`dailySeed`), so it is the same all day.
- **Difficulty is graded, not guessed.** Each board has exactly one answer and is accepted only when a deduction solver
  needs exactly the level's grade (`lib/queens.ts` `grade`, `lib/tango.ts` `tangoGrade`): Queens easy 7×7 with singles,
  medium 8×8 adding regions confined to a line, hard 9×9 adding confined groups and one-step look-ahead; Tango easy
  local rules, medium whole-line reading, hard look-ahead. Nothing needs guessing.
- **Orient's look, not LinkedIn's.** Queens regions are muted tints (`oklch(0.33 0.05 h)`, hues spread so touching
  regions differ) with drawn 2px region borders, so regions read without colour; the queen is a drawn crown and a
  ruled-out cell a thin cross, both SVG. Tango is hairline cells on `bg-1` (givens on `bg-2`), a disc and a ring for the
  two kinds, and `=`/`×` as small `bg-0` chips on the cell lines. A rule broken turns the pieces `alert`; a solve turns
  the board outline and clock `done`.
- **The console column** (`GameConsole`) matches the trainer's: the board's name, the level links (a drawn check on
  levels solved today), the rules in two sentences, a 22px clock from the first move, progress and clashes as text,
  undo / clear / another board, and the record (days in a row, today, best, median, solved per level). Solves log to
  `.knowledge/puzzles/games.jsonl`; the server decides whether a solve was the daily, and a daily is logged once.

## History (`/history`)

Claude Code sessions read from `~/.claude/projects`, one row per session; the transcript is a
sibling route. Gated to the hosts the terminal accepts.

- **A sortable table is server-rendered links**, not client state: each `th` is an `<a>` to
  `?sort=<key>&dir=<asc|desc>` that keeps `q` and `project`, so the order is applied *before* the
  100-row cut (sorting only the visible page would lie). `sort.ts` is pure and tested; a column
  starts in its natural direction (text A to Z, everything else biggest or newest first), and a
  row with no value for the column sorts last whichever way it runs. The default order is shown
  as an active ▼ on Last active, so the header is never unmarked.
- **The arrow has a reserved slot** (`2ch`, before the label on a right-aligned column, after it on
  a left one) and the `th` is `whitespace-nowrap`: a glyph that appears on click must not shift the
  label or wrap onto a second line. Check header `getBoundingClientRect().top` is equal across
  columns; two columns 17px high is the tell.
- **Numeric columns show from `lg` (1024px), not `sm`.** With the sidebar at 176px the five fixed
  columns need ~430px, which a 640px viewport cannot give; hiding the columns (and their `<col>`s)
  below `lg` lets the table drop its `overflow-x-auto` wrapper, which is what makes the sticky header
  possible. Below `lg` the same figures print as one `statsLine` under the title.
- **Width cap `max-w-[1400px]` on the table.** On 3440px the figures were ~1,600px from their
  title. This leaves empty space to the right on an ultrawide; a second pane (spend by project)
  is the unbuilt answer, not a wider table.
- **Quiet what carries no information:** a detached `HEAD` branch is not printed, and a bare
  housekeeping command as the first prompt (`/clear`, `/model …`) is `text-fg-2/60`.
- **Honest totals:** the header sums cost over sessions that recorded one and says how many did
  not ("6 unpriced"). A figure that is 0 on every row is a parser bug, not data: tool calls once
  read 0 everywhere because `type` follows the message on an assistant line.

## Maintenance (`/maintenance`)

SnapFulfil maintenance windows, one `Maintenance/` record per notice the `snap-maintenance` skill posts.
Operations group, `g z`. Answers one question: *when is Snap going to be unavailable or slow?*

- **Two sections, Ahead and Past, derived at render time** from `window_start`/`window_end`; a record
  carries no status, so it cannot go stale. Ahead is soonest first and includes a window that is under
  way; Past is newest first. `AutoRefresh` at 60s flips a window across without a reload. From 2200px
  they sit side by side, as on `/monitors`.
- **The header chip is red only for downtime happening now.** A live window with no downtime is amber, the
  next window within 48h is amber, otherwise muted: a notice days away is information, not an alarm.
- **Times are London wall-clock with the zone named** (`15:00–16:30 BST`), via `Intl` fields: never
  `dateStyle` with `timeZoneName`, which throws. A multi-day range prints the day span and the record's
  `window_note` (`daily 18:00–22:00 GMT`).
- **Quiet the past:** a past row is `text-fg-2` and its impact chip is muted whatever it was.
- **Notice is a column, a header row and a chart.** Notice = window start minus `notified_at`, the first
  email to reach the mailbox, so it measures what *we* were told, not what the sender knew
  (`announced_at`, when quoted, adds "announced 5d 19h ahead"). The column sits right after When so the
  pair reads together. Under 24h is amber text; zero or negative reads `none` in red with "told 6d 5h
  after", because a window we heard about after it ran is the finding this page exists to surface.
- **The summary is scoped to prod windows and says so.** A test or dev deploy is announced at 30
  minutes' notice by design; counting those made the median 20h and "5 under 24h" when the prod figures
  were 3d 5h and 2. `isProdWindow` leaves `test`/`dev` out, the label reads "Notice, prod windows", and
  "N of M recorded" is over those windows. The median is over windows given in advance; late ones are
  counted apart (`N after the fact`, red whenever above zero). A missing timestamp is never zero notice.
- **Notice by window** (`NoticeBars`) fills the left pane at 2200px under Ahead, and sits last below that:
  one bar per window on a fixed 0-7d scale, a line at 24h, a red tick for a window heard after it began,
  `›` on a clipped bar. A fixed scale keeps the bars comparable run to run; test/dev rows are dimmed.
  Ahead is usually empty or one row, so without this the left pane at 3440px was mostly void.
- **Past is quiet:** impact prints as plain `text-fg-2` text, not a chip, because the same bordered word
  on 8 of 11 rows carries nothing.
- **Record bodies are bullets.** Bare `**LABEL:**` lines with no blank line between them render as one
  paragraph in the reader; every labelled field is its own `- **LABEL:**` bullet.
- **Phone:** the `When` column wraps (a nowrap range ran into the next column); Env and Impact move
  under the title and are printed only when the record has a value.

## Pull requests (`/prs`) and the review page (`/pr/<owner>/<repo>/<n>`)

**`/prs` answers "which PR do I look at next".** Two groups, **In sprint** and **Other**, from the active sprint
board's ticket keys (`groupBySprint`); the In sprint header carries the sprint name and end date. When Jira
cannot name the sprint nothing is grouped and a `sprint unavailable` chip says so. The counts are true totals,
checked against GitHub's own search (24 + 10 = 34 = 8 + 26 on 2026-10-13); a search page cap shows an
`N older not shown` chip, never a quiet short list.

- **Row signals are exceptions, not states.** Only what needs a decision takes a chip: `you: requested`
  (filled accent, and those rows sort first within their group), `you approved`, `you: changes`, `ready`
  (filled; approved, CI passing, conflict-free, not a draft), `draft`, `ci failing`, `ci running`, `conflicts`,
  `behind`, and `ticket done` (the ticket is finished but its PR is open). **Passing CI is a muted `ci ✓`, not a
  chip**: a green chip on 70% of rows made them wrap and buried the red ones.
- **`PrCi` has `pending`.** A check still running is not green; `ciFrom` used to report it as green.
- **Size** is `+added −removed`, right-aligned and `tabular-nums`; a zero is muted (`text-fg-2/50`) so the alert
  colour is never spent on `−0`. The file count is the tooltip.
- **Authors drop their constant tail** (`shortLogin`: `_gfsdev`, `[bot]`, `gfs-bifrost-`), the same rule as
  monitor names. The full login is the tooltip.
- **Table**: columns 38/10/15/11/14/7/5 (title, repo, ticket, author, status, size, updated). The ticket column
  is sized for `FUSE-1203` plus its status chip so the chip stays on the row. Below 640px the header row is
  hidden (a lone "Pull request" label per group is noise) and a title wraps to two lines (`line-clamp-2`): it
  is the only identifying text on a phone. Rows take `hover:bg-bg-2`.
- **Wide**: from **2200px** the two groups sit side by side (`grid min-[2200px]:grid-cols-2`); each pane is
  ~1590px at 3440 and clips nothing. Below it they stack.

**The review page** is built to be read at 3440 as well as 1440. Split diff by default (`?view=unified` for the
old one), threads under the line they name, `+` on a line to comment. The Finish review control is a 34rem
popover (a form that spans a 3000px bar looks broken), the conversation is a dialog, and a polled fingerprint
refreshes the page for new comments but waits behind a **Load changes** banner for a moved head. A background
Claude review runs with **no tools, no MCP servers and no skills**; its findings arrive as pending comments
badged `claude` that the reviewer edits, dismisses or sends.

## Analytics (`/analytics`)

**Which pages earn their place.** A tiny client tracker (`PageTracker`, mounted in the root layout) sends one
`view` beacon per page and a `leave` carrying how long the page was actually in use: tab visible, window focused
and input within the last minute. `POST /api/analytics` appends route **templates** (`/doc/[id]`, `/pr/[…]`,
`/systems` plus its `?tab=`), never an id, path or title, to `analytics.jsonl` in the state dir. The log is
**not disposable** like the index: deleting it loses the history. It always answers 204, and it ignores
automated browsers (`HeadlessChrome`, `navigator.webdriver`) and the dev server, so screenshots and end-to-end
runs do not count as use.

- **The table is joined to every page, not just the visited ones.** Rows come from the nav views plus any
  `app/<name>/page.tsx` the nav does not list, so a page that fell out of the rail still shows as a row of zeros.
  A page nobody opens is the point of the view. Pages with several tabs get a sub-row per tab.
- **Columns**: views, days used (`n/30`), time in use, last opened (all time), a daily trend with the change on
  the window before, and a verdict (`never opened`, `unused 30d`, `rare` = used on at most `window/15` days).
- **Honest about a young log.** While the log is younger than the window there are no verdicts, because every
  page looks unused on day one; the page says how many of the window's days are recorded.
- **Elsewhere** lists the id-addressed families (a document, a pull request, a ticket) by kind.
- A new nav view needs its slug in `nav.groups` of `.knowledge/config.yaml` as well as `DEFAULT_NAV_GROUPS`.

## Document reader (`/doc/<id>`, explainers, Waypoint docs)

The one place long-form prose lives, so it is the one place sans is the voice. Three readers share it —
`ExplainerReader`, `WaypointReader` and the generic fallback in `DocumentView` — through the `prose-orient`
`prose-reader` classes. The plan, programme, digest, person and meeting readers set `prose-orient` beside
dense panels and are deliberately **not** `prose-reader`.

- **One column plus a rail, never CSS columns.** The grid is `grid-cols-1 lg:grid-cols-[minmax(0,T)_16rem]`
  with `lg:gap-10`, and the `Outline` rail (`components/reader/Outline.tsx`) beside it. The track `T`
  follows the content: `ExplainerReader` and `DocumentView` keep `68rem` so tables and diagrams can use it;
  `WaypointReader` picks its track from the source: a doc with an `orient-flow`, `orient-sequence`, mermaid
  block or a table gets `68rem`; a doc that is all prose gets `40rem` (about the 72ch measure) and the rail
  widens to `20rem` from `2xl`. A 68rem track under prose left ~300px of void between text and rail at 1440px.
  The wide case keeps that void beside the text, and accepts it: the diagram needs the room.
- **The rail is sticky and says where you are.** `ReaderRail` pins from `lg` (`top-5`, `max-h` of the viewport,
  scrolling inside itself when it outgrows it). `OutlineNav` is a client component that marks the last heading
  to have reached the top third of the screen with `aria-current` and an accent left rule. The test is the
  heading's rect, not an `IntersectionObserver`, because a section taller than the screen leaves one with no
  entry that is "intersecting".
- **Waypoint context is collapsed.** The rail shows Outline and This service; Verification, Plans in flight,
  Tickets & PRs and Mentioned by sit in a native `<details>` ("Context", with the verified date in the
  summary). They are reference, read once, and they pushed the outline below the fold.
- **Waypoint overview and architecture speak the explainer language.** BLUF, `orient-flow`, `orient-evidence`;
  the skeletons are in `~/.claude/skills/waypoint-onboard/doc-shapes.md` and the lint picks its mode from the
  file name. The doc is anchored, so unmarked claims read as confirmed and only ASSESSED and UNKNOWN are
  tagged. Mermaid is a fallback renderer only: it sits in a 880px scroll box and clipped inside a 40rem track.
- **Guardrails are drawn, not just listed.** A list item that opens `[contract|policy|operational|technical:Gn]`
  gets a kind chip (`remarkGuardrail`), and its trailing `— paths: …` moves onto its own muted mono line. The
  source stays the parseable form `wp context --paths` reads; only the rendering changes.
- **The h2 rule ends where the text ends.** `.prose-reader h2` is capped at `--measure` (72ch), a registered
  `@property` set on `.prose-reader` so `ch` resolves against the article's body font, not the 12px mono h2.
  Registering it with an `initial-value` in `ch` does not work: that resolves against the root font.
- **Rail rows wrap, they do not truncate.** Titles use `line-clamp-2`; a type chip beside a one-line
  `truncate` cut most titles at the second word. Below `lg` the rail gets a `border-t` so it reads as
  reference material, not more article. Explainers used two flowing columns; a full-width diagram
  inside them balanced the lede across the columns and, at 3440px, left ~970px of void per column. The
  `grid-cols-1` is load-bearing: an implicit `auto` track takes the min-content of a wide table and the
  whole page scrolls sideways at 390px.
- **Left-aligned, capped, void on the right at 3440px.** Same stance as `/history`: the unbuilt answer is a
  second pane, not a wider column.
- **Phone: article first, rail after.** The rail is reference material; it must not stand between the
  reader and the first paragraph.
- **Heading scale** (`prose-reader`, unlayered in `globals.css`): `h2` is the `Section` idiom — 12px mono
  uppercase `tracking-wider`, a `fg-2/40` top rule, no bottom rule, and none at all when it is the first thing
  in the article; `h3` is 15px/600 sans; `h4` stays 15px `fg-2`. The old 19/16/15px scale made h3 a bold
  body line. The body's own `# Title` is stripped when it repeats the header (`stripLeadingTitle`; pass
  `title` to `renderDocument`).
- **Inline code is quiet:** `0.85em` mono, `bg-2` fill, no border, `0.25em` padding, `box-decoration-break:
  clone`. A bordered chip per identifier read as a wall of chips in code-dense docs and broke into boxed
  fragments on a phone.
- **Diagrams in a generic doc (`Mermaid`)** use `theme: base` with `themeVariables` read from the `--color-*`
  tokens at render time (never literals), sit in a `border-line` box like a table, and **shrink to 880px then
  scroll in their own box** (`DIAGRAM_MIN_PX`). Natural width scrolled clipped the right of a 1200px diagram at
  1440; shrink-to-fit made labels ~5px on a phone. The box reserves `min-h-48` until the SVG lands. Explainers
  do not use mermaid: see *Explainer blocks* below.
- **Tables:** `.prose-flow table` wraps to 100% from 640px; below that a table with 3+ columns gets a
  `36rem` floor and scrolls in its `.table-scroll` box, since squeezing it to the viewport breaks every
  token mid-word.
- **`Callout` `superseded`** dims the body (`opacity-60`), never the label.

## Explainer blocks (`ExplainerReader`)

Explainers are written for orient, not Obsidian, so they are markdown plus typed fenced blocks orient draws
itself. The `explain` skill owns the authoring rules (BLUF, 22-word sentences, active voice, no hedges); orient
owns how each block looks. Block schemas live in `src/render/md/explainer-blocks.ts` and are mirrored by the
skill's `lint-explainer.mjs`: a new field goes in both.

- **`orient-bluf`** is the page's focal point: a `border-l-2 border-accent bg-bg-1` panel with the word BLUF, a
  `confidence high|moderate|low` chip (done / accent / alert), the conclusion in 16px sans at weight 500, and an
  `ACTION` line in mono (`fg-2` when it is `none`). Exactly one, before the first `##`. `thesis:` in the
  frontmatter equals its text, because `wp` and the Explainers view read `thesis`.
- **Claim tags.** A paragraph or top-level bullet that opens `**CONFIRMED**`, `**ASSESSED**` or `**UNKNOWN**`
  draws that word as a 16px tag (`remarkClaimTag`, classes in `src/lib/claim-tag.ts`): green fill, amber fill,
  dashed outline. Status is text first, so the tag is the word, never a bare colour.
- **`orient-evidence`** is a numbered list at the end. Prose cites a row as `[n]`, which `remarkEvidenceRef`
  turns into a superscript link to `#ev-n`; the plugin only runs on a page that has an evidence block, so a `[1]`
  elsewhere stays text. A `:target` row takes `bg-2`. Row kinds: `code` (path, `@sha`, lines), `pr` (links to
  GitHub), `ticket` (links to `/tickets/<key>`), `log`, `doc`, `url`.
- **Moved anchors.** The skill's `explain-drift.py` asks git whether each `code` anchor's path has changed since
  its sha and stamps `drifted_evidence`, `drift_checked` and `commits_behind` into the frontmatter. orient never
  runs git: it reads those keys into the explainer's meta, marks the row `moved`, and shows one header chip,
  "N anchors moved" (accent) or "anchors current" (muted). `wp stale` does not look inside `explainers/`.
- **`orient-flow` and `orient-sequence`** are server-rendered SVG, no client JS. Every colour is a token class
  (`fill-bg-1 stroke-line fill-fg-2 fill-accent`), type is mono at 12px / 10px / 9px, and the frame is the same
  `border-line` box as a table. The figure shrinks to its column down to 640px and then scrolls in its own box.
  - Flow layout is a pure function in `src/render/md/flow-layout.ts`: layers by longest path, a cycle's closing
    edge routed round the right side, dummy nodes for edges that skip a layer, barycenter ordering that leaves
    unconnected nodes in place, normalised to the left margin. Back-edge lanes start half a label clear of the
    nodes and are a label apart.
  - A node shows its **service name** above the label (with the service's identity colour, linking to its
    Waypoint docs) or its kind when the kind says something; a plain `step` shows no tag. A node or step that
    cites evidence reserves a head line for its `[n]` refs so they never print over the label.
  - `tone: alert` is the failure point and `accent` the point of the page; nothing else is coloured.
- **Typography scale is the document reader's**, not the app chrome's: the explainer is the one place sans is
  the voice, so a BLUF at 16px is correct here and nowhere else.

## Sprint (`/sprint`)

One page, tabs by `?tab=` (Sprint · Backlog · Runs). It absorbed `/team`, which redirects here. In the
sidebar it is nested under **Work** (`parent: 'work'`), first among Programmes / Plans / Tickets: it is the
live slice of the same work.

- **Board.** Flex-wrapped columns, each `flex-1 basis-60 max-w-[26rem]`; an empty column is
  `flex-none basis-40` and drops its points readout so the header never wraps. It stays a drop target.
- **People** sit under the board as a row of tiles (`SprintPeople`: name, open count, a points bar, done),
  `grid-cols-[repeat(auto-fill,minmax(14rem,1fr))]`. A narrow table here left a band of dead space beside it.
  Unassigned sorts last and reads as a gap.
- **Rail** (`SprintLayout` + `TeamRail`). From 1600px it sits beside the board as one column: Signals, then
  Needs attention. Signals are the team-status digest's KPIs, each a label, value, change since the
  previous run and a 72px sparkline, labelled as a snapshot with its time (the board is live; this is not).
  Below 1600px the rail follows the board as two columns (Signals | Needs attention), so no signal
  row is wider than half the page and a label stays near its value. The two-column rule is
  `md:max-[1599px]:grid-cols-2`: `min-[1600px]:grid-cols-1` loses to `md:grid-cols-2` in Tailwind's ordering.
- **Writes** go to the real Jira through `adapters/jira-write.ts`, each logged to `jira-write-log.jsonl`.
  Per ticket: ⚑ sets or clears Impediment, ▶ starts a run (its own confirm; it spends money), and ⋯ opens
  one menu with the statuses Jira offers *now* (board order, the current one left out) and where to move it.
  Dragging a card onto a column is the shortcut for a status change. **Drag is never the only path**: it
  does not fire on touch and has no keyboard route. The assignee's name opens a picker (you first, then
  people on the sprint, a filter, Escape closes).
- **A failed write says so under the card or row** (`ErrorScope`, 8s, `role="alert"`), never only in a
  tooltip. Done cards carry no controls.
- **Backlog rows** fade their controls in on row hover or focus, and always show them on a touch screen
  (`REVEAL`); a set flag stays visible. 163 rows each repeating `unassigned` and a button was the noise.
- **Phone.** Controls collapse to one 40px ⋯ (the menu gains a Flag item; ⚑ and ▶ are hidden). A backlog row
  reflows to key + ⋯, title, then a wrapping meta line. At 390px the page must not scroll sideways.

## Traps

- **A string exported from a `'use client'` module is a client reference when a server component imports
  it.** It arrives as a function and a class list built from it is garbage, with no error. Constants shared
  by server and client live in a plain module (`components/sprint/reveal.ts`).
- **`hover:` and `group-hover:` sit behind `@media (hover: hover)`.** Headless Chrome reports `hover: none`,
  so a hover reveal cannot be screenshot-tested. Check the computed opacity at rest and after focusing a
  control inside the row (`group-focus-within`) instead.
- **Tailwind `group-open` on nested `<details>` matches any open *ancestor*.** A collapsed child
  inside an open parent still reads as open, so its caret pointed down. Rotate the caret with
  `[&[open]>summary_[data-caret]]:rotate-90` on the `<details>` itself (direct-child `summary`
  only), never `group-open:`.

- **A grid that is one column below a breakpoint needs `grid-cols-[minmax(0,1fr)]`.** With no
  template, the implicit column is `auto`, so it grows to its widest child's min-content (a
  markdown table, a heatmap with `min-w-[30rem]`) and the whole page scrolls sideways. Hit on
  `/slack` analytics and `/jira/<KEY>`; measure `document.documentElement.scrollWidth` at 390
  and 1440 rather than trusting a cropped screenshot.
- **Adding or renaming a nav view** needs `~/Documents/obsidian/.knowledge/config.yaml` updated too —
  its `nav.groups` overrides `DEFAULT_NAV_GROUPS`, so a new or renamed slug silently falls into an
  "Other" group at the bottom of the sidebar until it is fixed.
- **Config is memoised at boot.** Editing `.knowledge/config.yaml` needs the dev server
  restarted (`pkill` by PID, not `-f`, which matches your own shell), not just a reload.
- **An entity fact copied from a file must take the fresh value on re-index.** `entities.sidecar` used to
  keep the first `waypoint.yaml` it saw (`found.sidecar ?? sidecar` in `src/index/writer.ts`). `wp onboard`
  writes a skeleton first, so every service onboarded that way showed `owner=bifrost` and nulls on
  `/service` and in the MCP, while the `sidecars` table was current. The fresh sidecar now wins, and only
  a reference that carries none (a mention from another folder) keeps the stored one. The `sidecars`
  table itself is never pruned, so a reader must check the folder still has live documents (the MCP's
  `SystemMembers` does).
- **`QUERY_LIMIT_MAX` clamps every query.** A domain module asking for more gets silently
  cut; check it before trusting any count on a page.
- The vault is authoritative and belongs to `wp.py` / `cust.py`. orient only ever adds
  `<vault>/.knowledge/`.
- Shared checkout, co-edited by several agents: `git status` before committing, stage
  explicit paths, never `git add -A`, never `git stash`.
