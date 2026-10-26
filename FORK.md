# Fork additions — better subagent-driven development

This branch is based on `v6.3.0` (`b36e082`), the release the author's harness
has installed. It is a personal fork branch, not a PR against upstream.

## Changes

- `skills/patched-subagent-driven-development/` — new skill: main loop by
  default; spec coverage gate; negative probes; Definition of Done; verifier
  as a second net.
- `skills/brainstorming/` — acceptance table, For the Plan Author, spec
  grill, approval brief, acceptance-integrity check.
- `skills/writing-plans/` — context task sizing, Spec Freeze Gate, Spec
  Coverage table, apply/build task types, Consumer test, negative probes,
  Definition of Done, plan review, execution brief.
- `docs/superpowers/specs/2026-10-26-patched-subagent-driven-development-design.md`
  — the design record and evidence baseline.
- `scripts/gate-check.py` in the new skill validates spec status/hash,
  coverage, task types, and Definition of Done.

## Base choice

Upstream `main` is v7.0.1 and has diverged (brainstorming retune, reviewer
prompt removal). Rebasing these changes onto `main` is a separate port; this
branch intentionally preserves the 6.3.0 base the author runs.

## Not for upstream PR

The upstream contribution guidelines reject fork-specific changes, and these
changes restructure behavior-shaping skill content. This branch is for the
fork only.
