# Debugging Intelligence System (DIS)

> An AI-powered debugging memory platform that turns incidents into a searchable knowledge base with hybrid retrieval, semantic deduplication, RAG explanations, and optional Neo4j graph relationships.

---

## What It Does

DIS ingests raw debugging input such as stack traces, logs, notes, and fixes, then:

- structures the incident with an LLM or fallback parser
- saves a markdown knowledge page
- queues projection work for ChromaDB, wiki links, and Neo4j
- supports hybrid search across semantic and lexical signals
- detects likely semantic duplicates
- generates grounded debug explanations with retrieved evidence
- exposes analytics, clustering, knowledge listing, and graph traversal APIs

---

## Architecture

```text
Raw Debug Input
      |
      v
+---------------------+
| Ingestion Service   |
| - parse             |
| - structure         |
| - dedupe warning    |
| - persist markdown  |
+----------+----------+
           |
           v
+---------------------+
| Projection Queue    |
| - queued tasks      |
| - replay/recovery   |
+----+-----------+----+
     |           |
     |           +------------------------------+
     v                                          v
+-------------+                         +----------------+
| ChromaDB    |                         | Neo4j Graph    |
| - vectors   |                         | - Bug nodes    |
| - metadata  |                         | - RootCause    |
| - retrieval |                         | - Tech/Tag/etc |
+------+------+                         +--------+-------+
       |                                         |
       +-------------------+---------------------+
                           |
                           v
                 +----------------------+
                 | Retrieval Services   |
                 | - semantic search    |
                 | - hybrid retrieval   |
                 | - similar entries    |
                 | - wiki linking       |
                 +----------+-----------+
                            |
                            v
                 +----------------------+
                 | FastAPI API Layer    |
                 | /debug, /analytics,  |
                 | /knowledge, /graph   |
                 +----------------------+
```

### Design Notes

- Markdown is the primary persisted artifact for a new incident.
- Secondary stores are updated through a projection queue to reduce multi-store inconsistency risk.
- ChromaDB is used for semantic retrieval.
- Neo4j is optional and adds explicit relationship traversal.
- Retrieval is hybrid: vector similarity plus lexical overlap, with filters and reranking.

---

## Features

### Core Ingestion

- LLM-backed structuring with `Gemini`, `OpenAI`, or fallback rule-based extraction
- markdown knowledge page generation
- deterministic entry IDs

### Retrieval

- semantic search with ChromaDB
- hybrid retrieval with lexical plus vector scoring
- similar incident suggestions
- semantic deduplication warnings on ingest

### Intelligence

- RAG-based debug explanation
- recurring failure analytics
- root-cause clustering
- automatic wiki linking

### Graph

- optional Neo4j root-cause knowledge graph
- bug neighborhood lookup
- graph summary and relationship counts

### Reliability

- projection queue for secondary-store sync
- startup replay of pending projection tasks
- manual projection replay script

---

## Tech Stack

| Component | Technology |
|:--|:--|
| Backend | Python 3.11+, FastAPI |
| Validation | Pydantic v2 |
| LLMs | Gemini, OpenAI, fallback provider |
| Embeddings | sentence-transformers (`all-MiniLM-L6-v2`) |
| Vector Store | ChromaDB |
| Graph Store | Neo4j (optional) |
| Primary Artifact | Markdown files on disk |
| Clustering | scikit-learn |
| HTTP Client | httpx |

---

## Project Structure

```text
DIS/
├── app/
│   ├── analytics/       # analytics and failure patterns
│   ├── api/             # FastAPI route handlers
│   ├── clustering/      # root-cause clustering
│   ├── embeddings/      # embedding generation
│   ├── explanations/    # RAG explanation orchestration
│   ├── graph/           # Neo4j graph integration
│   ├── ingestion/       # parsing and structuring pipeline
│   ├── llm/             # provider abstraction + implementations
│   ├── markdown/        # markdown storage and updates
│   ├── models/          # Pydantic models
│   ├── projections/     # projection queue and processors
│   ├── retrieval/       # search, dedupe, wiki linking
│   └── utils/           # ids, logging, text helpers
├── chroma_db/           # persistent vector store
├── knowledge_base/      # markdown knowledge pages
├── projection_queue/    # queued projection tasks
├── scripts/             # seeding, reindexing, projection replay
├── tests/               # test suite
├── implementation_plan.md
├── main.py
├── requirements.txt
└── README.md
```

---

## Setup

### Prerequisites

- Python 3.11+
- pip
- optional: Neo4j if you want graph features enabled

### Installation

```bash
git clone <repo-url>
cd DIS

python -m venv venv
venv\Scripts\activate

pip install -r requirements.txt

copy .env.example .env
```

Run the app:

```bash
python main.py
```

