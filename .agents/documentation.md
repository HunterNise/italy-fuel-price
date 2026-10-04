# Documentation conventions

Keep documentation current, non-duplicative, and owned by the narrowest scope it
actually governs.

## Ownership and placement

| Document | Owns |
| --- | --- |
| `README.md` | Repository overview and navigation |
| `DEVELOPMENT.md` | Human build/run/test, branch, merge, and release workflow |
| `ROADMAP.md` | Future ideas and planned work across the repository |
| `DATA_SOURCES_AND_LICENSES.md` | Cross-project provenance, attribution, and licensing |
| `station_map/README.md` | Current station-map usage and component-specific behavior |
| `station_map/ARCHITECTURE.md` | Implemented station-map/static-data architecture and invariants |
| `station_map/CHANGELOG.md` | Effective station-map version history |
| `analysis/README.md` | Analysis-toolkit usage, data semantics, provenance notes |
| `analysis/requirements.txt` | Analysis-only Python dependencies |

Component-owned documents and dependency manifests stay with their component
unless they genuinely become repository-wide concerns.

Do not duplicate operating instructions or policy across documents. Put the
authoritative content in its owner and link to it from other documents.

Do not use the changelog as a planning document. Planned features and ideas
belong in `ROADMAP.md`; the changelog records effective changes.

Do not duplicate a "current version" label in architecture documents. Version
authority belongs to the component's version source and release history.

## Markdown style

- Put code symbols, commands, options, filenames, paths, branch names, and
  configuration values in backticks.
- Use relative Markdown links for repository files.
- Use descriptive clickable Markdown links for external sources/readers; do not
  put a URL in backticks when it is intended to be followed.
- Use fenced code blocks with an appropriate language tag.
- Keep heading levels hierarchical and blank lines around lists, tables, and
  fenced blocks.
- Prefer prose for explanation and tables only for compact comparisons.
- Describe current behavior in present tense. Mark historical material as
  historical rather than leaving obsolete rollout notes in current guides.
- Keep future/planned material out of current-state architecture and usage docs.

Before finishing a documentation change, inspect changed regions for broken
relative links, stale paths/commands, malformed code fences/tables, and claims
about planned behavior presented as current behavior.
