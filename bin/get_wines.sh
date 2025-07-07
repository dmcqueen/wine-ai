#!/bin/bash

if [[ $2 = "default" ]] || [[ $2 = "default_2" ]]; then

	for word in $1; do
		Q=$Q"description contains \\\"$word\\\" or ";
	done 

	COND=${Q%???}

	DATA=$(cat <<-_QY
	{
		"yql" : "select id,winery,variety,description from wine where $COND limit 10 offset 0;", 
		"ranking": "$2" 
	}
	_QY)

else

	DATA='{"text" : "'$1'"}'
	TENSOR=$(curl -H "Content-Type: application/json" --data "$DATA"  http://localhost:8088/ | jq '."paraphrase-MiniLM-L6-v2"' | xargs)

	DATA=$(cat <<-_QY
	{
		"yql" : "select id,winery,variety,description from wine where ([{\"targetHits\": 1000}]nearestNeighbor(description_vector, query_vector)) limit 10 offset 0;", 
		"input.query(query_vector)" : "$TENSOR", 
		"ranking": "vector" 
	}
	_QY)

fi

curl -H "Content-Type: application/json" \
    --data "$DATA" \
    http://localhost:8080/search/ | jq -r '(.root.children[].fields | [.winery, .variety, .description])'


    
