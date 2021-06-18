import h5py
from numpy import *
import numpy as np
import matplotlib.pyplot as plt
import swiftsimio as sw
from mpl_toolkits.mplot3d import Axes3D



def set_particles(nparticles, tileh, tilev):
    TILE_H = int(tileh)
    TILE_V = int(tilev)
    nparticles = int(nparticles)

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

    coords = np.tile(coords, (TILE_V * TILE_H, 1))
    for i in range(TILE_H):
        coords[numPart * i * TILE_V:numPart * (i + 1) * TILE_V, 0] += i
        for j in range(TILE_V):
            coords[numPart * (i * TILE_V + j):numPart * (i * TILE_V + j + 1), 1] += j

    vel = np.tile(vel, (TILE_V * TILE_H, 1))

    m = np.tile(m, (TILE_V * TILE_H, 1))

    h = np.tile(h, (TILE_V * TILE_H, 1))

    u = np.tile(u, (TILE_V * TILE_H, 1))

    return coords, vel, m, h, u

def cuboid_data(o, size=(1, 1, 1)):
    # code taken from
    # https://stackoverflow.com/a/35978146/4124317
    # suppose axis direction: x: to left; y: to inside; z: to upper
    # get the length, width, and height
    l, w, h = size
    x = [[o[0], o[0] + l, o[0] + l, o[0], o[0]],
         [o[0], o[0] + l, o[0] + l, o[0], o[0]],
         [o[0], o[0] + l, o[0] + l, o[0], o[0]],
         [o[0], o[0] + l, o[0] + l, o[0], o[0]]]
    y = [[o[1], o[1], o[1] + w, o[1] + w, o[1]],
         [o[1], o[1], o[1] + w, o[1] + w, o[1]],
         [o[1], o[1], o[1], o[1], o[1]],
         [o[1] + w, o[1] + w, o[1] + w, o[1] + w, o[1] + w]]
    z = [[o[2], o[2], o[2], o[2], o[2]],
         [o[2] + h, o[2] + h, o[2] + h, o[2] + h, o[2] + h],
         [o[2], o[2], o[2] + h, o[2] + h, o[2]],
         [o[2], o[2], o[2] + h, o[2] + h, o[2]]]
    return np.array(x), np.array(y), np.array(z)


def plotCubeAt(pos=(0, 0, 0), size=(1, 1, 1), ax=None, **kwargs):
    # Plotting a cube element at position pos
    if ax != None:
        X, Y, Z = cuboid_data(pos, size)
        ax.plot_surface(X, Y, Z, rstride=1, cstride=1, **kwargs)


from matplotlib.patches import Rectangle

plt.style.use('../mnras.mplstyle')

fig, ax = plt.subplots()
coords, _, m, h, _ = set_particles(32, 2, 2)
x, y, z = coords.T
del coords

ax.scatter(x, y, s=0.5)
ax.add_patch(Rectangle((0, 0), 1, 1, fill=None, alpha=1, color='r'))

ax.annotate("Tile-unit",
            xy=(1, 1), xycoords='data',
            xytext=(-4, -4), textcoords='offset points',
            horizontalalignment='right', verticalalignment='top',
            bbox=dict(boxstyle="square,pad=0.3", fc="white", ec="none", lw=0)
            )
ax.annotate(r"Tiling: $2\times2$",
            xy=(2, 2), xycoords='data',
            xytext=(0, 0), textcoords='offset points',
            horizontalalignment='right', verticalalignment='top',
            bbox=dict(boxstyle="square,pad=0.3", fc="white", ec="none", lw=0)
            )

ax.annotate(r"High-density ($\rho_1$)",
            xy=(1.5, 0.5), xycoords='data',
            xytext=(0, 0), textcoords='offset points',
            horizontalalignment='center', verticalalignment='center',
            bbox=dict(boxstyle="square,pad=0.3", fc="white", ec="none", lw=0, alpha=0.4)
            )

ax.annotate(r"Low-density ($\rho_2$)",
            xy=(1.5, 1), xycoords='data',
            xytext=(0, 0), textcoords='offset points',
            horizontalalignment='center', verticalalignment='center',
            bbox=dict(boxstyle="square,pad=0.3", fc="white", ec="none", lw=0, alpha=0.4)
            )

ax.annotate("", xy=(1.3, 0.65), xytext=(1.7, 0.65), arrowprops=dict(arrowstyle="<-"))
ax.annotate("", xy=(1.3, 0.85), xytext=(1.7, 0.85), arrowprops=dict(arrowstyle="->"))
from matplotlib.colors import LightSource

ax.set_xlabel('$x$ [arbitrary units]')
ax.set_ylabel('$y$ [arbitrary units]')
plt.savefig('hk_setup.pdf')
plt.show()
plt.close(fig)

fig = plt.figure()
ax = fig.gca(projection='3d')
ax.set_aspect('equal')
ax.view_init(elev=30, azim=135)
ax.dist = 11
positions = []
sizes = []
colors = []

for i in range(2):
    for j in range(2):
        for k in range(2):
            positions.append(tuple([i, j, k]))
            sizes.append(tuple([1, 1, 1]))
            if (i + j + k) % 2 == 0:
                colors.append("crimson")
            else:
                colors.append("limegreen")

for p, s, c in zip(positions, sizes, colors):
    plotCubeAt(pos=p, size=s, ax=ax, color=c, alpha=0.7)

ax.scatter(x[::2], y[::2], z[::2]+2.4, s=0.1, facecolor='w', alpha=0.7)

x = linspace(0, 2, 45)

for value in x:
    ax.scatter(x, 2.5, value, s=0.1, facecolor='w', alpha=0.9)

ls = LightSource(azdeg=155, altdeg=75)
# Shade data, creating an rgb array.
# rgb = ls.shade(z, plt.cm.RdYlBu)
ax.xaxis.pane.set_facecolor('grey')
ax.yaxis.pane.set_facecolor('grey')
ax.zaxis.pane.set_facecolor('grey')
ax.xaxis.pane.set_edgecolor('grey')
ax.yaxis.pane.set_edgecolor('grey')
ax.zaxis.pane.set_edgecolor('grey')
ax.set_xlabel('$x$')
ax.set_ylabel('$y$')
ax.set_zlabel('$z$')
ax.set_xlim(0, 2.5)
ax.set_ylim(0, 2.5)
ax.set_zlim(0, 2.5)
ax.grid(False)
plt.savefig('tiles.pdf')
plt.show()
plt.close(fig)

