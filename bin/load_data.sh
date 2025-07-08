#!/bin/bash

docker run -it --rm --network vespa-net -v "$(pwd)":/opt/java -w /opt/java openjdk:23-jdk load/load.sh
