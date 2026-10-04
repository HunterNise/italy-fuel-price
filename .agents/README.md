# Agent instructions

These are action-specific instructions for working in this repository. Read this
index first, then follow every applicable instruction file.

| Category | What it governs | Instruction |
| --- | --- | --- |
| Workflow | Scope, work units, implementation boundaries, verification, handoffs | [workflow.md](workflow.md) |
| Git | Branch/worktree safety, diffs, commits, tags, remotes | [git.md](git.md) |
| Build and test | Running, testing, CI, generated verification artifacts | [build.md](build.md) |
| Documentation | Markdown ownership, placement, links, current vs planned material | [documentation.md](documentation.md) |

## Mandatory routing

1. Before any repository modification, read both
   [Workflow](workflow.md) and [Git](git.md).
2. Read [Build and test](build.md) before running tests/builds or changing
   verification/CI behavior.
3. Read [Documentation](documentation.md) before writing, restructuring, or
   reviewing repository documentation.
4. For read-only Git/history/branch inspection, read [Git](git.md).
5. If an action crosses categories, read every applicable instruction file.

If applicable instructions conflict, stop and report the conflict rather than
silently choosing one.
