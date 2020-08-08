#!/bin/bash -l

# Bash script that configures and compiles SWIFT.
# It then places the new compiled binaries in the current directory.

source modules.sh

old_directory=$(pwd)

if [ ! -d ~/swiftsim ]; then
  echo SWIFT source code not found - cloning from GitLab...
  cd ..
  git clone https://gitlab.cosma.dur.ac.uk/swift/swiftsim.git
  cd $old_directory
fi

cd ~/swiftsim
sh ./autogen.sh
sh ./configure \
  --with-hydro-dimension=2 \
  --with-hydro=sphenix \
  --with-kernel=quintic-spline \
  --disable-hand-vec

# Configure SWIFT with minimal hydrodynamics scheme
#sh ./configure \
#  --with-hydro-dimension=2 \
#  --with-hydro=minimal

# Compile into executables
make -j

# Refresh old compilations of SWIFT and replace with new ones
cd $old_directory
rm swift*
cp ~/swift_test/swiftsim-master/examples/swift_mpi .
cp ~/swift_test/swiftsim-master/examples/swift .