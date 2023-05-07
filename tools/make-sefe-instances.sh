#!/bin/bash

set -e

args=""
for n in 100 500 1000 2500 5000 7500 10000; do
  args="$args -n$n"
done
for d in 1 1.5 2 2.5; do
  args="$args -d$d"
done
args="$args -c1"
for s in 111111111 222222222 333333333; do
  args="$args -s$s"
done

mkdir -p "graphs-sefe"
pushd "graphs-sefe"
echo "$args" > random-graph-args.txt
python3 $SP_TOOLS_DIR/evaluation.py random-graph $args # --format=graphml
popd

files=$(find "graphs-sefe" -iname '*.gml' -or -iname '*.graphml')
cnt=$[ $(echo "$files" | wc -l) * 4 * 3 ] # XXX this needs to be the number of iterations we make
echo $(echo "$files" | wc -l) "input files, $cnt output files"
job=$(sbatch --job-name="random-sefe" --parsable \
        --array="0-$cnt:10" --time="350" \
        "$SP_TOOLS_DIR/sprun_job.sh")
echo -n "" > "slurm-$job.lookup.csv"

mkdir -p "instances-sefe"
for f in $files; do
  for d in 0.25 0.5 0.75 1; do
    for s in 111111111 222222222 333333333; do
      # XXX update $cnt when changing the number of iterations made here
      [[ $f =~ -n([0-9]+)- ]]
      n=${BASH_REMATCH[1]}
      [[ $f =~ -e([0-9]+)- ]]
      e=${BASH_REMATCH[1]}
      a=$(python3 -c "print(int((3 * $n - 6 - $e) * $d))")
      echo "$SP_BUILD_DIR/random-pqplan -m 2 -a $a -b $a -s $s "$f" 'instances-sefe/%n-sefe%s%e'" >> "slurm-$job.lookup.csv"
    done
  done
done

scontrol release "$job"
echo "Slurm job $job"
