"""Print basic facts about a raster so we can tell what it is.

Run from the project root:  python src/inspect_raster.py data/raw/YOUR_FILE.tif
"""
import sys

import rasterio

path = sys.argv[1]
with rasterio.open(path) as ds:
    print("size (cols x rows):", ds.width, "x", ds.height)
    print("bands:", ds.count, "| data type:", ds.dtypes[0])
    print("CRS:", ds.crs)
    print("bounds (left, bottom, right, top):", ds.bounds)
    print("pixel size:", ds.res)
    print("nodata value:", ds.nodata)
    for name, lat, lon in [
        ("Downtown LA", 34.0522, -118.2437),
        ("Keys View", 33.9269, -116.1866),
        ("Carrizo Plain", 35.1905, -119.6975),
    ]:
        value = next(ds.sample([(lon, lat)]))[0]
        print(f"{name}: {value}")