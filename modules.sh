#!/bin/bash -l

echo Loading modules for SWIFTsim...
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
echo All modules loaded.