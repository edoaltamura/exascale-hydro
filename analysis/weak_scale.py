import os
import unyt
import numpy as np
from typing import Tuple, List
from matplotlib import pyplot as plt

try:
    plt.style.use("../mnras.mplstyle")
except:
    pass

out_dir = '/cosma6/data/dp004/dc-alta2/exascale-hydro/kelvin-helmholtz-2D/analysis'


def get_timesteps_log(run_directory: str) -> str:
    for i in os.listdir(run_directory):
        if os.path.isfile(os.path.join(run_directory, i)) and i.startswith('timesteps_'):
            timesteps_glob = os.path.join(run_directory, i)
            break

    return timesteps_glob


def time_to_solution(timesteps_glob: str) -> float:
    data = np.genfromtxt(timesteps_glob, skip_footer=5, loose=True, invalid_raise=False).T
    time2sol = unyt.unyt_quantity(np.sum(data[-2]), units="ms").to("Hour")

    return time2sol.value


def number_of_threads(timesteps_glob: str) -> int:
    timesteps_basename = os.path.basename(timesteps_glob)

    # The total number of threads is written in the timesteps filename
    start = 'timesteps_'
    end = '.txt'

    threads = timesteps_basename[
              timesteps_basename.find(start) + len(start):timesteps_basename.rfind(end)
              ]

    try:
        threads = int(threads)
    except ValueError as e:
        print(
            "Error encountered when looking for the number of threads. "
            f"Integer expected, instead got {threads}."
        )
        raise e

    return threads


def weak_scale(run_list: List[str]) -> Tuple[np.ndarray]:
    threads = []
    time2sol = []
    for run in run_list:
        timesteps_file = get_timesteps_log(run)
        print(f"Processing run {timesteps_file}")
        threads.append(number_of_threads(timesteps_file))
        time2sol.append(time_to_solution(timesteps_file))

    threads = np.asarray(threads, dtype=np.int)
    time2sol = np.asarray(time2sol, dtype=np.float)

    sort_key = np.argsort(threads)
    return threads[sort_key], time2sol[sort_key]


fig, ax = plt.subplots()

threads, time2sol = weak_scale([
    "/cosma/home/dp004/dc-alta2/snap7/exascale-hydro/kelvin-helmholtz-3D/kh3d_N128_T1_P14_C3",
    "/cosma/home/dp004/dc-alta2/snap7/exascale-hydro/kelvin-helmholtz-3D/kh3d_N128_T2_P14_C3",
    "/cosma/home/dp004/dc-alta2/snap7/exascale-hydro/kelvin-helmholtz-3D/kh3d_N128_T3_P14_C3",
    "/cosma/home/dp004/dc-alta2/snap7/exascale-hydro/kelvin-helmholtz-3D/kh3d_N128_T4_P14_C3"
])
ax.plot(threads, time2sol)

ax.set_title("KH3D - SWIFT MPI - Cosma 7")
# ax.grid(linestyle='--', color='grey', linewidth=0.5)
ax.set_xlabel('Number of threads')
ax.set_ylabel('Time to solution [hours]')
ax.set_xscale('log')
# ax.set_ylim([0, 2])
fig.tight_layout()
plt.show()
# plt.savefig(f'{out_dir}/kh2d_omp_time2solution.png', dpi=300)
# plt.close(fig)

# fig, ax = plt.subplots()
#
# for n in range(1, 5):
#     threads, time2sol = weak_scale_omp(threads_per_tile=n)
#     ax.plot(threads, time2sol[0] / time2sol, label=f"threads_per_tile = {n}")
#
# ax.set_title("KH2D - SWIFT MPI:off - Cosma 6")
# ax.grid(linestyle='--', color='grey', linewidth=0.5)
# ax.set_xlabel('Number of threads')
# ax.set_ylabel('Weak-scaling efficiency ($t_0/t_N$)')
# ax.set_ylim([0, 1.1])
# ax.axvspan(16, ax.get_xlim()[-1], alpha=0.25, facecolor='red')
# ax.text(17, 0.1, "Hyper-threading", color="grey", ha="left", va="bottom")
# ax.axhline(1, linestyle='-', color='black', alpha=0.1)
# plt.legend()
# fig.tight_layout()
# # plt.show()
# plt.savefig(f'{out_dir}/kh2d_omp_weak_efficiency.png', dpi=300)
# plt.close(fig)
