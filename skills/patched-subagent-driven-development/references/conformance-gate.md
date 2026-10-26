# Conformance Gate (P1)

Run before the first line of code. The gate is the guarantee; the verifier is
the second net.

## Inputs

- spec (authority) — must have an Acceptance Criteria table with IDs and a
  status of Approved. A Draft spec is a stop, not a warning.
- plan — must have a Spec Coverage table, per-task Type, and a Definition of
  Done.
- ledger and workspace.

## Outputs

- conformance.md: one row per acceptance ID.
- gate-check JSON: PASS/FAIL plus missing IDs, extra IDs, missing task types,
  and spec-hash status.
- probe evidence: command and output for every gate.

## C1 — traceability

Every acceptance ID in the spec appears exactly once in the plan's Spec
Coverage table, with a task and an evidence test/probe. Every task has a Type
(apply or build); a task with no acceptance ID must declare itself scaffolding.
The plan also has a Definition of Done (see below); a plan that only says
"tests pass" is not done.

Run:

~~~bash
python scripts/gate-check.py --spec docs/specs/<spec>.md --plan docs/plans/<plan>.md
~~~

The script exits 1 on FAIL. It does not replace judgment: it proves presence,
not semantics.

## C2 — negative probes

For every gate, threshold, or exact-format rule, run the mutation that must
make it fail. A gate that cannot fail is decoration.

Examples from a real run:

| Probe | Expected |
|---|---|
| delete a label line from the rendered prompt | coverage_missing returns non-empty |
| replace the bootstrap resampler with a no-op | interval test fails |
| change the inline separator from "：" to "=" | spec §4.2 check fails |
| omit --s2-spec | dry run warns or refuses |
| remove a hash from metrics.json | A1 evidence check fails |

Record the command and the observed output in conformance.md. A probe that was
not run is a FAIL, not a PASS.

## C3 — interfaces

Producer signature vs consumer call, per batch. The plan's Interfaces block is
the contract; the Consumer test names who calls it and what happens on failure.

## C4 — rulings

Every controller ruling that overrides plan text is checked against the spec.
Spec wins. A ruling that changes a pre-registered acceptance item, threshold,
analysis definition, or scope is a "consequential ruling": stop and ask the
human. Everything else is yours to rule and record.

## Definition of Done

Read the plan's Definition of Done, not a generic rule. It must name:

- the acceptance evidence (IDs),
- an end-to-end command and its fixture/stub,
- the full-suite run,
- what is deferred to the human and the command they will run.

A green unit suite alone is not completion. If the plan has no Definition of
Done, the gate fails: the executor would otherwise invent one.

## C5 — environment

Exact paths, sizes, hashes, and data files referenced by the plan exist, or
are marked human-gated. Missing inputs are not "handled later"; they are a
gate finding.

## conformance.md row

~~~text
| id | spec line | plan step | check | evidence (command/output) | verdict |
| A1 | design.md:220 | plan:268 | C2 probe | pytest ...; metrics.json lacks hashes | FAIL -> R18 |
~~~

## Ruling format

~~~text
R18 <what you decided> — <why> — <what it costs if wrong>
~~~

One line in the ledger; the long argument stays in conformance.md.

## Time box

30 minutes for a ~1,000-line plan. If it exceeds that, hand the C2 probes to a
verifier — not the implementation to an implementer.
