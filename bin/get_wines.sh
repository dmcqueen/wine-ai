export QUERY=$1
export DATA='{"text" : "'$QUERY'"}'
echo $DATA

export TENSOR=$(curl -H "Content-Type: application/json" --data "$DATA"  http://localhost:8088/ | jq '."paraphrase-MiniLM-L6-v2"' | xargs)

curl -H "Content-Type: application/json" \
    --data '{"yql" : "select id,winery,variety,description from wine where ([{\"targetHits\": 1000}]nearestNeighbor(desc_vector, description_vector)) limit 10 offset 0;", "ranking.features.query(description_vector)" : '"$TENSOR"', "ranking": "vector" }' \
    http://localhost:8080/search/ | jq '.root.children[].fields | .winery, .variety, .description'
