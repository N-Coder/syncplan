#!/bin/bash

set -e

args=""
for n in 100 500 1000 5000 10000 50000 100000; do
  args="$args -n$n"
done
for d in 1.5 2 2.5; do
  args="$args -d$d"
done
for c in 1 10 100; do
  args="$args -c$c"
done
for s in 111111111 222222222 333333333; do
  args="$args -s$s"
done

mkdir -p "graphs-pq"
pushd "graphs-pq"
echo "$args" > random-graph-args.txt
python3 $SP_TOOLS_DIR/evaluation.py random-graph $args # --format=graphml
popd

files=$(find "graphs-pq" -iname '*.gml' -or -iname '*.graphml')
cnt=$[ $(echo "$files" | wc -l) * 3 * 3 ] # XXX this needs to be the number of iterations we make
echo $(echo "$files" | wc -l) "input files, $cnt output files"
job=$(sbatch --job-name="random-pq" --parsable \
        --array="0-$cnt:10" --time="350" \
        "$SP_TOOLS_DIR/sprun_job.sh")
echo -n "" > "slurm-$job.lookup.csv"

mkdir -p "instances-pq"
for f in $files; do
  for d in 0.05 0.1 0.2; do
    for s in 111111111 222222222 333333333; do
      # XXX update $cnt when chaning the number of iterations made here
      [[ $f =~ -n([0-9]+)- ]]
      n=${BASH_REMATCH[1]}
      a=$(python3 -c "print(int($d * $n))")
      echo "$SP_BUILD_DIR/random-pqplan -m 1 -a $a -b 4 -s $s "$f" 'instances-pq/%n-pq%s%e'" >> "slurm-$job.lookup.csv"
    done
  done
done

scontrol release "$job"
echo "Slurm job $job"
