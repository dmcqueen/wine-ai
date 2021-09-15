<!-- Copyright McQueen Media. Licensed under the terms of the Apache 2.0 license. See LICENSE in the project root. -->

# Searching for Wine with Appoximate Nearest Neighbor and Paragraph Vector Embeddings 

Sementic search over 150,000+ wine reviews.  Using the Vespa implementation of Approximate Nearest Neighbor (ANN) and
the Paraphrase pretrained model (paraphrase-MiniLM-L6-v2).  The csv data from Wine Enthusiast is run through the paragraph 
embedding model to get a tensor that's stored in the database.  Queries are then turned into tensors and used to produce close 
match results on their meaning.

## Prerequisites

### Shell Tools
docker, jq, curl, xargs

### Dataset
https://www.kaggle.com/zynicide/wine-reviews

### Model 
https://www.sbert.net/docs/pretrained_models.html#question-answer-retrieval-msmarco

## Steps

1. Deploy Vespa and Model Servers
	- `bin/deploy_servers.sh`

2. Check for 200 Return from Vespa Server
	- `watch curl -v -s --head http://localhost:19071/ApplicationStatus`

3. Build and Deploy Wine AI Application to Vespa
	- `bin/build_vespa_app.sh` 

4. Check for 200 Return from Deployed Application
	- `watch curl -v -s --head http://localhost:8080/ApplicationStatus`

5. Transform the Data
	- `bin/transform_data.sh`

6. Load Data
	- `bin/load_data.sh`

7. Query the Data 
	- `bin/get_wines.sh "goes with asian food"`


