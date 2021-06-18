from os.path import isfile
import re
import numpy as np
from typing import Tuple, Dict, Union
from unyt import unyt_array, unyt_quantity

# Matching tool for floats in strings
float_match = re.compile('\d+(\.\d+)?')


class Stdout:
    def __init__(self, stdout_file_path: str):
        assert isfile(stdout_file_path), f"File does not exist: {stdout_file_path}"
        with open(stdout_file_path, 'r') as file_handle:
            self.file_lines = file_handle.readlines()

    def find_value_in_line(self, delimiters: Tuple[str]) -> str:
        for line in self.file_lines:
            line = line.strip()

            # Check if both delimiters are in the line
            if delimiters[0] in line and delimiters[1] in line:
                result = re.search(f'{delimiters[0]}(.*){delimiters[1]}', line)
                if result is None:
                    raise ValueError(f'Keyword could not be matched to delimiters {delimiters}')
                result = result.group(1)

                # Convert to final value type. Returning stops the loop
                return result.strip()

    def num_particles(self) -> int:

        return int(
            self.find_value_in_line(
                delimiters=('main: Running on', 'gas'),
            )
        )

    def num_ranks(self) -> int:

        return int(
            self.find_value_in_line(
                delimiters=('main: MPI is up and running with', 'node'),
            )
        )

    def threads_per_rank(self) -> int:

        return int(
            self.find_value_in_line(
                delimiters=('ranks,', 'threads / rank'),
            )
        )

    def num_top_level_cells(self) -> int:

        return int(
            self.find_value_in_line(
                delimiters=('parts in', 'cells.'),
            )
        )

    def ic_loading_time(self) -> unyt_quantity:

        return unyt_quantity(
            float(
                self.find_value_in_line(
                    delimiters=('main: Reading initial conditions took', 'ms'),
                )
            ), 'ms'
        )

    def analyse_stdout(self, header: int = 40) -> Tuple[Union[np.ndarray, unyt_array]]:

        lines = self.file_lines[header:]
        timestep_number = np.empty(0, dtype=int)
        particle_updates = np.empty(0, dtype=int)
        timestep_duration = np.empty(0, dtype=float)
        timestep_properties = np.empty(0, dtype=int)

        for line in lines:
            if line.startswith(' '):
                line = line.strip().split()

                # Split time-step number and duration
                timestep_number = np.append(
                    timestep_number,
                    int(line[0])
                )
                particle_updates = np.append(
                    particle_updates,
                    int(line[7])
                )
                timestep_duration = np.append(
                    timestep_duration,
                    float(line[12])
                )
                timestep_properties = np.append(
                    timestep_properties,
                    int(line[13])
                )

        max_timestep = timestep_number[-1]
        assert len(timestep_number) == max_timestep + 1
        assert len(particle_updates) == max_timestep + 1
        assert len(timestep_duration) == max_timestep + 1
        assert len(timestep_properties) == max_timestep + 1

        return timestep_number, particle_updates, unyt_array(timestep_duration, 'ms'), timestep_properties

    def scheduler_report_task_times(self, no_zeros: bool = False) -> Dict[str, unyt_array]:

        categories = [
            'drift',
            'sorts',
            'resort',
            'hydro',
            'gravity',
            'feedback',
            'black holes',
            'cooling',
            'star formation',
            'limiter',
            'sync',
            'time integration',
            'mpi',
            'fof',
            'others',
            'sink',
            'dead time',
            'total'
        ]

        scheduler_report = dict()
        for category in categories:
            scheduler_report[category] = np.empty(0, dtype=float)

            for line in self.file_lines:
                if 'scheduler_report_task_times: ' in line and category in line:

                    # Search for value between delimiters
                    delimiters = f'{category}:', 'ms'
                    result = re.search(f'{delimiters[0]}(.*){delimiters[1]}', line)
                    result = result.group(1).strip()

                    assert float_match.match(result) is not None, f"{result}"
                    result = float(result)

                    # If slim version wanted, don't append zero values
                    if not (no_zeros and round(result, 2) == 0.):
                        scheduler_report[category] = np.append(
                            scheduler_report[category],
                            result
                        )

            # If slim version wanted, delete the fields with no contribution
            if no_zeros and len(scheduler_report[category]) == 0:
                del scheduler_report[category]

        # Note: these times are the total for all threads in rank 0.
        # To get the average time spent in the rank, divide by the
        # number of threads in each rank.
        number_threads = self.threads_per_rank()

        # Assign time units and format key names
        for category in scheduler_report.copy():
            scheduler_report[category] = unyt_array(scheduler_report[category] / number_threads, 'ms')
            if ' ' in category:
                new_category = category.replace(' ', '_')
                scheduler_report[new_category] = scheduler_report[category]
                del scheduler_report[category]

        return scheduler_report


if __name__ == '__main__':
    cwd = '/cosma8/data/dr004/dc-alta2/4ranks_node/kh3d_N128_T8_P32_C4'
    test = Stdout(cwd + 'logs/log_3494526.out')

    print('num_particles', test.num_particles())
    print('num_ranks', test.num_ranks())
    print('threads_per_rank', test.threads_per_rank())
    print('num_top_level_cells', test.num_top_level_cells())
    print('ic_loading_time', test.ic_loading_time().to('minute'))

    timesteps = test.analyse_stdout()

    is_clean = np.logical_and(timesteps[3] == 0, timesteps[1] == timesteps[1][0])

    print('total wall-clock time', timesteps[2][is_clean].sum().to('minute'))

    tasks = test.scheduler_report_task_times(no_zeros=True)
    for key in tasks:
        print(key, tasks[key].sum().to('minute'))
