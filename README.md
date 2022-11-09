Corona Mission 1117-2 Squiggle
==============================

![Image](https://pbs.twimg.com/media/FeVY6whagAAzlhU?format=jpg&name=medium)

Discovered by [@engelsjk on Twitter](https://twitter.com/engelsjk/status/1577826462597804032?s=20&t=tWb42z2bNYxUA0YG4BVcGg).

The contents of this repository are a work in progress but in general aim to
automate (to whatever degree possible) the processing of related data to
understand the actual motion of the spacecraft.

The files starting with a number can be run in order to process the core data
and some visualizations.

Some directories are deleted automatically on-rerun and some are not. Trying
to be friendly to people altering the data between phases for R&D purposes.

Everything after "phase 4" (`4-warp.py`) is not really functional.

Setup
-----

Install GDAL, ImageMagick, ffmpeg, and the Python dependencies (in a virtual
environment below. On a Mac with Homebrew this might look like:

```console
$ brew instal python gdal imagemagick ffmpeg
$ python -m venv venv
$ source venv/bin/activate
(venv) $ pip install affine rasterio requests
```

Pipeline
--------

### `1-filter.sh`

Extract only the squiggle from the full EarthExplorer dataset.

### `2-download-thumbnails.py`

Scrape low-res thumbnails from the USGS site.

### `3-georeference.py`

Add georeferencing information to the thumbnails.

### `4-warp.py`

Reproject thumbnails to ortho-space. This produces one set of images that are
naively reprojected to a target resolution and size that GDAL determines to be
appropriate, and another set of images that are reprojected to a fixed grid.
The latter are assembled into video frames.

### `5-composite-frames.py`

Generate individual video frames. Unclear how necessary this is and seems to
depend on if ffmpeg or ImageMagick is used to generate a video. The latter has
a method for compositing new data into the previously rendered frame, which
avoids some more bespoke compositing options.

### `6-video-frames.sh`

Convert composited frames to files that either ffmpeg or ImageMagick can
interpret. Again, this isn't quite done

### `7-video.sh`

Render a video with either ffmpeg or ImageMagic,. Unscoped.

### `inspect-broken.py`

Applies all possible versions of a thumbnail with GCPs applied. The idea is
that a human should just brute-force this process since the list is fairly
small. Probably needs a reference layer to help determine if a given GCP
order is correct.


Thematic Layers
---------------

Country borders provide some context:

```console
$ wget https://www.naturalearthdata.com/download/10m/cultural/ne_10m_admin_0_countries.zip
```
