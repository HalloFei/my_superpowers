---
name: patched-subagent-driven-development
description: Use when executing a written implementation plan with two or more tasks in the current session, especially when the plan already contains code or when a previous subagent-driven run cost more in review than implementation.
---

# Patched Subagent-Driven Development

Execute a written plan with the main loop by default. Dispatch a subagent only
when it buys something the loop cannot: an isolated context or parallel work.
Gate the plan against the spec before the first line of code.

**Core principle:** the plan is the argument, the spec is the authority, the
artifact is the proof. A fresh implementer per task is a cost, not a virtue.

## When to Use

- You have a written plan and the spec it implements.
- The work has 2+ tasks or touches more than a couple of files.
- You need to recover from compaction or hand off between sessions.

**Do not use** for a single task, a <100-line change, or pure exploration.
Use `dispatching-parallel-agents` for research fan-out.

## Decision Table

| Tier | Trigger | Who | Review |
|---|---|---|---|
| T0 apply | plan contains the complete code and test | main loop | tests only |
| T1 build | ≤2 files, interfaces fixed, no long wait | main loop | risk-triggered |
| T2 delegate | >3 files or >400 LoC, context-separable, or long-running | 1 implementer | 1 verifier per batch |
| T3 explore | independent, disposable, parallel | N researchers | aggregate |

Default to T1. A dispatch prompt containing a ruling means the decision was
made in the parent: implement it there, or write it into the plan first.

## The Loop

1. **P0 — workspace + ledger.** Reuse `scripts/sdd-workspace` and
   `scripts/task-brief`. The ledger's first line names the plan; one line per
   batch.
2. **P1 — conformance gate.** From this skill's base directory, run
   `python scripts/gate-check.py --spec SPEC --plan PLAN --strict`. It checks the spec
   status and hash, the Spec Coverage table, task types, the Definition of
   Done, and the evidence for every acceptance ID. Then run the negative probes for every gate (delete the
   token, no-op the resampler, change the separator). Do not dispatch until
   every row is PASS or RULED. See
   [references/conformance-gate.md](references/conformance-gate.md).
3. **P2 — apply or build.** T0: apply the plan's code, run the named test,
   commit. T1: build in the loop with TDD-lite. T2: dispatch the implementer
   with the brief + interfaces + binding spec slice; never the whole spec.
4. **P3 — verify.** T2/risk only: one verifier per batch, with the spec, the
   diff package, and the coverage table — not the brief or plan. The verifier
   is a second net, not a guarantee; confirm every finding with a command or a
   spec line.
5. **P4 — fix.** Critical/Important only, ≤2 rounds. Round 1 resumes the same
   implementer; round 2 is fresh. Re-review only when the fix touches an
   acceptance gate; else rerun the probe. Minors go to deferred.md.
6. **P5 — final gate.** Run the plan's **Definition of Done**: acceptance
   evidence, the E2E command on its fixture, the full suite once, and no open
   Critical/Important. A green suite alone is not completion. No second fix wave.

## Hard Rules

- **No polling.** After a dispatch, do local work or end the turn.
  `list_agents` is allowed once on wake, never while waiting.
- **Budgets.** 30 steps per child (45 hard), 400 LoC / 3 production files per
  batch, 150k context, ≤5 dispatches and ≤2 fix rounds per plan.
- **Files, not pastes.** Report/review/decisions are files; the message is ≤15
  lines (implementer) or ≤20 (verifier). Dispatch prompt ≤6k chars.
- **Tests.** Baseline once, full suite once per batch, focused tests ≤2 per
  task. No RED/GREEN theatre for apply tasks. No test for transcription.
- **No model routing.** This runtime exposes no model parameter for subagents.
  Cost control is dispatch count × context × turns.
- **Consequential rulings.** If a ruling changes a pre-registered acceptance
  item, threshold, analysis definition, or scope, stop and ask the human.
  Everything else is yours to rule and record in the ledger.
- **Stop** only for: irreversible/destructive work, security, out-of-worktree
  side effects, a plan that is all guesswork, an unreachable spec, or an
  exhausted budget with no ruling.

## Reports

The implementer returns DONE, DONE_WITH_CONCERNS, NEEDS_CONTEXT, or BLOCKED,
plus commits and a one-line test summary. The full report is a file. The
verifier returns Critical/Important findings with file:line and a spec ID;
Minor goes to deferred.md.

## Common Rationalizations

| Excuse | Reality |
|---|---|
| "The plan has the code, but a subagent is cleaner" | You are paying a handoff to copy text. Apply it. |
| "The reviewer will catch a spec mismatch" | The reviewer sees the diff, not absence. Gate the plan. |
| "More tests means more safety" | A test that cannot fail is decoration. Probe it. |
| "The child is still running; let me check" | That check is the poll. End the turn. |
| "One more fix round will converge" | Past round 2, the failure is structural. Rule on it. |

## References

- [Decision table](references/decision-table.md)
- [Conformance gate](references/conformance-gate.md)
- [Testing policy](references/testing-policy.md)
- [Review policy](references/review-policy.md)
- [Cost model](references/cost-model.md)
- Templates: [implementer](templates/implementer.md),
  [verifier](templates/verifier.md), [researcher](templates/researcher.md)
