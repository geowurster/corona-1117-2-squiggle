#!/usr/bin/env python3


import io
from multiprocessing.dummy import Pool as ThreadPool
import os

import fiona as fio
import requests


threads = os.cpu_count() * 4
outdir = os.path.join('frames', 'raw')
os.makedirs(outdir, exist_ok=True)


def download_thumbnail(entity_id):

    """

    https://ims.cr.usgs.gov/browse/DIT/1117-2/059D/F/DS1117-2059DF043.jpg
    https://ims.cr.usgs.gov/browse/DIT/1117-2/059D/F/DS1117-2059DF043.jpg


    DS1117-2059DA031

    :param str entity_id:
        ``DS1117-2059DF043``

    :return:
    """

    # Given an entity ID like this: DS1117-2059DF043
    # we want the 'F' -->     ...      ...      ^
    # which stands for 'Forward'. It could be an 'A' for 'Aft'.
    camchar = entity_id.split('-', 1)[1].split('D', 1)[1][0]

    filename = f'{entity_id}.jpg'
    outfile = os.path.join(outdir, filename)

    url = f"https://ims.cr.usgs.gov/browse/DIT/1117-2/059D/{camchar}/{filename}"

    resp = requests.get(url)
    resp.raise_for_status()

    with open(outfile, 'wb') as f:
        for chunk in resp.iter_content(io.DEFAULT_BUFFER_SIZE):
            f.write(chunk)

    return outfile


with fio.open('squiggle.shp') as src, ThreadPool(threads) as pool:

    entity_ids = (f['properties']['Entity ID'] for f in src)
    results = pool.imap_unordered(download_thumbnail, entity_ids)

    for path in results:
        print("Downloaded:", path)
