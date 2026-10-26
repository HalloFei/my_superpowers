# Verifier Prompt (T2 / risk only)

The verifier is a second net, not a guarantee. It checks the diff against the
spec, including absence.

~~~text
Subagent:
  description: "Verify batch <N> against the spec"
  prompt: |
    You are verifying batch <N> against its spec. You are read-only on this
    checkout: do not mutate the working tree, index, HEAD, or branch.

    ## Inputs
    - Spec (authority): <spec path>
    - Diff package: <diff path> (commit list, stat, full diff with context)
    - Spec Coverage table: <path or inline>
    - Implementer report: <report path>

    Do NOT read the task brief or the plan. They are the suspect; your job is
    to check the result against the spec, not to re-derive the plan's intent.

    ## What to check
    1. Every acceptance ID in scope: is the criterion met, and is the evidence
       present? Absence is a finding, not a gap to ignore.
    2. Coverage: every ID has a task and an evidence test/probe; a gate with no
       failing mutation is a finding.
    3. The diff's own quality: error handling, edge cases, hidden coupling.
    4. Only outside the diff when you can name a concrete risk.

    ## Output
    Write the full review to <review path>. Reply with at most 20 lines:
    Verdict: <clean | needs fixes>
    Critical: <ids or none>
    Important: <ids or none>
    Minor: <n> (deferred, do not fix)
    Review: <path>

    Each finding: id, spec line, file:line, what is wrong, why it matters,
    smallest fix. Maximum 10 findings; if more exist, report the top 10 by
    risk and say more exist.

    ## Rules
    - Do not re-run the suite. Run at most one focused command to resolve a
      named doubt.
    - Do not ask for more tests, style changes, or documentation.
    - "Cannot verify from the diff" is allowed, but name what the controller
      should run.
    - Do not dispatch subagents.
~~~

## Severity

Critical = wrong output, data loss, security. Important = an acceptance line is
unmet, a later task builds on it, or the run will waste more than an hour.
Minor = everything else, and it goes to deferred.md.
