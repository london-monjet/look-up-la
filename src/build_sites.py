"""Build the hand-curated list of candidate stargazing sites.

Run from the project root:  python src/build_sites.py
Writes: data/sites_candidates.geojson
"""
import json
from pathlib import Path

# (name, latitude, longitude, area)
SITES = [
    # Near LA: Angeles National Forest and nearby mountains
    ("Chilao Visitor Center", 34.3359, -118.0121, "Angeles National Forest"),
    ("Dawson Saddle", 34.3560, -117.8040, "Angeles National Forest"),
    ("Table Mountain Campground", 34.3790, -117.6900, "Angeles National Forest"),
    ("Manker Flats", 34.2390, -117.6520, "Mt. Baldy"),
    ("Devil's Punchbowl", 34.4125, -117.8570, "Antelope Valley"),
    ("Sandstone Peak Trailhead", 34.1186, -118.9293, "Santa Monica Mountains"),
    # Ventura, Kern, and Santa Barbara counties
    ("Mt. Pinos Parking Area", 34.8142, -119.1417, "Los Padres National Forest"),
    ("Figueroa Mountain", 34.7360, -119.9910, "Los Padres National Forest"),
    ("Carrizo Plain Goodwin Center", 35.1905, -119.6975, "Carrizo Plain National Monument"),
    ("Saddleback Butte State Park", 34.6760, -117.8310, "Antelope Valley"),
    # Inland mountains
    ("Humber Park", 33.7589, -116.7064, "San Jacinto Mountains"),
    ("Palomar Mountain State Park", 33.3480, -116.9110, "Palomar Mountain"),
    ("Paso Picacho Campground", 32.9494, -116.5597, "Cuyamaca Rancho State Park"),
    ("Laguna Mountain Recreation Area", 32.8700, -116.4200, "Cleveland National Forest"),
    ("Chula Vista Walk-In Campground", 34.82947045488243, -119.12609407064167, "Los Padres National Forest"),
    # Deserts
    ("Keys View", 33.9269, -116.1866, "Joshua Tree National Park"),
    ("Hidden Valley", 34.0125, -116.1678, "Joshua Tree National Park"),
    ("Jumbo Rocks Campground", 34.0128, -116.0683, "Joshua Tree National Park"),
    ("Cottonwood Spring", 33.7458, -115.8200, "Joshua Tree National Park"),
    ("Borrego Palm Canyon Campground", 33.2750, -116.4310, "Anza-Borrego Desert State Park"),
    ("Anza-Borrego Visitor Center", 33.2578, -116.4003, "Anza-Borrego Desert State Park"),
    ("Blair Valley Campground", 33.03818982184881, -116.40946556963132, "Borrego Springs"),
    ("Magic Portal Stargazer's Retreat", 34.75583111481551, -118.36629460025274, "Mojave Desert"),
]

# Rough box around Southern California, used to catch typos
LAT_MIN, LAT_MAX = 32.0, 36.0
LON_MIN, LON_MAX = -121.0, -114.5


def build_features(sites):
    seen = set()
    features = []
    for name, lat, lon, area in sites:
        if name in seen:
            raise ValueError(f"Duplicate site name: {name}")
        seen.add(name)
        if not (LAT_MIN <= lat <= LAT_MAX and LON_MIN <= lon <= LON_MAX):
            raise ValueError(
                f"{name}: ({lat}, {lon}) is outside the study area. "
            )
        features.append({
            "type": "Feature",
            # GeoJSON order is [longitude, latitude]
            "geometry": {"type": "Point", "coordinates": [lon, lat]},
            "properties": {
                "id": len(features) + 1,
                "name": name,
                "area": area,
                "source": "curated",
            },
        })
    return features


def main():
    out_path = Path(__file__).resolve().parent.parent / "data" / "sites_candidates.geojson"
    features = build_features(SITES)
    collection = {"type": "FeatureCollection", "features": features}
    out_path.write_text(json.dumps(collection, indent=2), encoding="utf-8")
    print(f"Wrote {len(features)} sites to {out_path}")


if __name__ == "__main__":
    main()