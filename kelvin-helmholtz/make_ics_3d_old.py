import h5py
import numpy as np
from numpy import *
import os
import psutil
import argparse

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
sigma = 0.05 / sqrt(2)
fileOutputName = "kelvin_helmholtz_3d.hdf5"
# ---------------------------------------------------

# Start by generating grids of particles at the two densities
numPart2 = L2 * L2
L1 = int(sqrt(numPart2 / rho2 * rho1))
numPart1 = L1 * L1
coords1 = zeros((numPart1, 3))
coords2 = zeros((numPart2, 3))
h1 = ones(numPart1) * 1.2348 / L1
h2 = ones(numPart2) * 1.2348 / L2
m1 = zeros(numPart1)
m2 = zeros(numPart2)
u1 = zeros(numPart1)
u2 = zeros(numPart2)
vel1 = zeros((numPart1, 3))
vel2 = zeros((numPart2, 3))

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
where1 = abs(coords1[:, 1] - 0.5) < 0.25
where2 = abs(coords2[:, 1] - 0.5) > 0.25

coords = append(coords1[where1, :], coords2[where2, :], axis=0)
vel = append(vel1[where1, :], vel2[where2, :], axis=0)
h = append(h1[where1], h2[where2], axis=0)
m = append(m1[where1], m2[where2], axis=0)
u = append(u1[where1], u2[where2], axis=0)
numPart = size(h)
ids = linspace(
    1,
    numPart * args.tile ** 3 * args.nparticles,
    numPart * args.tile ** 3 * args.nparticles,
    dtype=np.int64
)
m[:] = (0.5 * rho1 + 0.5 * rho2) / float(numPart)

# Velocity perturbation
vel[:, 1] = omega0 * sin(4 * pi * coords[:, 0]) * (
        exp(-(coords[:, 1] - 0.25) ** 2 / (2 * sigma ** 2)) + exp(-(coords[:, 1] - 0.75) ** 2 / (2 * sigma ** 2)))

# File
fileOutput = h5py.File(os.path.join(args.outdir, fileOutputName), 'w')
num_gas_particles = numPart * args.tile ** 3 * args.nparticles
print(f"Total number of gas particles (3D): {num_gas_particles:d}")

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
for i in range(args.tile):
    coords[numPart * args.tile * i:numPart * (i + 1) * args.tile, 0] += i
    for j in range(args.tile):
        coords[numPart * (i * args.tile + j):numPart * (i * args.tile + j + 1), 1] += j

# Stack layers
dump_memory_usage()
coords = np.tile(coords, (args.nparticles * args.tile, 1))
for k in range(args.nparticles * args.tile):
    coords[numPart * args.tile ** 2 * k:numPart * args.tile ** 2 * (k + 1), 2] += k / args.nparticles
ds[()] = coords
dump_memory_usage()
ds = grp.create_dataset('Velocities', (num_gas_particles, 3), 'f')
vel = np.tile(vel, (args.tile ** 2, 1))
vel = np.tile(vel, (args.tile * args.nparticles, 1))
ds[()] = vel
dump_memory_usage()
ds = grp.create_dataset('Masses', (num_gas_particles, 1), 'f')
m = np.tile(m, (args.tile ** 2, 1))
m = np.tile(m, (args.tile * args.nparticles, 1))
ds[()] = m.reshape((num_gas_particles, 1))
dump_memory_usage()
ds = grp.create_dataset('SmoothingLength', (num_gas_particles, 1), 'f')
h = np.tile(h, (args.tile ** 2, 1))
h = np.tile(h, (args.tile * args.nparticles, 1))
ds[()] = h.reshape((num_gas_particles, 1))
dump_memory_usage()
ds = grp.create_dataset('InternalEnergy', (num_gas_particles, 1), 'f')
u = np.tile(u, (args.tile ** 2, 1))
u = np.tile(u, (args.tile * args.nparticles, 1))
ds[()] = u.reshape((num_gas_particles, 1))
dump_memory_usage()
ds = grp.create_dataset('ParticleIDs', (num_gas_particles, 1), 'L')
ds[()] = ids.reshape((num_gas_particles, 1))
fileOutput.close()
