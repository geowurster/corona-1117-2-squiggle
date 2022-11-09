#!/usr/bin/env python3


from collections import defaultdict
import os
import shutil

import fiona as fio
import numpy as np
import rasterio as rio
from rasterio.enums import ColorInterp


warped_fix_grid_dir = os.path.join('frames', 'warped-fixed')
composited_frames_dir = os.path.join('frames', 'composited')


if os.path.exists(composited_frames_dir):
    shutil.rmtree(composited_frames_dir)
os.makedirs(composited_frames_dir, exist_ok=False)


template_path = os.listdir(warped_fix_grid_dir)[0]
with rio.open(os.path.join(warped_fix_grid_dir, template_path)) as src:
    assert len(set(src.dtypes)) == 1
    profile = src.profile.copy()
    profile.update(
        drier='GTiff',
        COMPRESS='DEFLATE',
        PREDICTOR='2',
        TILED='YES')


frame_to_entity_ids = defaultdict(list)
with fio.open('squiggle.shp') as src:
    for feature in src:
        frame = int(feature['properties']['Frame'])
        entity_id = feature['properties']['Entity ID']
        frame_to_entity_ids[frame].append(entity_id)


digits = len(str(max(frame_to_entity_ids)))
for frame in sorted(frame_to_entity_ids.keys()):

    composite = np.zeros(
        (profile['height'], profile['width']), dtype=profile['dtype'])
    composite_mask = np.ones_like(composite, dtype=bool)

    entity_ids = sorted(frame_to_entity_ids[frame])
    if len(entity_ids) == 0:
        raise ValueError("Something has gone horribly wrong...")
    elif len(entity_ids) > 2:
        raise ValueError(
            f"Frame {frame} has too many entity IDs: {', '.join(entity_ids)}")
    elif len(entity_ids) == 1:
        print(
            f"WARNING: Frame {frame} has {len(entity_ids)} entity IDs:"
            f" {', '.join(entity_ids)}")

    for eid in entity_ids:

        warped_path = os.path.join(warped_fix_grid_dir, f'{eid}.tif')
        with rio.open(warped_path) as src:

            data = src.read(1)
            mask = src.dataset_mask()

            unmasked = mask == 255
            composite[unmasked] = data[unmasked]
            composite_mask[unmasked] = False

    outfile = os.path.join(composited_frames_dir, f'{frame:0{digits}}.tif')
    with rio.open(outfile, 'w', **profile) as dst:
        dst.colorinterp = (ColorInterp.gray, ColorInterp.alpha)
        dst.write(composite, 1)
        mask_data = np.where(composite_mask, np.uint8(0), np.uint8(255))
        dst.write(mask_data, 2)

    print("Composited frame:", outfile)
