#!/bin/bash


set -eo xtrace


function translate() {

  for TIF in "${1}"/*.tif; do

    OUTFILE="${TIF/.tif/.png}"
    gdal_translate \
      -q \
      -f PNG \
      "$TIF" \
      "$OUTFILE"

    echo "Translated: $OUTFILE"

  done

}


translate frames/warped-fixed
translate frames/composited
