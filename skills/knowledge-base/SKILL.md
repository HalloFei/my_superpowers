---
name: knowledge-base
description: Use when adding, moving, archiving, or auditing documentation in any workspace that uses the kb protocol — including questions like "is this doc current?", "where did spec X go?", "archive the old specs", or when the docs tree looks messy. Also use before writing a new spec/plan, and when a session needs the authoritative status of a design document.
---

# Knowledge base protocol (kb)

One engine, one schema, many workspaces. **The rules live in this skill directory;
a workspace holds only paths.**

- Engine: `scripts/kb.py` (stdlib only, Python 3.8+)
- Rules: `schema.yaml` (status vocabulary, per-type lifecycle, transitions, index columns, header fields)
- Decision records: schema type `decisions` (opt-in; see [Decisions](#decisions-opt-in))
- Decisions: `decisions.md` (why index-as-truth, why superseded/historical is a field, why final is type-scoped)

## Non-negotiables

1. **Never hand-edit the indexed state.** Change status via `kb set-status` or `kb archive`;
   the tables in `docs/INDEX.md` and `docs/archive/INDEX.md` are generated.
2. **Archived content is frozen.** Only the retrieval flow may reopen it: move back with
   `kb`/git, mark a new revision, then edit.
3. **Workspaces never copy the schema.** If a workspace needs different paths it writes
   `docs/kb.yaml` (paths only, no rules).
4. **Status vocabulary** (closed set): draft / active / final / archived.
   - `final` is allowed **only** for plans and reviews (terminal records).
   - living docs (framework, specs, knowledge, ops) go draft → active → archived.
   - `superseded` vs `historical` is the `superseded_by` column of an archived row,
     not a status.
5. **Decision records are opt-in.** Map `decisions: docs/decisions` in `docs/kb.yaml`
   to enforce ADR ids, `Topic:` uniqueness, and the `Decision:` / `Spec:` bindings.
   Unmapped workspaces are unaffected.

## Commands

```bash
KB=~/.dsh/skills/knowledge-base/scripts/kb.py
python $KB check                    # validate: index<->tree, statuses, sha256 freeze, links
python $KB index                    # regenerate both tables (preserves statuses/reasons)
python $KB status  docs/specs/x.md  # what is it?
python $KB set-status docs/specs/x.md final
python $KB archive docs/plans/y.md --superseded-by docs/specs/z.md --reason superseded
python $KB refs ADR-0019           # active docs still binding that ADR (decision workspaces)
python $KB hook --install           # install the git pre-commit gate (runs check)
```

Run from the workspace root (or pass `--root DIR`). No config? `kb` walks up looking
for `docs/kb.yaml`.

## New document

1. Put it in the type directory (`docs/specs/`, `docs/knowledge/`, ...).
2. `python $KB index` — it appears with the type's default status.
3. Set the real status with `kb set-status`; for a new spec the default is `draft`.

## Decisions (opt-in)

Do this only in a workspace whose `docs/kb.yaml` maps `decisions: docs/decisions`.

- An ADR lives at `docs/decisions/NNNN-<slug>.md`; its id is `ADR-NNNN`.
  **Location is the status**: the active tree means effective; `docs/archive/decisions/`
  means superseded / absorbed / withdrawn and frozen (sha256). ADRs carry no status header.
- Every ADR declares `**Topic:** tag[, tag]`. A topic may have only one `active` ADR.
- A spec declares `**Decision:** ADR-NNNN[, ...]` (or `N/A — reason`); a plan declares
  `**Spec:** docs/specs/x.md` (or `N/A — reason`). Bindings must resolve to an
  **active** target: binding to an archived ADR fails `check` and names the successor.
- Prose mentions of archived decisions are not checked; only binding fields are.
- `kb refs ADR-NNNN` lists the active docs that still bind that ADR — run it before
  archiving the ADR; that list is the blast radius.
- Archive keeps the id: `kb archive docs/decisions/0004-x.md --superseded-by ADR-0019 --reason absorbed`.
- The cascade is intentional: when an ADR is archived, every spec/plan binding it fails
  `check` until you re-point the field (and add an `**Amended:**` line), archive that doc,
  or demote the reference to prose.
- No draft ADRs: a proposal belongs in a spec or an issue; an ADR records a decision already made.

## Archiving

1. `python $KB archive <path> [--superseded-by <successor>] [--reason <vocab>]`
   (uses git mv when tracked, then rebuilds both tables and records the sha256).
2. Never edit the file after archiving; `kb check` fails on any byte change.

## When `kb check` fails

- "missing from active index" → run `kb index`, then set the intended status.
- "invalid status" → set-status to a value allowed for that type.
- "frozen archive changed" → you edited an archived file; retrieve it properly.
- "broken link" → fix the referring document (active docs only; archived links may dangle).

## Reporting

After any change, run `kb check` and paste its one-line result. Do not claim the docs
tree is consistent without that line.
