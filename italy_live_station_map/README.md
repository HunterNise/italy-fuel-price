# Live Italian fuel-station price map

This is a price-centric station map: no reviews, ratings, brand cards or other
business metadata.

## Run

Requires Python 3.10+ and an internet connection.

```bash
python serve_map.py
```

Then open:

```text
http://127.0.0.1:8000
```

The local Python server proxies the Ministry's public station-price API. Keeping
the API call server-side avoids browser CORS/file-origin problems.

## UI

* Fuel selector: petrol, diesel, GPL, methane
* Self-service / served selector
* Radius: 1–10 km
* Click anywhere on the map to search around that point
* Optional `Use my location` asks the browser for location permission
* `Refresh` requests current prices again
* Stations are color-coded **relative to prices in the current result set**
  (green = lower, red = higher)
* Price labels appear on the map; station names and ratings are deliberately
  omitted
* Popups contain only price, fuel/mode, technical station ID and address
* Summary shows station count, minimum, median and maximum

## Data source

Primary endpoint used by the proxy:

```text
https://carburanti.mise.gov.it/ospzApi/search/zone
```

Request shape:

```json
{"points":[{"lat":"43.9303","lng":"10.9079"}],"radius":5}
```

The response contains station coordinates and `carburanti` price entries.

Fallback endpoint:

```text
https://carburanti.mise.gov.it/OssPrezziSearch/ricerca/position
```

This older public API is documented by an OpenAPI sample from the Italian
Digital Transformation Team.

## Map tiles

The basemap uses Leaflet + OpenStreetMap tiles. This avoids needing a Google Maps
API key and keeps the UI focused on the price layer. The underlying station
price data remain MIMIT data.

## Offline UI test

If MIMIT is unreachable, you can test the interface with clearly synthetic
points:

```bash
python serve_map.py --demo
```

Demo mode is **not** suitable for price analysis; it only validates the map UI.

## Notes

The exact availability and response behaviour of public ministry endpoints can
change. If the API changes, `fetch_live()` in `serve_map.py` is the single place
that needs updating.
