# ADR 0002: A transparent lightweight local mode

Status: accepted.

The product must boot without paid keys, model downloads, Docker Desktop, or GPU hardware. Local mode uses SQLite/local objects/API background tasks and BM25/extractive answers.

The full stack remains PostgreSQL/pgvector, Redis/Celery and MinIO. UI/API configuration disclose the actual provider and retrieval strategy. Lexical search is never labeled semantic. Full-stack and real-provider verification remain distinct from local acceptance results.
