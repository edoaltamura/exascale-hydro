"""
Plots wallclock v.s. simulation time.
"""
import unyt
import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LogNorm
from glob import glob
import os


try:
    plt.style.use("../mnras.mplstyle")
except:
    pass


def particle_updates_step_cost(
        run_name: str,
        snap_filepath_zoom: str,
        output_directory: str
) -> None:
    run_directory = os.path.join(os.path.dirname(snap_filepath_zoom), os.pardir)
    timesteps_glob = glob(f"{run_directory}/timesteps_*.txt")
    timesteps_filename = timesteps_glob[0]

    number_of_updates_bins = unyt.unyt_array(np.logspace(0, 10, 512), units="dimensionless")
    wallclock_time_bins = unyt.unyt_array(np.logspace(0, 6, 512), units="ms")

    data = np.genfromtxt(
        timesteps_filename, skip_footer=5, loose=True, invalid_raise=False
    ).T

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
    fig.savefig(f"{output_directory}/{run_name}_particle_updates_step_cost.png")

particle_updates_step_cost(
    "kh3d_N256_T5_P14_C3",
    "/cosma/home/dp004/dc-alta2/snap7/exascale-hydro/kelvin-helmholtz-3D/kh3d_N256_T5_P14_C3",
    "."
)