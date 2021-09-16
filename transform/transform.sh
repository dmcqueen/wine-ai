#!/bin/bash

pip install -U sentence-transformers

FILES=$(ls data/*.csv|xargs)
python transform/convert.py "$FILES"
