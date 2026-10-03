# Git conventions

## Repository safety

- Work on the currently selected branch unless the user requests otherwise.
- Preserve unrelated user changes.
- Do not stage, commit, push, force-push, reset, rebase, merge, or rewrite
  history unless the user explicitly requests the corresponding action.
- Before modifying files, inspect the current repository state.
- Before a requested commit, inspect the diff and verify that unrelated changes
  are not included.
- Keep commits reviewable and focused on one coherent purpose.
- Do not create a separate commit for a trivial follow-up that belongs naturally
  with the preceding change.

## Commit messages

Use Conventional Commits:

```text
<type>(<scope>): <imperative summary>
```

Common types include: `feat`, `fix`, `refactor`, `docs`, `test`, `build`, `ci`, `chore`, `perf`, `revert`.

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

Use ! and a BREAKING CHANGE: footer for breaking changes.
