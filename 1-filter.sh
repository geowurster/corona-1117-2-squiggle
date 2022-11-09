#!/bin/bash


set -eo xtrace


# Downloaded from EarthExplorer
EE_SHP="corona2_63029a261bfcd9a5/corona2_63029a261bfcd9a5.shp"
if [ ! -f "${EE_SHP}" ]; then
  echo "ERROR: Need the footprint shapefile downloaded from EarthExplorer: ${EE_SHP}"
  exit 1
fi


ogr2ogr \
  -f "ESRI Shapefile" \
  "squiggle.shp" \
  "${EE_SHP}" \
  -spat 2 32 6 39 \
  -where "\"Acquisitio\" = '1972-05-29' AND \"Mission\" = '1117-2' AND \"Camera Res\" = 'Stereo High'"
