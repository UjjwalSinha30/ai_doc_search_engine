# AI Knowledge Search Engine

A production-grade RAG system for uploading documents and chatting with content using local LLMs. Features hybrid retrieval, agentic tool-calling, multi-turn memory, and LangSmith observability.

<p align="center">
  <img src="frontend/public/assets/screenshot(23).png" alt="App Screenshot" width="800"/>
</p>

[![Python](https://img.shields.io/badge/Python-3.11-blue)](https://www.python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.128-green)](https://fastapi.tiangolo.com)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue)](https://www.docker.com)
[![LangChain](https://img.shields.io/badge/LangChain-Enabled-orange)](https://langchain.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Features

- Hybrid retrieval with vector search, BM25 keyword matching, and reranking
- Cross-encoder reranking with BAAI/bge-reranker-v2-m3
- Agentic tool-calling for search, summary, and extraction
- Multi-turn session memory for follow-up questions
- Document upload support for PDF, DOCX, and TXT
- Per-user vector isolation
- Streaming responses with source citations
- LangSmith observability support
- Dockerized FastAPI, MySQL, Ollama, and React setup

## RAGAs Evaluation Results

Evaluated on 15 domain-specific questions using Llama-3.3-70b as judge.

| Metric | Score |
| --- | --- |
| Faithfulness | 0.84 |
| Answer Relevancy | 0.91 |
| Context Precision | 0.86 |
| Context Recall | 0.90 |

## Tech Stack

| Layer | Technology |
| --- | --- |
| Backend | FastAPI, LangChain, SQLAlchemy |
| Vector DB | ChromaDB |
| Embeddings | sentence-transformers/all-MiniLM-L6-v2 |
| Reranker | BAAI/bge-reranker-v2-m3 |
| LLM | Ollama |
| Frontend | React, Tailwind CSS |
| Database | MySQL |
| Observability | LangSmith |
| Deployment | Docker |

## Quick Start

1. Clone repo:

```bash
git clone https://github.com/yourusername/ai-knowledge-search-engine.git
cd ai-knowledge-search-engine
```

2. Create `.env` in the root or configure `backend/.env`:

```env
OLLAMA_MODEL=qwen2.5:3b
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_key
LANGCHAIN_PROJECT=rag-knowledge-engine
```

3. Start with Docker:

```bash
docker compose up --build
```

4. Access:

- Frontend: http://localhost
- API Docs: http://localhost:8000/docs

## Structure

```text
.
├── backend/
│   ├── api/          # Chat, auth, document endpoints
│   ├── rag/          # Ingestion pipeline
│   ├── db/           # MySQL models
│   └── main.py
├── frontend/         # React app
├── evaluate.py       # RAGAs evaluation script
├── docker-compose.yml
└── README.md
```

## Contributing

See CONTRIBUTING.md

## License

MIT
