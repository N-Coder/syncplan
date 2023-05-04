#!/bin/bash

set -x
set -e

mkdir -p /run/munge
if [ ! -f /etc/munge/munge.key ]; then
  dd if=/dev/urandom bs=1 count=1024 > /etc/munge/munge.key
else
  echo "/etc/munge/munge.key already exists!"
fi
chown munge:munge /etc/munge/munge.key
chmod 400 /etc/munge/munge.key
chown munge:munge /run/munge

if [ ! -f /etc/slurm/slurm.conf ]; then
  cat > /etc/slurm/slurm.conf <<EOF
ClusterName=slurm-in-docker
SlurmctldHost=$(hostname -s)
$(slurmd -C | grep NodeName) State=UNKNOWN
PartitionName=slurm-in-docker-partition Nodes=$(hostname -s) Default=YES MaxTime=INFINITE State=UP
MailProg=/bin/true
ProctrackType=proctrack/pgid
SelectType=select/cons_res
SelectTypeParameters=CR_Core
MaxArraySize=200000

EOF
else
  echo "/etc/slurm/slurm.conf already exists!"
fi