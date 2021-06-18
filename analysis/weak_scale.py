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

print('particles', particles)
print('ranks', ranks)
print('threads', threads)
print('times', times)

fig, axes = plt.subplots()
axes.axhline(1, lw=0.5, ls='--', c='lightgrey')
axes.plot(threads, times / times[0], lw=0.5)
axes.set_xlabel('Cores [-]')
axes.set_ylabel('Parallel efficiency relative to $2^3$ tiles [-]')
axes.set_xscale('log')
axes.set_xlim(128, 5e4)
# axes.set_ylim(0, 1.5)

ax_nodes = axes.twiny()
ax_nodes.set_xscale("log")
ax_nodes.set_xlim(1, 5e4 / 128)
ax_nodes.set_xlabel("Nodes [-]")

for i in range(len(threads)):
    exponent = np.floor(np.log10(particles[i]))
    mantissa = np.floor(particles[i] / 10 ** (exponent - 2)) / 100.
    axes.text(threads[i], times[i] / times[0] - 0.14,
              "$N_p = %.2f\\times10^{%d}~\\rightarrow$" % (mantissa, exponent),
              rotation=90, va="top", fontsize=6, color='C0', ha="center", backgroundcolor='w')

plt.show()
