import swiftsimio as sw
from swiftsimio.visualisation.projection import project_gas
import argparse
from matplotlib.pyplot import imsave
from matplotlib.colors import LogNorm

parser = argparse.ArgumentParser()
parser.add_argument('-i', '--ic-file', type=str, required=True)
parser.add_argument('-t', '--top-cells-per-tile', type=int, default=3, required=False)
parser.add_argument('-o', '--outdir', type=str, default='.', required=False)
args = parser.parse_args()


mask = sw.mask(args.ic_file)
boxsize = mask.metadata.boxsize
load_region = [
    [0. * boxsize[0], 1. * boxsize[0]],
    [0. * boxsize[1], 1. * boxsize[1]],
    [0. * boxsize[2], 0.1 * boxsize[2]],
]

mask.constrain_spatial(load_region)
data = sw.load(args.ic_file, mask=mask)

mass_map = project_gas(
    data,
    resolution=1024,
    project="densities",
    parallel=True,
    backend="subsampled"
)

imsave("gas_slice_map.png", LogNorm()(mass_map), cmap="viridis")