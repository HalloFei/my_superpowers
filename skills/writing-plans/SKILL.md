---
name: writing-plans
description: Use when you have a spec or requirements for a multi-step task, before touching code
---

# Writing Plans

## Overview

Write comprehensive implementation plans assuming the engineer has zero context for our codebase and questionable taste. Document everything they need to know: which files to touch for each task, code, testing, docs they might need to check, how to test it. Give them the whole plan as bite-sized tasks. DRY. YAGNI. TDD. Frequent commits.

Assume they are a skilled developer, but know almost nothing about our toolset or problem domain. Assume they don't know good test design very well.

**Announce at start:** "I'm using the writing-plans skill to create the implementation plan."

**Context:** If working in an isolated worktree, it should have been created via the `using-git-worktrees` skill at execution time.

**Save plans to:** `docs/superpowers/plans/YYYY-MM-DD-<feature-name>.md`
- (User preferences for plan location override this default)
- If the project keeps a plan index or documents its own document-metadata convention (for example `docs/plans/README.md`), follow it and record the new plan there.

## Scope Check

If the spec covers multiple independent subsystems, it should have been broken into sub-project specs during brainstorming. If it wasn't, suggest breaking this into separate plans — one per subsystem. Each plan should produce working, testable software on its own.

## Spec Freeze Gate

Do not write a plan from a moving spec. Before the first task:

- the spec status is Approved (not Draft, not "pending review");
- its Acceptance Criteria table is complete: every row has an ID, a binary
  criterion, a runnable evidence command, and a fails-if condition;
- no TBD, open question, or "to be decided" remains in scope.

Record the spec's sha256 in the plan header. If the spec changes after this
point, stop: re-open the affected acceptance rows, re-run the Spec Coverage
table, and re-gate before touching code. A plan written against a moving spec
is the most expensive defect in this workflow.

## File Structure

Before defining tasks, map out which files will be created or modified and what each one is responsible for. This is where decomposition decisions get locked in.

- Design units with clear boundaries and well-defined interfaces. Each file should have one clear responsibility.
- You reason best about code you can hold in context at once, and your edits are more reliable when files are focused. Prefer smaller, focused files over large ones that do too much.
- Files that change together should live together. Split by responsibility, not by technical layer.
- In existing codebases, follow established patterns. If the codebase uses large files, don't unilaterally restructure - but if a file you're modifying has grown unwieldy, including a split in the plan is reasonable.

This structure informs the task decomposition. Each task should produce self-contained changes that make sense independently.

## Task Right-Sizing

A task is the smallest unit one implementer can complete without needing
another task's code. Draw boundaries by context, not by technical layer: if
task B cannot build or pass its tests without task A's output, they are one
task. Fold setup, configuration, scaffolding, and documentation into the
task whose deliverable needs them. Each task still ends with an
independently testable deliverable.

Do not size tasks for a reviewer's gate: the review unit is the batch, not
the task. A task that is only "small enough to review" but shares an
interface with its neighbor creates the telephone game this workflow is
trying to avoid.

## Bite-Sized Task Granularity

**Each step is one action (2-5 minutes):**
- "Write the failing test" - step
- "Run it to make sure it fails" - step
- "Implement the minimal code to make the test pass" - step
- "Run the tests and make sure they pass" - step
- "Commit" - step

**Type: apply** — the plan already contains the test and the code. Do not
re-enact RED/GREEN: the plan's test is the RED artifact. Steps are: apply the
code, run the named test, run the full suite once at the batch boundary, commit.

**Type: build** — keep the five-step RED/GREEN cycle above.

## Plan Document Header

**Every plan MUST start with this header:**

```markdown
# [Feature Name] Implementation Plan

**Status:** Draft (pending review) | Approved | Archived (YYYY-MM-DD)
**Created:** YYYY-MM-DD
**Last updated:** YYYY-MM-DD
**Active:** active | archived

> **For agentic workers:** REQUIRED SUB-SKILL: Use patched-subagent-driven-development (recommended for build tasks) or executing-plans (apply-heavy or ≤3 tasks) to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** [One sentence describing what this builds]

**Architecture:** [2-3 sentences about approach]

**Tech Stack:** [Key technologies/libraries]

**Spec:** [path to the spec/design doc this plan implements — the plan
argues from the spec, so the spec travels with it; executors read both]
**Spec hash:** sha256:<hex, 12+ chars>

## Global Constraints

[The spec's project-wide requirements — version floors, dependency limits,
naming and copy rules, platform requirements — one line each, with exact
values copied verbatim from the spec. Every task's requirements implicitly
include this section.]

## Spec Coverage

| Spec ID | Task | Evidence (test/probe) |
|---------|------|-----------------------|
| A1 | Task 2 | tests/test_x.py::test_y |
| A2 | Task 2 | tests/test_x.py::test_z (negative probe: delete the token) |

Every acceptance ID from the spec appears exactly once. A task with no
acceptance ID is allowed only for scaffolding, and must say so. This table
is what the execution gate verifies; without it the gate has to re-derive
the matrix from the spec.

## Definition of Done

- Every acceptance ID in scope has PASS evidence.
- End-to-end: `<command>` runs on `<fixture or stub>` and produces
  `<artifact>`. Unit tests alone are not completion.
- The full suite is green once.
- No open Critical/Important.
- Human-gated: `<what is deferred>` — the human runs `<command>`.

---
```

**Document metadata:** the four fields above are the same ones the
brainstorming step puts on the spec — a plan is a document too, and a plan
with no status is indistinguishable from a stale one. Fill them with real
values; never leave the placeholder text in a saved plan:

