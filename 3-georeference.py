#!/usr/bin/env python3


import os
import shutil
import warnings

import affine
import fiona as fio
import rasterio as rio
from rasterio.crs import CRS
from rasterio.control import GroundControlPoint
from rasterio.errors import NotGeoreferencedWarning


warnings.filterwarnings('ignore', category=NotGeoreferencedWarning)


raw_dir = os.path.join('frames', 'raw')
outdir = os.path.join('frames', 'georeferenced')

transform = affine.Affine(1.0, 0, 0, 0, 1, 0)
wgs84 = CRS.from_epsg(4326)


# Normally blindly deleting would be fine, but this is an exploratory project,
# and someone could have altered the data for R&D purposes, so deleting might
# be rude. However, the data could be in an ambiguous state, so just raise
# an error.
if os.path.exists(outdir):
    raise RuntimeError(
        f"Target directory exists - data could be in a weird state: {outdir}")
os.makedirs(outdir, exist_ok=False)


def gcps_for_frame(feature, rows, cols):
    
    p = feature['properties']
    
    # NE -> UL
    ulx = float(p['NE Corne_3'])
    uly = float(p['NE Corne_2'])

    # NW -> LL
    llx = float(p['NW Corne_2'])
    lly = float(p['NW Cormer'])

    # SW -> LR
    lrx = float(p['SW Corne_3'])
    lry = float(p['SW Corne_2'])

    # SE -> UR
    urx = float(p['SE Corne_3'])
    ury = float(p['SE Corne_2'])
    
    return (
        GroundControlPoint(col=0,    row=0,    x=ulx, y=uly),
        GroundControlPoint(col=0,    row=rows, x=llx, y=lly),
        GroundControlPoint(col=cols, row=rows, x=lrx, y=lry),
        GroundControlPoint(col=cols, row=0,    x=urx, y=ury)
    )


with fio.open('squiggle.shp') as src:

    for feature in src:

        entity_id = feature['properties']['Entity ID']
        filename = f'{entity_id}.jpg'

        raw_path = os.path.join(raw_dir, filename)
        goerf_path = os.path.join(outdir, filename)
        shutil.copy(raw_path, goerf_path)

        with rio.open(goerf_path, 'r+') as dst:

            gcps = gcps_for_frame(
                feature=feature,
                rows=dst.height,
                cols=dst.width)

            # South-up
            dst.transform = transform
            dst.gcps = (gcps, wgs84)

        print("Georeferenced:", goerf_path)
