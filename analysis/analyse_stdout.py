from os.path import isfile
import re
import subprocess
import numpy as np
from typing import Tuple, Dict

# Matching tool for floats in strings
float_match = re.compile('\d+(\.\d+)?')


class Stdout:
    def __init__(self, stdout_file_path: str):
        assert isfile(stdout_file_path), f"File does not exist: {stdout_file_path}"
        self.file_path = stdout_file_path
        self.file_handle = open(stdout_file_path, 'r')

    def __del__(self):
        self.file_handle.close()

    def analyse_stdout(self, header: int = 18) -> Tuple[np.ndarray]:

        lines = self.file_handle.readlines()[header:]
        timestep_number = np.empty(0, dtype=int)
        particle_updates = np.empty(0, dtype=int)
        timestep_duration = np.empty(0, dtype=float)

        for line in lines:
            print(line)
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

        return timestep_number, particle_updates, timestep_duration

    def find_value_in_line(self, delimiters: Tuple[str], value_type: type):
        for line in self.file_handle.readlines():
            line = line.strip()

            # Check if both delimiters are in the line
            if delimiters[0] in line and delimiters[1] in line:
                result = re.search(f'{delimiters[0]}(.*){delimiters[1]}', line)
                result = result.group(1)

                # Check if expecting a numeric value
                if value_type is int:
                    assert result.isnumeric()
                elif value_type is float:
                    assert float_match.match(result) is not None

                # Convert to final value type. Returning stops the loop
                return value_type(result)

    def num_particles(self):

        return self.find_value_in_line(
            delimiters=('main: Running on ', ' gas'),
            value_type=int
        )

    def num_ranks(self):

        return self.find_value_in_line(
            delimiters=('main: MPI is up and running with ', ' node(s)'),
            value_type=float
        )

    def ic_loading_time(self):

        return self.find_value_in_line(
            delimiters=('main: Reading initial conditions took ', ' ms.'),
            value_type=float
        )

    def scheduler_report_task_times(self, no_zeros: bool = False):
        command = [
            r"grep 'scheduler_report_task_times: '",
            f"{self.file_path}"
        ]
        output = subprocess.check_output(command, shell=True)

        # Convert from binary and split lines
        output = output.decode("utf-8").split('\n')

        # Remove empty lines
        output = list(filter(None, output))

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

        for line in output:
            for category in categories:
                if category in line:
                    # Search for value between delimiters
                    delimiters = f'{category}: ', ' ms'
                    result = re.search(f'{delimiters[0]}(.*){delimiters[1]}', line)
                    result = result.group(1)

                    assert float_match.match(result) is not None
                    result = float(result)

                    # If slim version wanted, don't append zero values
                    if not (no_zeros and round(result, 2) == 0.):
                        scheduler_report[category] = np.append(
                            scheduler_report[category],
                            result
                        )

        # If slim version wanted, delete the fields with no contribution
        if no_zeros:
            for category in categories:
                if len(scheduler_report[category]) == 0:
                    del scheduler_report[category]

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
    print(tasks)
