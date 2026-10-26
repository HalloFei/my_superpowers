# Review Policy

## When

Only for T2 batches, or when a risk trigger is present:

- auth/permissions, money, destructive operations, concurrency
- public API or an acceptance gate
- >300 LoC of new logic

T0/T1 get no reviewer. The conformance gate, the tests, and the final acceptance
are the checks.

## Inputs

- spec (authority)
- union diff package
- conformance.md / Spec Coverage table
- the implementer's report file

**Not** the brief or the plan. The plan is the suspect; giving it to the
reviewer makes the reviewer grade the plan's own work.

## Finding budget

- Max 10 findings.
- Critical and Important only.
- Minor: one line each to deferred.md. Do not fix, do not re-review.

## Severity

- **Critical** — wrong output, data loss, security.
- **Important** — a spec acceptance line is unmet; a later task builds on it;
  the run will waste more than an hour.
- **Minor** — style, docs, coverage outside acceptance, robustness.

Plan-mandated findings are still reported, but the controller rules on them
against the spec. If the spec agrees with the plan, it is not a defect.

**Promotion rule:** the controller may promote a Minor that directly affects an
acceptance item to Important, citing the spec line. That is how a real defect
labelled "Minor" still gets fixed.

## Output contract

- Full review.md on disk.
- Message ≤20 lines: verdict, finding IDs, path.
- At most one focused command to resolve a named doubt.
- Do not re-run the suite.
- Do not ask for more tests.

## Second net, not guarantee

The verifier finds what the gate's probes did not anticipate. Its verdict is a
hypothesis: the controller confirms every finding with a command or a spec
line before it enters the fix loop. A "spec compliant" verdict is not evidence.

## Re-review

Only when the fix touches an acceptance gate or a spec line. Otherwise rerun
the C2 probe. A re-review of a cosmetic fix is a duplicate seat.
