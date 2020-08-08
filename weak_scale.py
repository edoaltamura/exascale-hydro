import os
import warnings
import slack
import socket
from itertools import product
import numpy as np
import datetime
import matplotlib

matplotlib.use('Agg')
from matplotlib import pyplot as plt

basepath = os.path.dirname(os.path.abspath(__file__))
os.chdir(basepath)
plt.style.use("mnras.mplstyle")


def read(filepath: str) -> tuple:
    simtime = []
    wallclock = []
    with open(filepath) as f:
        lines = f.read().splitlines()

    for l in lines:
        if not l.startswith('#'):
            line = l.split()
            if len(line) > 10:
                simtime.append(line[1])
                wallclock.append(line[-2])

    incomplete_lines = min(len(simtime), len(wallclock))
    simtime = [float(i) for i in simtime[:incomplete_lines]]
    wallclock = [float(i) for i in wallclock[:incomplete_lines]]
    simtime = np.asarray(simtime)
    wallclock = np.asarray(np.cumsum(wallclock) / 1e3)
    assert len(simtime) == len(wallclock)
    return simtime, wallclock


def save_plot(filepath: str, to_slack: bool = False, **kwargs) -> None:
    """
        Function to parse the plt.savefig method and send the file to a slack channel.
        :param filepath: The path+filename+extension where to save the figure
        :param to_slack: Gives the option to send the the plot to slack
        :param kwargs: Other kwargs to parse into the plt.savefig
        :return: None
        """
    plt.savefig(filepath, **kwargs)
    if to_slack:
        print(
            "[+] Forwarding to the `#personal` Slack channel",
            f"\tDir: {os.path.dirname(filepath)}",
            f"\tFile: {os.path.basename(filepath)}",
            sep='\n'
        )
        slack_token = 'xoxp-452271173797-451476014913-1101193540773-57eb7b0d416e8764be6849fdeda52ce8'
        slack_msg = f"Host: {socket.gethostname()}\nDir: {os.path.dirname(filepath)}\nFile: {os.path.basename(filepath)}"
        try:
            # Send files to Slack: init slack client with access token
            client = slack.WebClient(token=slack_token)
            client.files_upload(file=filepath, initial_comment=slack_msg, channels='#personal')
        except:
            warnings.warn("[-] Failed to broadcast plot to Slack channel.")


# ax.set_xscale("log")
# ax.set_yscale("log")
# ax.axvline(15, linestyle='--', linewidth=0.3, color='blue')

print("Running processes status:")
os.system("sh runtime_summary.sh")

fig = plt.figure()
ax = fig.add_subplot(111)
ax.set_xlabel('Simulation time [Internal units]')
ax.set_ylabel('Wallclock time [seconds]')
colors = ['lime', 'orange', 'aqua']
nparts = [256, 512, 1024]
tiles = [1, 2, 3]
for npart in nparts:
    norepeat_runs = []
    for i, j in product(tiles, repeat=2):
        if (i * j) not in norepeat_runs:
            norepeat_runs.append(i * j)
            print(f"Reading tile{i}x{j}p{npart}...")
            savedir = f"/cosma6/data/dp004/dc-alta2/kh_weakscaling/tile{i}x{j}p{npart}"
            filename = [name for name in os.listdir(savedir) if name.startswith("timesteps_")]
            if len(filename) > 0 and os.path.isfile(os.path.join(savedir, filename[0])):
                simtime, wallclock = read(os.path.join(savedir, filename[0]))
                ax.plot(simtime, wallclock, color=colors[nparts.index(npart)], lw=i * j / 4,
                        alpha=(0.3 + 0.7 / np.sqrt(i * j)))
                if simtime[-1] == 15.0:
                    ax.scatter(simtime[-1], wallclock[-1], marker='*', c='r', s=i * j * 2,
                               alpha=(0.3 + 0.7 / np.sqrt(i * j)))

fig.tight_layout()
save_plot(os.path.join(basepath, 'wallclocktime.png'), to_slack=True, dpi=400)

colors = ['lime', 'orange', 'aqua']
nparts = [256, 512, 1024]
tiles = [1, 2, 3]
for npart in nparts:
    norepeat_runs = []
    threads = []
    simtimes = []
    simtime_last = []
    wallclocks = []
    for i, j in product(tiles, repeat=2):
        if (i * j) not in norepeat_runs:
            norepeat_runs.append(i * j)
            print(f"Reading tile{i}x{j}p{npart}...")
            savedir = f"/cosma6/data/dp004/dc-alta2/kh_weakscaling/tile{i}x{j}p{npart}"
            filename = [name for name in os.listdir(savedir) if name.startswith("timesteps_")]
            if len(filename) > 0 and os.path.isfile(os.path.join(savedir, filename[0])):
                simtime, wallclock = read(os.path.join(savedir, filename[0]))
                threads.append(i * j * 4)
                simtimes.append(simtime)
                simtime_last.append(simtime[-1])
                wallclocks.append(wallclock)

    # Normalise to slowest run
    if len(simtime_last) == 0:
        continue
    simtime_slowest = np.min(simtime_last)
    time2sol = []
    for st, wc in zip(simtimes, wallclocks):
        time2sol.append(wc[np.where(st <= simtime_slowest)[0]][-1])
    del simtimes

    # Sort lists
    time2sol = [x for _, x in sorted(zip(threads, time2sol), key=lambda pair: pair[0])]
    threads = sorted(threads)
    print("Benchmarks are normalised to the slowest run, currently at sim-time: ", simtime_slowest)
    ax.plot(threads, time2sol[0] / time2sol, color=colors[nparts.index(npart)],
            label=f"$N_\mathrm{{part}} = {npart}^2$")

ax.axvspan(16, ax.get_xlim()[-1], alpha=0.25, facecolor='red')
ax.axhline(1, linestyle='-', color='black')
plt.legend()
ax.grid(linestyle='--', color='grey', linewidth=0.5)
fig.tight_layout()
save_plot(os.path.join(basepath, 'wallclocktime.png'), to_slack=True, dpi=400)
