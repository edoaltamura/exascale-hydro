#!/bin/bash -l

module purge
module load python/3.6.5

# Set-up run function
setup_run(){

  # Gather function arguments
  resolution=$1
  tiles=$2
  threads_per_tile=$3
  top_cells_per_tile=$4

  # Set-up exa-scale project directories
  destination_directory=$HOME/snap7/exascale-hydro
  mkdir -p $destination_directory
  mkdir -p $destination_directory/kelvin-helmholtz-3D
  old_directory=$PWD

  echo "Run name structure: kh3d_N{num_particles-per-tile}_T{num_tiles}_P{processors-per-tile}_C{top_cells_per_tile}"
  run_name=kh3d_N"$resolution"_T"$tiles"_P"$threads_per_tile"_C"$top_cells_per_tile"
  echo $run_name
  run_dir=$destination_directory/kelvin-helmholtz-3D/$run_name
  mkdir -p $run_dir

  # We are now in the run data directory
  cd $run_dir
  mkdir -p ./logs
  cp "$old_directory"/param.yml .
  cp "$old_directory"/submit.slurm .

  # Set 1 cell per rank (2 ranks per node)
  # Note: this way you can allocate a max of 14 threads per cell
  nodes=$(( ($tiles * $tiles * $tiles) / 2 ))
  total_top_cells=$(( $tiles * $top_cells_per_tile ))

  sed -i "s/MAX_TOP_CELLS/$total_top_cells/" ./param.yml
  sed -i "s/NODES/$nodes/" ./submit.slurm
  sed -i "s/CPUSPTASK/$threads_per_tile/" ./submit.slurm
  sed -i "s/RUN_NAME/$run_name/" ./submit.slurm

  # Generate initial conditions
  python3 "$old_directory"/make_ics_3d.py -n $resolution -t $tiles -o $run_dir

  sbatch ./submit.slurm
  cd $old_directory
  sleep 5
  que

}


setup_run 128 2 14 3
setup_run 128 3 14 3
