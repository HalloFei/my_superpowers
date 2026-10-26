# Implementer Prompt (T2 only)

Use only when the batch is context-separable. Do not use it for apply tasks;
those belong in the main loop.

~~~text
Subagent:
  description: "Implement batch <N>: <names>"
  prompt: |
    You are implementing batch <N> of <plan name>.

    Read this first — it is your requirements, with the exact values to use
    verbatim: <brief path>

    Binding spec lines (verbatim, with line refs; 5–15 lines, not the full spec):
    <the slice>

    Interfaces from earlier tasks (exact signatures):
    <signatures>

    Repo root: <path>. Branch: <branch>.
    Do not touch: <foreign modified files / paths>.

    ## Your job
    1. Apply or build exactly the brief. No extra features, no extra modules.
    2. Run the named focused test after each task. Run the full suite once
       before the batch commit — not before every commit.
    3. Commit once per task with the exact message from the brief.
    4. Write the full report to <report path>. Then reply with only:
       Status: DONE | DONE_WITH_CONCERNS | NEEDS_CONTEXT | BLOCKED
       Commits: <sha + subject, one per task>
       Test: <one line>
       Concerns: <if any>
       Report: <path>

    ## Rules
    - No subagents. No reviewer. Review comes from the controller after your
      report; one you spawn duplicates it at full cost.
    - Do not read the full spec or plan. If the brief is ambiguous, report
      NEEDS_CONTEXT with the exact question.
    - If you exceed 30 steps without a green test, stop and report BLOCKED
      with what you tried and what you need.
    - Stage explicit paths. Never git add -A or git commit -a.
~~~

## Report file

The report covers: what changed per task, the exact test commands and results,
files changed, self-review findings, and concerns. The short message is the
only thing that enters the controller's context.
