# GraphRAG for SEC Filings — Implementation Runbook

**Status:** Design frozen at v1.0 (see design doc). This file is the execution layer.
**Purpose:** A step-by-step build plan an engineering agent can follow without re-deriving architecture decisions. If you are an agent picking this up cold, read §0 and §1, then start at §4 Sprint 1, Step 1.
**Rule:** Do not redesign schema, ontology, retrieval strategy, or pipeline architecture while executing this document. Those are closed. This document only produces code, data, and validated artifacts.
**Deadline:** Round 3 delivery July 26, 2026.

---

## 0. How to use this document

- Work top to bottom. Each Sprint has Steps. Each Step has an **Input**, **Action**, **Output**, and **Done when** condition. Do not move to the next Step until "Done when" is satisfied.
- If implementation surfaces a real issue (not a preference), log it under §7 (Open Issues) and keep moving — don't stop to write a new design doc.
- Every discovery below came from actually reading corpus text, not from statistics or assumption. Treat §2 as ground truth about the data; don't re-verify it, build against it.
- Grading weights (for prioritization when time is short): Answer Quality 40%, Token Efficiency 30%, Evidence/Citation 15%, Graph Contribution/Rigor 10%, Generalizability 5%. When in doubt, spend time on a working, measured pipeline over a more elegant unmeasured one.

---

## 1. Locked context (do not re-derive)

### 1.1 Corpus facts
- 100 companies, 400 filings total: 100×10-K, 200×8-K, 100×DEF 14A. Zero 10-Q. Every issuer has exactly 4 filings.
- `accession` is the only safe primary key for `Filing` — manifest has 3 duplicate `(ticker, form, filing_date)` keys but 0 duplicate accessions.
- The corpus is semi-structured, not free text: cover blocks, SEC Item numbers, and signature blocks are dependable and should be extracted deterministically. Only narrative content (risk prose, MD&A, person-name resolution) needs LLM extraction.

### 1.2 Non-negotiable extraction rules (RULE_001–012)
| ID | Rule |
|---|---|
| RULE_001 | Cover metadata via regex on the labeled cover block (~100% confidence) |
| RULE_002 | `filed_at` ≠ `event_date` for 8-Ks — parse both separately |
| RULE_003 | Signature-block name+title → `RoleAssignment` snapshot only, never an event |
| RULE_004 | Auditor precedence: opinion signature block > DEF14A ratification/corroborating 8-K vote > audit-committee statement > `unknown`. Never a bare text mention. |
| RULE_005 | 8-K event type = f(Item number, content) — Item narrows, content decides; one filing can carry multiple Items for one event, or multiple distinct events |
| RULE_006 | Metric canonicalization is context-scoped (statement family/table header first). Never map Gross Margin↔Gross Profit or Free Cash Flow↔Operating Cash Flow |
| RULE_007 | Person name normalization strips honorifics/suffixes/credentials into separate fields |
| RULE_008 | Cross-company person merge requires two independent corroborators — never merge on name-string match alone |
| RULE_009 | Segment metrics carry `as_reported_in` — no assumed cross-year comparability |
| RULE_010 | Narrative mention counts are never substituted for discrete `CorporateEvent` records |
| RULE_011 | "Role mentioned, name absent" is a valid terminal state — extract as `unknown`, never guess |
| RULE_012 | Pretrained/real-world name knowledge must never influence entity resolution (corpus is synthetic) |

### 1.3 Graph schema (frozen)
**Vertices:** `Company`, `Filing`, `Section`, `SourceSpan`, `Period`, `MetricDefinition`, `MetricObservation`, `Person`, `PersonCandidate`, `Role`, `RoleAssignment`, `Board`, `Committee`, `AuditFirm`, `AuditEngagement`, `CorporateEvent` (subtyped), `EventParty`, `RiskDisclosure`, `RiskTheme`, `Technology`, `Product`, `Segment`, `Organization`, `Location`, `Sector`.

