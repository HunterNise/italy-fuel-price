# Roadmap

This document collects future ideas and likely next steps. It is deliberately
separate from changelogs and current-state architecture documents.

The current working application line is **0.10.x**. It establishes the
touch-first mobile results/detail model, responsive Help & About, public/static
deployment metadata, and the existing local/static provider boundary. The
previous selected public milestone remains `station-map-pages-v0.9.7` until a
new 0.10.x milestone is merged and tagged.

Future work should remain incremental: preserve the working local and static
providers, prefer bounded changes, and keep larger external-service
dependencies isolated until their value and operating constraints are
understood.

## Current 0.10 baseline and remaining browser QoL

Implemented through 0.10.2:

- one lower results/detail surface on narrow screens, with desktop popups
  preserved;
- touch-first map controls, mobile information-density cleanup, and reliable
  marker selection;
- responsive Guide/About content with live provider/build metadata;
- prominent repository/source attribution paths and keyboard-accessible modal
  behavior;
- consolidated narrow-screen CSS ownership.

Remaining browser QoL:

- Add optional swipe/drag gestures and predictable peek/partial/expanded sheet
  positions while keeping explicit tap controls as the accessible fallback.
- Test and tune portrait phone, landscape phone, tablet, and desktop layouts as
  separate interaction targets.
- Add focused browser-level responsive regression checks if their value
  justifies introducing browser-test tooling.
- Keep Help copy synchronized with future gestures, service modes and routing
  features rather than duplicating detailed documentation.
- Consider exposing an exact deployed commit identifier if the public build
  manifest later makes it available without another runtime dependency.

### Smaller map QoL

- Consider shareable URL state for the selected location and useful active
  settings such as fuel, service mode, radius, freshness, and selected station.
- Add lightweight station actions where useful, such as copying an address or
  coordinates and opening the location in an external map/navigation app.
- Revisit collapsed/expanded summaries so important context remains visible
  without duplicating information already shown elsewhere.

## Service-mode QoL

- Revisit a combined self-service + served mode.
- Model it as **one physical station, one marker, one station card**, with both
  available service offers shown inside the card rather than as independently
  overlapping markers.
- Keep each offer's price, communication timestamp, freshness, and history
  distinguishable.
- Define ranking semantics explicitly before implementation. For example, a
  station row could show both offers while sorting by the cheapest applicable
  offer, but the UI must make clear which price determines the rank.
- Ensure desktop and mobile selection/history behavior use the same underlying
  multi-offer station model.

## Data reliability and GitHub Pages operations

- Keep 09:15 Europe/Rome as the current source-publication target: the
  2026-10-05 through 2026-10-11 probe observed prices updated by the 08:50
  sample and the registry aligned by the 09:00 sample on every measured day.
  Reopen source-time tuning only if later observations break that pattern.
- Treat GitHub Actions cron delivery separately from MIMIT publication timing.
  Scheduled runs are best-effort and have recently been delayed by hours; if
  timely daily publication becomes operationally important, evaluate a small
  external scheduler that dispatches the existing workflow rather than moving
  the source-time target later.
- Keep the scheduled Pages workflow active without synthetic commits by calling
  GitHub's workflow-enable API from the workflow's separate keepalive job.
  Treat this as a pragmatic mitigation for the public-repository 60-day
  inactivity rule; if GitHub still disables the schedule, fall back to manual
  re-enable or an external dispatcher.
- Consider rejecting a new public deployment when registry and price snapshots
  have inconsistent source dates, leaving the previous known-good deployment
  active instead of publishing a mixed-vintage snapshot.
- Preserve the current failure behavior where build/validation problems do not
  replace a known-good public site.
- Keep generated current data and rolling history state out of the source
  branch.
- Consider a service worker/PWA only after static cache/versioning behavior is
  proven sufficiently stable in production.

## Analysis and trends

Develop the existing analysis toolkit toward a public, reproducible trends
surface rather than treating the compact working dataset as an authoritative
live public feed.

### Data/build integration

- Build public analysis artifacts from fresh, clearly attributed official
  sources through a reproducible Python build step.
- Reuse the toolkit's existing frequency/provenance model.
- Keep observed/official, curated, derived, partial-period, and interpolated
  values visibly distinguishable in both generated data and UI.
- Do not silently expand coarse observations to finer frequencies or silently
  interpolate missing values.
- Keep station-level daily MIMIT data conceptually distinct from national MASE
  statistical series and derived national aggregates.

### Public analysis UI

- Add a separate Trends/Analysis page or section before trying to crowd
  analytical views into the station map itself.
- Initial useful views may include:
  - petrol vs diesel national price trends;
  - monthly/weekly history;
  - final-price decomposition into net/industrial price, excise, and VAT;
  - comparisons across supported fuels where units and methodology are
    compatible.
- Show source, frequency, geographic scope, service mode, provenance, and
  partial/interpolated status close to each chart.
- Later, add contextual links from the station map to relevant national trend
  views without implying that national and station-level series are directly
  interchangeable.

## Route-aware fuel-stop planning

Treat route planning as a separate advanced feature because it introduces a
routing dependency and materially different ranking semantics.

### Evaluation first

- Evaluate routing providers/engines, hosting options, licences, rate limits,
  privacy implications, reliability, and operating cost before selecting a
  dependency.
- Consider hosted APIs versus a separately hosted routing engine such as OSRM,
  Valhalla, or GraphHopper.
- Keep route planning optional so the existing static/local station map does
  not become dependent on a routing backend.

### Candidate feature

- Accept origin/destination locations or coordinates and obtain a real road
  route.
- Find stations within a practical corridor around that route.
- Rank candidate stops using real route/detour information rather than
  straight-line distance alone.
- Useful ranking inputs may include:
  - price;
  - distance along the trip before the station;
  - extra detour distance;
  - extra travel time;
  - estimated fuel consumed by the detour;
  - fill amount;
  - gross and net monetary saving.
- Make assumptions such as vehicle consumption and value-of-time explicit and
  user-configurable where they materially affect ranking.
- Consider GPX/GeoJSON route input as an intermediate prototype that exercises
  route-corridor and detour-aware UI ideas without first requiring an integrated
  origin/destination routing service.

## Later ideas

- Explore richer station/history comparison views once the mobile interaction
  model is stable.
- Reassess offline/PWA behavior only after the public static deployment has
  accumulated enough operational history to justify it.
