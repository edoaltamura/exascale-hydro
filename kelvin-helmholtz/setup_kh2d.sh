#!/bin/bash -l
# shellcheck disable=SC2164
# shellcheck disable=SC2004

# Bash script that configures and compiles SWIFT.
# It then places the new compiled binaries in the current directory.

source modules.sh
old_directory=$(pwd)

# Set-up run function
setup_run(){

  # Gather function arguments
  architecture=$1
  resolution=$2
  tiling=$3
  threads_per_tile=$4

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

    # When using the 2d kernel, remember to hack the runner_ghost.c file on line 1047:
    # Lines:  1045c1047
    #<         if (p->density.wcount <= 1e-5 * kernel_root) { /* No neighbours case */
    #---
    #>         if (p->density.wcount == 0.f) { /* No neighbours case */
    sed -i '1047s/== 0.f/<= 1e-5 * kernel_root/' $destination_directory/kelvin-helmholtz-2D/swiftsim/src/runner_ghost.c

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

  tile_x=$(echo $tiling | cut -f 1 -d 'x')
  tile_y=$(echo $tiling | cut -f 2 -d 'x')
  nodes=$((($tile_x * $tile_y * $threads_per_tile) / 16)) # Automatically rounds to nearest integer

  # Generate initial conditions if not present
  if find "$run_dir/ics" -mindepth 1 -print -quit 2>/dev/null | grep -q .; then
      echo "Initial conditions directory not empty. Contents are listed below:"
      ls -lh "$run_dir/ics"
  else
      echo "Initial conditions directory is empty - generating ICs..."
      python3 "$old_directory"/makeics.py \
        --nparticles=$resolution \
        --tileh=$tile_x \
        --tilev=$tile_y \
        --outdir=$run_dir/ics
  fi

  sed -i "s/RUN_NAME/$run_name/" ./param.yml
  sed -i "s/RUN_NAME/$run_name/" ./submit.slurm
  sed -i "s/MAX_TOP_CELLS/$(($tile_x * $threads_per_tile * 3))/" ./param.yml

  # Make a omp/mpi switch
  if [[ $run_dir == *"omp"* ]]; then

    sed -i "s/NODES/1/" ./submit.slurm
    sed -i "s/TASKSPNODE/1/" ./submit.slurm
#    sed -i "s/CPUSPTASK/$(($tile_x * $tile_y * $threads_per_tile))/" ./submit.slurm
    sed -i "s/CPUSPTASK/16/" ./submit.slurm  # Toggle this line for testing hyper-threading

  fi

  if [[ $run_dir == *"mpi"* ]]; then

    sed -i "s/NODES/$nodes/" ./submit.slurm
    sed -i "s/TASKSPNODE/2/" ./submit.slurm
    sed -i "s/CPUSPTASK/8/" ./submit.slurm

  fi

  sbatch ./submit.slurm
  cd "$old_directory"
  sh ../runtime_status.sh

}


#declare -a tilings=("1x1" "2x2" "3x3" "4x4")
#for tiling in "${tilings[@]}"
#do
#  setup_run "omp" 512 "$tiling" 1
#done
#
#declare -a tilings=("1x1" "2x2")
#for tiling in "${tilings[@]}"
#do
#  setup_run "omp" 512 "$tiling" 2
#done
#
#declare -a tilings=("1x1" "2x2")
#for tiling in "${tilings[@]}"
#do
#  setup_run "omp" 512 "$tiling" 3
#done
#
#declare -a tilings=("1x1" "2x2")
#for tiling in "${tilings[@]}"
#do
#  setup_run "omp" 512 "$tiling" 4
#done

# HYPER-THREAD OPEN-MP
declare -a tilings=("5x5" "6x6" "7x7")
for tiling in "${tilings[@]}"
do
  setup_run "omp" 512 "$tiling" 1
done

declare -a tilings=("3x3" "4x4" "5x5")
for tiling in "${tilings[@]}"
do
  setup_run "omp" 512 "$tiling" 2
done

declare -a tilings=("3x3" "4x4" "5x5")
for tiling in "${tilings[@]}"
do
  setup_run "omp" 512 "$tiling" 3
done

declare -a tilings=("3x3" "4x4" "5x5")
for tiling in "${tilings[@]}"
do
  setup_run "omp" 512 "$tiling" 4
done


#declare -a tilings=("1x1" "2x2" "3x3" "4x4" "5x5" "6x6" "7x7" "8x8" "9x9" "10x10")
#for tiling in "${tilings[@]}"
#do
#  setup_run "mpi" 512 "$tiling" 1
#done

#declare -a tilings=("1x1" "2x2" "3x3" "4x4" "5x5" "6x6" "7x7" "8x8" "9x9" "10x10")
#for tiling in "${tilings[@]}"
#do
#  setup_run "mpi" 512 "$tiling" 2
#done