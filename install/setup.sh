#!/bin/bash

set -x
set -e

BASE=$(pwd)
rm -rf ogdf/build-* pc-tree/build-* c-planarity/build-* || echo "Nothing to clean!"

ANY_OPTS="-DCMAKE_CXX_COMPILER_LAUNCHER=ccache"

RELEASE_OPTS="
  -DCMAKE_BUILD_TYPE=Release
  -DCMAKE_INTERPROCEDURAL_OPTIMIZATION=TRUE
  -DBUILD_SHARED_LIBS=OFF
  -DLIKWID_PERFMON=OFF"
DEBUG_OPTS="
  -DCMAKE_BUILD_TYPE=Debug
  -DCMAKE_INTERPROCEDURAL_OPTIMIZATION=FALSE
  -DBUILD_SHARED_LIBS=ON"

OGDF_OPTS="-DOGDF_MEMORY_MANAGER=POOL_NTS"
PCTREE_OPTS=""
CPLAN_OPTS=""

git clone --recurse-submodules https://github.com/N-Coder/ogdf.git ogdf || echo "Repo exists"
pushd ogdf
  git pull
  git submodule update --init --recursive
  git checkout syncplan
  mkdir -p build-debug build-release
  pushd build-debug
    cmake .. $ANY_OPTS $DEBUG_OPTS $OGDF_OPTS \
      -DOGDF_USE_ASSERT_EXCEPTIONS=ON \
      -DOGDF_USE_ASSERT_EXCEPTIONS_WITH_STACK_TRACE=ON_LIBUNWIND
  cd ../build-release
    cmake .. $ANY_OPTS $RELEASE_OPTS $OGDF_OPTS \
      -DOGDF_USE_ASSERT_EXCEPTIONS=OFF
  popd
popd

git clone --recurse-submodules https://github.com/N-Coder/pc-tree.git || echo "Repo exists"
pushd pc-tree
  git pull
  git submodule update --init --recursive
  git checkout syncplan
  mkdir -p build-debug build-release
  pushd build-debug
    cmake .. $ANY_OPTS $DEBUG_OPTS   $PCTREE_OPTS -DOGDF_DIR="$BASE/ogdf/build-debug"
  cd ../build-release
    cmake .. $ANY_OPTS $RELEASE_OPTS $PCTREE_OPTS -DOGDF_DIR="$BASE/ogdf/build-release"
  popd
popd

git clone --recurse-submodules https://github.com/N-Coder/syncplan.git || echo "Repo exists"
pushd syncplan
  git pull
  git submodule update --init --recursive
  mkdir -p build-debug build-release
  pushd build-debug
    cmake .. $ANY_OPTS $DEBUG_OPTS   $CPLAN_OPTS -DOGDF_DIR="$BASE/ogdf/build-debug"    -DPCTree_DIR="$BASE/pc-tree/build-debug"
  cd ../build-release
    cmake .. $ANY_OPTS $RELEASE_OPTS $CPLAN_OPTS -DOGDF_DIR="$BASE/ogdf/build-release"  -DPCTree_DIR="$BASE/pc-tree/build-release"
  popd

  pip install --no-cache-dir -r install/requirements.txt
popd


THREADS=$(nproc --all || echo "8")
for type in debug release; do
  for proj in ogdf pc-tree syncplan; do
    pushd "$proj/build-$type"
    cmake ..
    make -j $THREADS
    popd
  done
done
