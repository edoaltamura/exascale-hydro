import os.path
import numpy as np
import matplotlib.pyplot as plt
from analyse_stdout import Stdout

plt.style.use('../mnras.mplstyle')

cwd = '/cosma8/data/dr004/dc-alta2'


def get_stdout_path(
        ranks_per_node: int, particle_load: int, tiling_order: int, threads_per_rank: int
):
    log_directory = os.path.join(
        cwd,
        f'{ranks_per_node}ranks_node',
        f'kh3d_N{particle_load}_T{tiling_order}_P{threads_per_rank}_C4',
        'logs'
    )
    log_stdouts = [file for file in os.listdir(log_directory) if file.endswith('.out')]
    log_stdouts = [os.path.join(log_directory, file) for file in log_stdouts]
    latest_file = max(
        log_stdouts,
        key=os.path.getctime
    )

    return latest_file


logs = [get_stdout_path(2, 128, t, 64) for t in range(2, 9)]

good_timesteps = []
for i, log in enumerate(logs):
    print(log)
    test = Stdout(os.path.join(cwd, log))
    timestep_number, particle_updates, timestep_duration, timestep_properties = test.analyse_stdout()

    is_clean = np.logical_and(
        timestep_properties == 0,
        particle_updates == particle_updates[0]
    )
    print(timestep_number[is_clean])
    good_timesteps.append(
        list(timestep_number[is_clean])
    )

common_timesteps = list(set(good_timesteps[0]).intersection(*good_timesteps[1:]))
common_timesteps = np.asarray(common_timesteps)
print('common timesteps', common_timesteps)

particles = np.empty(len(logs))
ranks = np.empty(len(logs))
threads = np.empty(len(logs))
times = np.empty(len(logs))
time_per_update = np.empty(len(logs))

for i, log in enumerate(logs):
    test = Stdout(os.path.join(cwd, log))

    particles[i] = test.num_particles()
    ranks[i] = test.num_ranks()
    threads[i] = test.num_ranks() * test.threads_per_rank()

    timestep_number, particle_updates, timestep_duration, timestep_properties = test.analyse_stdout()
    timestep_number = timestep_number[common_timesteps]
    particle_updates = particle_updates[common_timesteps]
    timestep_duration = timestep_duration[common_timesteps]
    timestep_properties = timestep_properties[common_timesteps]

    is_clean = np.logical_and(
        timestep_properties == 0,
        particle_updates == particle_updates[0],
    )
    times[i] = timestep_duration[is_clean].sum().to('microsecond')

    time_per_update[i] = times[i] * threads[i] / particles[i]  # micro-second

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
axes.set_ylim(0, 1.5)

ax_nodes = axes.twiny()
ax_nodes.set_xscale("log")
ax_nodes.set_xlim(1, 5e4 / 128)
ax_nodes.set_xlabel("Nodes [-]")

ax_partupdate = axes.twinx()
ax_partupdate.set_ylim(0 * time_per_update.mean(), 1.5 * time_per_update.mean())
ax_partupdate.set_ylabel("Time to update one particle [$\\mu$s]", labelpad=4)

for i in range(len(threads)):
    exponent = np.floor(np.log10(particles[i]))
    mantissa = np.floor(particles[i] / 10 ** (exponent - 2)) / 100.
    axes.text(threads[i], times[i] / times[0] - 0.14,
              "$N_p = %.2f\\times10^{%d}~\\rightarrow$" % (mantissa, exponent),
              rotation=90, va="top", fontsize=6, color='C0', ha="center", backgroundcolor='w')

plt.show()
