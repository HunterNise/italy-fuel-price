# Data sources and third-party material

This repository combines project code with data and software originating from
other sources. A licence that applies to this repository's own code does not
replace or override the terms that apply to upstream data or third-party
software.

## MIMIT station and current-price data

The station map uses public data published by the Italian Ministry of
Enterprises and Made in Italy (MIMIT), including the current station registry
and the daily `Prezzo alle 8` price snapshot.

Primary current feeds used by the project:

- Station registry: [MIMIT station registry CSV](https://www.mimit.gov.it/images/exportCSV/anagrafica_impianti_attivi.csv)
- Current prices: [MIMIT current-price CSV](https://www.mimit.gov.it/images/exportCSV/prezzo_alle_8.csv)

MIMIT publishes the fuel-price/open-data datasets under the Italian Open Data
License 2.0 (IODL 2.0). Generated web datasets must retain clear source and
licence attribution. The project should not imply that MIMIT endorses this
application or its derived calculations.

[Official MIMIT dataset information](https://www.mimit.gov.it/index.php/it/open-data/elenco-dataset/carburanti-prezzi-praticati-e-anagrafica-degli-impianti)

[Italian Open Data License 2.0](https://www.dati.gov.it/content/italian-open-data-license-v20)

## MASE analysis data

The `analysis/` component references public price series from the Italian
Ministry of the Environment and Energy Security (MASE) open-data portal:

[MASE open-data portal](https://sisen.mase.gov.it/dgsaie/open-data)

The repository's bundled analysis working copy is not uniformly a raw official
export. Its own provenance fields distinguish official/imported observations,
curated chart copies, and derived tax components. Those distinctions must be
preserved when publishing or reusing results.

This repository does not relicense MASE source material. Where a downstream use
requires certainty about redistribution terms, verify the terms attached to the
specific MASE dataset/export being used.

## OpenStreetMap

The interactive map uses OpenStreetMap tiles and displays OpenStreetMap
attribution. The public site must continue to follow the OpenStreetMap tile
usage policy and attribution requirements.

[OpenStreetMap tile usage policy](https://operations.osmfoundation.org/policies/tiles/)

[OpenStreetMap copyright and attribution](https://www.openstreetmap.org/copyright)

The application must not bulk-download or prefetch OpenStreetMap tiles for
offline use from the standard public tile service.

## Leaflet

The browser map uses Leaflet 1.9.4. For the public build, this project vendors
the Leaflet distribution rather than executing it from a third-party CDN at
runtime.

Leaflet is distributed under the BSD 2-Clause licence. Keep the upstream Leaflet
`LICENSE` file beside the vendored files.

[Leaflet project](https://leafletjs.com/)

[Leaflet source repository](https://github.com/Leaflet/Leaflet)

## Runtime and generated data

The following local runtime paths are intentionally excluded from source
control and must not be copied into a GitHub Pages artifact:

- `station_map/data/`
- `station_map/cache/`
- local `.env` files

In particular, `station_map/data/station_history.sqlite` can contain local
station-view/history state and is not part of the public website.

Static Pages datasets generated from MIMIT should contain only fields required
by the public application plus explicit source/build metadata. Generated daily
snapshots should be deployed as build artifacts rather than accumulated on the
source branch.
