import h5py
import numpy as np
import os
import psutil
import argparse
from tqdm import trange

total_memory = psutil.virtual_memory().total
print(f"Total physical memory: {total_memory / 1024 / 1024 / 1024:.2f} GB")


def dump_memory_usage() -> None:
    process = psutil.Process(os.getpid())
    memory = process.memory_info().rss  # in bytes
    print((
        f"[Resources] Memory usage: {memory / 1024 / 1024:.2f} MB "
        f"({memory / total_memory * 100:.2f}%)"
    ))


# Generates a swift IC file for the Kelvin-Helmholtz vortex in a periodic box
parser = argparse.ArgumentParser()
parser.add_argument('-n', '--nparticles', type=int, default=128, required=False)
parser.add_argument('-t', '--tile', type=int, default=2, required=False)
parser.add_argument('-o', '--outdir', type=str, default='.', required=False)
parser.add_argument('-s', '--silent-progressbar', action='store_true', default=False, required=False)
args = parser.parse_args()

# Parameters
L2 = args.nparticles  # Particles along one edge in the low-density region
gamma = 5. / 3.  # Gas adiabatic index
P1 = 2.5  # Central region pressure
P2 = 2.5  # Outskirts pressure
v1 = 0.5  # Central region velocity
v2 = -0.5  # Outskirts vlocity
rho1 = 2  # Central density
rho2 = 1  # Outskirts density
omega0 = 0.1
sigma = 0.05 / np.sqrt(2)
fileOutputName = "kelvin_helmholtz_3d.hdf5"
# ---------------------------------------------------

# Start by generating grids of particles at the two densities
numPart2 = L2 * L2
L1 = int(np.sqrt(numPart2 / rho2 * rho1))
numPart1 = L1 * L1
coords1 = np.zeros((numPart1, 3))
coords2 = np.zeros((numPart2, 3))
h1 = np.ones(numPart1) * 1.2348 / L1
h2 = np.ones(numPart2) * 1.2348 / L2
m1 = np.zeros(numPart1)
m2 = np.zeros(numPart2)
u1 = np.zeros(numPart1)
u2 = np.zeros(numPart2)
vel1 = np.zeros((numPart1, 3))
vel2 = np.zeros((numPart2, 3))

# Particles in the central region
for i in range(L1):
    for j in range(L1):
        index = i * L1 + j
        x = i / float(L1) + 1. / (2. * L1)
        y = j / float(L1) + 1. / (2. * L1)
        coords1[index, 0] = x
        coords1[index, 1] = y
        u1[index] = P1 / (rho1 * (gamma - 1.))
        vel1[index, 0] = v1

# Particles in the outskirts
for i in range(L2):
    for j in range(L2):
        index = i * L2 + j
        x = i / float(L2) + 1. / (2. * L2)
        y = j / float(L2) + 1. / (2. * L2)
        coords2[index, 0] = x
        coords2[index, 1] = y
        u2[index] = P2 / (rho2 * (gamma - 1.))
        vel2[index, 0] = v2

# Now concatenate arrays
where1 = np.abs(coords1[:, 1] - 0.5) < 0.25
where2 = np.abs(coords2[:, 1] - 0.5) > 0.25

coords = np.append(coords1[where1, :], coords2[where2, :], axis=0)
vel = np.append(vel1[where1, :], vel2[where2, :], axis=0)
h = np.append(h1[where1], h2[where2], axis=0)
m = np.append(m1[where1], m2[where2], axis=0)
u = np.append(u1[where1], u2[where2], axis=0)
numPart = np.size(h)
m[:] = (0.5 * rho1 + 0.5 * rho2) / float(numPart)

# Velocity perturbation
vel[:, 1] = omega0 * np.sin(4 * np.pi * coords[:, 0]) * (
        np.exp(-(coords[:, 1] - 0.25) ** 2 / (2 * sigma ** 2)) + np.exp(-(coords[:, 1] - 0.75) ** 2 / (2 * sigma ** 2)))

# File
fileOutput = h5py.File(os.path.join(args.outdir, fileOutputName), 'w')
num_gas_particles = numPart * args.tile ** 3 * args.nparticles
print((
    f"Total number of gas particles (3D): {num_gas_particles:d} "
    f"(approx. 10^{np.log10(num_gas_particles):.1f}) "
    f"(approx. 2^{np.log2(num_gas_particles):.0f})"
))

