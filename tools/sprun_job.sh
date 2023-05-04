#!/bin/bash

CSV="slurm-${SLURM_ARRAY_JOB_ID}_${SLURM_ARRAY_TASK_ID}.csv"
START=$SLURM_ARRAY_TASK_ID
STOP=$(($SLURM_ARRAY_TASK_ID + $SLURM_ARRAY_TASK_STEP - 1))

code=0
echo -n > "$CSV"
echo $SLURM_ARRAY_JOB_ID $SLURM_ARRAY_TASK_ID $SLURM_ARRAY_TASK_STEP $START $STOP
for i in $(seq $START $STOP); do
  CMD=$(sed "$((i+1))q;d" "slurm-$SLURM_ARRAY_JOB_ID.lookup.csv")
  echo "TASK $i: $CMD"
  /usr/bin/time -q -f "$i,'%C',%x,%U,%S,%E,%P,%X,%D,%M" -a -o "$CSV" bash -c "$CMD"
  ret=$?
  if [ $ret -ne 0 ]; then
    code=$ret
  fi
  echo "EXIT $i: $ret"
done
exit $code
