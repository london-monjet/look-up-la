"""Add elevation (meters) to each candidate site using the USGS Elevation Point Query Service.

Run from the project root:  python src/add_elevation.py
Reads:  data/sites_candidates.geojson
Writes: data/sites_static.geojson
"""
import json
import time
from pathlib import Path

import requests

EPQS_URL = "https://epqs.nationalmap.gov/v1/json"
ROOT = Path(__file__).resolve().parent.parent


def get_elevation_m(lat, lon, retries=3):
    params = {"x": lon, "y": lat, "wkid": 4326, "units": "Meters", "includeDate": "false"}
    for attempt in range(1, retries + 1):
        try:
            r = requests.get(EPQS_URL, params=params, timeout=30)
            r.raise_for_status()
            value = float(r.json()["value"])
            if value < -1000:  # the service returns a huge negative number for "no data"
                raise ValueError("no elevation data returned")
            return round(value, 1)
        except (requests.RequestException, KeyError, ValueError) as err:
            if attempt == retries:
                raise RuntimeError(f"Elevation lookup failed for ({lat}, {lon}): {err}") from err
            time.sleep(2 * attempt)


def main():
    src = ROOT / "data" / "sites_candidates.geojson"
    dst = ROOT / "data" / "sites_static.geojson"
    collection = json.loads(src.read_text(encoding="utf-8"))
    for feature in collection["features"]:
        lon, lat = feature["geometry"]["coordinates"]  # GeoJSON order: lon first
        feature["properties"]["elevation_m"] = get_elevation_m(lat, lon)
        print(f'{feature["properties"]["name"]}: {feature["properties"]["elevation_m"]} m')
        time.sleep(0.2)  # be polite to a free public service
    dst.write_text(json.dumps(collection, indent=2), encoding="utf-8")
    print(f"Wrote {len(collection['features'])} sites to {dst}")


if __name__ == "__main__":
    main()