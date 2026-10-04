# Roadmap

This document collects future ideas and likely next steps. It is deliberately
separate from changelogs and current-state architecture documents.

## GitHub Pages deployment

Near-term work:

- Add a small browser data-provider boundary so the existing UI can use either
  the local `/api/*` backend or generated static data.
- Add the static provider for 0.5° current-price cells and the generated
  municipality index.
- Expose generated seven-day rolling history through lazy-loaded history cells,
  preserving missing dates without interpolation.
- Assemble an allowlisted Pages artifact containing only public HTML/CSS/JS,
  vendored Leaflet assets, and generated public data.
- Add the Pages deployment workflow with validation, manual dispatch, and
  scheduled refreshes.
- Measure actual morning MIMIT publication timing and keep a fallback schedule
  only if the data justify it.
- Make stale-data status visible when the upstream snapshot or scheduled
  deployment has not refreshed.

## Analysis and trends

Possible follow-up work:

- Build public trend views from fresh, clearly attributed source data rather
  than treating the compact analysis working copy as an authoritative public
  feed.
- Keep observed/official, curated, derived, and secondary values visibly
  distinguishable.

## Later ideas

- Evaluate route-aware fuel-stop planning as a separate service/module if a
  concrete trip-planning workflow justifies the routing provider and
  detour/vehicle-cost assumptions.
- Consider a service worker/PWA only after static cache/versioning behavior is
  proven in production.
- If GitHub's public-repository inactivity rule becomes operationally relevant,
  add the smallest safe workflow-maintenance mechanism rather than synthetic
  source commits.
