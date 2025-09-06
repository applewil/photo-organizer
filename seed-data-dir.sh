#!/usr/bin/env sh

rm -rf data
index=0
for path in ~/Downloads/photo-corpus/*; do
  mkdir -p data/input/$index
  cd data/input/$index
  unzip "$path"
  cd ..
  ((index++))
done
