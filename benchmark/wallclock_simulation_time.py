"""
Plots wallclock v.s. simulation time.
"""
import unyt
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from swiftsimio import load
from glob import glob
import os


try:
    plt.style.use("../mnras.mplstyle")
except:
    pass


def wallclock_simulation_time(
        run_name: str,
        snap_filepath_zoom: str,
        output_directory: str
) -> None:
    run_directory = os.path.join(os.path.dirname(snap_filepath_zoom), os.pardir)
    timesteps_glob = glob(f"{run_directory}/timesteps_*.txt")
    timesteps_filename = timesteps_glob[0]

    snapshot = load(snap_filepath_zoom)
    data = np.genfromtxt(
        timesteps_filename, skip_footer=5, loose=True, invalid_raise=False
    ).T
    
    sim_time = unyt.unyt_array(data[1], units=snapshot.units.time).to("Gyr")
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
    fig.savefig(f"{output_directory}/{run_name}_wallclock_simulation_time.png")
