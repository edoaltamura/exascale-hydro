import os.path
import numpy as np
import matplotlib.pyplot as plt
from analyse_stdout import Stdout

plt.style.use('../mnras.mplstyle')

cwd = '/cosma8/data/dr004/dc-alta2'  # /with_intelmpi2020u2'
threads_per_node = 128
__particle_load = 256
__ranks_per_node = 4
plot_annotations = False


def get_stdout_path(
        ranks_per_node: int, particle_load: int, tiling_order: int, threads_per_rank: int
):
    ranks_per_node = int(ranks_per_node)
    particle_load = int(particle_load)
    tiling_order = int(tiling_order)
    threads_per_rank = int(threads_per_rank)

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


tiling_orders = {
    2: [2, 3, 4, 5, 6, 7, 8],
    4: [2, 3, 4, 5, 6, 7, 8, 9, 11],
    8: [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 13, 14]
}

# Setup figure structure
fig, axes = plt.subplots()
axes.axhline(1, lw=0.5, ls='--', c='lightgrey')
axes.set_xlabel('Cores [-]')
axes.set_ylabel('Parallel efficiency relative to $2^3$ tiles [-]')
axes.set_xscale('log')
axes.set_xlim(threads_per_node / 2, 5e5)
axes.set_ylim(0, 1.5)
ax_nodes = axes.twiny()
ax_nodes.set_xscale("log")
ax_nodes.set_xlim(0.5, 5e5 / threads_per_node)
ax_nodes.set_xlabel("Nodes [-]")
ax_partupdate = axes.twinx()
ax_partupdate.set_ylabel("Time to update one particle [$\\mu$s]", labelpad=4)

for __ranks_per_node in [2, 4, 8]:

    logs = []
    for t in tiling_orders[__ranks_per_node]:
        logs.append(get_stdout_path(
            __ranks_per_node, __particle_load, t, threads_per_node / __ranks_per_node
        ))

    good_timesteps = []
    no_clean_steps = []
    for i, log in enumerate(logs):
        print(log)
        test = Stdout(os.path.join(cwd, log))
        timestep_number, particle_updates, timestep_duration, timestep_properties = test.analyse_stdout()

        if len(timestep_number) > 0:
            is_clean = np.logical_and(
                timestep_properties == 0,
                particle_updates == particle_updates[0]
            )

            if len(timestep_number[is_clean]) > 0:
                good_timesteps.append(
                    list(timestep_number[is_clean])
                )
            else:
                no_clean_steps.append(log)

        else:
            no_clean_steps.append(log)

    common_timesteps = list(set(good_timesteps[0]).intersection(*good_timesteps[1:]))
    common_timesteps = np.asarray(common_timesteps)
    print('common timesteps', common_timesteps)

    print('runs with no clean timesteps:', no_clean_steps)
    logs = [log for log in logs if log not in no_clean_steps]

    particles = np.empty(len(logs))
    ranks = np.empty(len(logs))
    threads = np.empty(len(logs))
    times_mean = np.empty(len(logs))
    times_std = np.empty(len(logs))
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
        times_mean[i] = timestep_duration[is_clean].mean().to('microsecond')
        times_std[i] = timestep_duration[is_clean].std().to('microsecond')
        time_per_update[i] = times_mean[i] * threads[i] / particles[i]  # micro-second

    print('particles', particles)
    print('ranks', ranks)
    print('threads', threads)
    print('times_mean', times_mean)

    axes.errorbar(
        threads,
        times_mean / times_mean[0],
        yerr=times_std / times_mean[0],
        lw=0.5, marker='o', markersize=2,
        label=f'COSMA8 - Full steps, {__ranks_per_node} MPI ranks per node, {__particle_load}$^2$ particles per tile'
    )

    ax_partupdate.set_ylim(0 * np.median(time_per_update), 1.5 * np.median(time_per_update))

    if plot_annotations:
        for i in range(len(threads)):
            exponent = np.floor(np.log10(particles[i]))
            mantissa = np.floor(particles[i] / 10 ** (exponent - 2)) / 100.
            axes.text(
                threads[i],
                times_mean[i] / times_mean[0] - 0.14,
                "$N_p = %.2f\\times10^{%d}~\\rightarrow$" % (mantissa, exponent),
                rotation=90, va="top", fontsize=4, color='C0', ha="center", backgroundcolor='none'
            )

axes.legend(loc="lower left")
plt.show()
