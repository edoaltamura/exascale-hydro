import h5py
from numpy import *
import numpy as np
import os
import argparse

# Generates a swift IC file for the Kelvin-Helmholtz vortex in a periodic box
parser = argparse.ArgumentParser()
parser.add_argument('--nparticles', type=str)
parser.add_argument('--tileh', type=str)
parser.add_argument('--tilev', type=str)
parser.add_argument('--outdir', type=str)
args = parser.parse_args()
TILE_H = int(args.tileh) if vars(args)['tileh'] else 1
TILE_V = int(args.tilev) if vars(args)['tilev'] else 1
nparticles = int(args.nparticles) if vars(args)['nparticles'] else 256
outdir = args.outdir if vars(args)['outdir'] else '.'

# Parameters
L2 = nparticles  # Particles along one edge in the low-density region
gamma = 5. / 3.  # Gas adiabatic index
P1 = 2.5  # Central region pressure
P2 = 2.5  # Outskirts pressure
v1 = 0.5  # Central region velocity
v2 = -0.5  # Outskirts vlocity
rho1 = 2  # Central density
rho2 = 1  # Outskirts density
omega0 = 0.1
sigma = 0.05 / sqrt(2)
fileOutputName = "kelvinHelmholtz.hdf5"
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
ids = linspace(1, numPart * TILE_V * TILE_H, numPart * TILE_V * TILE_H)
m[:] = (0.5 * rho1 + 0.5 * rho2) / float(numPart)

# Velocity perturbation
vel[:, 1] = omega0 * sin(4 * pi * coords[:, 0]) * (
            exp(-(coords[:, 1] - 0.25) ** 2 / (2 * sigma ** 2)) + exp(-(coords[:, 1] - 0.75) ** 2 / (2 * sigma ** 2)))

# File
fileOutput = h5py.File(os.path.join(outdir, fileOutputName), 'w')

# Header
grp = fileOutput.create_group("/Header")
grp.attrs["BoxSize"] = [1. * TILE_H, 1. * TILE_V, 0.1]
grp.attrs["NumPart_Total"] = [numPart * TILE_V * TILE_H, 0, 0, 0, 0, 0]
grp.attrs["NumPart_Total_HighWord"] = [0, 0, 0, 0, 0, 0]
grp.attrs["NumPart_ThisFile"] = [numPart * TILE_V * TILE_H, 0, 0, 0, 0, 0]
grp.attrs["Time"] = 0.0
grp.attrs["NumFileOutputsPerSnapshot"] = 1
grp.attrs["MassTable"] = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
grp.attrs["Flag_Entropy_ICs"] = [0, 0, 0, 0, 0, 0]
grp.attrs["Dimension"] = 2

# Units
grp = fileOutput.create_group("/Units")
grp.attrs["Unit length in cgs (U_L)"] = 1.
grp.attrs["Unit mass in cgs (U_M)"] = 1.
grp.attrs["Unit time in cgs (U_t)"] = 1.
grp.attrs["Unit current in cgs (U_I)"] = 1.
grp.attrs["Unit temperature in cgs (U_T)"] = 1.

# Particle group
grp = fileOutput.create_group("/PartType0")
ds = grp.create_dataset('Coordinates', (numPart * TILE_V * TILE_H, 3), 'd')
coords = np.tile(coords, (TILE_V * TILE_H, 1))

for i in range(TILE_H):
    coords[numPart * i * TILE_V:numPart * (i + 1) * TILE_V, 0] += i
    for j in range(TILE_V):
        coords[numPart * (i * TILE_V + j):numPart * (i * TILE_V + j + 1), 1] += j

ds[()] = coords
ds = grp.create_dataset('Velocities', (numPart * TILE_V * TILE_H, 3), 'f')
vel = np.tile(vel, (TILE_V * TILE_H, 1))
ds[()] = vel
ds = grp.create_dataset('Masses', (numPart * TILE_V * TILE_H, 1), 'f')
m = np.tile(m, (TILE_V * TILE_H, 1))
ds[()] = m.reshape((numPart * TILE_V * TILE_H, 1))
ds = grp.create_dataset('SmoothingLength', (numPart * TILE_V * TILE_H, 1), 'f')
h = np.tile(h, (TILE_V * TILE_H, 1))
ds[()] = h.reshape((numPart * TILE_V * TILE_H, 1))
ds = grp.create_dataset('InternalEnergy', (numPart * TILE_V * TILE_H, 1), 'f')
u = np.tile(u, (TILE_V * TILE_H, 1))
ds[()] = u.reshape((numPart * TILE_V * TILE_H, 1))
ds = grp.create_dataset('ParticleIDs', (numPart * TILE_V * TILE_H, 1), 'L')
ds[()] = ids.reshape((numPart * TILE_V * TILE_H, 1))

fileOutput.close()