- **Status** — `Draft (pending review)` while the human still has to approve
  the plan (or its execution mode); `Approved` once they have;
  `Archived (YYYY-MM-DD)` when the plan is superseded or fully executed.
- **Created** / **Last updated** — `YYYY-MM-DD`. Bump `Last updated` on every
  edit.
- **Active** — `active`, or `archived` together with an `Archived (YYYY-MM-DD)`
  status plus a `**Reason:**` line and, if useful, a `**Note:**` line.
- **Spec** — the path to the spec this plan implements. For bounded work with
  no spec, write `N/A` and one clause explaining why.

A project that documents its own document-metadata convention overrides this
block — copy that convention's exact field names and values (pi-ab-sdk, for
example, defines it in `docs/specs/archive/README.md` and repeats it in
`docs/plans/README.md`).

## Task Structure

````markdown
### Task N: [Component Name]

**Files:**
- Create: `exact/path/to/file.py`
- Modify: `exact/path/to/existing.py:123-145`
- Test: `tests/exact/path/to/test.py`

**Type:** <apply | build> — apply: the plan contains the complete code;
build: only the interfaces, the implementer designs the body.

**Interfaces:**
- Consumes: [what this task uses from earlier tasks — exact signatures]
- Produces: [what later tasks rely on — exact function names, parameter
  and return types. A task's implementer sees only their own task; this
  block is how they learn the names and types neighboring tasks use.]
- Consumer test: [who calls this, with what shape, and what must happen
  on failure — the interface is not done until a consumer can use it]

- [ ] **Step 1: Write the failing test**

```python
def test_specific_behavior():
    result = function(input)
    assert result == expected
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/path/test.py::test_name -v`
Expected: FAIL with "function not defined"

- [ ] **Step 3: Write minimal implementation**

```python
def function(input):
    return expected
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/path/test.py::test_name -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/path/test.py src/path/file.py
git commit -m "feat: add specific feature"
```
````

## No Placeholders

Every step must contain the actual content an engineer needs. These are **plan failures** — never write them:
- "TBD", "TODO", "implement later", "fill in details"
- "Add appropriate error handling" / "add validation" / "handle edge cases"
- "Write tests for the above" (without actual test code)
- "Similar to Task N" (repeat the code — the engineer may be reading tasks out of order)
- Steps that describe what to do without showing how (code blocks required for code steps)
- References to types, functions, or methods not defined in any task

## Self-Review

After writing the complete plan, look at the spec with fresh eyes and check the plan against it. This is a checklist you run yourself — not a subagent dispatch.

**1. Coverage table:** Every acceptance ID from the spec appears in the Spec Coverage table, and every row names a task and an evidence test/probe. An unmapped ID, a row without evidence, or a task with no ID (other than declared scaffolding) is a gap. Fix it before handoff.

**2. Negative probes:** For every gate, threshold, or exact-format rule, name the mutation that must make its test fail — delete the guarded token, replace the resampler with a no-op, change the separator, omit the flag. If you cannot name one, the test is decorative: fix the test or the gate.

**3. Placeholder scan:** Search your plan for red flags — any of the patterns from the "No Placeholders" section above. Fix them.

**4. Type consistency:** Do the types, method signatures, and property names you used in later tasks match what you defined in earlier tasks? A function called `clearLayers()` in Task 3 but `clearFullLayers()` in Task 7 is a bug.

**5. Test budget:** One test per acceptance behaviour. Do not write tests for pure transcription. The full suite runs once at the baseline, once per batch, and once at the final gate — not before every commit.

**6. Definition of Done:** the plan names the end-to-end command and its fixture, not just the tests; and it names anything deferred to the human. A plan that only says "tests pass" is not done.

If you find issues, fix them inline. No need to re-review — just fix and move on. If you find a spec requirement with no task, add the task. If a task contradicts the spec, the spec wins.

## Plan Review

If the plan has more than 3 tasks, or any task carries an acceptance gate,
dispatch the plan document reviewer before handoff:
[plan-document-reviewer-prompt.md](plan-document-reviewer-prompt.md), with
the plan, the spec, and the Spec Coverage table. One pass; fix findings in the
plan, not in the code. The reviewer returns a status and the acceptance IDs it
could verify.

Skip this for small plans (≤3 tasks) where the coverage table already accounts
for every ID.

## Execution Handoff

After saving the plan, present a one-page **Execution Brief** in chat:

- Coverage: A1→Task 1, A2→Task 1, ... (the IDs and where they are proven)
- Task groups and types: Task 1–3 apply; Task 4–5 build; ...
- Dispatch plan: inline for apply/≤3 tasks; one implementer per context
  cluster for build tasks; parallel researchers only for independent work
- Test budget: baseline 1, per batch 1, final 1
- Top 3 risks and the stop conditions

Then ask: "Approve this execution brief? The full plan is at `<path>` for
reference; I'll verify the rest mechanically."

Choose one execution mode from the brief:

1. **Inline** — for apply-heavy plans, ≤3 tasks, or tightly coupled work:
   execute in this session via executing-plans.
2. **Patched SDD** — for context-separable build work with ≥2 batches:
   use patched-subagent-driven-development. Default main loop;
   subagents only for context-separable batches.
3. **Original SDD** — only when the plan is genuinely task-parallel with
   disposable context; use subagent-driven-development.

Default to inline for apply-heavy plans. Do not recommend subagent-driven
execution by reflex: a fresh implementer per task is a cost, not a virtue.
