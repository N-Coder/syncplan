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


for m in "PQPlanarity" "PQPlanarity-p" "PQPlanarity-p-b" "PQPlanarity-p-b-s" \
         "PQPlanarity-c" "PQPlanarity-i" "PQPlanarity-c-i" \
         "PQPlanarity-p-c" "PQPlanarity-p-i" "PQPlanarity-p-c-i" \
         "PQPlanarity-p-b-c" "PQPlanarity-p-b-i" "PQPlanarity-p-b-c-i" \
         "PQPlanarity-p-b-s-c" "PQPlanarity-p-b-s-i" "PQPlanarity-p-b-s-c-i" \
         "PQPlanarity-r" "PQPlanarity-c-i-r" \
         "PQPlanarity-a" "PQPlanarity-c-i-a" \
         "PQPlanarity-b" "PQPlanarity-c-i-b" \
         "PQPlanarity-b-s" "PQPlanarity-c-i-b-s"; do
  profile "$m" 10 --timeout="01:00:00"
done
