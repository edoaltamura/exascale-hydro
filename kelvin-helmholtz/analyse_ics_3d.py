import h5py
import numpy as np
import os
import argparse
from matplotlib import pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

parser = argparse.ArgumentParser()
parser.add_argument('-i', '--ic-file', type=str, required=True)
parser.add_argument('-t', '--top-cells-per-tile', type=int, default=3, required=False)
parser.add_argument('-o', '--outdir', type=str, default='.', required=False)
args = parser.parse_args()


def logger_info(category: str, length: int = 12) -> str:
    num_blanks = length - 2 - len(category)
    if num_blanks < 1:
        num_blanks = 0
    return f"[{category}]" + ' ' * num_blanks


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


with h5py.File(args.ic_file, 'r') as ic_data:
    coords = ic_data['/PartType0/Coordinates'][:]
    boxsize = ic_data['/Header'].attrs["BoxSize"]
    num_particles = ic_data['/Header'].attrs["NumPart_Total"][0]

print(f"{logger_info('ICs file')} Analysing 3D initial conditions file: {args.ic_file}")
print(f"{logger_info('ICs file')} Box size: {boxsize}")
print(f"{logger_info('ICs file')} Total number of gas particles: {num_particles}")

# Retrieve the number of stacked layers from z-coordinates
num_2dlayers = len(np.unique(coords[:, 2]))
print(f"{logger_info('Stacking')} Number of 2D layers stacked along z for one tile: {int(num_2dlayers / boxsize[0]):d}")
print(f"{logger_info('Stacking')} Number of 2D layers stacked along z in total: {num_2dlayers:d}")

print(f"{logger_info('Tiling')} Number of tiles in each dimension (x, y, z): {[int(i) for i in boxsize]}")
print(f"{logger_info('Domain decomposition')} Top-level-cells per tile: {args.top_cells_per_tile}^3")
print(f"{logger_info('Domain decomposition')} Top-level-cells total: {args.top_cells_per_tile * int(boxsize[0])}^3")
print(
    f"{logger_info('Domain decomposition')} Average particles per top-level-cell: {num_particles / (args.top_cells_per_tile * boxsize[0]) ** 3:.2f}")

stride = 1
if num_particles > 32 ** 3:
    stride = int(np.log10(num_particles) ** 2 - 4 * np.log10(num_particles))

fig = plt.figure()
ax = Axes3D(fig)
print(f"{logger_info('Plotting')} Generating dot-plot of particle positions... (Sampling one every {stride} particles)")
# ax.scatter(coords[::stride, 0], coords[::stride, 1], coords[::stride, 2], marker=',', lw=0, s=1)
# ax.set_xlabel('x')
# ax.set_ylabel('y')
# ax.set_zlabel('z')
# # ax.set_axis_off()
# ax.set_aspect('equal')
# plt.tight_layout()
# plt.savefig(os.path.join(args.outdir, 'coordinates.png'))
# plt.close(fig)

fig = plt.figure()
ax = fig.gca(projection='3d')
ax.set_aspect('equal')
print(f"{logger_info('Plotting')} Generating tiling block-diagram...")
positions = []
sizes = []
colors = []

for i in range(int(boxsize[0])):
    for j in range(int(boxsize[1])):
        for k in range(int(boxsize[2])):
            positions.append(tuple([i, j, k]))
            sizes.append(tuple([1, 1, 1]))
            if (i + j + k) % 2 == 0:
                colors.append("crimson")
            else:
                colors.append("limegreen")

for p, s, c in zip(positions, sizes, colors):
    plotCubeAt(pos=p, size=s, ax=ax, color=c)

ax.set_xlabel('x')
ax.set_ylabel('y')
ax.set_zlabel('z')
plt.tight_layout()
plt.savefig(os.path.join(args.outdir, 'tiles.png'))
plt.close(fig)

fig = plt.figure()
ax = fig.gca(projection='3d')
ax.set_aspect('equal')
print(f"{logger_info('Plotting')} Generating tiling top-level-cells diagram...")

for p, s, c in zip(positions, sizes, colors):
    plotCubeAt(pos=p, size=s, ax=ax, color=c, alpha=0.2)

top_cells_positions = []
top_cells_sizes = []
top_cells_colors = []

for i in range(int(boxsize[0]) * args.top_cells_per_tile):
    for j in range(int(boxsize[1]) * args.top_cells_per_tile):
        for k in range(int(boxsize[2]) * args.top_cells_per_tile):
            top_cells_positions.append(tuple([i / 3, j / 3, k / 3]))
            top_cells_sizes.append(tuple([1 / 3, 1 / 3, 1 / 3]))
            if (i + j + k) % 2 == 0:
                top_cells_colors.append("grey")
            else:
                top_cells_colors.append("white")

for p, s, c in zip(top_cells_positions, top_cells_sizes, top_cells_colors):
    plotCubeAt(pos=p, size=s, ax=ax, color=c, alpha=0.8)
ax.set_xlabel('x')
ax.set_ylabel('y')
ax.set_zlabel('z')
plt.tight_layout()
plt.savefig(os.path.join(args.outdir, 'topcells.png'))
plt.close(fig)
