source modules.sh
source compile.sh

mkdir -p $plot_directory/$run_name
# Check if run exists before doing any of this stuff!
if [[ -f $run_directory/$snapshot_name ]]
then
  plot_run $run_directory $run_name $plot_directory $snapshot_name $catalogue_name
  create_summary_plot $run_directory $run_name $plot_directory $snapshot_name $catalogue_name
  #image_run $run_directory $run_name $plot_directory $snapshot_name $catalogue_name
fi