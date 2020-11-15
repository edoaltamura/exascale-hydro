#!/bin/bash -l

#SBATCH -N NODES
#SBATCH --tasks-per-node=TASKSPNODE
#SBATCH --cpus-per-task=CPUSPTASK
#SBATCH -J RUN_NAME
#SBATCH -o ./logs/log_%J.out
#SBATCH -e ./logs/log_%J.err
#SBATCH -p cosma7
#SBATCH -A do006
#SBATCH --exclusive
#SBATCH -t 72:00:00

module purge
module load intel_comp/2020-update2
module load intel_mpi/2020-update2
module load ucx/1.8.1
module load parmetis/4.0.3-64bit
module load parallel_hdf5/1.10.6
module load fftw/3.3.8cosma7
module load gsl/2.5

mpirun -np $SLURM_NTASKS \
  /cosma6/data/dp004/dc-alta2/exascale-hydro/kelvin-helmholtz-3D/swiftsim/examples/swift_mpi \
    --restart \
    --hydro \
    -v 1 \
    --pin \
    --threads=$SLURM_CPUS_PER_TASK ./param.yml


echo "Job done, info follows."
sacct -j $SLURM_JOBID --format=JobID,JobName,Partition,AveRSS,MaxRSS,AveVMSize,MaxVMSize,Elapsed,ExitCode