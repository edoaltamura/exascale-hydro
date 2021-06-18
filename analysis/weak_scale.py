import os.path
import numpy as np
import matplotlib.pyplot as plt
from analyse_stdout import Stdout

plt.style.use('../mnras.mplstyle')

cwd = '/cosma8/data/dr004/dc-alta2'

logs = [
    '2ranks_node/kh3d_N128_T2_P64_C4/logs/log_3494228.out',
    '2ranks_node/kh3d_N128_T3_P64_C4/logs/log_3494229.out',
    '2ranks_node/kh3d_N128_T4_P64_C4/logs/log_3494230.out',
    '2ranks_node/kh3d_N128_T5_P64_C4/logs/log_3494231.out',
    '2ranks_node/kh3d_N128_T6_P64_C4/logs/log_3494233.out',
    '2ranks_node/kh3d_N128_T7_P64_C4/logs/log_3494232.out',
    '2ranks_node/kh3d_N128_T8_P64_C4/logs/log_3494234.out',
]

particles = np.empty(len(logs))
ranks = np.empty(len(logs))
threads = np.empty(len(logs))
times = np.empty(len(logs))

for i, log in enumerate(logs):
    test = Stdout(os.path.join(cwd, log))

    particles[i] = test.num_particles()
    ranks[i] = test.num_ranks()
    threads[i] = test.num_ranks() * test.threads_per_rank()

    timesteps = test.analyse_stdout()
    is_clean = np.logical_and(timesteps[3] == 0, timesteps[1] == timesteps[1][0])
    times[i] = timesteps[2][is_clean].sum().to('minute')


fig, axes = plt.subplots()
axes.plot(threads, times / times[0])
axes.set_xlabel('Cores [-]')
axes.set_ylabel('Parallel efficiency relative to $2^3$ tiles [-]')
axes.set_xscale('log')
axes.set_ylim(0, 1.5)
axes.set_xlim(6e1, 3e4)
plt.show()
