#!/bin/bash

curl --header Content-Type:application/zip --data-binary @vespa_app/target/application.zip \
  localhost:19071/application/v2/tenant/default/prepareandactivate | jq '.'