**CorporateEvent subtypes:** `EarningsRelease`, `OfficerAppointmentOrDeparture`, `DirectorChange`, `DividendDeclaration`, `ShareRepurchase`, `AcquisitionOrMerger`, `JointVentureOrPartnership`, `Restructuring`, `LegalOrRegulatoryMatter`, `MaterialAgreement`, `ShareholderVote`, `OtherMaterialDisclosure` (catch-all).

**Keys:** `Company`=ticker · `Filing`=accession · `Chunk`=accession\|section\|ordinal · `Person`=normalized name+company+proxy year (within-company) · `MetricObservation`=ticker\|metric\|period\|units\|scope.

Every edge carries: `filing_accession`, `source_span_id`, `extraction_method`, `confidence`, `reported_at`, valid-time fields where relevant. Non-negotiable.

### 1.4 Eval set caveats — use for coverage validation, never for tuning
- Query-intent classification must be built from question **structure/phrasing**, not from the eval set's own Tier A/B/C/D labels (dev/test isolation).
- EQ32/EQ33 (GLP-1): eval key itself flags `‡` as unverified — needs Item 1A text pulled for the 13 named companies before building the risk-theme tag.
- EQ37: KPMG/Financials answer key hedges on Visa's sector classification.
- **EQ17/EQ45 (AMGN CFO transition):** cited source "AMGN 8-K 2026-05-19" does not contain CFO transition content in the copy on file — that filing is an Item 5.07 annual-meeting-vote-results 8-K only. Treat this as unresolved; do not build extraction logic against the wrong filing. See §7.

---

## 2. Real corpus edge cases already found (build tests around these, don't wait to discover them)

| Source | Edge case | Why it matters |
|---|---|---|
| AMGN 8-K 2026-05-19 | Contains only Item 5.07 vote results (directors, say-on-pay, EY ratification, stockholder proposal). No CFO transition content. | Eval-key citation mismatch — flag, don't build against it (§1.4) |
| ConocoPhillips 8-K 2026-05-12 | Director William H. McRaven's "Abstentions" column reads 11,985,168 — a value copy-pasted from the row above (Kathleen McGinty's "Against" column), ~1000x every neighboring abstain count | Silent wrong-number extraction risk; needs an automated arithmetic check, not eyeballing |
| Cisco 8-K 2026-05-13 | One filing carries two distinct events: Item 2.02 (earnings release) AND Item 2.05 (restructuring, $1B pre-tax charges) | Section/event splitter must detect ALL Item headers, not just the first |
| Disney DEF14A | Amy L. Chang is a current director at Disney AND Procter & Gamble, formerly at Cisco — stated in one bio | Real fixture for RULE_008: one-source mention is NOT enough to cross-company merge; needs P&G's own DEF14A to corroborate |
| Disney DEF14A | Very large document (100+ pages of content) | Stress test for Traditional RAG chunking before hitting it at scale |
| Disney DEF14A Annex A | Adjusted EPS vs. GAAP diluted EPS; Total Segment Operating Income vs. income before taxes, fully reconciled | Confirms RULE_006 non-GAAP guard is warranted, not over-engineered |
| CAT 10-K | 24-term issuer glossary defining company-specific metric labels | High-confidence per-issuer definitions source (Discovery 9) |
| CVS 8-K | Item 5.02(e) + Item 5.07 in one filing, single underlying event (annual meeting) | Item number alone does not determine event type (Discovery 3) |

---

## 3. Project structure

