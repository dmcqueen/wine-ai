#!/bin/bash

docker run -it --rm -v "$(pwd)":/opt/python -w /opt/python python:3.12.4 transform/transform.sh
