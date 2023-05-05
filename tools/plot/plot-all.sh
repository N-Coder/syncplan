#!/bin/bash

set -e
unset SP_MAX_IDX
mkdir -p $SP_PLOT_DIR

python ../tools/plot/ds_stats.py > "$SP_PLOT_DIR/log.txt"

for ds in "clusters-large" "clusters-med" "clusters-medncp" "dsold" "instances-sefe" "instances-pq"; do
  echo $ds
  export SP_COLLECTION="stats-$ds"
  export SP_INDEX="index-$ds.csv"
  python ../tools/plot/plot.py > "$SP_PLOT_DIR/log-$ds.txt"
done
