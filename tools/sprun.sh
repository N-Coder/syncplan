#!/bin/bash

job=$(sbatch --hold --parsable "$@" "$(dirname -- $(realpath -- "${BASH_SOURCE[0]}"))/sprun_job.sh")
echo "$(</dev/stdin)" > "slurm-$job.lookup.csv"
sync
scontrol release $job
echo $job
