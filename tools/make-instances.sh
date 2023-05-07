#!/bin/bash

set -e

args=""

for n in 100 500 1000; do # testing
#for n in 100 500 1000 5000 10000 50000 100000; do # large
#for n in 100 200 300 400 500 600 700 800 900 1000; do # med
#for n in 100 200 300 400 500; do # med-ncp
  args="$args -n$n"
done

for d in 1 1.5 2 2.5 3; do
  args="$args -d$d"
done

for c in 10; do # testing
#for c in 1 10 100; do # large
#for c in 1 10 25 50; do # med
#for c in 10 20 30 40 50; do # med-ncp
  args="$args -c$c"
done

for s in 111111111; do # testing
#for s in 111111111 222222222 333333333; do # large, med, medncp
  args="$args -s$s"
done

suffix="testing"
mkdir -p "graphs-$suffix"
pushd "graphs-$suffix"
echo "$args" > random-graph-args.txt
python3 $SP_TOOLS_DIR/evaluation.py random-graph $args # --format=graphml
popd

files=$(find "graphs-$suffix" -iname '*.gml' -or -iname '*.graphml')
cnt=$[ $(echo "$files" | wc -l) * 2 ] # XXX this needs to be the number of iterations we make
echo $(echo "$files" | wc -l) "input files, $cnt output files"
job=$(sbatch --job-name="random-clusters" --parsable \
        --array="0-$cnt:10" --time="350" \
        "$SP_TOOLS_DIR/sprun_job.sh")
echo -n "" > "slurm-$job.lookup.csv"

mkdir -p "clusters-$suffix"
for f in $files; do
  for c in 10 50; do # testing
#  for c in 3 5 10 25 50 100 1000; do # large
#  for c in 3 5 10 20 30 40 50; do # med, med-ncp
    for s in 111111111; do # testing
#    for s in 111111111 222222222 333333333; do # large, med, medncp
      # XXX update $cnt when changing the number of iterations made here

      # echo "random-clusters '$f' -c $c -s $s"
      # -j 0 default CPlanar
      echo "$SP_BUILD_DIR/random-cplan -t 1800 -j 0 -a -l 3 -c $c -s $s '$f' 'clusters-$suffix/%n-cg-j0%s%e'" >> "slurm-$job.lookup.csv" # large, med
      # -j 1 old maybe CPlanar
      echo "$SP_BUILD_DIR/random-cplan -t 1800 -j 1 -a -l 3 -d $c -s $s '$f' 'clusters-$suffix/%n-cg-j1%s%e'" >> "slurm-$job.lookup.csv" # medncp
      # -j 2 old non CPlanar
      echo "$SP_BUILD_DIR/random-cplan -t 1800 -j 2 -a -l 3 -d $c -s $s '$f' 'clusters-$suffix/%n-cg-j2%s%e'" >> "slurm-$job.lookup.csv" # medncp
    done
  done
done

scontrol release "$job"
echo "Slurm job $job"
