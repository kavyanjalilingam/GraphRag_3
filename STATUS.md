# Project Status

## 1. Project Maturity

| Layer | Status |
|--------|--------|
| SEC Corpus Analysis | ✅ Complete |
| Parser | ✅ Stable |
| Metadata Extraction | ✅ Stable |
| Auditor Extraction | ✅ Stable |
| Financial Metric Extraction | ✅ Stable |
| Event Extraction | ✅ Stable |
| Graph Construction | ✅ Stable |
| TigerGraph Integration | ✅ Stable |
| GSQL Query Layer | ✅ Stable |
| Retrieval Service | ✅ Stable |
| GraphRAG (LLM) | ⏳ Next |
| Evaluation | ⏳ Pending |

---

## 2. Frozen Components

**Version: v0.4-graph-ingestion-stable**

The following modules should NOT be modified unless a modeling bug is discovered:

- Parser
- Metadata extraction
- Auditor extraction
- Metric extraction
- Event extraction
- Vertex schema
- Edge schema
- ID generation
- Provenance model
- Graph Builder
- GSQL query interface

Future work should extend the retrieval layer rather than changing the graph model.

---

## 3. Active Development

**Current Sprint:** Sprint 5C — GraphRAG

**Goal:** Generate grounded answers using retrieved graph evidence.

**Current Tasks:**
- Prompt Builder
- Evidence Bundle
- Gemini Integration
- Citation Generation
- Evaluation Dataset

---

## 4. Architecture Snapshot

```text
SEC Filing
      │
      ▼
Parser
      │
      ▼
Deterministic Extractors
      │
      ▼
Validation
      │
      ▼
Graph Builder
      │
      ▼
TigerGraph
      │
      ▼
Parameterized GSQL
      │
      ▼
Retriever
      │
      ▼
Evidence Bundle
      │
      ▼
Gemini
```

---

## 5. Current Repository State

**Stable Tag:** `v0.4-graph-ingestion-stable`

**Pilot Dataset Companies:**
- AMGN
- CAT
- COP
- CSCO
- DIS

**TigerGraph:**
- **Graph:** SecGraph
- **Schema:** Stable
- **Queries Installed:** 9
- **Retrieval API:** Working

---

## 6. Next Milestone

**Sprint 5C — GraphRAG**

**Deliverables:**
- Evidence Bundle Builder
- Prompt Templates
- Gemini Integration
- Grounded Answer Generation
- SourceSpan Citations
- Evaluation Suite

---

## 7. Technical Debt

**Deferred Items:**
- Segment metric extraction
- Cross-company entity resolution
- Filing-specific AUDITED_BY edge
- Remove Company -> HAS_EVIDENCE edge
- Retrieval ranking improvements
