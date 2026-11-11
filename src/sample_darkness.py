"""Add a 0-1 darkness score to each site from the Falchi artificial sky brightness atlas.

Run from the project root:  python src/sample_darkness.py
Reads and updates: data/sites_static.geojson (raster is found automatically in data/raw/)
Optional: python src/sample_darkness.py path\to\raster.tif
"""
import json
import math
import sys
from pathlib import Path

import rasterio

ROOT = Path(__file__).resolve().parent.parent

NATURAL_MCD = 0.174   # natural sky brightness, mcd/m^2
NATURAL_MAG = 22.0    # sky brightness with no artificial light, mag/arcsec^2
BRIGHT_MAG = 17.0     # a sky this bright (or brighter) scores 0


def sky_mag(artificial_mcd):
    """Total sky brightness in mag/arcsec^2 (bigger number = darker sky)."""
    ratio = artificial_mcd / NATURAL_MCD
    return NATURAL_MAG - 2.5 * math.log10(1 + ratio)


def darkness_score(artificial_mcd):
    """Map sky brightness onto 0 (very bright) to 1 (natural dark sky)."""
    score = (sky_mag(artificial_mcd) - BRIGHT_MAG) / (NATURAL_MAG - BRIGHT_MAG)
    return min(max(score, 0.0), 1.0)


def find_raster():
    if len(sys.argv) > 1:
        return Path(sys.argv[1])
    tifs = [
        p for p in (ROOT / "data" / "raw").rglob("*")
        if p.suffix.lower() in (".tif", ".tiff")
    ]
    if not tifs:
        raise FileNotFoundError("No .tif file found under data/raw/")
    return max(tifs, key=lambda p: p.stat().st_size)


def main():
    path = ROOT / "data" / "sites_static.geojson"
    collection = json.loads(path.read_text(encoding="utf-8"))
    features = collection["features"]

    raster_path = find_raster()
    print(f"Reading {raster_path}")
    with rasterio.open(raster_path) as ds:
        points = [tuple(f["geometry"]["coordinates"]) for f in features]  # (lon, lat)
        values = [float(v[0]) for v in ds.sample(points)]

    for feature, value in zip(features, values):
        props = feature["properties"]
        if math.isnan(value) or value < 0:
            raise ValueError(f"{props['name']}: no valid raster value ({value})")
        props["artificial_mcd"] = round(value, 4)
        props["sky_mag"] = round(sky_mag(value), 2)
        props["dark"] = round(darkness_score(value), 3)
        print(f"{props['name']}: {props['sky_mag']} mag/arcsec^2, dark = {props['dark']}")

    path.write_text(json.dumps(collection, indent=2), encoding="utf-8")
    print(f"Updated {len(features)} sites in {path}")


if __name__ == "__main__":
    main()