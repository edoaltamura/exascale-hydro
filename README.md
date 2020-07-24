exascale-hydro
============
This repository contains scripts for generating and analysing [SWIFT](https://github.com/SWIFTSIM)
hydrodynamic simulations. Focus is on code performance and benchmarks in running hydrodynamics problems
on an increasingly large number of threads and nodes.

The tests mostly involve weak and strong-scaling. An example of scaling test is the one based on the Kelvin-Helmholtz (KH) instability. The following Twitter post includes the output image from a large KH simulation.

```{r echo=FALSE}
blogdown::shortcode('tweet', '1276814541486243843')
```

Computing architecture
------------
Hydro simulations are run with single-node (OpenMP) and multi-node (MPI)  configurations, preferably on the `cosma6` and `cosma7` computer clusters. `Cosma7` is equipped with 
452 compute nodes, each with 512GB RAM and 28 cores (2x Intel Xeon Gold 5120 CPU @ 2.20GHz). Visit the [COSMA-DiRAC pages](https://www.dur.ac.uk/icc/cosma/)
for more info.
