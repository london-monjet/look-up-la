"""Build tonight's stargazing scores from darkness + weather (Open-Meteo) + moon (Skyfield).

Run from the project root:  python src/update_data.py
Reads:  data/sites_static.geojson
Writes: docs/data/tonight.geojson

Weather data by Open-Meteo.com (CC BY 4.0).
"""
import json
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import requests
from skyfield.api import Loader, wgs84

from scoring import DARK_HOURS, mean_in_window, night_window, tonight_score

ROOT = Path(__file__).resolve().parent.parent
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
TIMEZONE = "America/Los_Angeles"
BATCH_SIZE = 50
MOON_POINT = (34.0, -118.0)  # one reference point is fine for a region this size


def fetch_weather(coords, retries=4):
    """coords is a list of (lat, lon). Returns one forecast dict per coordinate, same order."""
    params = {
        "latitude": ",".join(str(lat) for lat, lon in coords),
        "longitude": ",".join(str(lon) for lat, lon in coords),
        "hourly": "cloud_cover,relative_humidity_2m",
        "past_days": 1,      # covers the "after midnight" case
        "forecast_days": 2,
        "timezone": TIMEZONE,
    }
    for attempt in range(1, retries + 1):
        try:
            r = requests.get(FORECAST_URL, params=params, timeout=60)
            r.raise_for_status()
            data = r.json()
            # One coordinate comes back as a dict, several come back as a list.
            results = data if isinstance(data, list) else [data]
            if len(results) != len(coords):
                raise ValueError("response has the wrong number of locations")
            return results
        except (requests.RequestException, ValueError) as err:
            if attempt == retries:
                raise RuntimeError(f"Weather lookup failed: {err}") from err
            wait = 5 * attempt
            print(f"  attempt {attempt} failed ({err}); retrying in {wait}s...")
            time.sleep(wait)


def moon_state(start, end):
    """Average moon illumination (0-1) and the share of the window the moon is up (0-1)."""
    cache_dir = ROOT / "data" / "raw"          # gitignored; holds the ephemeris download
    cache_dir.mkdir(parents=True, exist_ok=True)
    load = Loader(str(cache_dir))
    ts = load.timescale()
    eph = load("de421.bsp")                    # downloads ~17 MB the first time

    step = timedelta(minutes=30)
    count = int((end - start) / step)
    samples = [(start + i * step).astimezone(timezone.utc) for i in range(count)]
    t = ts.from_datetimes(samples)

    earth = eph["earth"]
    moon = earth.at(t).observe(eph["moon"]).apparent()
    illumination = moon.fraction_illuminated(eph["sun"])

    observer = earth + wgs84.latlon(*MOON_POINT)
    altitude = observer.at(t).observe(eph["moon"]).apparent().altaz()[0].degrees

    return float(illumination.mean()), float((altitude > 0).mean())


def main():
    start, end = night_window(datetime.now(ZoneInfo(TIMEZONE)))
    illum, up_fraction = moon_state(start, end)
    print(f"Night window: {start:%Y-%m-%d %H:%M} to {end:%Y-%m-%d %H:%M} ({TIMEZONE})")
    print(f"Moon: {illum:.0%} lit, above the horizon for {up_fraction:.0%} of the window")

    src = ROOT / "data" / "sites_static.geojson"
    collection = json.loads(src.read_text(encoding="utf-8"))
    features = collection["features"]
    if any("dark" not in f["properties"] for f in features):
        raise RuntimeError("Some sites have no 'dark' value. Run sample_darkness.py first.")

    updated = datetime.now(timezone.utc).isoformat(timespec="seconds")
    out_features = []

    for i in range(0, len(features), BATCH_SIZE):
        batch = features[i:i + BATCH_SIZE]
        coords = [
            (f["geometry"]["coordinates"][1], f["geometry"]["coordinates"][0])
            for f in batch
        ]
        results = fetch_weather(coords)
        for feature, result in zip(batch, results):
            hourly = result["hourly"]
            cloud = mean_in_window(hourly["time"], hourly["cloud_cover"], start, end)
            humidity = mean_in_window(hourly["time"], hourly["relative_humidity_2m"], start, end)
            props = feature["properties"]
            score = tonight_score(props["dark"], cloud, humidity, illum, up_fraction)
            out_features.append({
                "type": "Feature",
                "geometry": feature["geometry"],
                "properties": {
                    "id": props["id"],
                    "name": props["name"],
                    "area": props["area"],
                    "elevation_m": props["elevation_m"],
                    "dark": props["dark"],
                    "score": score,
                    "cloud": round(cloud),
                    "humidity": round(humidity),
                    "moon_illum": round(illum * 100),
                    "updated": updated,
                },
            })
            print(f"{props['name']}: score {score} "
                  f"(cloud {cloud:.0f}%, humidity {humidity:.0f}%, dark {props['dark']})")

    out_path = ROOT / "docs" / "data" / "tonight.geojson"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    result = {"type": "FeatureCollection", "features": out_features}
    out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"Wrote {len(out_features)} sites to {out_path}")


if __name__ == "__main__":
    main()