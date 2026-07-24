# Hackathon Evaluation Harness

This directory contains a lightweight starter harness for the TigerGraph GraphRAG Hackathon Round 3 comparison.

## What it includes

- `question_loader.py` for loading evaluation questions from CSV, JSON, or DOCX.
- `run_three_pipelines.py` for a reproducible runner skeleton for:
  - LLM-only baseline
  - Traditional RAG baseline
  - Optimized TigerGraph GraphRAG

## Required environment

Set the Gemini API key before using the Gemini-backed code path:

```bash
export GEMINI_API_KEY="<your-key>"
```

## How to use it

1. Put the official question file in a machine-readable form such as CSV or JSON.
2. Run the harness:

```bash
python project/hackathon_eval/run_three_pipelines.py --questions ./questions.csv --output ./results/results.json
```

## Next engineering steps

1. Replace the placeholder pipelines with real chunking, retrieval, reranking, and graph traversal code.
2. Add exact token accounting per model call.
3. Add BERTScore and judge-based scoring.
4. Add a dashboard output for per-question and aggregate results.