```
project/
│
├── parser/
│   ├── form_parser.py         # form-type detection + section splitting
│   └── manifest.py            # manifest load + accession/ticker reconciliation
│
├── extractors/
│   ├── metadata.py            # RULE_001, RULE_002
│   ├── metrics.py             # RULE_006, table-aware parsing
│   ├── people.py              # RULE_007, RULE_008, RULE_011, RULE_012
│   ├── auditors.py            # RULE_004
│   ├── events.py              # RULE_003, RULE_005, RULE_010, multi-event 8-Ks
│   └── risks.py                # RiskDisclosure + RiskTheme tagging
│
├── canonicalization/
│   ├── metric_aliases.py      # alias table, append-only
│   └── auditor_aliases.py     # normalization keys
│
├── validation/
│   ├── vote_arithmetic.py     # Item 5.07 quorum/sum checks
│   ├── accession_checks.py    # uniqueness, manifest reconciliation
│   ├── event_dedup.py         # multi-Item / multi-event detection
│   └── report.py              # aggregate validation report generator
│
├── graph_loader/
├── retrieval/
├── evaluation/
├── prompts/
├── pipelines/
├── artifacts/                  # per-filing intermediate output chain (§3a.1), gitignored
│   └── <accession>/
└── fixtures/                   # hand-verified expected outputs for pilot companies (§3a.6)
    ├── AMGN/ CAT/ CSCO/ COP/ DIS/
```

---

## 3a. Engineering conventions (apply from Sprint 1 onward)

These aren't new architecture — they're how every Step in Sprints 1–3 should actually be built and checked. Adopt them now so debugging doesn't get harder as filings scale from 5 → 100.

### 3a.1 Per-filing artifact chain
Each filing produces a numbered, inspectable chain on disk, not just a final JSON blob:

```
raw.txt → parsed.json (sections) → metadata.json → entities.json → graph.csv
```

Write each intermediate artifact to `artifacts/<accession>/`. When something looks wrong downstream, you should be able to open the intermediate file and see exactly which stage introduced the error, instead of re-running the whole extractor with print statements.

### 3a.2 Logging
Every extractor call logs, at minimum: `file/accession`, `rule_id` applied (e.g. RULE_004), `confidence`, `evidence` (source span or short excerpt), `duration`, `error` (if any). Plain structured logs (JSON lines) are enough — no logging framework needed for a project this size.

### 3a.3 Failure policy — scoped per filing, not global
A bad filing should stop *that filing's* processing and get logged, not halt the 400-filing run. Distinguish:

| Condition | Behavior |
|---|---|
| Cover metadata missing/unparseable for a filing | Stop processing **that filing**, log it, continue the batch |
| Person name present but no name text found | Extract as `unknown` (RULE_011) — not a failure |
| Metric label has no canonical alias | Store as `IssuerDefinedMetric` with `raw_label` — not a failure |
| Vote arithmetic doesn't sum to quorum | Flag the filing for manual review, do not silently ingest the value |
| Graph load rejects a batch | Stop the load, do not partially commit |

The distinction that matters: extraction-level ambiguity (person/metric/role unknown) is an expected terminal state, not an error — only structural failures (unparseable cover block, failed graph commit) should stop anything.

### 3a.4 Alias tables are frozen, versioned data — not code
`canonicalization/metric_aliases.yml`, `auditor_aliases.yml`, `role_aliases.yml`, `risk_aliases.yml`. New aliases are appended to the YAML, never hardcoded into extractor logic. Keep a one-line changelog comment at the top of each file (`# added: <alias> — <date> — <filing that surfaced it>`) — no heavier versioning system needed for ~100 companies.

### 3a.5 Acceptance tests per extractor
Each extractor module gets golden test cases in the form:
```
Input (specific filing/section) → Extraction → Expected output → PASS/FAIL
```
Example: `AMGN 8-K 2026-05-19 → extract_events() → event_type == "ShareholderVote" → PASS`.

Aim for 3–5 cases per module **where the pilot set actually supports it**. Don't manufacture synthetic filings to hit that number — some modules (foundry tagging, risk-theme tagging) have zero real cases in this 5-company pilot because none of AMGN/CAT/CSCO/COP/DIS mention foundries or GLP-1 drugs. Mark those modules `coverage deferred to 100-company scale-up` in the test file rather than padding with fabricated fixtures.

