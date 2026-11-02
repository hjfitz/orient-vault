---
tags: [waypoint, ui-toolkit]
verified: '2026-08-24'
verified_paths: []
title: ui-toolkit — known context
---

# ui-toolkit — known context

`known-context.md` is exempt from staleness checks — this is interview/investigation
truth, not a claim about current source. Re-verify against code before trusting a
specific implementation detail below.

## Ownership

Confirmed 2026-08-24: this is the `gfs-ecm`/`ui-core` team's repo (`CXD`
tickets), not Fuse-owned. **Harry is a pure consumer** — but **Humby, on
Harry's own team, is expected to start contributing here.** If a future
agent is asked to make a change in this repo on Harry's behalf, that's a
new development (previously he had zero contribution history) — don't
assume established familiarity with this codebase's review norms just
because other ilg-platform repos have it.

## A confirmed, still-live bug (snapshot 2026-08-24): `SelectTrigger`'s icon stacks above its label

Verified directly against the current clone (2026-08-24, version 1.28.3):
`packages/ui-toolkit/src/shadcn/select.tsx`'s trigger class carries
`data-[slot=select-value]:*:flex` (and the matching `line-clamp-1`/
`items-center`/`gap-2` variants) — but the trigger's own `data-slot` is
`select-trigger`, not `select-value`, so this variant **never matches**.
Canonical shadcn has the arrow the other way round:
`*:data-[slot=select-value]:flex` ("children carrying this slot get
flexed"), not "this element carrying the slot flexes its children". The
practical effect: any `SelectItem` whose children are `<Icon /> Label`
renders with the icon stacked **above** the text in the **closed** trigger
— the open dropdown list looks fine (`SelectItem` uses the correctly-ordered
`*:[span]:last:flex`), which is what makes this read like a one-off
rendering quirk rather than a toolkit-wide bug.

**Deliberately left as known-context only, not escalated, per explicit
instruction during this onboarding pass** — no PR filed, no issue raised.
If a Select trigger anywhere in the Fuse estate (or elsewhere) shows its
icon above its label, this is why; don't chase the icon component itself.
`fuse-ui`'s `add-connector-modal.tsx` carries a local workaround (the
correctly-ordered variant added directly on the trigger's `className`,
which becomes a harmless duplicate once/if this is fixed upstream).

## Unknowns

- Whether Humby's contribution work has started, and what area of the
  toolkit it touches — not investigated during this onboarding pass.
- Whether the `SelectTrigger` bug has been reported upstream by anyone
  else, independent of this pass's deliberate choice not to escalate it.
