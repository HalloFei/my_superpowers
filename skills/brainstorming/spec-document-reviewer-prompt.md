# Spec Document Reviewer Prompt Template

Use this template when dispatching a spec document reviewer subagent.

**Purpose:** Verify the spec is complete, consistent, and ready for implementation planning.

**Dispatch after:** Spec document is written to docs/superpowers/specs/

```
Subagent (general-purpose):
  description: "Review spec document"
  prompt: |
    You are a spec document reviewer. Verify this spec is complete and ready for planning.

    **Spec to review:** [SPEC_FILE_PATH]

    ## What to Check

    | Category | What to Look For |
    |----------|------------------|
    | Completeness | TODOs, placeholders, "TBD", incomplete sections |
    | Consistency | Internal contradictions, conflicting requirements |
    | Clarity | Requirements ambiguous enough to cause someone to build the wrong thing |
    | Scope | Focused enough for a single plan — not covering multiple independent subsystems |
    | YAGNI | Unrequested features, over-engineering |

    ## The Seven Elements — a spec is incomplete without all seven

    A spec can be internally consistent, unambiguous and correctly scoped, and
    still be unexecutable because it never answered one of these. Check every one
    and name the ones that are missing:

    | Element | Minimum bar |
    |---------|-------------|
    | Goal | One measurable outcome, independently verifiable — not a list of activities |
    | Context | The current state as fact, each claim traceable to evidence (command / file / run + date); no guess presented as fact |
    | Boundary | In-Scope and Out-of-Scope both stated explicitly |
    | Constraint | Every rule judgeable (a reader can say pass/fail), and a stated precedence when two rules conflict |
    | Acceptance | Binary pass/fail criteria, each naming the evidence that proves it |
    | Edge cases | Behaviour outside the happy path: inputs, dependencies, state, concurrency |
    | NFR | Quantified quality baselines (performance, security, observability, …), or an explicit "none apply, because …" |

    ## Calibration

    **Only flag issues that would cause real problems during implementation planning.**
    A missing section, a contradiction, or a requirement so ambiguous it could be
    interpreted two different ways — those are issues. Minor wording improvements,
    stylistic preferences, and "sections less detailed than others" are not.

    **Any of the seven elements above that is absent — or present but unanswerable —
    IS an issue.** That is a missing section, not a section "less detailed than
    others": report it under Issues, never under Recommendations.

    Approve unless there are serious gaps that would lead to a flawed plan.

    ## Output Format

    ## Spec Review

    **Status:** Approved | Issues Found

    **Issues (if any):**
    - [Section X]: [specific issue] - [why it matters for planning]

    **Recommendations (advisory, do not block approval):**
    - [suggestions for improvement]
```

**Reviewer returns:** Status, Issues (if any), Recommendations
