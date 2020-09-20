import os
import unyt
import numpy as np
from typing import Tuple
from matplotlib import pyplot as plt

try:
    plt.style.use("../mnras.mplstyle")
except:
    pass

out_dir = '/cosma6/data/dp004/dc-alta2/exascale-hydro/kelvin-helmholtz-2D/analysis'


def time_to_solution(run_directory: str) -> float:

    for i in os.listdir(run_directory):
        if os.path.isfile(os.path.join(run_directory, i)) and i.startswith('timesteps_'):
            timesteps_glob = os.path.join(run_directory, i)
            break

    data = np.genfromtxt(
        timesteps_glob, skip_footer=5, loose=True, invalid_raise=False
    ).T
    wallclock_time = unyt.unyt_array(np.cumsum(data[-2]), units="ms").to("Hour")
    time2sol = wallclock_time[-1]

    return time2sol

def number_of_threads(run_directory: str) -> int:
    dir_basename = os.path.basename(os.path.normpath(run_directory))
    assert len(dir_basename.split('x')) == 2
    tile_x = dir_basename.split('x')[0][-1]
    tile_y = dir_basename.split('x')[1][0]
    threads_per_tile = dir_basename.split('_')[-1][0]
    return int(tile_x) * int(tile_y) * int(threads_per_tile)

def weak_scale_omp(threads_per_tile: int = 1) -> Tuple[np.ndarray]:
    # Open-MP runs directory
    omp_dir = '/cosma6/data/dp004/dc-alta2/exascale-hydro/kelvin-helmholtz-2D/omp'
    omp_runs = [os.path.join(omp_dir, i) for i in os.listdir(omp_dir) if
                os.path.isdir(os.path.join(omp_dir, i)) and i.endswith(str(threads_per_tile))]
    threads = []
    time2sol = []
    for run in omp_runs:
        threads.append(number_of_threads(run))
        time2sol.append(time_to_solution(run))

    threads = np.asarray(threads, dtype=np.int)
    time2sol = np.asarray(time2sol, dtype=np.float)

    sort_key = np.argsort(threads)
    return threads[sort_key], time2sol[sort_key]


fig, ax = plt.subplots()

for n in range(1, 5):
    threads, time2sol = weak_scale_omp(threads_per_tile=n)
    ax.plot(threads, time2sol, label=f"threads_per_tile = {n}")

ax.set_title("KH2D - SWIFT Open-MP - Cosma 6")
ax.grid(linestyle='--', color='grey', linewidth=0.5)
ax.set_xlabel('Number of threads')
ax.set_ylabel('Time to solution [hours]')
ax.set_ylim([0, 1])
ax.axvspan(16, ax.get_xlim()[-1], alpha=0.25, facecolor='red')
ax.text(17, 0.1, "Hyper-threading", color="grey", ha="left", va="bottom")
ax.axhline(1, linestyle='-', color='black', alpha=0.1)
plt.legend()
fig.tight_layout()
plt.show()
plt.savefig(f'{out_dir}/kh2d_omp_time2solution.png', dpi=300)

fig, ax = plt.subplots()

for n in range(1, 5):
    threads, time2sol = weak_scale_omp(threads_per_tile=n)
    ax.plot(threads, time2sol / time2sol[0], label=f"threads_per_tile = {n}")

ax.set_title("KH2D - SWIFT Open-MP - Cosma 6")
ax.grid(linestyle='--', color='grey', linewidth=0.5)
ax.set_xlabel('Number of threads')
ax.set_ylabel('Weak-scaling efficiency ($t_N/t_0$)')
ax.set_ylim([0, 1])
ax.axvspan(16, ax.get_xlim()[-1], alpha=0.25, facecolor='red')
ax.text(17, 0.1, "Hyper-threading", color="grey", ha="left", va="bottom")
ax.axhline(1, linestyle='-', color='black', alpha=0.1)
plt.legend()
fig.tight_layout()
plt.show()
plt.savefig(f'{out_dir}/kh2d_omp_weak_efficiency.png', dpi=300)