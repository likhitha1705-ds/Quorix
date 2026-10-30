# Quorix

> **Intelligent Context Selection & Retrieval Optimization Engine**  
> Decide where to search before retrieval. Decide what to trust after.

Quorix is an intelligent Retrieval-Augmented Generation (RAG) system that selects the most relevant knowledge sources before retrieval, evaluates retrieved evidence across multiple criteria, and generates trustworthy responses with explicit inline citations while mitigating hallucinations.

---

## Architecture Overview

1. **Phase 1: Foundation & Observability** — FastAPI backend, structured schemas, health checks, and lifecycle managers.
2. **Phase 2: Ingestion & Storage** — Adapters for technical documentation, conversations, and tickets with sentence-transformers embeddings and Qdrant vector storage.
3. **Phase 3: Query Intelligence & Source Selection** — Analyzes query intent, extracts entities, and selects relevant knowledge sources.
4. **Phase 4: Retrieval Budget & Hybrid Retrieval** — Manages retrieval budgets and executes fused semantic (Qdrant) and lexical (BM25) searches with deduplication.
5. **Phase 5: Evidence Intelligence & Sufficiency** — Multi-criterion evidence scoring (relevance, authority, freshness, directness) and conflict detection.
6. **Phase 6: Answer Generation & Citations** — Synthesizes answers strictly grounded in evaluated evidence with validated inline citations.

---

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+ and npm

### Backend Setup

```bash
cd backend

# Create and activate a virtual environment (optional)
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run backend development server
uvicorn app.main:app --reload --port 8000
```

The API will be available at `http://127.0.0.1:8000`. Health check endpoint: `GET /api/health`.

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start Vite development server
npm run dev
```

The frontend will be accessible at `http://localhost:5173`.

---

## Running Tests

```bash
cd backend
pytest
```

---

## Deployment Configuration

- **Backend API URL**: Configure `VITE_API_URL` or `VITE_BACKEND_URL` in `frontend` environment.
- **Gemini API Key**: Set `GEMINI_API_KEY` in `backend/.env` for live Google GenAI generation; if omitted, the deterministic grounded offline generator will execute automatically.

