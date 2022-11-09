#!/usr/bin/env python3


from math import ceil
import os
from statistics import mean

import affine
import fiona as fio
import numpy as np
import rasterio as rio
from rasterio.crs import CRS
from rasterio.enums import ColorInterp
from rasterio.warp import (
    calculate_default_transform, transform_bounds, reproject, Resampling)


georf_dir = os.path.join('frames', 'georeferenced')
per_frame_dir = os.path.join('frames', 'warped-naive')
fixed_grid_dir = os.path.join('frames', 'warped-fixed')
resampling = Resampling.cubic


wgs84 = CRS.from_epsg(4326)
utm31 = CRS.from_epsg(32631)


colorinterp = (ColorInterp.gray, ColorInterp.alpha)
dst_alpha_idx = colorinterp.index(ColorInterp.alpha)
template_profile = {
    'driver': 'GTiff',
    'count': len(colorinterp),
    'dtype': rio.uint8,
    'crs': utm31,
    'COMPRESS': 'DEFLATE',
    'PREDICTOR': '2',
    'TILED': 'YES',
}


# Normally blindly deleting would be fine, but this is an exploratory project,
# and someone could have altered the data for R&D purposes, so deleting might
# be rude. However, the data could be in an ambiguous state, so just raise
# an error.
for d in (per_frame_dir, fixed_grid_dir):
    if os.path.exists(d):
        raise RuntimeError(
            f"Target directory exists: {d}")
    os.makedirs(d, exist_ok=False)


def xres_yres(entity_ids):

    all_xres = []
    all_yres = []

    for eid in entity_ids:
        georf_path = os.path.join(georf_dir, f'{eid}.jpg')

        with rio.open(georf_path) as src:

            # Extremely shouldn't happen, but worth checking to make
            # assumptions elsewhere valid.
            _, gcp_crs = src.gcps
            if gcp_crs != wgs84:
                raise ValueError(f"CRS mismatch: {gcp_crs} != {wgs84}")

            gcps, gcps_crs = src.gcps
            transform, _, _ = calculate_default_transform(
                src_crs=gcps_crs,
                dst_crs=utm31,
                width=src.width,
                height=src.height,
                gcps=gcps)

            all_xres.append(transform.a)
            all_yres.append(transform.e)

    return mean(all_xres), mean(all_yres)


def read_with_alpha(src):

    """Append an entirely transparent alpha band in order to make Rasterio's
    `reproject()` function produce a proper mask. Cannot assume 0 since some
    valid values in the source images are 0, and continue to be 0 after warping.

    Parameters
    ----------
    src : rasterio.DatasetReader
    """

    data = np.empty((2, src.height, src.width), dtype=src.dtypes[0])
    data[1] = 255
    src.read(1, out=data[0])

    return data


def warp_naive(georf, outfile):

    with rio.open(georf) as src:

        data = read_with_alpha(src)

        gcps, gcps_crs = src.gcps
        reprojected, transform = reproject(
            source=data,
            src_crs=gcps_crs,
            gcps=gcps,
            dst_crs=utm31,
            dst_resolution=(xres, abs(yres)),
            dst_alpha=dst_alpha_idx,
            resampling=resampling)

    count, height, width = reprojected.shape
    profile = template_profile.copy()
    profile.update(
        count=count,
        height=height,
        width=width,
        transform=transform)

    with rio.open(outfile, 'w', **profile) as dst:
        dst.colorinterp = colorinterp
        dst.write(reprojected)

    return outfile


def warp_fixed(georf, transform, height, width, outfile):

    with rio.open(georf) as src:

        data = read_with_alpha(src)
        out = np.zeros((data.shape[0], height, width), dtype=data.dtype)

        gcps, gcps_crs = src.gcps
        reprojected, _ = reproject(
            source=data,
            destination=out,
            src_crs=gcps_crs,
            gcps=gcps,
            dst_crs=utm31,
            dst_alpha=dst_alpha_idx,
            resampling=resampling,
            dst_transform=transform)

    count = data.shape[0]
    profile = template_profile.copy()
    profile.update(
        count=count,
        height=height,
        width=width,
        transform=transform)

    with rio.open(outfile, 'w', **profile) as dst:
        dst.colorinterp = colorinterp
        dst.write(reprojected)

    return outfile


with fio.open('squiggle.shp') as src:

    entity_ids = tuple(f['properties']['Entity ID'] for f in src)
    utm_bounds = transform_bounds(src.crs, utm31, *src.bounds)


# Use a fixed cell size for all warping
xres, yres = xres_yres(entity_ids)

# Calculate information for warping to a fixed grid
fixed_xmin, fixed_ymin, fixed_xmax, fixed_ymax = utm_bounds
fixed_rows = int(ceil((fixed_ymax - fixed_ymin) / abs(yres)))
fixed_cols = int(ceil((fixed_xmax - fixed_xmin) / xres))
fixed_transform = affine.Affine(
    xres, 0.0, fixed_xmin,
    0.0, yres, fixed_ymax)


for eid in entity_ids:

    georf_path = os.path.join(georf_dir, f'{eid}.jpg')

    warped_naive_path = os.path.join(per_frame_dir, f'{eid}.tif')
    res = warp_naive(georf_path, warped_naive_path)
    print("Warped:", res)

    warped_fixed_path = os.path.join(fixed_grid_dir, f'{eid}.tif')
    res = warp_fixed(
        georf=georf_path,
        transform=fixed_transform,
        height=fixed_rows,
        width=fixed_cols,
        outfile=warped_fixed_path)
    print("Warped:", res)
