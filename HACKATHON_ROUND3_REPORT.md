# TigerGraph GraphRAG Hackathon – Round 3

## Executive Summary

This repository already contains a usable SEC/financial filing corpus and a graph ingestion pipeline. The current codebase is not yet a full Round 3 submission, but it is strong enough to be the foundation for a disciplined GraphRAG + context-optimization entry.

From fresh verification in this workspace:

- The pilot integrity script passed with 5 companies and 20 filings checked.
- The parsing and extraction stages ran successfully for the pilot corpus.
- The graph builder produced 140 nodes and 290 edges.
- The dataset exploration report confirms a clean 100-company / 400-filing corpus with a highly regular folder structure.

## Current State of the Repository

### What is already working

- [verify_pilot.py](verify_pilot.py) validates the pilot corpus.
- [explore_dataset.py](explore_dataset.py) generates corpus-level analysis and exploration assets.
- [project/run_parser.py](project/run_parser.py) parses the filings.
- [project/run_metadata.py](project/run_metadata.py) extracts metadata.
- [project/run_metrics.py](project/run_metrics.py) extracts financial metrics.
- [project/run_events.py](project/run_events.py) extracts event signals.
- [project/run_auditors.py](project/run_auditors.py) resolves auditors.
- [project/build_graph.py](project/build_graph.py) materializes graph JSON/CSV outputs.

### What is still blocked

- [explore_dataset.py](explore_dataset.py) currently has a syntax issue in the report-generation section.
- The Round 3 official question set is not yet integrated into the repo.
- The GraphRAG application layer, evaluation harness, and token-accounting dashboard are not yet fully implemented.
- The TigerGraph Savanna / vector pipeline still needs a clean end-to-end reporting path.

## Evidence from the Workspace

### Verified commands

1. Pilot verification:
   - Command: `verify_pilot.py`
   - Result: `✅ Pilot corpus verification PASSED`

2. Graph build:
   - Command: `build_graph.py`
   - Result: `Generated 140 nodes and 290 edges.`

### Verified dataset insights

From [exploration_report/report.md](exploration_report/report.md):

- 100 companies
- 400 matched filings
- 4 filings per company on average
- Clean sector distribution across Information Technology, Financials, Health Care, and Industrials
- 0 missing manifest values
- 0 exact duplicate rows
- 0 duplicate accession numbers
- 0 manifest rows lacking a matched file

## What the Hackathon Team Should Build Next

### 1. Fix the dataset exploration script

The first technical action item is to repair [explore_dataset.py](explore_dataset.py) so the repo can regenerate the corpus analysis cleanly.

Reason:
- It is a repository-level execution check.
- It confirms your corpus and retrieval assumptions are grounded in the actual data.
- It helps produce the report artifacts required for documentation and comparison.

### 2. Add the official evaluation question loader

The attached Round 3 question set must be turned into a reproducible input artifact.

Recommended approach:
- Convert the document into a machine-readable JSON/CSV format.
- Store question ID, question text, expected answer form, source evidence hints, and question tier.
- Keep the official holdout questions separate from the dev set.

### 3. Implement the three-pipeline baseline

You need three clearly separated execution paths:

1. LLM-only baseline
   - Direct answer generation from the question, with no retrieval.

2. Traditional RAG baseline
   - Chunk the dataset and retrieve top-k evidence.
   - Use one fixed embedding model and one documented retrieval setup.

3. Optimized TigerGraph GraphRAG
   - Use TigerGraph as graph storage and vector retrieval.
   - Retrieve graph-neighborhood evidence, not just disconnected chunks.
   - Use context optimization to compress and select the evidence before generation.

### 4. Standardize token accounting

This challenge is heavily weighted on token efficiency, so your evaluation harness must record per-question token usage for every model call.

Record at minimum:

- System prompt tokens
- Question tokens
- Retrieved context tokens
- Reranking / compression tokens
- Output tokens
- Total inference tokens per question

### 5. Add an evaluation dashboard

You need a dashboard or at least a reproducible results table with:

- BERTScore F1
- strict pass/fail
- judge score
- citation quality
- latency
- total inference tokens
- per-question evidence used

### 6. Add ablation analysis

To make the GraphRAG claim credible, you need to show what part of the improvement is due to:

- graph retrieval itself
- reranking
- filtering/deduplication
- evidence compression
- multi-hop traversal

Without ablations, the judges may treat the token savings as unconvincing.

## Recommended Technical Roadmap

### Phase 1 — Stabilize the repo

- Repair [explore_dataset.py](explore_dataset.py)
- Confirm the full corpus path is consistent with [manifest.csv](manifest.csv)
- Freeze a reproducible pilot run with deterministic outputs

### Phase 2 — Build the evaluation harness

- Load the official questions
- Run each question through all three pipelines
- Save raw answers, retrieved chunks, and evidence artifacts for every run

### Phase 3 — Add graph-aware retrieval

- Use TigerGraph for entity / relationship traversal
- Build graph neighborhoods around issuer, event, metric, and governance entities
- Add graph-derived ranking signals to the retrieval loop

### Phase 4 — Add optimization

- Deduplicate semantic duplicates
- Preserve complementary evidence from multiple sources
- Use MMR or diversity-aware ranking
- Remove repetitive boilerplate and low-value context
- Compress evidence into a smaller, high-signal bundle

### Phase 5 — Report and present

- Create per-question result tables
- Create aggregate charts
- Write the architecture and methodology write-up
- Prepare a public-facing blog/social post

## Final Recommendation

The strongest path for this hackathon is:

1. Use this repo as the ingestion and graph foundation.
2. Keep the pipeline honest with a strict baseline comparison.
3. Focus the innovation on context optimization, not just retrieval.
4. Measure everything per-question, per-pipeline, and per-stage.
5. Make the final claims traceable to code, prompts, evidence bundles, and evaluation outputs.

## Immediate Next Actions

1. Repair [explore_dataset.py](explore_dataset.py) so the report regenerates.
2. Convert the attached question document into a structured JSON/CSV input.
3. Implement a baseline retrieval service.
4. Build a GraphRAG retrieval service on top of TigerGraph.
5. Add token-accounting instrumentation.
6. Add the evaluation dashboard and ablation reporting.

## Suggested Submission Narrative

The team should present this as a graph-aware context optimization pipeline for heterogeneous SEC-style enterprise knowledge, not just a graph database demo. The key claim should be:

> We built a graph-grounded retrieval and context-selection system that uses the graph to identify the most relevant evidence neighborhood, then compresses that neighborhood into a smaller, higher-quality context bundle before generation.

This would align directly with the Round 3 challenge statement.
