#!/bin/bash

set -e

env | grep SP_

profile () {
  m="$1"
  shift
  b="$1"
  shift
  a=$(python3 $SP_TOOLS_DIR/evaluation.py find-missing-prog -m "$m" -b "$b")
  echo "$m: batch size $b, array $a, args $@"
  if [ -z "$a" ]; then echo "skipping"; return; fi
  cmd="python3 $SP_TOOLS_DIR/evaluation.py profile -m '$m' $@"
  sbatch --job-name="sp $m" --array="$a" --cpus-per-task=2 --mem="6600M" --time="610" --wrap="$cmd"
}


#profile "PQPlanarity"     100 --timeout="00:05:00"
profile "PQPlanarity-c-i" 100 --timeout="00:05:00"
#profile "CConnected"      100 --timeout="00:05:00"
profile "HananiTutte"      10 --timeout="00:05:00"
profile "HananiTutte-f"    10 --timeout="00:05:00"
profile "ILP"              10 --timeout="00:05:30" --timeout-ilp="00:05:00"
