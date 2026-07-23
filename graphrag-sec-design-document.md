# GraphRAG for SEC Filings — Design & Research Document

**Version:** v1.1
**Status:** Pre-implementation, frozen. Consolidates all research/critique conversations into one reference. Supersedes any single prior report — where sources conflict, this document states the resolution and why.
**Owners:** [fill in — see §12]
**Deadline:** Round 3 delivery July 26, 2026 (launched July 17, 2026)

> **How to use this document:** This is the single source of truth going forward. When a design decision changes, edit this file and note it in a changelog at the bottom — don't let new decisions live only in chat.

---

## 1. Project Overview

### Problem Statement

TigerGraph GraphRAG Hackathon Round 3 requires building and comparing **three pipelines** — LLM-only, Traditional RAG, and Optimized GraphRAG — on a fixed, shared SEC-filings dataset and a fixed question set, under controlled experimental conditions. The graded question is not "what's the biggest token reduction" but **"does graph-derived structure demonstrably improve token efficiency without sacrificing answer quality, in a rigorous, reproducible, disclosed comparison."**

### What's actually being scored

| Criterion | Weight |
|---|---|
| Answer Quality & Accuracy (BERTScore F1, strict pass, graded judge) | 40% |
| Token Efficiency (vs. Traditional RAG, full inference accounting) | 30% |
| Evidence & Citation Quality | 15% |
| Graph Contribution & Experimental Rigor (ablations, reproducibility) | 10% |
| Generalizability & Solution Quality | 5% |

**Implication for priorities:** schema elegance and generalization stories are 5% of the grade. A working, fully-instrumented, three-times-repeated evaluation across all 50 questions is worth far more than a beautiful ontology with no runs behind it. Section 15 reflects this.

### Hard constraints from the brief

- TigerGraph Savanna must be **both** the graph store and the vector index for GraphRAG — not an external vector DB with graph relationships bolted on.
- Traditional RAG and GraphRAG must use the **same embedding model**.
- BERTScore config is pinned: `bert-score==0.3.13`, `roberta-large`, `rescale_with_baseline=True`, `idf=False`.
- Full token accounting per question, per pipeline: system/instruction, question, retrieved context, any LLM-based routing/rerank/filter/compression, output, total inference. Ingestion/embedding costs reported separately, once.
- 3 repeated runs of the full held-out set, frozen config, mean + variance reported.
- Dev/tuning set must be disjoint from the held-out evaluation set — **see §13, this is currently unresolved and time-sensitive.**

### 1.4 Architecture Principles

These aren't new decisions — each one is a compression of something already argued from evidence elsewhere in this document. They exist so a reviewer (or a teammate joining late) gets the design philosophy in one minute instead of reconstructing it from 20 pages. If a principle below ever seems to conflict with an implementation choice, the underlying Discovery/Rule it cites is the tiebreaker, not the one-line summary.

1. **Corpus-first, not benchmark-first.** Build the graph from what the SEC filings' own structure supports, not by reverse-engineering the 50 eval questions. *Grounded in: §10's routing principle, and the Lessons Learned note that the router must not be built from the eval set's own tier labels.*
2. **Deterministic extraction wherever the corpus's own structure allows it.** Cover pages, SEC Items, tables, and signature blocks are dependable; parse them with rules, not a model. *Grounded in: the §2 major finding and Discovery 1.*
3. **LLM extraction is reserved for genuine narrative ambiguity** — risk disclosure prose, MD&A, and person-identity resolution where deterministic rules run out. *Grounded in: same §2 finding, applied at its boundary.*
4. **The graph stores facts; vector search retrieves narrative.** Structured entities and relationships live in TigerGraph as queryable properties. Prose that resists structuring is retrieved, not force-fit into a vertex. *Grounded in: Discovery 4 (cover facts must be properties, never just embedded prose) and the §10 hybrid-retrieval design for the narrative/risk query class.*
5. **Every asserted fact carries provenance.** `filing_accession` and `source_span_id` on every edge, not just the ones that seem citation-worthy. *Grounded in: §7's non-negotiable edge-property list — this is what Tier D temporal questions and the Evidence & Citation Quality criterion both depend on.*
6. **`unknown` is a valid terminal state, not a failure to hide.** Where evidence is genuinely insufficient — an unnamed officer, an unresolvable person merge, an unmapped metric label — extraction stops and records that, rather than guessing. *Grounded in: RULE_008, RULE_011, RULE_012, and Discovery 10.*

---

## 2. Dataset Exploration

### Actual corpus composition (verified, not the brief's approximate figures)

