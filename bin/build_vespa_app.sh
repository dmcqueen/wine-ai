#!/bin/bash

docker run -it --rm -v "$(pwd)/vespa_app":/opt/maven -w /opt/maven maven:3.9.8-eclipse-temurin-17 mvn clean package