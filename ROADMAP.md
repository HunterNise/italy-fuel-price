# Roadmap

This document collects future ideas and likely next steps. It is deliberately
separate from changelogs and current-state architecture documents.

The current public deployment milestone is `station-map-pages-v0.9.7`. Future
work should remain incremental: preserve the working local and static providers,
prefer bounded changes, and keep larger external-service dependencies isolated
until their value and operating constraints are understood.

## Next phase: mobile UX and browser QoL

The next development phase should focus on making the map genuinely touch-first
on narrow screens instead of only compressing the desktop layout.

### Mobile interaction model

- Redesign the mobile ranking/sidebar as a touch-friendly bottom sheet with
  predictable collapsed/peek, partial, and expanded states.
- On narrow screens, use the mobile detail sheet for selected-station details
  instead of allowing the ranking panel, top controls, and a large Leaflet popup
  to compete for vertical space.
- Fix the current mobile station-selection/docking bug where opening a station
  with the bottom panel docked can move the top controls out of view and leave
  the docking control ineffective.
- Keep explicit tap/click controls as an accessible fallback even if swipe/drag
  gestures are added.
- Remove narrow-layout whitespace and control-position glitches, including top
  panel empty space and dock/undock controls moving to surprising positions.
- Avoid scroll traps between the map, details/ranking sheet, dialogs, and page
  itself.
- Respect mobile safe areas and use touch-sized controls suitable for phones.
- Test portrait phone, landscape phone, tablet, and desktop layouts as separate
  interaction targets rather than assuming one responsive layout covers all of
  them.
- Add focused browser-level responsive regression checks for important
  interactions that DOM/unit tests cannot adequately cover.

### Help and secondary information

- Rework the current Help dialog into a clearer **Help & About** surface.
- Revise usage instructions so desktop users see keyboard/mouse guidance and
  mobile users see touch/swipe guidance.
- Include useful secondary information such as:
  - application version;
  - local vs public/static data mode;
  - price-snapshot and registry dates;
  - public build/generation time;
  - normal Pages refresh cadence;
  - repository link;
  - primary data-source and licence links.
- Keep source attribution concise in the interface and link to the repository
  provenance/licensing documentation for details.

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

- Continue measuring morning MIMIT publication timing over several weekdays;
  adjust the 09:15 Europe/Rome schedule or add a fallback only if repeated
  observations justify it.
- Consider rejecting a new public deployment when registry and price snapshots
  have inconsistent source dates, leaving the previous known-good deployment
  active instead of publishing a mixed-vintage snapshot.
- Preserve the current failure behavior where build/validation problems do not
  replace a known-good public site.
- Keep generated current data and rolling history state out of the source
  branch.
- Consider a service worker/PWA only after static cache/versioning behavior is
  proven sufficiently stable in production.
- If GitHub's public-repository inactivity rule becomes operationally relevant,
  add the smallest safe workflow-maintenance mechanism rather than synthetic
  source commits.

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