# Header
grp = fileOutput.create_group("/Header")
grp.attrs["BoxSize"] = [1. * args.tile] * 3
grp.attrs["NumPart_Total"] = [num_gas_particles, 0, 0, 0, 0, 0]
grp.attrs["NumPart_Total_HighWord"] = [0, 0, 0, 0, 0, 0]
grp.attrs["NumPart_ThisFile"] = [num_gas_particles, 0, 0, 0, 0, 0]
grp.attrs["Time"] = 0.0
grp.attrs["NumFileOutputsPerSnapshot"] = 1
grp.attrs["MassTable"] = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
grp.attrs["Flag_Entropy_ICs"] = [0, 0, 0, 0, 0, 0]
grp.attrs["Dimension"] = 3

# Units
grp = fileOutput.create_group("/Units")
grp.attrs["Unit length in cgs (U_L)"] = 1.
grp.attrs["Unit mass in cgs (U_M)"] = 1.
grp.attrs["Unit time in cgs (U_t)"] = 1.
grp.attrs["Unit current in cgs (U_I)"] = 1.
grp.attrs["Unit temperature in cgs (U_T)"] = 1.

# Particle group
grp = fileOutput.create_group("/PartType0")
dump_memory_usage()
ds = grp.create_dataset('Coordinates', (num_gas_particles, 3), 'd')
coords = np.tile(coords, (args.tile ** 2, 1))
for i in trange(args.tile, desc=f"[x-stack]{ds.name.replace('/', ' ')}", disable=args.silent_progressbar):
    coords[numPart * args.tile * i:numPart * (i + 1) * args.tile, 0] += i
    for j in trange(args.tile, desc=f"[y-stack]{ds.name.replace('/', ' ')}", leave=None,
                    disable=args.silent_progressbar):
        coords[numPart * (i * args.tile + j):numPart * (i * args.tile + j + 1), 1] += j

# Stack layers
dump_memory_usage()
for k in trange(args.nparticles * args.tile, desc=f"[z-stack]{ds.name.replace('/', ' ')}",
                disable=args.silent_progressbar):
    buffer = coords.copy()
    buffer[:, 2] += k / args.nparticles
    ds[numPart * args.tile ** 2 * k:numPart * args.tile ** 2 * (k + 1)] = buffer
del coords

dump_memory_usage()
ds = grp.create_dataset('Velocities', (num_gas_particles, 3), 'f')
vel = np.tile(vel, (args.tile ** 2, 1)).reshape((-1, 3))
for k in trange(args.nparticles * args.tile, desc=f"[z-stack]{ds.name.replace('/', ' ')}",
                disable=args.silent_progressbar):
    ds[numPart * args.tile ** 2 * k:numPart * args.tile ** 2 * (k + 1)] = vel
del vel

dump_memory_usage()
ds = grp.create_dataset('Masses', (num_gas_particles, 1), 'f')
m = np.tile(m, (args.tile ** 2, 1)).reshape((-1, 1))
for k in trange(args.nparticles * args.tile, desc=f"[z-stack]{ds.name.replace('/', ' ')}",
                disable=args.silent_progressbar):
    ds[numPart * args.tile ** 2 * k:numPart * args.tile ** 2 * (k + 1)] = m
del m

dump_memory_usage()
ds = grp.create_dataset('SmoothingLength', (num_gas_particles, 1), 'f')
h = np.tile(h, (args.tile ** 2, 1)).reshape((-1, 1))
for k in trange(args.nparticles * args.tile, desc=f"[z-stack]{ds.name.replace('/', ' ')}",
                disable=args.silent_progressbar):
    ds[numPart * args.tile ** 2 * k:numPart * args.tile ** 2 * (k + 1)] = h
del h

dump_memory_usage()
ds = grp.create_dataset('InternalEnergy', (num_gas_particles, 1), 'f')
u = np.tile(u, (args.tile ** 2, 1)).reshape((-1, 1))
for k in trange(args.nparticles * args.tile, desc=f"[z-stack]{ds.name.replace('/', ' ')}",
                disable=args.silent_progressbar):
    ds[numPart * args.tile ** 2 * k:numPart * args.tile ** 2 * (k + 1)] = u
buffer_len = u.shape[0]
del u

dump_memory_usage()
ds = grp.create_dataset('ParticleIDs', (num_gas_particles, 1), dtype=np.uint64)
ids = np.linspace(1, buffer_len, buffer_len, dtype=np.uint64).reshape((-1, 1))
for k in trange(args.nparticles * args.tile, desc=f"[z-stack]{ds.name.replace('/', ' ')}",
                disable=args.silent_progressbar):
    buffer = ids.copy()
    buffer[:] += k * buffer_len
    ds[numPart * args.tile ** 2 * k:numPart * args.tile ** 2 * (k + 1)] = buffer.reshape((-1, 1))
del ids

fileOutput.close()
