# Git conventions

## Repository safety

- Work on the currently selected branch or worktree. Do not create, switch, or
  replace branches/worktrees unless the user explicitly requests it.
- Preserve unrelated user changes.
- Do not stage, commit, push, force-push, reset, rebase, merge, tag, rewrite
  history, change remotes, change repository settings, or edit the remote
  repository unless the user explicitly requests the corresponding action.
- Before modifying repository files, inspect the current repository state.
- Before a requested commit, inspect the staged diff and verify that unrelated
  changes are not included.
- Keep commits reviewable and focused on one coherent purpose.
- Do not create a separate commit for a trivial follow-up that belongs naturally
  with the preceding change.
- Follow the project branch and release workflow documented in
  [`DEVELOPMENT.md`](../DEVELOPMENT.md), but never switch branches on the user's
  behalf merely to satisfy that convention.

## Commit messages

Use Conventional Commits:

```text
<type>(<scope>): <imperative summary>
```

Common types include `feat`, `fix`, `refactor`, `docs`, `test`, `build`, `ci`,
`chore`, `perf`, and `revert`.

Use a short lowercase scope when it adds useful information, for example:

```text
fix(map): use Rome as the default location
docs(repo): add repository overview
ci(pages): validate generated station data
feat(web): add static station-data provider
```

Omit the scope when it adds no useful information.

Keep the summary imperative, specific, and preferably no longer than 72
characters. Do not end it with a period.

Use a commit body when the reason, tradeoff, migration, or compatibility impact
is not obvious from the subject.

Use `!` and a `BREAKING CHANGE:` footer for breaking changes.

## Release/tag safety

- Tags are selected stable milestones, not a requirement for every changelog
  version or every commit.
- Prefer descriptive component-prefixed tag names when that gives useful
  context, for example `station-map-local-v0.8.10`.
- Scheduled/generated data refreshes must not create source commits or release
  tags.
- Follow [`DEVELOPMENT.md`](../DEVELOPMENT.md) for the project release/tag
  workflow; this file governs only agent safety around those actions.
