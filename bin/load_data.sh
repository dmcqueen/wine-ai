#!/bin/bash

while true; do
    status=$(curl -s --head http://localhost:8080/ApplicationStatus | head -n 1 | grep "200 OK")
    if [ -n "$status" ]; then
        break
    fi
    echo "Waiting for ApplicationStatus to return 200..."
    sleep 2
done

docker run -it --rm --network vespa-net -v "$(pwd)":/opt/java -w /opt/java openjdk:23-jdk load/load.sh
