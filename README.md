# Wine‑AI — Semantic Wine Recommendation & Vector Search with Vespa

**Wine‑AI** is an open‑source **semantic search / recommendation engine** that lets you discover the perfect wine pairing using **vector search** powered by [Vespa.ai](https://vespa.ai/) and dense embeddings from [SentenceTransformers](https://www.sbert.net/docs/sentence_transformer/pretrained_models.html) model [`paraphrase-multilingual-MiniLM-L12-v2`](https://www.sbert.net/docs/sentence_transformer/pretrained_models.html).
It indexes the 150K‑review [Wine Enthusiast dataset](https://www.kaggle.com/datasets/zynicide/wine-reviews) and serves instant results via a lightweight [FastAPI](https://fastapi.tiangolo.com/) micro‑service.

> Ask questions like **“budget‑friendly Napa Cabernet for steak”** or **“wines that go with spicy Thai food”** and get context‑aware matches ranked by both semantic similarity and BM25 relevance.

---

## Features

* **Hybrid ranking**: vector closeness + Vespa BM25 / nativeRank
* **Approximate Nearest Neighbor (ANN)** search for sub‑100 ms latency
* **End‑to‑end Docker workflow**: one script to spin up the Vespa cluster, ML model server, and ETL pipeline
* **Scales to million‑plus vectors** thanks to Vespa’s streaming HNSW indexes

---

## Architecture<a id="architecture"></a>

1. **Tensor Server** embeds user queries and document descriptions with SentenceTransformers.
2. **Vespa** app stores each wine review plus its `description_vector` (384‑d).
3. Hybrid rank profiles fuse **vector similarity** and **text relevance**.

---

## Quick Start<a id="quick-start"></a>

> **Prerequisite:** Docker Engine ≥ 20.10

***In a terminal from the project root run*** `./run.sh`

What it does

```bash
# Launch Vespa & model‑server containers
bin/deploy_servers.sh

# Verify Vespa is live
curl -s --head http://localhost:19071/ApplicationStatus

# Build Vespa application
bin/build_vespa_app.sh

# Deploy Vespa application
bin/deploy_vespa_app.sh

# Check application is up
curl -s --head http://localhost:8080/ApplicationStatus

# Transform CSV → Vespa JSON with embeddings
bin/transform_data.sh

# Feed documents into Vespa
bin/load_data.sh
```

Run a semantic query

```bash
bin/search_wines.sh "goes with poultry" vector
```

Switch to classic BM25 ranking:

```bash
bin/search_wines.sh "goes with poultry" default
```

Switch to Vespa NativeRank ranking:

```bash
bin/search_wines.sh "goes with poultry" default_2
```

---

## Repository Layout<a id="repository-layout"></a>

```
bin/              End‑to‑end scripts: deploy, transform, feed, search
data/             Raw Kaggle CSV files
load/             Load transformed data into Vespa app
tensor_server/    FastAPI + SentenceTransformers model service
transform/        CSV → Vespa JSON ETL utilities
vespa_app/        Vespa application package (schema, services, query‑profiles)
run.sh            To run the demo
```

---

## Vespa Schema & Ranking<a id="vespa-schema--ranking"></a>

Schema file: `vespa_app/src/main/application/schemas/wine.sd`

| Field type | Example fields                               |
| ---------- | -------------------------------------------- |
| Text       | province, variety, description               |
| Numeric    | points, price                                |
| Vector     | description\_vector (tensor<float>(x\[384])) |

**Rank Profiles**

| Profile    | Expression                                                              |
| ---------- | ----------------------------------------------------------------------- |
| default    | bm25(description)                                                       |
| default\_2 | nativeRank(description)                                                 |
| vector     | closeness(description\_vector, query\_vector) + nativeRank(description) |

---

## Data Pipeline<a id="data-pipeline"></a>

* `csv_to_vespa_json.py` — reads CSV, removes duplicates, embeds descriptions, writes feed files.
* `transform.sh` wraps the above in a Python Docker container.
* Feeds are loaded into Vespa via `load_data.sh`.
* SentenceTransformers can be accelerated with ONNX or quantization if desired.

---

## Contributing<a id="contributing"></a>

Pull requests are welcome! If you use Wine‑AI in research or production, please ★ star the repo and open an issue to share your story. For significant changes, discuss your proposal in an issue first.

---

## License<a id="license"></a>

Apache 2.0

**Citation:** If you build upon this work in an academic context, please cite the Kaggle Wine Enthusiast dataset and link back to this repository.

<!-- GitHub Topics (add in repo settings for better discoverability): vespa, vector-search, semantic-search, sentence-transformers, wine, recommendation-system, information-retrieval, fastapi, approximate-nearest-neighbors, machine-learning -->