### 3a.6 Fixtures folder
```
fixtures/
├── AMGN/expected_metadata.json, expected_events.json, expected_auditor.json
├── CAT/expected_metadata.json, expected_metrics.json, expected_glossary.json
├── CSCO/expected_events.json   ← must show 2 events, not 1
├── COP/expected_vote_arithmetic.json  ← must flag the McRaven anomaly
└── DIS/expected_people.json    ← must show Amy Chang's 3-company history
```
Hand-build these expected outputs once, by reading the source filings, before writing the extractors that should reproduce them. This turns Sprint 1 Step 6 (manual validation) into an automated regression test you can re-run after every code change — build fixtures only for the 5 pilot companies now; don't attempt this for the full 100 until after scale-up.

---

## 4. Sprint 1 — Pilot ingestion (today, 2–3 hours)

### Step 1 — Freeze design
**Action:** Confirm design doc is v1.0. No edits except logged real issues (§7).
**Done when:** Design doc has no open TODOs blocking implementation.

### Step 2 — Scaffold project structure
**Action:** Create the directory tree in §3. Empty files with docstrings stating which RULE_### each module implements.
**Done when:** `tree project/` matches §3.

### Step 3 — Select the 5 pilot companies (not arbitrary — chosen to hit known edge cases)

| Ticker | Forces you to build/test |
|---|---|
| AMGN | Citation-mismatch handling; Item 5.07 vote parsing |
| CAT | Glossary extraction (Discovery 9); segment restatement (`as_reported_in`, RULE_009) |
| CSCO | Multi-event single-8-K splitting (Item 2.02 + Item 2.05) |
| COP | Vote-table arithmetic validation (the McRaven anomaly) |
| DIS | Large-document chunking stress test; cross-company person resolution (RULE_008) |

**Done when:** All 4 filings (10-K, 2×8-K, DEF14A) for these 5 tickers are located on disk and readable, and `fixtures/<TICKER>/expected_*.json` files exist with hand-verified values pulled directly from the source text (see §3a.6).

### Step 4 — Implement the parser (`parser/form_parser.py`)
**Action:** For each filing: read file → identify form type → split into sections → extract cover page block → store section text with ordinals. Nothing else yet — no entity extraction.
```
Read file → Identify form → Split into sections → Extract cover page → Store section text
```
Critical: the section splitter must detect **every** SEC Item heading in an 8-K, not just the first (CSCO case).
**Done when:** Running the parser on all 20 pilot filings produces a section list per filing with no exceptions, and CSCO's 8-K shows two separate Item sections (2.02 and 2.05).

### Step 5 — Implement metadata extraction (`extractors/metadata.py`)
**Action:** Implement RULE_001 and RULE_002. Extract: company, form, accession, filing date, event date (8-K only), fiscal year end, registrant name.
**Output shape:**
```json
{
  "ticker": "MSFT",
  "form": "10-K",
  "accession": "...",
  "filing_date": "...",
  "fiscal_year_end": "...",
  "sections": [...]
}
```
**Done when:** JSON output exists for all 20 pilot filings.

### Step 6 — Manual + automated validation (do not skip)
**Action:**
- Manually open 2–3 filings and check every extracted metadata field against source text.
- Run the automated checks now, not later (this is the change from the original plan — see reviewer feedback):
  - **Vote arithmetic** (`validation/vote_arithmetic.py`): for every Item 5.07 section, sum For+Against+Abstain+Broker-Non-Votes per proposal and compare to stated quorum/shares outstanding. Flag any per-director row whose value is a statistical outlier vs. its neighbors (catches the COP/McRaven case).
  - **Accession uniqueness + manifest reconciliation** (`validation/accession_checks.py`).
  - **Multi-Item / multi-event detection** (`validation/event_dedup.py`): confirm CSCO's 8-K yields 2 candidate events, not 1.
