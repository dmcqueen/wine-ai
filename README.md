# Wine Search with Vespa

This repository demonstrates how to build a small semantic search engine over the Wine Enthusiast review dataset. Documents are indexed in [Vespa](https://vespa.ai/) with dense vector representations generated from [SentenceTransformers](https://www.sbert.net/). Queries are embedded at runtime using a lightweight Flask service so that similar wines can be retrieved using Approximate Nearest Neighbor (ANN) search.

The project is split into several components that can each be run in Docker containers. The provided shell scripts orchestrate the workflow of building the Vespa application, transforming the dataset and querying the service.

## Repository layout

```
bin/              Shell scripts for data processing and deployment
codex/            Environment setup helpers for Codex
src/main/         Vespa application package (schema, services and query profiles)
data/             Wine Enthusiast CSV files
transform/        Python utilities to convert the CSV files to Vespa JSON feed format
tensor_server/    Flask server that exposes the SentenceTransformer model
tests/            Simple integration test that follows the README instructions
pom.xml           Maven configuration used to package the Vespa application
```

### Vespa application
The Vespa schema (`src/main/application/schemas/wine.sd`) defines the fields stored for each wine review, including a `desc_vector` tensor of size 384 that stores the document embedding. Query profiles expose a query tensor feature and `services.xml` configures a single content node and search container.

### Model server
`tensor_server/server.py` starts a small Flask app which loads the pretrained `paraphrase-MiniLM-L6-v2` model from SentenceTransformers. It accepts JSON payloads of the form `{ "text": "..." }` and returns the embedding as a list of floats. The Dockerfile in the same directory installs the necessary dependencies so the service can be run as a container.

### Data transformation
`transform/convert.py` reads the CSV files, removes obvious duplicates and writes Vespa feed files with the embedding precomputed for each review. `transform/transform.sh` executes this script in a Python Docker container and outputs one JSON file per input CSV.

## Running the example
The workflow below assumes Docker is installed and accessible by the current user.

1. **Pre Download Docker Images**
   ```bash
   bin/init.sh
   ```

2. **Deploy Vespa and the model server**
   ```bash
   bin/deploy_servers.sh
   ```
   Two containers will be started: one running Vespa and one running the Flask embedding service.

3. **Verify Vespa is up**
   ```bash
   watch curl -s --head http://localhost:19071/ApplicationStatus
   ```

4. **Build and deploy the Vespa application**
   ```bash
   bin/build_vespa_app.sh
   ```

5. **Wait for the application to report ApplicationStatus**
   ```bash
   watch curl -s --head http://localhost:8080/ApplicationStatus
   ```

6. **Transform the dataset and compute document embeddings**
   ```bash
   bin/transform_data.sh
   ```
   Each CSV file is converted to a JSON document feed with an additional `desc_vector` tensor.

7. **Load the documents into Vespa**
   ```bash
   bin/load_data.sh
   ```

8. **Query**
   ```bash
   bin/get_wines.sh "goes with asian food"
   ```
   The script sends the query text to the model server to obtain a vector and then performs an ANN search against the Vespa index.

The `tests/test_readme.sh` script runs these steps automatically and can be used as a simple integration test when Docker is available.

