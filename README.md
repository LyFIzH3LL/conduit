# Conduit

A production-focused AI engineering monorepo built around reliability, observability, and cost control.

## Architecture

- **`services/gateway`** — Centralized FastAPI inference gateway handling PII redaction (emails, BD/US phone numbers), SHA-256 Redis response caching (1-hour TTL), and provider-agnostic LLM routing.
- **`services/core`** — Async structured extraction pipeline with Pydantic validation/self-healing retries and Hybrid RAG (Qdrant + BM25).
- **`evals/`** — Automated regression suite wired into GitHub Actions to gate PRs on accuracy and hallucination rates.

## Quick Start

1. **Configure environment**
   ```bash
   cp .env.example .env