# AI Knowledge Search Engine

A RAG application for uploading documents and chatting with their content using a local Ollama model. The app includes document ingestion, vector search, reranking, streaming chat responses, source citations, multi-turn memory, and LangSmith tracing.

<p align="center">
  <img src="frontend/public/assets/screenshot(23).png" alt="App Screenshot" width="800"/>
</p>

[![Python](https://img.shields.io/badge/Python-3.11-blue)](https://www.python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.128-green)](https://fastapi.tiangolo.com)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue)](https://www.docker.com)
[![LangChain](https://img.shields.io/badge/LangChain-Enabled-orange)](https://langchain.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Features

- Document upload and chat for PDF, DOCX, TXT, MD, and CSV files
- Vector retrieval with ChromaDB
- Cross-encoder reranking with `BAAI/bge-reranker-v2-m3`
- Embeddings with `sentence-transformers/all-MiniLM-L6-v2`
- Agentic tool-calling for search, summary, and extraction
- Multi-turn session memory for follow-up questions
- Per-user document/vector isolation
- Streaming responses with source citations
- LangSmith tracing support
- Docker setup for frontend, backend, and MySQL
- Ollama runs locally on the host machine

## Tech Stack

| Layer | Technology |
| --- | --- |
| Frontend | React, Vite, Tailwind CSS |
| Frontend Docker Server | Nginx |
| Backend | FastAPI, LangChain, SQLAlchemy |
| Database | MySQL |
| Vector Store | ChromaDB |
| Embeddings | sentence-transformers/all-MiniLM-L6-v2 |
| Reranker | BAAI/bge-reranker-v2-m3 |
| Chat LLM | Ollama |
| Observability | LangSmith |
| Evaluation Judge | Groq, configured by `GROQ_EVAL_MODEL` |

## Architecture

### Local Development

```text
Browser
  -> http://localhost:5173
  -> Vite React frontend
  -> http://localhost:8000/api/*
  -> FastAPI backend
  -> MySQL at localhost:3306
  -> Chroma local storage
  -> Ollama at localhost:11434
```

In local mode, Vite serves the frontend and FastAPI runs directly in your Python environment.

### Docker

```text
Browser
  -> http://localhost
  -> frontend Nginx container
  -> React calls /api/*
  -> Nginx proxies /api/* to http://backend:8000
  -> FastAPI backend container
  -> MySQL container at mysql:3306
  -> Chroma Docker volume
  -> Ollama on Windows host at host.docker.internal:11434
```

Docker Compose runs:

```text
rag_frontend  -> React build served by Nginx on port 80
rag-backend   -> FastAPI on port 8000
rag_mysql     -> MySQL on port 3306
```

Ollama is not started by Docker in the current setup. It should run locally on the host.

## Environment Files

Real `.env` files are ignored by Git. Use `.env.example` as the safe template.

```text
.env.example             safe template, no real secrets
backend/.env             local backend config
backend/.env.docker      Docker backend config
frontend/.env            local frontend config
frontend/.env.production optional Docker frontend config, usually empty
```

Local backend example:

```env
DATABASE_URL=mysql+pymysql://root:@localhost:3306/newdatabase
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:3b
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=your_langsmith_api_key_here
LANGSMITH_PROJECT=rag-knowledge-engine
GROQ_API_KEY=your_groq_api_key_here
GROQ_EVAL_MODEL=openai/gpt-oss-120b
```

Docker backend example:

```env
DATABASE_URL=mysql+pymysql://root:password123@mysql:3306/newdatabase
OLLAMA_BASE_URL=http://host.docker.internal:11434
OLLAMA_MODEL=qwen2.5:3b
```

Local frontend example:

```env
VITE_API_BASE_URL=http://localhost:8000
```

Docker frontend should use an empty API base so React calls relative URLs such as `/api/chat`:

```env
VITE_API_BASE_URL=
```

## Run Locally

Start Ollama and make sure the configured model exists:

```powershell
ollama serve
ollama list
```

Start the backend:

```powershell
cd backend
.\venv\Scripts\activate
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Start the frontend:

```powershell
cd frontend
npm install
npm run dev
```

Open:

```text
http://localhost:5173
```

Backend health:

```text
http://localhost:8000/health
```

## Run With Docker

Start Ollama locally first:

```powershell
ollama serve
```

Build and run the app:

```powershell
docker compose up --build
```

Open:

```text
http://localhost
```

Backend health:

```text
http://localhost:8000/health
```

Run in the background:

```powershell
docker compose up --build -d
```

Check containers:

```powershell
docker compose ps
```

Stop containers:

```powershell
docker compose down
```

## Docker Notes

Docker does not use the local Python virtual environment. The backend image installs Python dependencies inside a Linux container.

`sentence-transformers` depends on PyTorch. On weaker machines, prefer CPU-only PyTorch in the backend Dockerfile before installing the rest of the requirements:

```dockerfile
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir -r requirements.txt
```

This avoids downloading large CUDA/NVIDIA packages that are not needed for this Docker setup.

## Evaluation And LangSmith

Normal app chat uses Ollama.

Evaluation uses Groq as the judge model and LangSmith for tracing/monitoring.

Run evaluation:

```powershell
cd backend
$env:PYTHONIOENCODING='utf-8'
..\venv\Scripts\python.exe evaluate.py
```

Configured evaluation model:

```env
GROQ_EVAL_MODEL=openai/gpt-oss-120b
```

LangSmith traces appear under:

```env
LANGSMITH_PROJECT=rag-knowledge-engine
```

## API Routes

Backend routes are created in `backend/main.py` by including routers from `backend/api`.

Examples:

```text
/api/login
/api/me
/api/upload
/api/documents
/api/chat
/health
/docs
```

## Structure

```text
.
├── backend/
│   ├── api/              # Chat, auth, upload, document endpoints
│   ├── db/               # Database connection
│   ├── rag/              # Ingestion and vector pipeline
│   ├── Dockerfile
│   ├── requirements.txt
│   └── main.py
├── frontend/
│   ├── src/              # React app
│   ├── Dockerfile
│   ├── nginx.conf        # Static serving and /api proxy
│   └── package.json
├── docker-compose.yml
├── .env.example
└── README.md
```

## Contributing

See `CONTRIBUTING.md`.

## License

MIT
