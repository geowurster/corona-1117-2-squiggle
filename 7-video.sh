#!/bin/bash


set -e


function gif(){

  ARGS=("$@")

  DISPOSE_FLAG="-dispose"
  if [[ ${ARGS[*]} =~ $DISPOSE_FLAG ]]; then
    DISPOSE=(-dispose previous)
    ARGS=("${ARGS[@]/$DISPOSE}")
  else
    DISPOSE=("" "")
  fi

  RNARGS=2
  if [ ${#ARGS} -lt $RNARGS ]; then
    echo "ERROR: Need at least $RNARGS arguments: ${ARGS[*]}"
    exit 1
  fi


  INFILES=${ARGS[*]::${#ARGS[*]}-1}
  OUTFILE=${ARGS[*]: -1}

  convert \
    -delay 50 \
    "${DISPOSE[@]}" \
    $INFILES \
    "$OUTFILE"

}


function vid() {

  ffmpeg \
    -y \
    -framerate 0.5 \
    -hide_banner \
    -loglevel error \
    -pattern_type glob \
    -i "$1" \
    -c:v libx264 \
    -pix_fmt yuv420p \
    "$2"

}


AFT_PNGS=frames/warped-fixed/*DA*.png
gif $AFT_PNGS aft-only-iterative.gif
gif -dispose $AFT_PNGS aft-individual.gif


FWD_PNGS=frames/warped-fixed/*DF*.png
gif $FWD_PNGS aft-only-iterative.gif
gif -dispose $FWD_PNGS aft-individual.gif


COMPOSITED_PNGS=frames/composited/*.png
gif $COMPOSITED_PNGS composited-iterative.gif
gif $COMPOSITED_PNGS composited-individual.gif
