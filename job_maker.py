import subprocess
import os
import shutil
import yaml
import time
from itertools import product
import numpy as np

basepath = os.path.dirname(os.path.abspath(__file__))


def bash(command: str) -> None:
    process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
    output, error = process.communicate()


def edit_yaml(file: str, group: str, newvalue) -> None:
    with open(file) as f:
        list_doc = yaml.load(f)
    groups = group.split('/')
    if groups[0] in list_doc and groups[1] in list_doc[groups[0]]:
        if not newvalue:
            del list_doc[groups[0]][groups[1]]
        else:
            list_doc[groups[0]][groups[1]] = newvalue
    with open(file, "w") as f:
        yaml.dump(list_doc, f, default_flow_style=False)


def edit_slurm(file: str, key: str, newline: str) -> None:
    with open(file) as f:
        list_doc = f.readlines()
    for i, line in enumerate(list_doc):
        if key in line:
            list_doc[i] = newline + '\n'
    with open(file, 'w') as file:
        file.writelines(list_doc)


def launch(i: int, j: int, nparts: int, threads_per_tile: int = 1, mpi: bool = False) -> None:
    os.chdir(basepath)
    savedir = f"/cosma6/data/dp004/dc-alta2/kh_weakscaling/tile{i}x{j}p{npart}"

    if not os.path.exists(savedir):
        os.makedirs(savedir)
    if not os.path.exists(os.path.join(savedir, 'data')):
        os.makedirs(os.path.join(savedir, 'data'))

    # Create initial conditions and move to data folders
    if not os.path.isfile(os.path.join(savedir, "kelvinHelmholtz.hdf5")):
        bash(f"python3 makeIC_tile.py --nparticles={npart} --tileh={i} --tilev={j}")
        shutil.move(os.path.join(basepath, "kelvinHelmholtz.hdf5"), savedir)

    shutil.copyfile(os.path.join(basepath, "kelvin-helmholtz/param.yml"), os.path.join(savedir,
                                                                                       "kelvin-helmholtz/param.yml"))
    shutil.copyfile(os.path.join(basepath, "run.sh"), os.path.join(savedir, "run.sh"))

    # Copy parameter files into data folders and change parameters
    os.chdir(savedir)
    edit_yaml("kelvin-helmholtz/param.yml", "Snapshots/subdir", os.path.join(savedir, 'data'))
    edit_yaml("kelvin-helmholtz/param.yml", "Snapshots/time_first", 3)
    edit_yaml("kelvin-helmholtz/param.yml", "Snapshots/delta_time", 0.04)
    edit_yaml("kelvin-helmholtz/param.yml", "InitialConditions/file_name", os.path.join(savedir, "kelvinHelmholtz.hdf5"))
    edit_yaml("kelvin-helmholtz/param.yml", "Scheduler/max_top_level_cells", i * threads_per_tile if i == j else None)

    # Create SLURM submission scripts
    edit_slurm(f"run.sh", "#SBATCH -N", "#SBATCH -N 1")
    edit_slurm(f"run.sh", "#SBATCH --ntasks-per-node", "#SBATCH --ntasks-per-node 1")
    edit_slurm(f"run.sh", "#SBATCH -J", f"#SBATCH -J {i}x{j}p{npart}")
    edit_slurm(f"run.sh", "#SBATCH -t", f"#SBATCH -t 72:00:00")
    if mpi:
        edit_slurm(f"run.sh", "mpirun",
                   f"mpirun {os.path.join(basepath, 'swift_mpi')} --hydro -v 1 --pin --threads=8 param.yml 2>&1 | tee output.log")
    else:
        edit_slurm(f"run.sh", "mpirun",
                   f"{os.path.join(basepath, 'swift')} --hydro -v 1 --pin --threads={i * j * threads_per_tile} param.yml 2>&1 | tee output.log")

    # Submit to SLURM
    print(f"Submitting tile{i}x{j}p{npart}...")
    bash("sbatch run.sh")


nparts = [256, 512, 1024]
tiles = [1, 2, 3]
for npart in nparts:
    norepeat_runs = []
    for i, j in product(tiles, repeat=2):
        if (i * j) not in norepeat_runs:
            norepeat_runs.append(i * j)
            launch(i, j, nparts, threads_per_tile=4, mpi=False)

os.chdir(basepath)
print(f"Total number of submissions: {len(norepeat_runs) * len(nparts)}\n\nActive:")
os.system("sh runtime_summary.sh")
