#!/bin/bash -l

#SBATCH -N NODES
#SBATCH --tasks-per-node=2
#SBATCH -J kh-THREADS
#SBATCH -o output-THREADS.%J.out
#SBATCH -e error-THREADS.%J.err
#SBATCH -p cosma6
#SBATCH -A dp004
#SBATCH --exclusive
#SBATCH -t 96:00:00

module purge
module load intel_comp/2020
module load intel_mpi/2020
module load parmetis/4.0.3
module load parallel_hdf5/1.10.3
module load gsl/2.4
module load fftw/3.3.7
module load cmake
module load python/3.6.5
module load ffmpeg/4.0.2

ranks=$((NODES*2))

mpirun -np $ranks ./swift_mpi --hydro -v 1 --pin --threads=8 kelvinHelmholtz.yml 2>&1 | tee output.log