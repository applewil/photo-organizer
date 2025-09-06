#!/usr/bin/env sh

set -euxo pipefail

rm -rf data/input
mkdir -p data/input
cd data/input

for path in ~/Downloads/photo-corpus/*; do
  (( index = ${index:-0} + 1 ))
  mkdir -p $index
  cd $index
  unzip "$path"
  cd ..
done
