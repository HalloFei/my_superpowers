# Decision Table

## Tiers

| Tier | Trigger (any) | Executor | Review | Example |
|---|---|---|---|---|
| **T0 apply** | the plan/brief contains the complete code and test for the file; no new decision | main loop (write/edit) | none; gate + tests | 3 pure functions, code blocks complete |
| **T1 build** | ≤2 files, ≤30 steps, interfaces fixed, needs local judgment | main loop | risk-triggered only | one module from a prose spec |
| **T2 delegate** | >3 files or >400 LoC; or a long wait/command; and context is separable (own files/data, no shared interface) | 1 implementer | 1 verifier per batch | an independent package with a clean boundary |
| **T3 explore** | independent, disposable, parallel | N researchers (≤4) | aggregate check | four papers read in parallel |

Decision order:

~~~text
if plan_block_is_complete and no_new_decision:      T0
elif files <= 2 and steps <= 30 and no_long_wait:   T1
elif context_separable and (files > 3 or loc > 400 or long_wait): T2
elif independent and disposable:                    T3
else:                                               T1
~~~

Default to T1. T0 is the cheapest and the most common when the plan contains
code. T2 is the exception, not the default.

## Context, not problem type

If task B cannot build or pass without task A's output, they are one context.
Tasks split by technical layer (spec / renderer / split / harness / measure /
report / CLI) share interfaces and will produce the telephone game. Group by
interface cluster, not by layer.

## Batch sizing

- One batch = one interface cluster.
- ≤3 production files, ≤400 changed LoC including tests, ≤3 plan tasks.
- The producer and consumer of an interface are in the same batch.
- One implementer per batch; do not run two implementers in parallel unless
  their file sets are disjoint.

## Rulings

A dispatch prompt that contains a "Ruling:" line means the decision was made
in the parent context. Either implement it in the parent (T1), or write it into
the plan/brief first and let T0 apply it. Do not translate a 9k-char decision
into a prompt for a child to reconstruct.

## Model routing

This runtime exposes no model parameter for subagents. Do not write "use the
cheapest model" into a dispatch; it is unenforceable here. Cost control is
dispatch count × context size × turns. If the harness later exposes a model
parameter, map T0/T1 to the cheapest tier, T2 to a mid tier, and the final
verification to the strongest tier.

## When to keep the original SDD

Use `subagent-driven-development` only when the plan is genuinely
task-parallel with disposable context, or when a task needs a fresh context
larger than the main loop can hold. That is T3/T2 territory, not the default.
