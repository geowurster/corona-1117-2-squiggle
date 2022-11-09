#!/usr/bin/env python3


from collections import deque
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
outdir = os.path.join('frames', 'inspect-broken')

bad_entity_ids = [
    "DS1117-2059DF054",
    "DS1117-2059DF053",
    "DS1117-2059DF052",
    "DS1117-2059DF051",
    "DS1117-2059DF050",
    "DS1117-2059DF049",
    "DS1117-2059DF048",
    "DS1117-2059DF047",
    "DS1117-2059DF046",
    "DS1117-2059DF045",
    "DS1117-2059DF044",
    "DS1117-2059DF043",
    "DS1117-2059DA053",
    "DS1117-2059DA052",
    "DS1117-2059DA051",
    "DS1117-2059DA050",
    "DS1117-2059DA049",
    "DS1117-2059DA048",
    "DS1117-2059DA047",
    "DS1117-2059DA046",
    "DS1117-2059DA045",
    "DS1117-2059DA044",
    "DS1117-2059DA043",
    "DS1117-2059DA042"
]


# Normally blindly deleting would be fine, but this is an exploratory project,
# and someone could have altered the data for R&D purposes, so deleting might
# be rude. However, the data could be in an ambiguous state, so just raise
# an error.
if os.path.exists(outdir):
    raise RuntimeError(
        f"Target directory exists - data could be in a weird state: {outdir}")
os.makedirs(outdir, exist_ok=False)


def georeference(entity_id, feature, corner_cols):

    infile = os.path.join(raw_dir, f'{entity_id}.jpg')
    otags = []
    for xcol, ycol in corner_cols:
        otags.append(f"{xcol}--{ycol}")
    tag = "__".join(otags)
    outfile = os.path.join(outdir, f"{entity_id}--{tag}.jpg")

    p = feature['properties']

    (
        (culx, culy),
        (curx, cury),
        (clrx, clry),
        (cllx, clly)
    ) = corner_cols

    ulx = float(p[culx])
    uly = float(p[culy])

    urx = float(p[curx])
    ury = float(p[cury])

    lrx = float(p[clrx])
    lry = float(p[clry])

    llx = float(p[cllx])
    lly = float(p[clly])

    transform = affine.Affine(1.0, 0, 0, 0, 1, 0)
    wgs84 = CRS.from_epsg(4326)

    with rio.open(infile) as src:
        rows = src.height
        cols = src.width

    gcps = (
        GroundControlPoint(col=0, row=0, x=ulx, y=uly),
        GroundControlPoint(col=0, row=rows, x=llx, y=lly),
        GroundControlPoint(col=cols, row=rows, x=lrx, y=lry),
        GroundControlPoint(col=cols, row=0, x=urx, y=ury)
    )

    shutil.copy(infile, outfile)

    with rio.open(outfile, 'r+') as dst:
        dst.transform = transform
        dst.gcps = (gcps, wgs84)

    return outfile


for entity_id in bad_entity_ids:

    with fio.open('squiggle.shp') as src:
        feature = [f for f in src if f['properties']['Entity ID'] == entity_id]
        assert len(feature) == 1
        feature = feature[0]

    corner_cols = deque([
        ('NE Corne_3', 'NE Corne_2'),
        ('NW Corne_2', 'NW Cormer'),
        ('SW Corne_3', 'SW Corne_2'),
        ('SE Corne_3', 'SE Corne_2')
    ])

    for steps in range(len(corner_cols)):

        corner_cols.rotate(steps)

        res = georeference(
            entity_id=entity_id,
            feature=feature,
            corner_cols=corner_cols)

        print("Georeferenced:", res)
