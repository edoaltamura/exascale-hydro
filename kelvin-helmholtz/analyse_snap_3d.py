from swiftsimio import load
from swiftsimio.visualisation.slice import slice_gas
import argparse
from matplotlib.pyplot import imsave
from matplotlib.colors import LogNorm

parser = argparse.ArgumentParser()
parser.add_argument('-i', '--ic-file', type=str, required=True)
parser.add_argument('-t', '--top-cells-per-tile', type=int, default=3, required=False)
parser.add_argument('-o', '--outdir', type=str, default='.', required=False)
args = parser.parse_args()

data = load(args.ic_file)

mass_map = slice_gas(
    data,
    slice=0.5,
    resolution=1024,
    project="masses",
    parallel=True
)

imsave("gas_slice_map.png", LogNorm()(mass_map), cmap="viridis")