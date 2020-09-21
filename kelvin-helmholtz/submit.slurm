#!/bin/bash -l

#SBATCH -N NODES
#SBATCH --tasks-per-node=TASKSPNODE
#SBATCH --cpus-per-task=CPUSPTASK # Hard-set to "16" for testing hyper-threading on OMP
#SBATCH -J RUN_NAME
#SBATCH -o ./logs/%x.%J.swift.out
#SBATCH -e ./logs/%x.%J.swift.err
#SBATCH -p cosma6
#SBATCH -A dp004
#SBATCH --exclusive
#SBATCH -t 6:00:00

source ~/exascale-hydro/modules.sh

# Make a omp/mpi switch
if [[ $PWD == *"omp"* ]]; then

  export OMP_NUM_THREADS=$SLURM_CPUS_PER_TASK

  /cosma6/data/dp004/dc-alta2/exascale-hydro/kelvin-helmholtz-2D/swiftsim/examples/swift \
    --hydro \
    -v 1 \
    --pin \
    --threads=CPUSPTASK ./param.yml
fi

if [[ $PWD == *"mpi"* ]]; then

  mpirun -np "$SLURM_NTASKS" \
    /cosma6/data/dp004/dc-alta2/exascale-hydro/kelvin-helmholtz-2D/swiftsim/examples/swift_mpi \
      --hydro \
      -v 1 \
      --pin \
      --threads="$SLURM_CPUS_PER_TASK" ./param.yml

fi