#!/bin/bash

if ! docker network ls --format '{{.Name}}' | grep -wq vespa-net; then
    docker network create vespa-net
fi

docker run --detach --name vespa --network vespa-net --publish 8080:8080 --publish 19071:19071 vespaengine/vespa

docker build tensor_server -t modelserver
docker run --detach --name models --network vespa-net --publish 8088:8088 modelserver

docker build ui -t streamlitserver
docker run --detach --name streamlit --network vespa-net --publish 8501:8501 -v $(pwd)/ui/secrets.toml:/app/.streamlit/secrets.toml streamlitserver
