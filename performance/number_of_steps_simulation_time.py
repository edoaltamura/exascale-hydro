"""
Plots wallclock v.s. simulation time.
"""
import unyt
import matplotlib.pyplot as plt
import numpy as np
from swiftsimio import load
try:
    plt.style.use("mnras.mplstyle")
except:
    pass

from glob import glob
import sys

run_name = sys.argv[1]
run_directory = sys.argv[2]
snapshot_name = sys.argv[3]
output_path = sys.argv[4]

timesteps_glob = glob(f"{run_directory}/timesteps_*.txt")
timesteps_filename = timesteps_glob[0]
snapshot_filename = f"{run_directory}/{snapshot_name}"

snapshot = load(snapshot_filename)
data = np.genfromtxt(
    timesteps_filename, skip_footer=5, loose=True, invalid_raise=False
).T

sim_time = unyt.unyt_array(data[1], units=snapshot.units.time).to("Gyr")
number_of_steps = np.arange(sim_time.size) / 1e6

fig, ax = plt.subplots()

# Simulation data plotting
ax.plot(number_of_steps, sim_time, color="C0")
ax.scatter(number_of_steps[-1], sim_time[-1], color="C0", marker=".", zorder=10)
ax.set_ylabel("Simulation time [Gyr]")
ax.set_xlabel("Number of steps [millions]")
ax.set_xlim(0, None)
ax.set_ylim(0, None)
fig.tight_layout()
fig.savefig(f"{output_path}/number_of_steps_simulation_time.png")
