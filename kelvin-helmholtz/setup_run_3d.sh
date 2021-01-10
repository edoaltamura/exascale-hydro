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
  cp "$old_directory"/resubmit.slurm .
  cp "$old_directory"/auto_resubmit.sh .

  # Make launch scripts executable by SWIFT
  chmod 744 ./submit.slurm
  chmod 744 ./resubmit.slurm
  chmod 744 ./auto_resubmit.sh

  # Set 1 cell per rank (2 ranks per node)
  # Note: this way you can allocate a max of 14 threads per cell
  # Take particular care in rounding up the number of nodes, otherwise the
  # last rank will be left out if $tiles^3 is an odd number.
  # Examples:
  # $(( (1 + 1) / 2 )) = 1
  # $(( (2 + 1) / 2 )) = 1 --> int(1.5) = 1
  # $(( (3 + 1) / 2 )) = 2
  # $(( (4 + 1) / 2 )) = 2 --> int(2.5) = 2
  # $(( (5 + 1) / 2 )) = 3
  # $(( (6 + 1) / 2 )) = 3 --> int(3.5) = 3
  tasks_per_node=2
  nodes=$(( ($tiles * $tiles * $tiles + 1) / $tasks_per_node ))
  total_top_cells=$(( $tiles * $top_cells_per_tile ))
  echo "Nodes: $nodes"
  echo "MPI ranks: $(( $tiles * $tiles * $tiles ))"
  echo "CPUs (= threads): $(( $tiles * $tiles * $tiles * $threads_per_tile ))"

  # If single tile, special case
  if [[ "$tiles" -eq 1 ]]; then
    tasks_per_node=1
  fi

  # Edit mutable parameters in the SWIFT param.yml
  sed -i "s/MAX_TOP_CELLS/$total_top_cells/" ./param.yml

  # Edit mutable parameters in the submit file
  sed -i "s/NODES/$nodes/" ./submit.slurm
  sed -i "s/CPUSPTASK/$threads_per_tile/" ./submit.slurm
  sed -i "s/TASKSPNODE/$tasks_per_node/" ./submit.slurm
  sed -i "s/RUN_NAME/$run_name/" ./submit.slurm
  sed -i "s/NTASKS_TRUE/$(( $tiles * $tiles * $tiles ))/" ./submit.slurm

  # Edit mutable parameters in the resubmit file
  sed -i "s/NODES/$nodes/" ./resubmit.slurm
  sed -i "s/CPUSPTASK/$threads_per_tile/" ./resubmit.slurm
  sed -i "s/TASKSPNODE/$tasks_per_node/" ./resubmit.slurm
  sed -i "s/RUN_NAME/$run_name/" ./resubmit.slurm
  sed -i "s/NTASKS_TRUE/$(( $tiles * $tiles * $tiles ))/" ./resubmit.slurm

  # Generate initial conditions
  python3 "$old_directory"/make_ics_3d.py -n $resolution -t $tiles -o $run_dir

  sbatch ./submit.slurm
  cd $old_directory
  sleep 4
  que

}

#setup_run 128 1 14 3
setup_run 128 2 14 5
#setup_run 128 3 14 3
setup_run 128 4 14 5
#setup_run 128 5 14 3
setup_run 128 6 14 5
setup_run 128 8 14 5

#setup_run 256 1 14 3
setup_run 256 2 14 5
#setup_run 256 3 14 3
setup_run 256 4 14 5
#setup_run 256 5 14 3
setup_run 256 6 14 5
setup_run 256 8 14 5

#setup_run 512 1 14 3
#setup_run 512 2 14 3
#setup_run 512 3 14 3
#setup_run 512 4 14 3
#setup_run 512 5 14 3

#setup_run 256 2 14 21
