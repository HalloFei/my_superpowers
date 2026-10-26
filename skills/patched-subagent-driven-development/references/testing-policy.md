# Testing Policy

## Budget

| Moment | Allowed | Cap |
|---|---|---|
| plan start | one full suite baseline (record commit + result) | 1 |
| each task | the plan's focused test | ≤2 |
| batch end | one full suite | 1 |
| fix round | the covering test + touched files | 1 |
| final | full suite + acceptance script | 1 |
| flaky | rerun the same test | ≤1; then log it and move on |

A full suite before every commit is a policy bug, not diligence. It is how a
90-minute run spends 16 full suites.

## Apply vs build

- **apply** (the plan contains the test and code): the plan's test is the RED
  artifact. Apply the code, run the named test, commit. No RED/GREEN theatre.
- **build**: keep TDD. Write the failing test, watch it fail for the right
  reason, implement, pass.

## Test power

The acceptance question is: "if I delete the implementation, does this test
fail?" If not, it is decoration. For gates, the question is sharper: "name the
mutation that makes this gate fail." If you cannot name one, fix the test or
the gate.

A test suite whose line count exceeds the production code is a warning, not an
achievement. One strong test beats five trivial ones.

## New tests

Add a test only when a fix changes behaviour that no existing test covers. One
new test per finding, maximum. Do not add tests for pure transcription.

## Not findings

The reviewer does not get to open:

- "coverage could be broader"
- "test output has warnings" (unless the warning is a real failure)
- test style, naming, or file size

These are how 31 minors were generated in one run.
