# Cost Model

Baseline from one real run (7 tasks, 3 batches, ~1,500 lines, 10 subagents):

| Item | Baseline |
|---|---|
| total tokens | 48.5M |
| parent | 9.5M |
| implementers (incl. fixes) | 27.0M |
| reviewers + re-reviews | 12.0M |
| wall time | ~100 min |
| full-suite runs | 16 |
| test commands | 54 |
| dispatches | 10 |
| polling calls | 23 (≈3.2M tokens) |
| findings | 39 (0 Critical, 12 substantive) |
| fix rounds | 4 |

The substantive defects were all traceable to the plan or a controller ruling,
not to the implementer. The review seats were sampling the plan's defects after
transcription.

## Budgets

| Object | Soft | Hard / action |
|---|---|---|
| child | 30 steps | 45: report partial + blocker |
| batch | 400 LoC / 3 production files | split |
| child context | 150k | split the batch |
| plan | 5 dispatches, 2 fix rounds | stop and rule |
| tests | see testing-policy | process defect |

## Why these numbers

A wrong brief costs a fix round + re-review (24 min, 6.7M tokens in the
baseline). A 5–15 line spec slice in the brief costs ~2k tokens. The trade is
roughly 1:2000. Do not save the slice.

## Model caveat

The "models are more capable, so the harness can be thinner" argument comes
from newer Anthropic models. On a smaller/faster model, the structure still
matters: the baseline showed 23 polls, a 100-step child, and 15 reruns of one
flaky test. Remove ceremony (RED/GREEN theatre, per-task review), keep gates
(traceability, negative probes, end-to-end acceptance).
