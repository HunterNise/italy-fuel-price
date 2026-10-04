# Workflow conventions

These conventions govern how repository work is scoped, executed, verified, and
handed off. [`git.md`](git.md) governs repository state and history.

## Scope

- Understand the relevant existing behavior before changing it.
- Keep each change focused on the requested objective.
- Do not absorb unrelated cleanup merely because it is nearby.
- For substantial work, divide the objective into coherent, reviewable units.
- Pause for the user's decision before introducing a new architecture,
  dependency, external service, or materially broader scope unless that
  direction has already been explicitly approved.
- Treat work-unit and commit boundaries as review boundaries rather than a
  target number of commits.

## Implementation

- Prefer the smallest implementation that satisfies the requirement cleanly.
- Preserve existing behavior unless the change intentionally modifies it.
- Keep generated/runtime data out of source control.
- Do not run bulk formatters, generators, or automatic rewrites over existing
  files unless their scope has been explicitly approved.
- Update the authoritative documentation when behavior, architecture, operating
  workflow, or public-data semantics change.
- Keep planned/future behavior separate from implemented/current behavior.
- Unless the user explicitly requests direct repository editing, hand off
  ready-to-copy files, a patch, a small modifying script, or exact local edit
  instructions plus the intended commit split/messages.

## Verification

- Run focused checks appropriate to the files changed, following
  [`build.md`](build.md).
- Do not claim that code was tested, built, or validated unless that check was
  actually performed.
- Inspect the final diff for accidental or unrelated changes.
- If a relevant check cannot be run, say so explicitly.

## Handoff

At the end of a substantive change, report:

- the outcome;
- the meaningful files or behavior changed;
- verification performed;
- any unresolved limitation or next decision;
- the proposed commit split/messages when the user will commit locally.

Keep routine command narration out of the handoff unless it is relevant to a
failure or decision.
