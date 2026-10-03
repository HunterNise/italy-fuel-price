# Workflow conventions

## Scope

- Understand the relevant existing behavior before changing it.
- Keep each change focused on the requested objective.
- Do not absorb unrelated cleanup merely because it is nearby.
- For substantial work, divide the objective into coherent reviewable units.
- Pause for the user's decision before introducing a new architecture,
  dependency, external service, or materially broader scope.

## Implementation

- Prefer the smallest implementation that satisfies the requirement cleanly.
- Preserve existing behavior unless the change intentionally modifies it.
- Keep generated/runtime data out of source control.
- Do not run bulk formatters, generators, or automatic rewrites over existing
  files unless their scope has been explicitly approved.
- Update authoritative documentation when behavior or usage changes.

## Verification

- Run focused checks appropriate to the files changed.
- Do not claim that code was tested, built, or validated unless that check was
  actually performed.
- Inspect the final diff for accidental or unrelated changes.
- If a relevant check cannot be run, say so explicitly.

## Handoff

At the end of a substantive change, report:

- the outcome;
- the meaningful files or behavior changed;
- verification performed;
- any unresolved limitation or next decision.

Keep routine command narration out of the handoff unless it is relevant to a
failure or decision.
