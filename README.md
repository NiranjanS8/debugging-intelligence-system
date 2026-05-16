# Debugging Intelligence System (DIS)

> An AI-powered debugging memory and intelligence engine that converts debugging sessions into a self-evolving knowledge base with semantic search, similarity detection, and debugging intelligence.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        FastAPI REST Layer                           │
│                                                                     │
│  POST /debug/add   POST /debug/query   GET /debug/similar/{id}     │
│  GET /analytics    GET /knowledge       POST /analytics/cluster     │
└─────────┬──────────────────┬──────────────────────┬─────────────────┘
          │                  │                      │
    ┌─────▼──────┐    ┌─────▼──────┐         ┌─────▼──────┐
    │ Ingestion  │    │ Retrieval  │         │ Analytics  │
    │  Service   │    │  Service   │         │  Service   │
    └─────┬──────┘    └─────┬──────┘         └─────┬──────┘
          │                 │                      │
    ┌─────▼──────┐    ┌─────▼──────┐         ┌─────▼──────┐
    │    LLM     │    │ Embedding  │         │ Clustering │
    │  Engine    │    │ Pipeline   │         │  Engine    │
    │            │    │            │         │            │
    │ • Gemini   │    │ • MiniLM   │         │ • Agglo.   │
    │ • OpenAI   │    │ • sentence │         │ • DBSCAN   │
    │ • Fallback │    │   -trans.  │         │            │
    └─────┬──────┘    └─────┬──────┘         └────────────┘
          │                 │
    ┌─────▼──────┐    ┌─────▼──────┐
    │ Markdown   │    │  ChromaDB  │
    │ Generator  │    │   Store    │
    │            │    │            │
    │ → .md files│    │ → vectors  │
    │ → wiki     │    │ → metadata │
    │   links    │    │ → search   │
    └────────────┘    └────────────┘
```

### Data Flow

```
Raw Debug Input (stack trace, error log, notes)
        │
        ▼
┌─── Ingestion Pipeline ───┐
│  1. Parse & normalize     │
│  2. LLM structuring       │
│  3. ID generation          │
└───────────┬───────────────┘
            │
     ┌──────┴──────┐
     ▼              ▼
 Markdown        ChromaDB
 Knowledge       Vector
 Page (.md)      Embedding
     │              │
     ▼              ▼
 File System     Semantic
 Storage         Search Index
```

---

## Tech Stack

| Component       | Technology                              |
|:----------------|:----------------------------------------|
| Backend         | Python 3.11+, FastAPI                   |
| Embeddings      | sentence-transformers (`all-MiniLM-L6-v2`) |
| Vector DB       | ChromaDB (persistent)                   |
| Storage         | Markdown files on disk                  |
| LLM             | Gemini / OpenAI / Rule-based fallback   |
| Validation      | Pydantic v2                             |
| Config          | pydantic-settings + `.env`              |

---

## Project Structure

```
DIS/
├── app/
│   ├── api/              # FastAPI route handlers
│   ├── ingestion/        # Raw input parsing & structuring pipeline
│   ├── llm/              # LLM provider abstraction (Gemini/OpenAI/fallback)
│   ├── embeddings/       # Sentence-transformer encoding pipeline
│   ├── retrieval/        # ChromaDB storage & semantic search
│   ├── clustering/       # Root-cause clustering engine
│   ├── analytics/        # Failure pattern detection & statistics
│   ├── markdown/         # Knowledge page generation & storage
│   ├── models/           # Pydantic domain models
│   └── utils/            # Logging, ID generation, text processing
│
├── knowledge_base/       # Generated markdown knowledge pages
│   ├── frontend/
│   ├── backend/
│   ├── infra/
│   └── uncategorized/
│
├── chroma_db/            # ChromaDB persistent vector storage
├── tests/                # Test suite
├── scripts/              # CLI tools, seed data, reindexing
├── main.py               # FastAPI application entry point
├── requirements.txt      # Python dependencies
├── .env.example          # Environment configuration template
└── README.md
```

---

## Setup

### Prerequisites
- Python 3.11+
- pip

### Installation

```bash
# 1. Clone the repository
git clone <repo-url>
cd DIS

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
copy .env.example .env
# Edit .env with your API keys (optional — fallback mode works without keys)

# 5. Run the server
python main.py
```

The API will be available at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs`.

