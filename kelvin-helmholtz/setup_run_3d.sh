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
  tasks_per_node=$5

  # Set-up exa-scale project directories
  destination_directory=/cosma8/data/dr004/dc-alta2/"$tasks_per_node"ranks_node
  mkdir -p $destination_directory
  old_directory=$PWD

  echo "Run name structure: kh3d_N{num_particles-per-tile}_T{num_tiles}_P{processors-per-tile}_C{top_cells_per_tile}"
  run_name=kh3d_N"$resolution"_T"$tiles"_P"$threads_per_tile"_C"$top_cells_per_tile"
  echo $run_name
  run_dir=$destination_directory/$run_name
  mkdir -p $run_dir

  # We are now in the run data directory
  cd $run_dir
  mkdir -p ./logs
  cp "$old_directory"/param.yml .
  cp "$old_directory"/submit.slurm .
#  cp "$old_directory"/resubmit.slurm .
#  cp "$old_directory"/auto_resubmit.sh .

  # Make launch scripts executable by SWIFT
  chmod 744 ./submit.slurm
#  chmod 744 ./resubmit.slurm
#  chmod 744 ./auto_resubmit.sh

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
  sed -i "s/NTILES/$tiles/g" ./param.yml
#  sed -i "s/file_name:  .\/kelvin_helmholtz_3d.hdf5/file_name:  ..\/..\/with_intelmpi\/$run_name\/kelvin_helmholtz_3d.hdf5/" ./param.yml

  # Edit mutable parameters in the submit file
  cat > submit.slurm << EOF
#!/bin/bash -l

#SBATCH -N $nodes
#SBATCH --tasks-per-node=$tasks_per_node
#SBATCH --cpus-per-task=$threads_per_tile
#SBATCH -J swtile_$run_name
#SBATCH -o ./logs/log_%J.out
#SBATCH -e ./logs/log_%J.err
#SBATCH -p cosma8
#SBATCH -A dr004
#SBATCH --exclusive
#SBATCH -t 3:00:00

module purge
module load intel_comp/2021.1.0
module load compiler
module load intel_mpi/2018
module load ucx/1.8.1
module load fftw/3.3.9epyc
module load parallel_hdf5/1.10.6
module load parmetis/4.0.3-64bit
module load gsl/2.5


mpirun -np $(( $tiles * $tiles * $tiles )) \
  ../../swiftsim/examples/swift_mpi \
    --hydro \
    -v 1 \
    --pin \
    --threads=\$SLURM_CPUS_PER_TASK ./param.yml


echo "Job done, info follows."
sacct -j \$SLURM_JOBID --format=JobID,JobName,Partition,AveRSS,MaxRSS,AveVMSize,MaxVMSize,Elapsed,ExitCode
EOF

  # Generate the output list with times in the future
  # Don't dump snapshots
  cat > output_list.txt << EOF
# Time
89
90
EOF

  # Generate initial conditions
  if [ ! -f "$destination_directory"/kelvin_helmholtz_3d.hdf5 ]; then
      #  python3 "$old_directory"/make_ics_3d.py -n $resolution -t $tiles -o $run_dir
      python3 "$old_directory"/make_ics_3d.py -n $resolution -t 1 -o $destination_directory
  fi

  sbatch ./submit.slurm
  cd $old_directory
  sleep 2

}

setup_run 256 2 64 4 2
setup_run 256 3 64 4 2
setup_run 256 4 64 4 2
setup_run 256 5 64 4 2
setup_run 256 6 64 4 2
setup_run 256 7 64 4 2
setup_run 256 8 64 4 2

setup_run 256 2 32 4 4
setup_run 256 3 32 4 4
setup_run 256 4 32 4 4
setup_run 256 5 32 4 4
setup_run 256 6 32 4 4
setup_run 256 7 32 4 4
setup_run 256 8 32 4 4
setup_run 256 9 32 4 4
setup_run 256 10 32 4 4
setup_run 256 11 32 4 4

setup_run 256 2 16 4 8
setup_run 256 3 16 4 8
setup_run 256 4 16 4 8
setup_run 256 5 16 4 8
setup_run 256 6 16 4 8
setup_run 256 7 16 4 8
setup_run 256 8 16 4 8
setup_run 256 9 16 4 8
setup_run 256 10 16 4 8
setup_run 256 11 16 4 8
setup_run 256 12 16 4 8
setup_run 256 13 16 4 8
setup_run 256 14 16 4 8

wait
squeue -u dc-alta2
echo "All done!"