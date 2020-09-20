import os
import glob
import unyt
import numpy as np
from matplotlib import pyplot as plt

basepath = os.path.dirname(os.path.abspath(__file__))
os.chdir(basepath)
try:
    plt.style.use("../mnras.mplstyle")
except:
    pass


def time_to_solution(run_directory: str) -> float:
    timesteps_glob = glob(f"{run_directory}/timesteps_*.txt")
    timesteps_filename = timesteps_glob[0]
    data = np.genfromtxt(
        timesteps_filename, skip_footer=5, loose=True, invalid_raise=False
    ).T
    wallclock_time = unyt.unyt_array(np.cumsum(data[-2]), units="ms").to("Hour")
    time2sol = wallclock_time[-1]

    return time2sol


fig = plt.figure()
ax = fig.add_subplot(111)
ax.set_xlabel('Number of threads')
ax.set_ylabel('Time to solution [hours]')
ax.axvspan(16, ax.get_xlim()[-1], alpha=0.25, facecolor='red')
ax.axhline(1, linestyle='-', color='black')

# Open-MP runs directory
omp_dir = '/cosma6/data/dp004/dc-alta2/exascale-hydro/kelvin-helmholtz-2D/omp'
omp_runs = [os.path.join(omp_dir, i) for i in os.listdir(path=omp_dir) if os.path.isdir(i)]
print(omp_runs)
for run in omp_runs:
    print(time_to_solution(run))


# ax.grid(linestyle='--', color='grey', linewidth=0.5)
# fig.tight_layout()
# plt.savefig(os.path.join(basepath, 'wallclocktime.png'), to_slack=True, dpi=400)
