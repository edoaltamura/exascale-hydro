from os.path import isfile
import re
import numpy as np
from typing import Tuple, Dict
from unyt import unyt_array

# Matching tool for floats in strings
float_match = re.compile('\d+(\.\d+)?')


class Stdout:
    def __init__(self, stdout_file_path: str):
        assert isfile(stdout_file_path), f"File does not exist: {stdout_file_path}"
        with open(stdout_file_path, 'r') as file_handle:
            self.file_lines = file_handle.readlines()

    def find_value_in_line(self, delimiters: Tuple[str]):
        for line in self.file_lines:
            line = line.strip()

            # Check if both delimiters are in the line
            if delimiters[0] in line and delimiters[1] in line:
                result = re.search(f'{delimiters[0]}(.*){delimiters[1]}', line)
                result = result.group(1)

                # Convert to final value type. Returning stops the loop
                return result.strip()

    def num_particles(self):

        return self.find_value_in_line(
            delimiters=('main: Running on', 'gas'),
        )

    def num_ranks(self):

        return self.find_value_in_line(
            delimiters=('main: MPI is up and running with', 'node'),
        )

    def ic_loading_time(self):

        return self.find_value_in_line(
            delimiters=('main: Reading initial conditions took', 'ms'),
        )

    def analyse_stdout(self, header: int = 40) -> Tuple[np.ndarray]:

        lines = self.file_lines[header:]
        timestep_number = np.empty(0, dtype=int)
        particle_updates = np.empty(0, dtype=int)
        timestep_duration = np.empty(0, dtype=float)

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

        max_timestep = timestep_number[-1]
        assert len(timestep_number) == max_timestep + 1
        assert len(particle_updates) == max_timestep + 1
        assert len(timestep_duration) == max_timestep + 1

        return timestep_number, particle_updates, unyt_array(timestep_duration, 'ms')

    def scheduler_report_task_times(self, no_zeros: bool = False):

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

        # Assign time units and format key names
        for category in list(scheduler_report):
            new_category = category.replace(' ', '_')
            scheduler_report[new_category] = scheduler_report[category]
            del scheduler_report[category]
            scheduler_report[new_category] = unyt_array(scheduler_report[new_category], 'ms')

        return scheduler_report


if __name__ == '__main__':
    cwd = '/cosma/home/dp004/dc-alta2/data7/exascale-hydro/kelvin-helmholtz-3D/february_mpi_tests/with_intelmpi/'
    test = Stdout(cwd + 'kh3d_N256_T9_P14_C5/logs/log_2951736.out')

    print(test.num_particles())
    print(test.num_ranks())
    print(test.ic_loading_time())

    timesteps = test.analyse_stdout()
    print(timesteps[2].sum())

    tasks = test.scheduler_report_task_times(no_zeros=True)
    for key in tasks:
        print(key, tasks[key])
