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
  destination_directory=$HOME/data7/exascale-hydro
  mkdir -p $destination_directory
  mkdir -p $destination_directory/kelvin-helmholtz-3D
  old_directory=$PWD

  echo "Run name structure: kh3d_N{num_particles-per-tile}_T{num_tiles}_P{processors-per-tile}_C{top_cells_per_tile}"
  run_name=kh3d_N"$resolution"_T"$tiles"_P"$threads_per_tile"_C"$top_cells_per_tile"
  echo $run_name
  run_dir=$destination_directory/kelvin-helmholtz-3D/memory_usage/$run_name
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
  cat > submit.slurm << EOF
#!/bin/bash -l

#SBATCH -N $nodes
#SBATCH --tasks-per-node=$tasks_per_node
#SBATCH --cpus-per-task=$threads_per_tile
#SBATCH -J $run_name
#SBATCH -o ./logs/log_%J.out
#SBATCH -e ./logs/log_%J.err
#SBATCH -p cosma7
#SBATCH -A do006
#SBATCH --exclusive
#SBATCH -t 72:00:00
#SBATCH --exclude=m7448,m7449,m7450,m7451,m7452

module purge
module load intel_comp/2020-update2
module load intel_mpi/2020-update2
module load ucx/1.8.1
module load parmetis/4.0.3-64bit
module load parallel_hdf5/1.10.6
module load fftw/3.3.8cosma7
module load gsl/2.5

mpirun -np $(( $tiles * $tiles * $tiles )) \
  /cosma6/data/dp004/dc-alta2/exascale-hydro/kelvin-helmholtz-3D/swiftsim_intelmpi2020_fftwcosma7_memusage/examples/swift_mpi \
    --hydro \
    -v 1 \
    --pin \
    --threads=$threads_per_tile ./param.yml


echo "Job done, info follows."
sacct -j "$SLURM_JOBID" --format=JobID,JobName,Partition,AveRSS,MaxRSS,AveVMSize,MaxVMSize,Elapsed,ExitCode
EOF

  # Generate the output list with times in the future
  # Don't dump snapshots
  cat > output_list.txt << EOF
# Time
100
EOF

  # Generate initial conditions
  python3 "$old_directory"/make_ics_3d.py -n $resolution -t $tiles -o $run_dir

#  sbatch ./submit.slurm
  cd $old_directory
#  sleep 4
  que

}


setup_run 256 2 14 5
#setup_run 512 2 14 3
#setup_run 512 3 14 3
#setup_run 512 4 14 3
#setup_run 512 5 14 3