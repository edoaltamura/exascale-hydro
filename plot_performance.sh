#!/bin/bash -l

# Bash function that provides plotting and analysis ability for a specific run
# Adapted from Josh's xl-pipeline

# Parameters are as follows:
# 1. Run directory - location of the run. E.g. Run/Run1
# 2. Run name - symbolic name for this run. E.g. MyRun
# 3. Plot directory - where the plots should be stored. E.g. Plots
# 4. Snapshot name - name of the snapshot. E.g. eagle_0036.hdf5
# 5. Catalogue name - name of the halo properties. E.g. stf/stf.properties
#
# For the above, this will assume that:
# + There is a directory Run/Run1
# + The snapshot lives at Run/Run1/eagle_0036.hdf5
# + The halo catalogue lives at Run/Run1/stf/stf.properties
# + You want the plots to be saved in Plots/MyRun
# + You want the run to be called MyRun on the summary plot.
#
plot_run () {
  run_directory=$1
  run_name=$2
  plot_directory=$3
  snapshot_name=$4

  output_path=$plot_directory/$run_name

  python3 performance/number_of_steps_simulation_time.py \
    $run_name \
    $run_directory \
    $snapshot_name \
    $output_path

  python3 performance/particle_updates_step_cost.py \
    $run_name \
    $run_directory \
    $snapshot_name \
    $output_path

  python3 performance/wallclock_number_of_steps.py \
    $run_name \
    $run_directory \
    $snapshot_name \
    $output_path

  python3 performance/wallclock_simulation_time.py \
    $run_name \
    $run_directory \
    $snapshot_name \
    $output_path
}

export -f plot_run