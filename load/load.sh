#!/bin/bash

for file in $(ls data/*.json); do  
  java -jar load/vespa-http-client-jar-with-dependencies.jar \
    --verbose --file $file --endpoint http://vespa:8080; 
done