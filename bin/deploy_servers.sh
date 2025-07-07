#!/bin/bash

docker build tensor_server -t modelserver
docker run --detach --name models --hostname models-container --publish 8088:8088 modelserver

docker run --detach --name vespa --hostname vespa-container --publish 8080:8080 --publish 19071:19071 vespaengine/vespa
