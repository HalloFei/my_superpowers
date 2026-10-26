# Researcher Prompt (T3 only)

Use for independent exploration whose context can be discarded. Not for
implementation.

~~~text
Subagent:
  description: "Research <question>"
  prompt: |
    Answer this question: <question>

    Inputs you may read: <paths / URLs>
    Write the result to: <output path>

    Rules:
    - Do not modify code, config, or data. Read-only.
    - Do not dispatch subagents.
    - Cite the file/line or URL for every factual claim.
    - Separate "what the source says" from "what I infer".
    - If the source is unavailable, say so and stop; do not fabricate.

    Reply with at most 10 lines: answer, confidence, output path.
~~~

## Aggregation

The controller reads the output files and reconciles conflicts. Do not have
researchers read each other's outputs; that recreates the telephone game.
