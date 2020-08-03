#!/bin/bash -l

# Bash script that configures and compiles SWIFT.
# It then places the new compiled binaries in the current directory.

old_directory=$(pwd)

if [ ! -d ../swiftsim-master ]; then
  echo SWIFT source code not found - cloning from GitLab...
  cd ..
  git clone https://gitlab.cosma.dur.ac.uk/swift/swiftsim.git
  cd $old_directory
fi

cd ../swiftsim-master
sh ./autogen.sh
sh ./configure \
  --with-hydro-dimension=2 \
  --with-hydro=sphenix \
  --with-kernel=quintic-spline \
  --disable-hand-vec

#sh ./configure \
#  --with-hydro-dimension=2 \
#  --with-hydro=minimal

make -j

# Refresh old compilations of SWIFT and replace with new ones
cd $old_directory
rm swift*
cp ~/swift_test/swiftsim-master/examples/swift_mpi .
cp ~/swift_test/swiftsim-master/examples/swift .