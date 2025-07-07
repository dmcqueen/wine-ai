# Wine Pairings Search with Vespa

This repository demonstrates how to build a small semantic search engine over the Wine Enthusiast review dataset. Documents are indexed in [Vespa](https://vespa.ai/) with dense vector representations generated from [SentenceTransformers](https://www.sbert.net/). Queries are embedded at runtime using a lightweight FastAPI service so that similar wines can be retrieved using Approximate Nearest Neighbor (ANN) search.

The project is split into several components that can each be run in Docker containers. The provided shell scripts orchestrate the workflow of building the Vespa application, transforming the dataset and querying the service.

## Repository layout

```
bin/              Shell scripts for data processing and deployment
data/             Wine Enthusiast CSV files
src/main/         Vespa application package (schema, services and query profiles)
tensor_server/    FastAPI server that exposes the SentenceTransformer model
transform/        Python utilities to convert the CSV files to Vespa JSON feed format
pom.xml           Maven configuration used to package the Vespa application
```

### Vespa application
The Vespa schema (`src/main/application/schemas/wine.sd`) defines the fields stored for each wine review, including a `description_vector` tensor of size 384 that stores the document embedding. Query profiles expose a query tensor feature and `services.xml` configures a single content node and search container.

### Wine schema and ranking
The schema lists textual fields like `province`, `variety` and `description` together with numeric attributes such as `points` and `price`. Each document also contains a 384‑dimensional `description_vector` tensor used for semantic search.

Ranking of results is controlled by four rank profiles in `wine.sd`:

```text
rank-profile default {
   first-phase {
      expression: bm25(description) 
   }
}

rank-profile default_2 {
   first-phase {
      expression: nativeRank(description) 
   }
}

rank-profile vector inherits default {
   inputs {
      query(query_vector) tensor<float>(x[384])
   }
   first-phase {
      expression: closeness(field, description_vector) + nativeRank(description)
   }
}
```

The `default` and `default_2` profiles rely purely on text ranking, using BM25 or
Vespa's `nativeRank` respectively. The `vector` profiles combine nearest‑neighbor
similarity on `description_vector` with the nativeRank text score.

### Default rank profile 
In the `bin/get_wines.sh` script is the http POST to Vespa.  The default query is.

```
"yql" : "select id,winery,variety,description from wine where ([{\"targetHits\": 1000}]nearestNeighbor(description_vector, query_vector)) limit 10 offset 0;", 
"input.query(query_vector)" : "$TENSOR", 
"ranking": "vector" 
```

### Model server
`tensor_server/server.py` starts a small FastAPI application which loads the pretrained `paraphrase-MiniLM-L6-v2` model from SentenceTransformers. It accepts JSON payloads of the form `{ "text": "..." }` and returns the embedding as a list of floats. The Dockerfile in the same directory installs the necessary dependencies so the service can be run as a container using Uvicorn.

### Data transformation
`transform/csv_to_vespa_json.py` reads the CSV files, removes obvious duplicates and writes Vespa feed files with the embedding precomputed for each review. `transform/transform.sh` executes this script in a Python Docker container and outputs one JSON file per input CSV.

## Running the example
The workflow below assumes Docker is installed and accessible by the current user.

1. **Pre-Download Docker Images**
   ```bash
   bin/predownload_docker.sh
   ```

2. **Deploy Vespa and the model server**
   ```bash
   bin/deploy_servers.sh
   ```
   Two containers will be started: one running Vespa and one running the FastAPI embedding service.

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
   Each CSV file is converted to a JSON document feed with an additional `description_vector` tensor.

7. **Load the documents into Vespa**
   ```bash
   bin/load_data.sh
   ```

8. **Query**
   ```bash
   bin/get_wines.sh "goes with asian food"
   ```
   The script sends the query text to the model server to obtain a `query_vector` and then performs an ANN search against the Vespa index.  By default the `vector` search rank profile is used but a parameter can be passed to choose a different ranking profile. 
   
   ```bash
   bin/get_wines.sh "goes with asian food" "default"
   ```

   Would choose the bm25 profile.

9. **Expected results of above query with `vector` ranking**
   

   ```
   [
      "Spann Vineyards",
      "Red Blend",
      "Tastes like orange, apricot and cherry sweet-and-sour sauce you get in a Chinese restaurant over pork or chicken. The flavors are of those fruits, with some white sugar and rice vinegar."
   ]
   [
      "Curtis",
      "Viognier",
      "A little one-dimensional, but clean and crisp in acids, with the exotic floral and spice flavors the variety is noted for. Try with Asian fare."
   ]
   [
      "Marcato",
      "Garganega",
      "Very clean, compact and fresh, here is a Soave to pair with take-away Chinese food. The wine is acidic and light with subtle aromas of peach, citrus and white flower."
   ]
   [
      "Stormhoek",
      "Sauvignon Blanc",
      "An appealing nose of tropical fruit, citrus and spice, followed by a clean, dry, spicy combination of citrus and fresh fruit, give this white a summer sipping appeal. A great partner to salads, grilled seafood, Thai cuisine."
   ]
   [
      "Joseph Swan Vineyards",
      "Gewürztraminer",
      "Tasting somewhere between dry and off dry on the sweetness spectrum, this has tropical fruit, white flower and spice flavors that make it a perfect accompaniment to modern Thai, Vietnamese, Chinese, Burmese and even Indian fare."
   ]
   [
      "Vermeil",
      "Sauvignon Blanc",
      "Dryish and crisp, this shows citrus, lemongrass, herb and honey flavors, with a sweet bitterness that will play well with a wide range of food, especially modern Asian fare."
   ]
   [
      "Lucas & Lewellen",
      "Merlot",
      "Awkward, with sweet-and-sour Chinese food flavors. Now it's cherries, then it's balsamic. Finishes sugary sweet."
   ]
   [
      "Cline",
      "Rosé",
      "A bit simple, but useful, with flavors of lightly sugared rosehip tea, cherries and Asian spices, offset with brisk acidity. Versatile with grilled veggies, chicken, Vietnamese food."
   ]
   [
      "Insomnia",
      "White Blend",
      "This has flavors of oranges, Meyer lemons and tropical fruits, and there's a good burst of acidity that lends balance. The finish tastes a bit sweet. Pair this selection with Vietnamese, Chinese, Thai, Indian or Ethiopian dishes."
   ]
   [
      "Flocchini",
      "Sauvignon Blanc",
      "Clean, tart and expressive, this has flavors of Asian pear, orange, lime, vanilla and gooseberry. Bright and zesty, this would make for a fine apéritif, and it would also pair well with Asian fare."
   ]
   ```