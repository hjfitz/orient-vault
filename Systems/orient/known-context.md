---
tags:
- system
- orient
verified: '2026-11-03'
title: orient — known context
---
# orient — known context

Decisions and hazards that source cannot tell you. Interview truth — exempt from commit
anchors by convention.

## Decisions

**The vault is plain Markdown, forever.** Every design choice defers to "could Obsidian and
`grep` still read this with the app deleted?" Frontmatter is edited raw rather than
re-serialised, so unknown keys survive byte-for-byte.

**The index is disposable, the vault is not.** SQLite can be deleted and rebuilt at any time.
Nothing may live only in the index.

**Membership over nesting.** A service declares its system in its own `waypoint.yaml`;
`Systems/` holds no member list. Two sources of truth would rot the moment a service was
onboarded. Services deliberately stay flat under `Engineering/` — `locate()` resolves
`ENG/<name>`, and every `verified_paths` and wikilink assumes it.

**Docs are anchored to code, not to a date.** `verified_sha` + `verified_paths` means
`wp stale` can say a doc is behind its source. A doc that cannot be anchored (interview truth,
or cross-repo system docs) is exempt on purpose rather than anchored to a lie.

**No LLM calls in the app.** It emits a prompt; Claude Code executes it. Keeps the app fast,
free and offline.

## Diagrams in vault docs

orient renders fenced ```` ```mermaid ```` blocks client-side (mermaid 11.17, dark theme,
`fontFamily: inherit`). A block that fails to parse **degrades to a readable code block**
rather than an empty box, so a broken diagram is visible, not silent.

**Every one of these was probed against the installed version and renders** — use the one
that fits the job rather than defaulting to a flowchart:

| Job | Type |
| --- | --- |
| Topology, flow, a loop | `flowchart` |
| Who calls whom, in order, over time | `sequenceDiagram` |
| Actors and system boundaries | `C4Context` |
| Lifecycle / status machine | `stateDiagram-v2` |
| Data relationships, cardinality | `erDiagram` |
| Contract shapes side by side | `classDiagram` |
| Shape of a system at a glance | `mindmap` |
| What happened when | `timeline`, `gitGraph` |
| Trade-off placement | `quadrantChart`, `radar-beta` |
| Proportion / flow volume | `pie`, `sankey-beta`, `treemap-beta`, `xychart-beta` |
| Infra grouping | `architecture-beta`, `block-beta` |
| Work state | `kanban` |
| Wire format | `packet-beta` |

**Conventions learned the hard way.** A diagram must be *easier* than the prose it replaces —
the first cut of `Systems/fuse/architecture.md` used nested subgraphs with a config-service
fan-out to four nodes and rendered as an unreadable sprawl of crossing edges. Keep the spine
linear, push ambient relationships (config, observers) into prose beneath, and let the
diagram carry one idea. If it needs a legend to read, it is doing too much.

## Hazards

**Shared checkout, many agents.** `~/projects/orient` is co-edited by several concurrent
sessions and often carries a multi-vintage pile of uncommitted work. Committing sweeps the
whole tree — check `git status` and ask before committing someone else's in-flight edits.
Never `git stash`: the stash stack is shared.

**Every repo has a private GitHub remote (snapshot 2026-11-03):** `hjfitz/orient`, `hjfitz/orient-writers` and `hjfitz/orient-vault`. Each clone pins its key with `core.sshCommand`: the personal key through `~/.ssh/config-self` on the laptop, and a per-repo deploy key on the VM. The old local stand-in `~/.local/state/orient/vault-remote.git` is a stale backup and can be deleted.

**Never use `gitswitch` for anything unattended.** It swaps the whole global SSH config between the personal and work accounts. The orient repos pin the personal key per repo with `core.sshCommand "ssh -F ~/.ssh/config-self"`.

**The vault commits itself.** `orient-vault-sync` commits everything every 90 s and after every writer's kick. Anything dropped into the vault is committed and pushed unless `.gitignore` excludes it. Keep secrets, audio and per-machine state out, or ignore them first.

**Writers are linked into `~/.claude` by directory, never by file.** Claude Code's Edit and Write refuse to write through a symlinked file, but write through a symlinked directory. A new skill goes in `orient-writers/skills/<name>/` with a directory link.

**The retired `sync-claude-config` copier ships far more than skills.** It copies CLAUDE.md, settings, the statusline, agents, hooks, project memory, `~/code` and the MCP servers with their tokens from `~/.claude.json`. It is disabled (unit files kept). Re-enabling it would overwrite the VM's git-managed writers and leak tokens.

**A destructive job wired into a service's start runs the moment it deploys.** Run its dry run (`orient-scribe prune -dry-run`) *before* deploying the build. Audio for four 2026-10-19 recordings was lost this way.

**The VM cannot connect to the laptop.** The workstation image sets `AllowTcpForwarding local` (ilg-platform/images, checked by its smoke test). Anything that goes VM → laptop has to be pulled by the laptop: the scribe relay polls, and the vault follower tails over ssh. Don't design a feature that needs the VM to reach the laptop.

**The laptop's top bar presses the VM's buttons with a copy of the VM's write token** (`~/.config/orient/peer-write-token`, from the VM's `~/.local/state/orient/write-token`). orient mints that token lazily on first use, so a fresh VM has none until something asks. If the VM ever mints a new one, the desk gets 401 until it's copied again.

**`pnpm deploy:web` once hung for 10+ minutes in static generation** (2026-11-09, laptop), with a prerender worker idle in `epoll` and no network wait. orient-web stays stopped meanwhile. Killing the process group and rerunning built normally. If it recurs, look at the prerender workers before suspecting the code.

**`wp tick --note` drops the `done:` stamp if the note contains the sha.** `cmd_tick` checks `sha not in new` as a substring. Leave the commit out of the note.

**Config is memoised at boot.** Editing `.knowledge/config.yaml` needs the dev server
restarted, not just a reload. Kill by PID — `pkill -f` matches the agent's own shell.

**A meta-schema change needs more than a reindex:** `systemctl --user restart
orient-index.service` then `POST /api/reindex`, or a re-derived field stays null while the
watcher reports healthy throughout.

**Hand-mirrored constants.** orient copies `wp.py`'s doc-kind list and frontmatter rules.
Changing one without the other fails silently rather than loudly.

## Related

[[fuse]] and [[ilg-platform]] are what this system is about.
