#!/bin/bash

pip install -U sentence-transformers
for file in $(ls data/*.csv); do
    python transform/convert.py $file
done;