- Fix the parser based on findings. Re-run until clean.
**Done when:** All 20 pilot filings pass the validation suite with zero unresolved arithmetic flags (the McRaven anomaly should be caught and logged, not silently ingested), and metadata spot-checks match source text exactly.

---

## 5. Sprint 2 — Deterministic extraction (highest ROI, lowest risk)

### Step 1 — Auditor extraction (`extractors/auditors.py`)
**Action:** Implement RULE_004 precedence order. Test specifically against COP and AMGN's Item 5.07 auditor-ratification results as a corroborating source (both show EY ratification votes in this pilot set).
**Done when:** Auditor extracted correctly for all 5 pilot companies with source-span provenance, and the CVS-style dual-source corroboration path (DEF14A + 8-K vote) is exercised at least once.

### Step 2 — Foundry / closed-set entity tagging
**Action:** Not present in the 5-company pilot (no semiconductor names) — implement the mechanism generically, defer testing to full-corpus scale-up.

### Step 3 — Manifest reconciliation module (`parser/manifest.py`)
**Action:** Cross-check manifest `(ticker, accession, form, filing_date)` against cover-page-extracted values for all pilot filings. Surface the 3 known duplicate-key rows from the full manifest as a warning, not a failure (they resolve on accession, which is the real key).
**Done when:** Reconciliation report runs clean on pilot set.

---

## 6. Sprint 3 — Metric and event extraction

### Step 1 — Table-aware metric parsing (`extractors/metrics.py`)
**Action:** Implement RULE_006. Use CAT's 10-K as the primary test case — it has both the 24-term glossary (Discovery 9) and the segment restatement note (RULE_009). Extract the glossary as a first-class per-issuer definitions table.
**Done when:** CAT's issuer-specific labels resolve via the glossary before falling back to cross-company canonical mapping; segment observations carry `as_reported_in`.

