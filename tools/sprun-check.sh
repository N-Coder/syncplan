#!/bin/bash

set -e

[ -z "$2" ] || cd $2

JOBID=$1
if [ ! -f "slurm-$JOBID.lookup.csv" ]; then
    echo "Did not find lookup file slurm-$JOBID.lookup.csv in $(pwd)!" >&2
    exit 1
fi
NRS="slurm-$JOBID.nrs.csv"
MAX=$(cat "slurm-$JOBID.lookup.csv" | wc -l)
echo "Checking $MAX jobs..." >&2
[ -f "slurm-$JOBID.stats.csv" ] || find . -name "slurm-${JOBID}_*.csv" -exec cat \{} \; | sort -h > "slurm-$JOBID.stats.csv"
cat "slurm-$JOBID.stats.csv" | cut -d , -f 1,3 | sort -h > "$NRS"
seq -f "%.f,0" 0 $MAX | grep -vwFf "$NRS" - | cut -d , -f 1 > "slurm-$JOBID.failed.csv"
CNT=$(wc -l "slurm-$JOBID.failed.csv" | cut -d " " -f 1)
if [ $CNT > 0 ]; then
    echo "$CNT jobs failed:" >&2
    head -c -1 "slurm-$JOBID.failed.csv" | tr "\n" ","
    echo
else
    echo "All jobs successful!" >&2
fi

# sacct -o "Submit,Start,End,JobID,JobName,State,Reason,ExitCode,NodeList,UserCPU" -S "now-2days" --units=G -P > stats.psv