- **100 companies** (S&P-100-style), **400 filings total** — not ~401 as the challenge brief states informally.
- Exactly **100 10-K, 200 8-K, 100 DEF 14A**. No 10-Q present anywhere in the corpus — drop this form type from the design; it was an initial assumption, not a fact.
- 85.79 MB total (filings + manifest), ~13.06M words, ~17.4M estimated tokens (word-count approximation only — see §16 on why this must not be used for actual token accounting).
- Every issuer has exactly 4 filings: 1×10-K, 2×8-K, 1×DEF 14A. Structurally uniform — **zero** issuers deviate from this pattern.
- Manifest has 3 duplicate `(ticker, form, filing_date)` keys but 0 duplicate accession numbers — accession is the only safe primary key for `Filing`.

### Data characteristics (confirmed against raw text, not just statistics)

- Structured financial tables (income statement, balance sheet, segment tables) — genuinely complex, multi-dimensional, whitespace-delimited in the raw text export.
- Deterministic cover-page metadata (registrant name, Commission File Number, IRS EIN, filing date, event date) — clean and consistently labeled.
- Snapshot facts in signature blocks (name + title of the certifying officer) — **not** the same thing as an appointment event.
- Governance content: board rosters, committee membership, auditor ratification, executive officer tables with tenure.
- Corporate events reported via SEC Item number in 8-Ks, but **Item number alone is an unreliable proxy for event type** (see Discovery 3 below).
- Company-specific glossaries (seen in CAT's 10-K) defining issuer-specific metric labels in the issuer's own words.
- Segment reporting that gets **retroactively restated** across filing years for the same company (see Discovery 8).

### Major finding

**The corpus is semi-structured, not unstructured free text.** SEC filings follow dependable form-level structure (headings, Items, cover blocks, signature blocks) that a generic document-chunking pipeline would throw away. This is the single biggest architectural implication of the whole exploration phase:

> **Deterministic, structure-aware extraction should be preferred over LLM-based extraction wherever the corpus's own structure makes it possible.** LLM extraction should be reserved for the genuinely unstructured residue — narrative risk disclosure, MD&A prose, person-name resolution ambiguity.

---

## 3. Corpus Investigation

Findings below are grounded in actual raw filing text reviewed during this project (AMT 8-K, BKNG 8-K, CAT 10-K, CVS 8-K), not inferred from statistics alone. Each entry: **evidence → decision.**

### Discovery 1 — Cover metadata is deterministic
**Evidence:** AMT, BKNG, CAT, CVS 8-Ks and CAT's 10-K all present `Date of Report (Date of earliest event reported)`, exact registrant name, Commission File Number, and IRS EIN in a stable labeled cover block.
**Decision:** Regex/pattern extraction, ~100% confidence. No LLM needed for this field class.

### Discovery 2 — Signature blocks are snapshot facts, not events
**Evidence:** AMT's 8-K signature — `Rodney M. Smith, Executive Vice President, Chief Financial Officer and Treasurer` — is a routine attestation required on every filing, not a CFO appointment. Doc 1's original rule-based scan counted 259 "Company → CFO" evidence filings almost certainly by conflating these two things.
**Decision:** Signature-block name+title pairs populate `RoleAssignment` (current-as-of-this-filing) only. They never independently create an `OfficerChangeEvent`. Compound titles ("Executive Vice President, Chief Financial Officer and Treasurer") require substring/contains matching against the role ontology, not exact-string match.

### Discovery 3 — Item numbers are hints, not event-type determinants
**Evidence:** CVS's May 2026 8-K carries **both** Item 5.02(e) (a compensation-plan stockholder approval — no appointment/departure language at all) and Item 5.07 (shareholder vote results) for a single underlying event: the annual meeting.
**Decision:** Content classifies the event type; Item number only narrows the candidate set. Item 5.02 sub-classifies into at least two disjoint types: officer/director changes vs. compensation-plan approvals. `ShareholderVote` is added as its own first-class event type (see §7), separate from doc 7's original 11-type taxonomy — it was a genuine gap.

### Discovery 4 — Cover-page facts are sometimes the answer, so metadata must be extracted, never merely discarded
**Evidence:** EQ06 ("On what date does Microsoft's FY2025 end?") is a cover-page fact.
**Decision:** Extract cover metadata into structured graph properties at ingestion. Never embed or retrieve the raw cover block as prose — the fact must be queryable as a property, not fished for via vector search.

### Discovery 5 — Auditor identity requires guarded, positional extraction, not corpus-wide substring search
**Evidence:** A raw substring scan for audit-firm names across the corpus finds EY in 35 filings, Deloitte in 27, PwC in 35, KPMG in 15 — noisy, because it also catches historical, subsidiary, comparative, and critical-audit-matter mentions. The eval set's own ground truth (EQ44) sums to exactly EY 35 + PwC 29 + Deloitte 25 + KPMG 11 = 100 — a clean one-firm-per-company partition that the naive scan does **not** reproduce.
**Decision:** Precedence order for current auditor: (1) firm name in the signature block of the current Report of Independent Registered Public Accounting Firm; (2) DEF 14A auditor-ratification proposal *and*, now confirmed, the 8-K reporting that vote's result (CVS's 8-K independently confirms EY as auditor via the Item 5.07 vote tally — this is a genuine second corroborating source class); (3) explicit audit-committee selection statement; (4) otherwise `unknown`. A text mention outside these three contexts is never sufficient. Auditor-ratification 8-K vote outcomes should be cross-checked against DEF14A signature-block findings; agreement raises confidence, disagreement is flagged for review.

