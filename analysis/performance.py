import unyt
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LogNorm

try:
    plt.style.use("../mnras.mplstyle")
except:
    pass

from glob import glob
import sys

run_directory = sys.argv[1]
output_path = sys.argv[2]

timesteps_glob = glob(f"{run_directory}/timesteps_*.txt")
timesteps_filename = timesteps_glob[0]

data = np.genfromtxt(
    timesteps_filename, skip_footer=5, loose=True, invalid_raise=False
).T

# ========================================================================================= #

sim_time = data[1]
number_of_steps = np.arange(sim_time.size) / 1e3

fig, ax = plt.subplots()

# Simulation data plotting
ax.plot(number_of_steps, sim_time, color="C0")
ax.scatter(number_of_steps[-1], sim_time[-1], color="C0", marker=".", zorder=10)
ax.set_ylabel("Simulation time [Sim units]")
ax.set_xlabel("Number of steps [thousands]")
ax.set_xlim(0, None)
ax.set_ylim(0, None)
fig.tight_layout()
fig.savefig(f"{output_path}/number_of_steps_simulation_time.png")

# ========================================================================================= #

number_of_updates_bins = unyt.unyt_array(np.logspace(0, 10, 512), units="dimensionless")
wallclock_time_bins = unyt.unyt_array(np.logspace(0, 6, 512), units="ms")

number_of_updates = unyt.unyt_array(data[8], units="dimensionless")
wallclock_time = unyt.unyt_array(data[-2], units="ms")

fig, ax = plt.subplots()
ax.loglog()

# Simulation data plotting
H, updates_edges, wallclock_edges = np.histogram2d(
    number_of_updates.value,
    wallclock_time.value,
    bins=[number_of_updates_bins.value, wallclock_time_bins.value],
)

mappable = ax.pcolormesh(updates_edges, wallclock_edges, H.T, norm=LogNorm(vmin=1))
fig.colorbar(mappable, label="Number of steps", pad=0)

# Add on propto n line
x_values = np.logspace(5, 9, 512)
y_values = np.logspace(1, 5, 512)
ax.plot(x_values, y_values, color="grey", linestyle="dashed")
ax.text(2e7, 0.5e3, "$\\propto n$", color="grey", ha="left", va="top")
ax.set_ylabel("Wallclock time for step [ms]")
ax.set_xlabel("Number of particle updates in step")
ax.set_xlim(updates_edges[0], updates_edges[-1])
ax.set_ylim(wallclock_edges[0], wallclock_edges[-1])
fig.tight_layout()
fig.savefig(f"{output_path}/particle_updates_step_cost.png")

# ========================================================================================= #

wallclock_time = unyt.unyt_array(np.cumsum(data[-2]), units="ms").to("Hour")
number_of_steps = np.arange(wallclock_time.size) / 1e6

fig, ax = plt.subplots()

# Simulation data plotting
ax.plot(wallclock_time, number_of_steps, color="C0")
ax.scatter(wallclock_time[-1], number_of_steps[-1], color="C0", marker=".", zorder=10)
ax.set_ylabel("Number of steps [millions]")
ax.set_xlabel("Wallclock time [Hours]")
ax.set_xlim(0, None)
ax.set_ylim(0, None)
fig.tight_layout()
fig.savefig(f"{output_path}/wallclock_number_of_steps.png")

# ========================================================================================= #

sim_time = data[1]
wallclock_time = unyt.unyt_array(np.cumsum(data[-2]), units="ms").to("Hour")

fig, ax = plt.subplots()

# Simulation data plotting
ax.plot(wallclock_time, sim_time, color="C0")
ax.scatter(wallclock_time[-1], sim_time[-1], color="C0", marker=".", zorder=10)
ax.set_ylabel("Simulation time [Gyr]")
ax.set_xlabel("Wallclock time [Hours]")
ax.set_xlim(0, None)
ax.set_ylim(0, None)
fig.tight_layout()
fig.savefig(f"{output_path}/wallclock_simulation_time.png")