---

## API Documentation

### System

| Endpoint       | Method | Description              |
|:---------------|:-------|:-------------------------|
| `/health`      | GET    | Health check             |
| `/docs`        | GET    | Swagger UI (auto-generated) |

### Debug Operations

| Endpoint              | Method | Description                          |
|:----------------------|:-------|:-------------------------------------|
| `/debug/add`          | POST   | Ingest raw debugging input           |
| `/debug/query`        | POST   | Semantic search across knowledge base |
| `/debug/similar/{id}` | GET    | Find bugs similar to a given entry   |

### Analytics

| Endpoint              | Method | Description                        |
|:----------------------|:-------|:-----------------------------------|
| `/analytics/summary`  | GET    | Knowledge base statistics          |
| `/analytics/patterns` | GET    | Recurring failure patterns         |
| `/analytics/cluster`  | POST   | Trigger root-cause clustering      |

### Knowledge Base

| Endpoint              | Method | Description                        |
|:----------------------|:-------|:-----------------------------------|
| `/knowledge/{id}`     | GET    | Retrieve a specific knowledge page |
| `/knowledge/list`     | GET    | List all knowledge entries         |

### Example: Add Debug Entry

```bash
curl -X POST http://localhost:8000/debug/add \
  -H "Content-Type: application/json" \
  -d '{
    "raw_input": "TypeError: undefined is not a function\nOccurred when clicking submit button in registration form.\nFix: forgot to bind this in React component constructor.\nUsed arrow function instead."
  }'
```

### Example: Semantic Query

```bash
curl -X POST http://localhost:8000/debug/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "null errors in React components",
    "top_k": 5,
    "tech_stack": ["react"]
  }'
```

---

## Semantic Search — How It Works

DIS uses **sentence-transformers** (`all-MiniLM-L6-v2`) to convert debug entries into 384-dimensional vector embeddings. These vectors capture the *semantic meaning* of the debugging context.

```
"forgot to bind this in React"
        │
        ▼
  Embedding Model
        │
        ▼
  [0.023, -0.156, 0.891, ..., 0.034]   (384 dims)
```

When you query "issues with this binding in JavaScript", the query is also embedded, and **cosine similarity** is computed against all stored vectors. The most semantically similar entries are returned — even if they don't share exact keywords.

### Embedding Strategy

Each entry's embedding is generated from a concatenated document:

```
Title: {title} | Root Cause: {root_cause} | Fix: {fix} | Symptoms: {symptoms}
```

This captures the full semantic context in a single vector.

---

## Clustering — Root Cause Groups

DIS uses **Agglomerative Clustering** on the embedding vectors to automatically group related bugs:

- **Async State Issues** — race conditions, stale closures, useEffect bugs
- **Null/Undefined Errors** — missing null checks, optional chaining issues
- **API Failures** — timeout, auth, CORS, serialization errors
- **Configuration Bugs** — env vars, build configs, dependency mismatches

Clusters update dynamically as new entries are added.

---

## LLM Providers

DIS supports multiple LLM backends via a **provider pattern**:

| Provider   | Config Value | Requirements        |
|:-----------|:-------------|:--------------------|
| Gemini     | `gemini`     | `GEMINI_API_KEY`    |
| OpenAI     | `openai`     | `OPENAI_API_KEY`    |
| Fallback   | `fallback`   | None (rule-based)   |

Set `LLM_PROVIDER` in `.env`. The fallback provider uses regex-based extraction and works without any API key — ideal for development and testing.

---

## Configuration

All settings are managed via environment variables. See [`.env.example`](.env.example) for the full list.

Key settings:

| Variable                  | Default            | Description                     |
|:--------------------------|:-------------------|:--------------------------------|
| `LLM_PROVIDER`            | `fallback`         | LLM backend to use              |
| `EMBEDDING_MODEL`         | `all-MiniLM-L6-v2` | Sentence-transformer model      |
| `CHROMA_PERSIST_DIR`      | `./chroma_db`      | ChromaDB storage path           |
| `KNOWLEDGE_BASE_DIR`      | `./knowledge_base`  | Markdown output directory       |
| `DEFAULT_TOP_K`           | `5`                | Default results per query       |
| `SIMILARITY_THRESHOLD`    | `0.75`             | Minimum similarity for matches  |

---