The API is available at `http://localhost:8000`, with docs at `http://localhost:8000/docs`.

---

## Configuration

All settings are controlled through `.env`.

### Important Variables

| Variable | Default | Purpose |
|:--|:--|:--|
| `LLM_PROVIDER` | `fallback` | active LLM backend |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | embedding model |
| `CHROMA_PERSIST_DIR` | `./chroma_db` | vector store location |
| `KNOWLEDGE_BASE_DIR` | `./knowledge_base` | markdown storage |
| `PROJECTION_QUEUE_DIR` | `./projection_queue` | queued projection tasks |
| `SIMILARITY_THRESHOLD` | `0.75` | similar-entry threshold |
| `DEDUPLICATION_THRESHOLD` | `0.92` | semantic dedupe warning threshold |
| `WIKI_LINK_THRESHOLD` | `0.65` | wiki-link scoring threshold |
| `WIKI_MAX_LINKS` | `5` | max related wiki links |
| `NEO4J_ENABLED` | `false` | enable graph sync |
| `NEO4J_URI` | `bolt://localhost:7687` | Neo4j connection URI |

### Neo4j

Graph features are optional.

To enable them:

```env
NEO4J_ENABLED=true
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-password
NEO4J_DATABASE=neo4j
```

---

## API Overview

### System

| Method | Endpoint | Description |
|:--|:--|:--|
| `GET` | `/health` | health check |

### Debug

| Method | Endpoint | Description |
|:--|:--|:--|
| `POST` | `/debug/add` | ingest a debug incident and queue projections |
| `POST` | `/debug/query` | hybrid retrieval across the knowledge base |
| `GET` | `/debug/similar/{id}` | fetch similar incidents |
| `POST` | `/debug/explain` | generate a grounded RAG explanation |

### Analytics

| Method | Endpoint | Description |
|:--|:--|:--|
| `GET` | `/analytics/summary` | KB summary stats |
| `GET` | `/analytics/patterns` | recurring failure patterns |
| `POST` | `/analytics/cluster` | root-cause clustering |

### Knowledge

| Method | Endpoint | Description |
|:--|:--|:--|
| `GET` | `/knowledge/list` | list known incidents |
| `GET` | `/knowledge/{id}` | fetch one incident and markdown |

### Graph

| Method | Endpoint | Description |
|:--|:--|:--|
| `GET` | `/graph/summary` | graph counts and relationship summary |
| `GET` | `/graph/entry/{id}` | local graph neighborhood for an incident |

---

## Example Requests

### Add Debug Entry

```bash
curl -X POST http://localhost:8000/debug/add ^
  -H "Content-Type: application/json" ^
  -d "{\"raw_input\":\"TypeError: undefined is not a function\nFix: forgot to bind this in React component\"}"
```

Response highlights:

- `similar_entries`
- `is_duplicate`
- `duplicate_of`
- `projection_task_id`
- `projection_status`

### Hybrid Query

```bash
curl -X POST http://localhost:8000/debug/query ^
  -H "Content-Type: application/json" ^
  -d "{\"query\":\"react cors blocked request\",\"top_k\":5,\"tech_stack\":[\"react\"]}"
```

### RAG Explanation

```bash
curl -X POST http://localhost:8000/debug/explain ^
  -H "Content-Type: application/json" ^
  -d "{\"raw_input\":\"CORS error blocked by access-control-allow-origin\",\"top_k\":3}"
```

---

## Data Flow

### Ingest Path

1. Parse and normalize raw input
2. Structure it with the active LLM provider or fallback parser
3. Check for semantic duplicates
4. Save markdown knowledge page
5. Queue projection task
6. Background projection updates:
   - Chroma index
   - wiki links
   - Neo4j graph

### Query Path

1. Vector retrieval from ChromaDB
2. Lexical overlap scoring
3. Filter by tags and tech stack
4. Merge and rerank into hybrid results

### Explanation Path

1. Hybrid retrieval
2. Optional graph neighborhood expansion
3. Grounded LLM explanation using retrieved evidence

---

## Operational Scripts

| Script | Purpose |
|:--|:--|
| `python scripts/seed_data.py` | seed sample incidents |
| `python scripts/reindex.py` | rebuild vectors and relink wiki pages |
| `python scripts/process_projection_queue.py` | replay queued projection tasks |
| `python scripts/verify_phase1.py` | basic Phase 1 checks |
| `python scripts/verify_phase3.py` | basic Phase 3 checks |

---

## Testing

Run tests with:

```bash
pytest tests -v
```

Suggested smoke flow:

```bash
python scripts/seed_data.py
python scripts/process_projection_queue.py
```

Then hit:

- `/debug/add`
- `/debug/query`
- `/debug/explain`
- `/analytics/summary`
- `/graph/summary` if Neo4j is enabled
