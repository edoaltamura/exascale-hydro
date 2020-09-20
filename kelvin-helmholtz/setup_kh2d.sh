#!/bin/bash -l
# shellcheck disable=SC2164
# shellcheck disable=SC2004

# Bash script that configures and compiles SWIFT.
# It then places the new compiled binaries in the current directory.

source modules.sh
old_directory=$(pwd)

# Set-up run | you can change these values
architecture="omp"
resolution=512
tiling="1x1"
threads_per_tile=1
nodes=1

# Set-up exa-scale project directories
destination_directory=/cosma6/data/dp004/dc-alta2/exascale-hydro
mkdir -p $destination_directory
mkdir -p $destination_directory/kelvin-helmholtz-2D
mkdir -p $destination_directory/kelvin-helmholtz-2D/omp
mkdir -p $destination_directory/kelvin-helmholtz-2D/mpi

echo "Run name structure: kh2d_{resolution-per-tile}_tile{tiling-scheme}_{threads_per_tile}"
run_name=kh2d_"$resolution"_tile"$tiling"_"$threads_per_tile"
echo $run_name
run_dir=$destination_directory/kelvin-helmholtz-2D/$architecture/$run_name
mkdir -p $run_dir

# Prepare SWIFT
cd $destination_directory/kelvin-helmholtz-2D
if [ ! -d $destination_directory/kelvin-helmholtz-2D/swiftsim ]; then
  echo SWIFT source code not found - cloning from GitLab...
  git clone https://gitlab.cosma.dur.ac.uk/swift/swiftsim.git
  cd $destination_directory/kelvin-helmholtz-2D/swiftsim
  sh ./autogen.sh
  sh ./configure \
    --with-hydro-dimension=2 \
    --with-hydro=sphenix \
    --with-kernel=quintic-spline \
    --disable-hand-vec
  # Configure SWIFT with minimal hydrodynamics scheme
  #  --with-hydro-dimension=2 \
  #  --with-hydro=minimal
  make -j
fi

# We are now in the run data directory
cd $run_dir
mkdir -p ./logs
mkdir -p ./ics

cp "$old_directory"/param.yml .
cp "$old_directory"/submit.slurm .

# Generate initial conditions
python3 "$old_directory"/makeics.py \
  --nparticles=$resolution \
  --tileh=$(echo $tiling | cut -f 1 -d 'x') \
  --tilev=$(echo $tiling | cut -f 2 -d 'x') \
  --outdir=$run_dir/ics

sed -i "s/RUN_NAME/$run_name/" ./param.yml
sed -i "s/RUN_NAME/$run_name/" ./submit.slurm
sed -i "s/MAX_TOP_CELLS/$(($(echo $tiling | cut -f 1 -d 'x') * $threads_per_tile * 3))/" ./param.yml

# Make a omp/mpi switch
if [[ $run_dir == *"omp"* ]]; then

  sed -i "s/NODES/1/" ./submit.slurm
  sed -i "s/TASKSPNODE/1/" ./submit.slurm
  sed -i "s/CPUSPTASK/16/" ./submit.slurm

fi

if [[ $run_dir == *"mpi"* ]]; then

  sed -i "s/NODES/$nodes/" ./submit.slurm
  sed -i "s/TASKSPNODE/2/" ./submit.slurm
  sed -i "s/CPUSPTASK/8/" ./submit.slurm

fi

#sbatch ./submit.slurm
cd "$old_directory"
sh ../runtime_status