### Step 2 — 8-K event extraction, content-classified (`extractors/events.py`)
**Action:** Implement RULE_003, RULE_005, RULE_010. Test against:
- CSCO (two distinct events, one filing)
- AMGN and COP (Item 5.07 → `ShareholderVote` event type, not `OfficerAppointmentOrDeparture`)
- Signature blocks (Cisco's Mark Patterson, CFO signature) must populate `RoleAssignment` only, never spawn an event
**Done when:** Event extraction on all 5 pilot companies' 8-Ks produces the correct event count and type per filing, with signature-block names never appearing as event-triggering entities.

---

## 7. Open issues to track (log here, don't let these block Sprint 1–3 unless noted)

- [ ] **[BLOCKING for EQ17/EQ45]** Verify AMGN CFO-transition citation — locate the correct source filing/date, or flag the eval key as erroneous. Do not encode extraction logic against the wrong filing.
- [ ] Is the published 50-question set the actual held-out eval set, or dev/tuning? Ask organizers — still unresolved per design doc §13.
- [ ] Is `sp100_dataset` the official corpus? Confirm alongside the above.
- [ ] GLP-1/obesity risk-theme discrepancy (EQ32/33): pull actual Item 1A text for the 13 named companies before building the theme tag.
- [ ] EQ37 sector-classification ambiguity (Visa) — note in evaluation harness, don't silently resolve one way.

---

## 8. Validation suite — automated, not manual (applies at every scale)

Run this suite after every ingestion batch, not just the pilot:

| Check | What it catches |
|---|---|
| Vote arithmetic (Item 5.07) | Silent copy/OCR errors in vote tables (McRaven case) |
| Accession uniqueness | Duplicate/malformed accessions |
| Manifest reconciliation | Ticker/form/date mismatches vs. cover page |
| Multi-Item detection | Missed second event in a single 8-K (Cisco case) |
| Section ordering | Malformed/truncated filings |
| Duplicate event detection | Same event double-counted across Item headings (CVS case) |
| Segment sum-to-consolidated check | Table-parsing errors in complex segment tables (CAT case) |

A failure in any of these is a **stop-and-fix** signal for that filing, not a warning to note and move past — per the design doc's own risk #4 (silent wrong numbers are worse than missing extractions).

---

## 9. What NOT to do right now

- ❌ Read more GraphRAG/HippoRAG/TERAG/AdaGReS papers
- ❌ Implement PPR, MMR, or context compression
- ❌ Touch retrieval, Gemini, or GraphRAG query logic
- ❌ Modify the graph schema, ontology, or pipeline architecture
- ❌ Build the dashboard or presentation
- ❌ Tune extraction rules by reverse-engineering EQ01–EQ50 answer keys

---

## 10. Milestone checkpoint (end of Sprint 1–3)

You are ready to move to graph loading and GSQL validation only when all of these are true:

- [ ] Parser works cleanly on the 5 pilot companies (20 filings)
- [ ] Metadata extraction verified against source text, not just "ran without error"
- [ ] Vote arithmetic validator catches the COP anomaly and passes on clean filings
- [ ] CSCO's 8-K yields 2 distinct events
- [ ] Auditor extraction correct for all 5 companies with provenance
- [ ] CAT's glossary and segment restatement both handled correctly
- [ ] Manifest reconciliation runs clean
- [ ] AMGN citation issue is logged and NOT silently built around
- [ ] All fixtures in `fixtures/<TICKER>/` pass as automated regression tests, not just manually eyeballed once

Then: load pilot graph into TigerGraph → check vertex/edge counts, duplicates, missing values → write 5–10 GSQL queries (e.g., "Who audits Microsoft?" / "Companies audited by Deloitte" / "Microsoft fiscal year end" / "All Information Technology companies" / "Companies with dividend declaration events") → only after these return correct results, scale from 5 → 100 companies, then begin the three-pipeline build (LLM-only, Traditional RAG, GraphRAG).

---

## 11. Parallel workstream (non-blocking teammate track)

While ingestion is being built:
- Review the SEC question set for coverage gaps
- Build the metric alias table (append-only, per RULE_006 context-scoping)
- Build the risk-theme alias table, starting with the GLP-1 discrepancy (§7)
- Independently verify auditor extraction on sample filings (cross-check against §5 Step 1 output)
- Independently verify person-name variations against real bios (Disney's Amy Chang cross-company case is a ready-made test)

---

## 12. Sprints 4–8 (names only — do not expand into step tables until Sprint 3's milestone checklist is fully green)

- **Sprint 4 — Graph Loading:** load validated pilot entities into TigerGraph, confirm vertex/edge counts, then scale to 100 companies.
- **Sprint 5 — Traditional RAG:** embedding search baseline, same embedding model GraphRAG will use.
- **Sprint 6 — GraphRAG:** query-intent routing, native GSQL aggregation path, hybrid retrieval.
- **Sprint 7 — Evaluation:** full token/answer/citation logging, BERTScore, 3 repeated runs.
- **Sprint 8 — Optimizations (only if Sprint 7's numbers say it's needed):** MMR, dedup, compression — in that priority order, per the design doc's own risk assessment.

Each of these gets its own §-level step breakdown *when its turn comes*, written the same way Sprints 1–3 are written above — not before, and not as a new standalone document.

---

## Changelog
- v1.0 — Consolidated design doc (frozen)
- runbook v1.0 — Translates design into sequenced, testable engineering steps grounded in real corpus edge cases found during document review (AMGN citation gap, COP vote-table anomaly, CSCO multi-event 8-K, Disney scale/person-resolution cases).
- runbook v1.1 — Added engineering conventions (§3a): per-filing artifact chain, structured logging, per-filing (not global) failure policy, versioned alias YAMLs, acceptance-test format, fixtures folder. Added thin Sprint 4–8 stub (§12) to close the loop without pre-writing unexecuted sprints in detail.
