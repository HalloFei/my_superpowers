# Decisions — KB lifecycle protocol (ADR)

Append-only. Each decision records what was decided, why, and what it overrides.
Never rewrite an accepted decision; supersede it with a new numbered entry.

## KB-1. State lives in the central index, not in per-file headers

**Decision (2026-11-03).** The authoritative status of a document is its row in
`docs/INDEX.md` (active tree) or `docs/archive/INDEX.md` (archived). Files carry no
status header.

**Why.**
1. Archived files are frozen by rule; adding a header to them is a content change,
   so a per-file header cannot be the authority for archived docs anyway.
2. The repo had 88 free-text `Status:` lines in incompatible formats; a second
   copy of status in a header would drift.
3. The index is generated and checked by `kb`, so it cannot drift silently.

**Consequence.** `docs/specs/2026-09-22-judge-review-stats-design.md` proposed a
per-file `Active:` header; this ADR supersedes that part of it.

## KB-2. "superseded" vs "historical" is a field, not a status

Both mean "do not act on this"; they differ only in whether there is a successor to
redirect to. That difference is one pointer, so it is the `superseded_by` column of
an `archived` row. A publishing layer may derive the two labels later without
changing storage.

**Consequence.** The status vocabulary stays closed at four values; no `superseded`
or `historical` status exists, and adding one would be a schema break.

## KB-3. `final` is type-scoped: plans and reviews only

`final` means "terminal record: executed/observed, frozen, citable but not an
instruction". Living artifacts (framework, specs, knowledge, ops) never reach a
terminal event: they are either current authority (`active`, revisable) or replaced
(`archived`). Marking a living doc `final` would freeze the authority while reality
keeps moving.

**Why the distinction is operational, not cosmetic.**

| | `active` | `final` |
|---|---|---|
| What the reader does with it | acts on it — it is authority or an instruction | cites it / reproduces it, does not execute it again |
| May it change | yes, append a Revision | no, errata only |

For a plan this is the whole point: an `active` plan says "do this"; a `final` plan
says "this was done, do not run it again". For specs and knowledge the distinction
does not exist — a spec is the design of record, so implementation is not its
terminal event (the code moves, the spec gains a Revision).

**Consequence.** A realized plan is `final`; authority returns to the spec plus the
code. `plans` may legally go `active → archived` directly, but that is discouraged:
it loses the "record, not instruction" signal that prevents a re-run.

## KB-4. One engine, thin interfaces

The rules live in `schema.yaml` + `scripts/kb.py` in this skill directory. Workspaces
hold only a `docs/kb.yaml` with path overrides. MCP is a future `kb mcp` wrapper over
the same engine; a DSH plugin is only justified if write-time interception is needed.

**Why.** A copied schema is a second source of authority, and the two copies drift
the moment one workspace tunes a rule. Paths are the only thing that legitimately
varies per workspace.

## KB-5. Archived content is frozen; retrieval re-opens it

An archived file may only change by the retrieval flow: move it back into the active
tree, mark a new revision, then edit. `kb check` enforces the freeze with sha256.

**Why.** The archive is evidence. If archived bytes can change, "what did we believe
on 2026-09-17" stops being answerable.

## KB-6. Lifecycle state machines (per type family)

```
living  (framework / specs / knowledge / ops)
    draft ──approve──> active ──replaced|retired──> archived
      └────────────────abandon──────────────────────^

terminal (plans / reviews)
    draft ──start──> active ──done──> final ──no longer cited──> archived
      └────────────────abandon──────────────────────────────────^
```

The only backward edge is retrieval (`archived → draft|active`), and it requires a
new Revision marker. `kb check` rejects any other transition.

## KB-7. Status assignment for the 2026-11-03 migration

Applied once, to the 38 active files of this workspace:

- framework 1 → `active`
- specs 20 → `active`, except the two under review → `draft`
- plans 3 → `final` (all executed; kept as reproduction entry points)
- knowledge 10 → `active`
- reviews 2 → `final`
- ops 2 → `active`

**Why plans are `final` and not `archived`.** They are still cited by the current
campaign and by code docstrings, so they must stay in the active tree — but they must
not read as pending instructions.

## KB-8. For decision records, location is the status

An ADR is a record of a decision already made. It has no `draft` and no status header:
a file in `docs/decisions/` is `active` (effective), and a file in
`docs/archive/decisions/` is `archived` (superseded / absorbed / withdrawn, sha256-frozen).

**Why.** A per-file status is a second source of truth. The pi-ab-sdk corpus proved the
failure mode: `ADR-0014` / `ADR-0017` carry `**Active:** pending`, a value outside its own
enum, and nothing checks it. Deriving status from location means the drift is structurally
impossible, and it reuses kb's existing active-tree/archive-freeze machinery unchanged.

**Consequence.** Changing a decision = write a new ADR on the same `Topic`, then archive the
old one with `--superseded-by ADR-NNNN`. No in-place status edits, no generated header blocks.

## KB-9. Stable ADR ids; binding and mention are different relations

References to decisions use the stable id `ADR-NNNN`, resolved through the active and archive
indexes; moving a file to the archive never breaks a reference. Only **binding fields** are
validated (`specs` `Decision:`, `plans` `Spec:`), and a binding must resolve to an `active`
target. Prose mentions of archived decisions are allowed and unchecked.

**Why.** A spec's relationship to a decision is either "this is the authority I now obey"
(a live dependency, which must follow the current authority) or "this is where I came from"
(provenance, which must keep pointing at the old record). One rule cannot serve both without
falsifying the design date. Binding is the live half; a re-point records the change in
`**Amended:**`, and the archive's `superseded_by` chain plus git hold the history.

**Consequence.** Archiving an ADR fails `check` for every active doc still binding it. That
cascade is the impact analysis; `kb refs ADR-NNNN` prints the same list before the move.

## KB-10. The decision protocol is opt-in and has no draft state

`decisions` is a schema type, but the protocol only switches on when a workspace maps
`decisions: docs/decisions` in `docs/kb.yaml`. Unmapped workspaces keep the old behaviour
byte for byte. ADRs are born `active`; proposals live in a spec or an issue.

**Why.** The rules add required header fields to specs and plans. Two live workspaces
(24 specs, 5 plans) had zero `Decision:` fields and only 3/5 parseable `**Spec:**` lines;
enforcing globally would have broken them on upgrade. Paths are the only thing a workspace
declares, so mapping the type is the adoption action.

**Consequence.** No `schema_version` bump: additive and opt-in.

## KB-11. One topic, one authoritative ADR

Every ADR declares `**Topic:**` with one or more stable tags. Within the active tree each tag
may belong to at most one `active` ADR. A new ADR that absorbs old ones claims their tags,
and the old files are archived.

**Why.** This is the only mechanically checkable form of pi-ab-sdk's R5a ("one issue, one
authoritative ADR"). Without a comparable topic key, two live ADRs can each claim authority
and every citation is "correct" while pointing at different conclusions.

**Consequence.** The tag granularity is a human judgement — the engine guarantees uniqueness,
not that the topic was carved correctly.