### Discovery 6 — Person-name variation is real and must be catalogued, not assumed
**Evidence, catalogued across filings seen so far:**
- Comma-suffix: "Robert J. Mylod, Jr." (BKNG)
- Inline professional credentials: "Jeffrey R. Balser, M.D., Ph.D." (CVS)
- Bare surname-only table references (implied by doc 7's original governance-table description)
**Decision:** Normalization strips honorifics, generational suffixes (Jr./III), and credentials (M.D./Ph.D.) into separate fields, distinct from the name itself. Within-company canonical key = normalized name + ticker + proxy year. Cross-company merge requires two independent corroborators (full name + biography/employer, or a stable identifier) — never merge on name-string match alone. **Real-world name recognition is not evidence of identity in this corpus**: it is explicitly synthetic and future-dated, and at least one board-member name observed (CVS's "J. Scott Kirby") coincides with a real, unrelated public figure. Extraction must not let pretrained knowledge "correct" or backfill what the filing text actually says.

### Discovery 7 — 8-K "mention" counts vastly overstate discrete events
**Evidence:** Doc 1's rule-based scan counted 214 "Company → Dividend" and 215 "Company → Acquisition" evidence filings. A structurally-scoped, Item-aware pass over the same 8-Ks finds far fewer real discrete events (~16 dividend declarations, ~16–21 acquisitions), matching the scale implied by EQ34/EQ35's answer keys (specific short company lists, not ~200 companies).
**Decision:** The large narrative-mention counts describe topical *discussion* (e.g., a 10-K's ongoing dividend policy language) and must never be confused with the small, discrete, dated `CorporateEvent` set that questions like EQ34–EQ46 require. Two different graph objects; do not let one substitute for the other.

### Discovery 8 — Segment definitions can be retroactively restated across filing years
**Evidence:** CAT's FY2025 10-K states responsibility for certain product lines moved between segments effective July 1, 2025, and *"Segment information for 2024 and 2023 has been retrospectively adjusted to conform to the 2025 presentation."*
**Decision:** A same-named segment's historical revenue figure, as reported in the current filing, is not guaranteed to match what was originally reported in that prior year's own 10-K. `MetricObservation` needs an `as_reported_in` / restatement-aware field for any segment-level time series; do not assume naive year-over-year comparability from a single filing's tables.

### Discovery 9 — Some filings provide issuer-defined term glossaries; treat as a first-class, high-confidence source
**Evidence:** CAT's 10-K includes a 24-term glossary defining company-specific metric labels ("Price Realization," "Sales Volume," "Adjusted Operating Profit Margin") in the issuer's own words.
**Decision:** Where present, extract the glossary directly as a per-issuer definitions table — higher confidence than any cross-company synonym inference, since it resolves ambiguity with authorial intent. Check how common this is across the 100 10-Ks before investing further; if rare, it's a bonus signal, not a load-bearing extraction path.

### Discovery 10 — Not every role has a discoverable name
**Evidence:** CAT's Item 1C describes its CIO's tenure and background in detail but never names her in visible text — she is not among the eight officers Caterpillar classifies as Section 16 executive officers in Item 1D.
**Decision:** "Role mentioned, name absent" is a valid terminal extraction state. Flag as `unknown`; never force a guess.

### Discovery 11 — Internal arithmetic checks are a cheap, real data-quality validator
**Evidence:** CVS's 8-K vote tallies sum exactly to the stated quorum (1,142,802,406 shares) across every proposal checked. CAT's 10-K dividend figure ($1.51/share, Dec 2025) matches exactly what EQ24's answer key expects as the pre-raise baseline.
**Decision:** Build lightweight automated consistency checks (vote-column sums = quorum; segment sums = consolidated total; etc.) as a cheap way to catch extraction bugs during ingestion, not just as one-off manual spot checks.

---

## 4. Critiques & Architecture Reviews

This project went through several rounds of independent review. Documenting the arc matters for the methodology writeup (judges explicitly want to see disciplined iteration, not just a final answer).

### Phase 1 — Initial exploration (Codex, dataset stats)
Produced corpus statistics, manifest QA, folder-structure audit, rule-based entity/relationship mention counts, chunking and graph-schema recommendations. Solid on structure; its entity/relationship counts (see Discovery 5, 7 above) later turned out to conflate mentions with discrete facts — corrected in Phase 3.

### Phase 2 — "Entity-centric vs document-centric" review (Codex/ChatGPT)
**Accepted:** company-as-root-vertex framing; entities (not chunks) as the graph's primary objects.
**Rejected / corrected:** the claim that the original report hadn't already specified both a document hierarchy *and* an entity graph — it had (§10 of the original report). Framed as a new discovery when it was closer to a restatement.
**Lesson applied going forward:** watch for "I completely agree" review patterns that restate existing content as new insight — a real risk flagged and later explicitly confirmed as having occurred (accession-ID discussion, cover-metadata discussion).

### Phase 3 — Content-driven semantic knowledge model (doc 7)
The strongest single input to this document. Went back to the corpus text itself rather than continuing meta-discussion. Produced the guarded auditor-extraction rule, the person-resolution ambiguity catalogue, the 8-K event taxonomy, the risk-theme taxonomy, and the `MetricDefinition`/`MetricObservation` split. Most of §3 and §7 below trace directly to this phase.
**Correction it forced:** auditor extraction, previously assumed "trivially closed-set," is actually noisy without positional guarding (Discovery 5).

### Phase 4 — Generic entity-resolution industry synthesis
Useful for exactly one concrete idea: a controlled synonym taxonomy for the GLP-1/obesity risk theme (linking specific drug/condition terms under one higher-level theme node), which addresses a real, still-open discrepancy (see §5, §13). **Rejected wholesale:** the full nine-phase batch-clustering/embedding/governance pipeline (HDBSCAN, query telemetry, human-review queues, ongoing monitoring) — built for an open-ended, continuously-growing corpus; this corpus is closed, bounded (~100 companies, ~1,000–1,500 people), and fixed for the contest's duration. Implementing that machinery would spend scarce time solving a scale problem this project doesn't have.

### Phase 5 — "Two-track" resolution (implementation vs. architecture story)
**Accepted:** separate what ships (deterministic extraction + known canonical rules) from what the architecture *supports* (an offline, read-only, non-blocking discovery pass, documented but not built out further than what already exists in Phases 1 and 3).
**Rejected:** building a new formal "Corpus Discovery Notebook" (n-grams, TF-IDF, embedding clustering) from scratch — Phases 1 and 3 already are that discovery pass, done with more domain grounding than a generic statistical sweep would provide. One caveat noted in that review turn: it opened by attributing an idea to "you" that had not actually been proposed in the conversation — a fabricated-callback pattern worth naming and discounting on its own, independent of whether the underlying idea was good.

### Phase 6 — Raw-text validation (AMT, BKNG, CAT, CVS filings)
Grounded every prior assumption against real filing text. Produced Discoveries 1–11 in §3. This phase should be treated as authoritative wherever it conflicts with earlier, more abstract phases.

### Final decisions after all phases
1. Deterministic extraction first; LLM extraction reserved for narrative/ambiguous content.
2. Entity graph is primary; documents/chunks are provenance, not the retrieval target.
3. Auditor and metric extraction both require *guarded, contextual* rules — neither is a trivial closed-set match, contrary to early assumptions.
4. Person resolution stays conservative (two-corroborator cross-company merge rule); no heavy embedding-based ER pipeline.
5. Discovery/ontology-evolution machinery is an architecture-note sentence, not a Phase 1 deliverable.
6. 8-K event classification uses content, not Item number alone.

---

## 5. Evaluation Analysis

The official 50-question set (v3) is stratified by expected GraphRAG benefit = hop depth × fan-out.

| Tier | Count | Benefit | Pattern |
|---|---|---|---|
| A — single-hop controls | 8 | Low | One fact, one document |
| B — two-hop bridges | 16 | Medium | Event/person bridges to a second fact |
| C — multi-hop aggregation/intersection | 20 | High | Corpus-wide set intersection, GROUP BY, COUNT |
| D — cross-document & temporal | 6 | Medium–High | Chronological ordering, multi-filing synthesis |

**Question archetypes present:** entity lookup, numeric comparison, set intersection, aggregation/count, temporal ordering, multi-hop bridging. Tier C questions (EQ25, EQ30–EQ33, EQ44, etc.) are frequently not retrieval problems at all — they're `MATCH ... WHERE ... GROUP BY / COUNT` queries that a native GSQL aggregation can answer directly, with the LLM only phrasing the result and attaching citations. This is likely the single strongest demonstrable use of graph structure for the 10%-weighted Graph Contribution criterion — stronger than using graph traversal merely to improve retrieval recall.

### Known discrepancies in the eval key (flag, don't silently "fix")

- **EQ32/EQ33 (GLP-1/obesity):** the eval key needs 13 companies to mention weight-loss/obesity language; a literal "GLP-1" keyword count across the corpus finds only 6. The eval set itself marks both with `‡` ("exhaustive keyword-sweep key; spot-check before final scoring") — i.e., the compiler already flagged this answer as less certain than the rest. **Unresolved as of this document** — needs the actual Item 1A text for the 13 named companies pulled and checked before building the risk-theme tag (see §13).
- **EQ37 (KPMG-audited Financials):** the answer key itself hedges — "+ Visa if classed Financials" — signaling that even ground truth has some sector-classification ambiguity at the edges.

### Question-to-capability mapping

See §9 for the full table. High-level takeaway: Tier A is unlocked by deterministic metadata + metric extraction alone; Tier B needs event extraction plus one-hop graph traversal; Tier C needs the entity graph (auditor, foundry, risk-theme, director edges) plus native aggregation; Tier D needs event dating and cross-filing temporal ordering.

---

## 6. Final Architecture

```text
SEC Filing (raw text)
      │
      ▼
Section / Form Parser        (form-aware: 10-K / 8-K / DEF 14A have different structure)
      │
      ▼
Deterministic Metadata Extraction   (cover block, dates, accession, registrant — regex/pattern, ~100% confidence)
      │
      ▼
Entity Extraction              (financial metrics via table-aware parsing; people/roles; auditor via guarded rule)
      │
      ▼
Event Extraction                (8-K Item + content classification → typed CorporateEvent)
      │
      ▼
Canonicalization                (known-alias mapping for metrics/auditors/roles; conservative person merge)
      │
      ▼
TigerGraph  (graph store + vector index — both, per contest requirement)
      │
      ▼
GraphRAG Retrieval   (query classification → native GSQL aggregation | graph traversal | hybrid vector+graph)
      │
      ▼
Gemini (generation)
```

Both **Traditional RAG** and **LLM-only** pipelines run in parallel as required baselines — see §10.

---

## 7. Graph Schema

### Vertices

`Company`, `Filing`, `Section`, `SourceSpan`, `Period`, `MetricDefinition`, `MetricObservation`, `Person`, `PersonCandidate`, `Role`, `RoleAssignment`, `Board`, `Committee`, `AuditFirm`, `AuditEngagement`, `CorporateEvent` (subtyped — see below), `EventParty`, `RiskDisclosure`, `RiskTheme`, `Technology`, `Product`, `Segment`, `Organization`, `Location`, `Sector`.

> Note: this is deliberately more granular than a flat `Metric`/`Event`/`Topic` schema. The `MetricDefinition` (canonical, stable) vs. `MetricObservation` (a reported value, with raw label preserved) split, and the typed `CorporateEvent` subtypes below, are load-bearing — they're what make canonicalization guarded rather than lossy (see Discovery 5, and the Gross Margin ≠ Gross Profit caution from Phase 4).

### CorporateEvent subtypes
`EarningsRelease`, `OfficerAppointmentOrDeparture`, `DirectorChange`, `DividendDeclaration`, `ShareRepurchase`, `AcquisitionOrMerger`, `JointVentureOrPartnership`, `Restructuring`, `LegalOrRegulatoryMatter`, `MaterialAgreement`, `ShareholderVote` *(added — Discovery 3)*, `OtherMaterialDisclosure` (explicit catch-all; never force a fit).

### Essential edges

`Company-FILED→Filing`, `Filing-HAS_SECTION→Section`, `Section-HAS_EVIDENCE→SourceSpan`, `Company-REPORTED→MetricObservation`, `MetricObservation-OF_METRIC→MetricDefinition`, `MetricObservation-FOR_PERIOD→Period`, `Person-HELD→RoleAssignment-AT→Company`, `RoleAssignment-SERVED_ON→Board/Committee`, `Company-AUDITED_BY→AuditEngagement→AuditFirm`, `Company-DISCLOSED→CorporateEvent`, `EventParty-PARTICIPATED_IN→CorporateEvent`, `Company-DISCLOSED_RISK→RiskDisclosure-HAS_THEME→RiskTheme`, `Company-IN_SECTOR→Sector`.

Every asserted edge carries: `filing_accession`, `source_span_id`, `extraction_method`, `confidence`, `reported_at`, and valid-time fields where relevant. **Non-negotiable** — this is what citations and temporal questions (Tier D) depend on.

### IDs / keys

- `Company` = `ticker`
- `Filing` = `accession` (never `ticker|form|date` — see Discovery 5's manifest-duplicate finding)
- `Chunk` = `accession|section|ordinal`
- `Person` = normalized name + company + proxy year (within-company); cross-company merge only with two corroborators
- `MetricObservation` = `ticker|metric|period|units|scope`

---

## 8. Extraction Rules

| ID | Rule | Confidence |
|---|---|---|
| RULE_001 | Cover metadata (registrant name, dates, accession, CIK-adjacent IDs) via regex on the labeled cover block | ~100% |
| RULE_002 | `Filing.filed_at` ≠ `Filing.event_date` for 8-Ks — parse both, never assume they're equal | ~100% |
| RULE_003 | Signature-block name+title → `RoleAssignment` snapshot only, never an event, unless independently corroborated by event content | High |
| RULE_004 | Auditor identity: audit-opinion signature block > DEF14A ratification proposal / corroborating 8-K vote result > audit-committee statement > `unknown`. Never a bare text mention. | Medium–High |
| RULE_005 | 8-K event type = f(Item number, content) — Item narrows candidates, content decides; a single filing may carry multiple Items for one meeting/event | Medium |
| RULE_006 | Metric canonicalization is context-scoped: identify statement family/table header first, map label only within that context. Never map Gross Margin↔Gross Profit or Free Cash Flow↔Operating Cash Flow. | Medium |
| RULE_007 | Person name normalization strips honorifics, suffixes (Jr./III), and inline credentials (M.D./Ph.D.) into separate fields before comparison | High (within-company) |
| RULE_008 | Cross-company person merge requires two independent corroborators; otherwise keep as separate `PersonCandidate` | Explicit low-confidence path required |
| RULE_009 | Segment-level metrics carry an `as_reported_in` tag; do not assume cross-year comparability without checking for restatement language | Medium |
| RULE_010 | Narrative topical mention counts (e.g., "dividend" appearing in MD&A prose) are never substituted for discrete, dated `CorporateEvent` records | High (as a guardrail) |
| RULE_011 | "Role mentioned, name absent" is a valid terminal state — extract as `unknown`, never guess | ~100% |
| RULE_012 | Real-world name recognition/pretrained knowledge must never influence entity resolution in this synthetic, future-dated corpus | ~100% (as a guardrail) |

*(Extend this table as extraction is implemented and new edge cases surface — this is a living list, not a final one.)*

---

## 9. Evaluation Coverage

Which extraction capability unlocks which questions:

| Capability | Unlocks |
|---|---|
| Deterministic cover metadata (RULE_001–002) | EQ06 and any date/registrant-identity question |
| Table-aware metric extraction + canonicalization (RULE_006) | EQ01–EQ05, EQ13–EQ15 (revenue/net-income comparisons) |
| Guarded auditor extraction (RULE_004) | EQ10, EQ12, EQ17, EQ18, EQ25, EQ36–EQ41, EQ44 |
| Foundry entity tagging (closed, ~5-term set) | EQ23, EQ26, EQ38, EQ39 |
| 8-K event extraction, content-classified (RULE_005) | EQ09, EQ11, EQ16, EQ21, EQ22, EQ24, EQ34, EQ35, EQ45–EQ50 |
| Person/board resolution (RULE_007–008) | EQ27, EQ28, EQ29 |
| Risk-theme tagging (climate, GLP-1) | EQ30–EQ33 *(GLP-1 tag is currently the least certain — see §13)* |
| Native GSQL aggregation over the entity graph | EQ25, EQ30–EQ33, EQ44 (all Tier C set/count questions) |
| Cross-filing temporal ordering | EQ45, EQ46, EQ47 |

This table should be kept up to date as extraction modules are built — it's a direct, auditable link from implementation work to eval-set coverage, which is exactly the kind of traceability the rubric rewards.

---

## 10. Retrieval Design

### Traditional RAG (baseline)
```
Question → Embedding search (same embedding model as GraphRAG) → Top-k chunks → Gemini
```
Must be a **competent, good-faith baseline** — sensible chunking (form/section-aware, per §11 of the original exploration report's chunking recommendations), sensible top-k. Not deliberately under- or over-retrieved.

### GraphRAG
```
Question → Query-intent classification → {
    Fact lookup / metric        → Graph property lookup / MetricObservation traversal
    Set intersection / count    → Native GSQL aggregation (MATCH/WHERE/GROUP BY/COUNT)
    Entity lookup (person/role) → Temporal RoleAssignment traversal, filtered by date
    Temporal sequence           → Event traversal ordered by date
    Narrative / risk / strategy → Hybrid: graph-filtered candidate set + vector similarity + rerank
} → cited SourceSpans → Gemini
```

**Key principle:** query-intent classification should be derived from the question's own structure and phrasing at build time — **not** from the eval set's own Tier A/B/C/D labels, to avoid any appearance of tuning against the held-out set (see §13).

### Why this should beat Traditional RAG on tokens without losing accuracy
Aggregation and set-intersection questions (Tier C, 20 of 50 questions) are exactly the case where vector-only RAG must retrieve and have the LLM reason over a large, noisy chunk set, while a native graph query returns the exact answer set directly — the clearest, most defensible demonstration of graph contribution available in this dataset.

---

## 11. Planned Enhancements

### Phase 1 (Required for a valid, scored submission)
- Graph construction (schema in §7, rules in §8) over a meaningful subset, then full 100 companies
- Traditional RAG and LLM-only baselines, running end to end
- GraphRAG retrieval with query-intent routing
- Full per-question, per-pipeline token/answer/citation logging from the first line of code (retrofitting this later is high-risk)
- Evaluation harness: BERTScore (pinned config), strict pass/fail, graded judge (blind, different model from generator), 3 repeated runs
- Dashboard comparing all three pipelines

### Phase 2 (Enhancements — only after Phase 1 is fully working and evaluated)

| Enhancement | Description | Expected benefit | Complexity | Required? |
|---|---|---|---|---|
| Maximum Marginal Relevance (MMR) | Diversity-aware reranking of retrieved chunks | Reduces redundant evidence in hybrid-retrieval questions | Low | No — nice-to-have for evidence-quality score |
| Semantic deduplication | Collapse near-duplicate boilerplate before it reaches context | Token savings on repeated safe-harbor / cover language | Low–Medium | No, but cheap and likely worthwhile |
| Context compression / summarization | Shrink retrieved evidence before generation | Further token reduction | Medium | No — only if Phase 1 token numbers need it |
| Personalized PageRank (PPR) | Graph-native relevance propagation for fuzzy entity queries | Possible improvement on ambiguous multi-hop questions | High | No — unproven need; evaluate only if BFS/direct traversal underperforms |
| Adaptive retrieval routing | Already partially in Phase 1's query classifier; could be extended/learned | Marginal, given Phase 1's rule-based router should already cover the 4 tiers | Medium | No |
| Corpus discovery pass (frequency/TF-IDF over risk/metric vocabulary) | Documents §3/§4's already-completed discovery work; optionally extend with one lightweight automated pass | Mostly an architecture-story artifact, not a functional gap | Low | No — 1–2 hours max if time allows, see Phase 5 decision in §4 |

**Explicit recommendation:** do not start Phase 2 work until Phase 1 has produced real per-question results across all 50 questions. A large, sophisticated Phase 2 optimization layered onto an unmeasured or partially-broken Phase 1 pipeline is a worse outcome than a simple, fully-measured Phase 1.

---

## 12. Team Responsibilities

*(Placeholder — fill in with actual owners. Not populated here since I don't have authoritative information on current team assignments; the structure below is a starting template only.)*

| Area | Owner |
|---|---|
| Architecture, SEC extraction rules, graph schema | ? |
| TigerGraph Savanna setup, GSQL queries | ? |
| GraphRAG retrieval logic, query routing | ? |
| Traditional RAG baseline, embedding setup | ? |
| Evaluation harness, token logging, dashboard | ? |
| Documentation, methodology writeup, ablations | ? |

---

## 13. Open Questions

Ranked by urgency:

1. **Is the published 50-question set (v3, with answer keys) the actual held-out evaluation set, or a dev/tuning set?** Highest priority — resolve with organizers immediately. If it's held-out, tuning against it (including designing the query router around its own tier labels) risks violating the brief's dev/test isolation rule. Build a separate, disjoint hand-written dev set in parallel rather than waiting on a reply.
2. **Is the local `sp100_dataset` corpus the official TigerGraph-provided dataset, or a practice/independently-assembled one?** Worth a quick confirming question alongside #1 — costly to discover late that ingestion targeted the wrong corpus.
3. **What's the real GLP-1/obesity language across the 13 companies EQ32/33 expect, versus the 6 a literal keyword count finds?** The eval set itself flags this pair as unverified (`‡`). Needs the actual Item 1A text pulled and checked before the risk-theme tag is built.
4. **Should PPR replace direct graph traversal for any query class?** No evidence yet that BFS/direct traversal is insufficient — defer until Phase 1 data says otherwise.
5. **Should financial tables be chunked, or kept atomic?** Current recommendation (per original exploration report and CAT's segment-table complexity) is atomic — a table plus its caption/units should not be split across chunks.
6. **Should graph edges cache traversal results for repeated query patterns?** Performance question, not correctness — defer to Phase 1 measurement.
7. **Best graph-vector fusion strategy for the "narrative/risk" query class?** Only relevant once Phase 1 hybrid retrieval is working and measured.

---

## 14. Risks

Ranked by likely impact:

1. **Schedule risk.** ~8 days from this document's writing to the July 26 delivery date, against a deliverable list including a live Savanna instance, three working pipelines, a dashboard, ablations, docs, and a presentation. This is the dominant risk — not architecture quality.
2. **Dev/test contamination.** See Open Question 1. Could invalidate the token-efficiency claim entirely if not resolved before tuning begins.
3. **Person cross-company resolution errors** (false merges or false splits) directly affect strict-pass rate on EQ27–29 and similar. Mitigated by the conservative two-corroborator rule (RULE_008), but the confidence-threshold policy itself needs to be decided and tested, not left implicit.
4. **Table-parsing failures that produce wrong numbers silently** (rather than failing loudly) are worse than a missing extraction — CAT's segment table is close to worst-case complexity in this corpus and should be used as an explicit test case before extraction rules are frozen.
5. **GLP-1/obesity answer-key uncertainty** (Open Question 3) — could cost points on EQ32/33 regardless of extraction quality, since the ground truth itself may be incomplete.
6. **Retrofitting token accounting late.** If the LLM-call wrapper isn't built first, reconstructing accurate per-call token counts after the fact is expensive and error-prone, and this is 30% of the score.
7. **Over-investment in Phase 2 enhancements before Phase 1 is measured** — a design-quality risk, not a data risk, but a real one given how much of this project's time so far has gone into architecture discussion relative to code.

---

## 15. Implementation Roadmap

Given the actual time remaining, sprints should be short and outcome-focused rather than calendar-blocked by component:

**Sprint 1 — Foundations (do first, in parallel):**
- Token-logging LLM wrapper (every call, from day one)
- TigerGraph Savanna instance stood up, schema loaded, on a 5–10 company subset
- LLM-only and Traditional RAG baselines running end to end on all 50 questions (even with weak extraction — these need to exist early as the comparison floor)

**Sprint 2 — Deterministic extraction (highest ROI, lowest risk):**
- RULE_001–002 (cover metadata), RULE_004 (auditor), foundry tagging
- Unlocks EQ06, EQ10, EQ12, EQ17, EQ18, EQ23, EQ25, EQ26, EQ36–EQ41, EQ44 per §9

**Sprint 3 — Metric and event extraction:**
- Table-aware metric parsing + canonicalization (RULE_006)
- 8-K event extraction, content-classified (RULE_005), including the new `ShareholderVote` type
- Unlocks EQ01–05, EQ09, EQ11, EQ13–16, EQ21, EQ22, EQ24, EQ34, EQ35, EQ45–50

**Sprint 4 — Person resolution and risk themes:**
- Board/director extraction and cross-company merge policy (RULE_007–008)
- Risk-theme tagging, with the GLP-1 discrepancy (Open Question 3) resolved first
- Unlocks EQ27–33

**Sprint 5 — GraphRAG retrieval, query router, and full evaluation:**
- Query-intent classifier (built from question structure, not eval-set tier labels)
- Native GSQL aggregation path for Tier C questions
- Full 3× repeated evaluation run, dashboard, ablations

**Sprint 6 (if time remains) — Phase 2 enhancements, per §11, only after Sprint 5's results exist.**

---

## 16. Lessons Learned

- **The dataset is far more structured than an "SEC filings = unstructured text" assumption would suggest.** SEC form conventions (cover blocks, Item numbers, signature blocks) are dependable enough to extract deterministically for a large share of the content.
- **Deterministic extraction outperforms LLM extraction for most structured fields** — and is dramatically cheaper and more auditable. LLM extraction should be reserved for genuinely ambiguous residue.
- **Raw substring/keyword counts systematically overstate discrete facts.** Every rule-based mention count checked against real filing text (auditor mentions, dividend/acquisition mentions, GLP-1 mentions) turned out to need guarding, positional context, or a narrower definition than a naive scan provides. Treat any purely statistical corpus summary as a hypothesis to verify against raw text, not a fact to build on directly.
- **Evaluation questions should drive extraction priority, but the router itself must not be built from the eval set's own labels** — a subtle but important line, given the contest's explicit dev/test isolation rule.
- **Cross-document relationships (auditor-vote corroboration, event-to-metric bridges, board membership across companies) are where GraphRAG's advantage over plain RAG is most demonstrable** — particularly Tier C set-intersection/aggregation questions, which are closer to database queries than retrieval problems.
- **Watch for "agreement bias" in iterative review.** Across this project's review cycles, several turns opened with blanket agreement and then restated existing decisions as new discoveries; one turn fabricated a callback to something never actually said. Genuine review should surface disagreement and correction, not just validation — and should be checked against source material, not taken at face value.
- **Grounding claims in actual raw filing text repeatedly caught things that pure architectural discussion missed** (auditor noise, the Item 5.02/5.07 overlap, segment restatement, the GLP-1 discrepancy). Several more raw-text spot checks (a DEF14A director table, a 10-K risk-factor section) remain worth doing before extraction rules are fully frozen.
- **Architecture discussion is now well past the point of diminishing returns relative to the time remaining.** The design has been directionally stable for several review cycles; the dominant remaining risk is schedule and execution, not design quality.

---

## Changelog

- v1.0 — Initial consolidation of all research/critique phases into a single reference document.
- v1.1 — Added §1.4 Architecture Principles. Each principle is a compression of a decision already argued elsewhere in this document (cross-referenced inline); nothing new was introduced, and no other section changed. Document remains frozen for implementation purposes.
