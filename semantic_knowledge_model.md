# SEC filing semantic knowledge model — analysis only

This document is a corpus-content analysis to guide a future ingestion design. It does not prescribe executable GraphRAG, GSQL, or ingestion code. Counts marked **filings** are document-presence counts (one filing counted once when it contains a signal), not counts of extracted facts. The source corpus has 100 10-Ks, 200 8-Ks, and 100 DEF 14As.

## Decisions that matter most

1. Treat a reported financial value as an observation with a metric, scope, units, period, accounting basis, and source table/row—not as a property of a Company.
2. Use the manifest for issuer/accession/sector metadata, and extract facts from the filing only with source-span provenance.
3. A text occurrence of an audit-firm name is not evidence of the current auditor. Extract the signer in the current independent-auditor opinion zone.
4. A person string is only a candidate person. The company/proxy/role/year context is the deterministic key; cross-company identity is an exception workflow.
5. Represent 8-K disclosures as dated events, with an SEC Item and event type. Keyword hits alone are not events.

## 1. Financial ontology and canonicalization

### What the 10-Ks show

The same economic concept is expressed differently in statement titles, statement rows, MD&A, notes, and non-GAAP discussion. A raw label must therefore be retained alongside a canonical metric. Examples from the corpus include the following observed label families (companies listed are all filing-level text matches, so a match can occur in narrative as well as a primary statement):

| Canonical metric | Observed aliases | 10-Ks containing alias | Companies using a distinctive alias | Ontology mapping |
| --- | --- | ---: | --- | --- |
| `Revenue` | Revenue; Net Revenue; Net Sales; Net Operating Revenues; Total Revenue(s); Total Revenues and Other Income; Operating Revenues | Revenue 100; Net Revenue 29; Net Sales 38; Net Operating Revenues 1; Total Revenues and Other Income 4; Operating Revenues 14 | Net Operating Revenues: KO. Total Revenues and Other Income: BRK.B, COP, CVX, XOM. Net Revenue includes ADBE, AMD, AVGO, BKNG, GOOGL, MA, NVDA, PYPL, UBER, V. Net Sales includes AAPL, AMZN, COST, GM, HD, MCD, PG, TGT, WMT. | `IncomeStatement.Revenue`, with `presentation_label`, `net_or_gross`, `includes_other_income`, `segment_scope` |
| `OperatingIncome` | Operating Income; Income from Operations | 68; 12 | Income from Operations: AVGO, CRM, GOOGL, ISRG, META, NOW, ORCL, PLTR, TMUS, TSLA, UBER, V | `IncomeStatement.OperatingIncome` |
| `NetIncome` | Net Income; Net Earnings; Net (Loss); Income (Loss) | 91; 27; 6; 78 | Net Earnings: ABBV, BA, BMY, GE, LMT, PG, UPS. Net (Loss): DHR, DUK, GILD, MO, TSLA, UPS | `IncomeStatement.NetIncome`, with `attributable_to`, `continuing_operations`, `loss_flag` |
| `GrossProfit` | Gross Profit; Gross Margin | 34; 36 | Gross Profit: AMD, AMZN, JNJ, NKE, TXN. Gross Margin is a percentage/rate, not interchangeable with Gross Profit. | `IncomeStatement.GrossProfit`; `FinancialRatio.GrossMargin` |
| `EarningsPerShare` | Basic earnings per share; Diluted earnings per share; EPS | 42; 62 | Basic/Diluted both appear broadly; preserve class and numerator attribution | `PerShareMetric.EPS`, dimensions `basic_or_diluted`, `continuing_ops`, `currency_per_share` |
| `Assets` | Total Assets | 99 | All but one filing text has this phrase | `BalanceSheet.TotalAssets` |
| `Equity` | Total Equity; Stockholders' Equity; Shareholders' Equity | 57; 25; 18 | Stockholders' Equity: ADBE, AMD, GOOGL, META, MSFT. Shareholders' Equity: GE, LLY, PG, WMT | `BalanceSheet.TotalEquity`, dimensions `parent_or_total`, `noncontrolling_interest` |
| `OperatingCashFlow` | Net Cash Provided by Operating Activities; Cash Flows from Operating Activities | 67; 63 | Both formulations recur across sectors | `CashFlow.OperatingCashFlow` |
| `FreeCashFlow` | Free Cash Flow | 37 | AMZN, AVGO, CSCO, GE, META, ORCL, UPS, WMT and others | `NonGAAP.FreeCashFlow`; never coerce it to GAAP operating cash flow |

Other reusable canonical families present in financial statements/notes: cost of revenue/sales, selling/general/administrative expense, R&D expense, interest income/expense, income-tax expense/benefit, depreciation/amortization, cash and cash equivalents, receivables, inventories, debt, leases, goodwill, intangible assets, liabilities, common stock, dividends, repurchases, segment revenue, and segment profit/loss.

### Reusable metric model

Use `MetricDefinition` (canonical, stable) and `MetricObservation` (a reported value) rather than a mapping table that destroys issuer language.

`MetricDefinition`: `metric_id`, canonical_name, statement_family, calculation_kind (`reported`, `derived`, `non_gaap`), default unit type, taxonomy aliases. `MetricObservation`: `company_id`, `metric_id`, raw_label, raw_value, normalized_value, currency, scale, period_start/end, instant_or_duration, comparative_period, statement/table/row, scope, GAAP/non-GAAP, consolidation/attribution, filing_id, source_span, confidence.

Canonicalization must be rule-and-context based: normalize case/punctuation, identify statement family and table header first, then map a label only within that context. Do **not** map `gross margin` to `gross profit`, `free cash flow` to operating cash flow, `income` to net income, or an insurer/bank revenue label to a generic value without a `business_model`/scope qualifier. Preserve unmapped labels as `IssuerDefinedMetric` candidates.

## 2. Deterministic metadata schema

| Field | Deterministic source/method | Reliability | Example | Graph property |
| --- | --- | --- | --- | --- |
| Ticker | manifest `ticker`; folder name is a reconciliation check | Very high | `AAPL` | `Company.ticker` |
| Company legal/display name | manifest `name`; cover “Exact name of Registrant” verifies | Very high | `Apple Inc.` | `Company.legal_name`, aliases |
| Form | manifest `form`; cover `FORM 10-K`, `FORM 8-K`, Schedule 14A verifies | Very high | `10-K` | `Filing.form_type` |
| Filing date | manifest `filing_date`; filename is a reconciliation check | Very high | `2025-10-31` | `Filing.filed_at` |
| Accession | manifest `accession` (unique in this corpus) | Very high | `0000320193-26-000011` | `Filing.accession` unique key |
| Source URL/local path/status | manifest | Very high | SEC URL / `AAPL/...txt` | `Filing.source_url`, provenance |
| Sector | manifest only; not a deterministic filing fact | High if manifest is authoritative | `Information Technology` | `Company.sector` plus source=`manifest` |
| Fiscal year end / period of report | cover phrase `For the fiscal year ended ...`; extract normalized date | High for 10-K; event date differs for 8-K | Apple: `September 27, 2025` | `Filing.period_end` |
| 8-K event date | cover `Date of Report (Date of earliest event reported)` | High, but distinct from filed_at | `April 30, 2026` | `Filing.event_date` |
| Auditor | current independent-auditor report/signature, not general mentions | Medium-high after structural localization | firm signature near Item 8 | `AuditEngagement.firm_id` |
| SEC Item/section | headings (e.g. Item 1A, 2.02, 5.02) | High where retained text has heading | `Item 2.02` | `Section.sec_item` |

No current extraction should invent CIK, exchange, SIC, fiscal-quarter, or metric units when they are not sourced to the relevant field/table.

## 3. Auditor normalization

The corpus contains many references to audit firms. Direct text presence alone is noisy: it finds Ernst & Young in 35 filings, Deloitte in 27, PricewaterhouseCoopers in 35, KPMG in 15, and also BDO, RSM, Crowe and Grant/other names in historical, subsidiary, acquired-business, service-provider, or comparative contexts. Therefore the statement “every company uses only the Big Four” is **not validated by a corpus-wide substring scan**.

Use this deterministic precedence order: (1) firm name in the signature block of the current `Report of Independent Registered Public Accounting Firm` that opines on the consolidated financial statements; (2) DEF 14A auditor-ratification proposal; (3) explicit audit-committee selection statement; (4) otherwise `unknown/review`. Do not pick a firm from a critical-audit-matter mention, a former auditor, or an acquired entity's report.

Normalization keys are lowercase, remove punctuation/LLP/LLC/PC, collapse whitespace and `&`/`and`:

| Canonical firm | Normalize these variants to it |
| --- | --- |
| `EY` | Ernst & Young; Ernst and Young; Ernst & Young LLP; EY; EY LLP |
| `Deloitte` | Deloitte & Touche; Deloitte and Touche; Deloitte LLP; Deloitte & Touche LLP |
| `PwC` | PricewaterhouseCoopers; Price Waterhouse Coopers; PricewaterhouseCoopers LLP; PwC; PwC LLP |
| `KPMG` | KPMG; KPMG LLP; KPMG LLP, PCAOB ID … |

Store `raw_name`, `canonical_firm`, `PCAOB_id` when present, opinion date, opinion subject (`financial_statements` vs `internal_control`), and source span. Unknown firms must remain first-class `AuditFirm` values—not be forced into Big Four.

## 4. Person and board-member canonicalization

All 100 DEF 14As contain director/governance material, but the corpus has no single safe raw-text layout for names. Common forms are board slate/profile headings, director biography headings, compensation/ownership tables, and signature/proxy-card repeats. The same person commonly appears as `First Last`, `First M. Last`, `First Middle Last`, `First Last, Ph.D.`, `Mr./Ms. Last`, and a surname-only table reference. A person may also be an executive officer, director nominee, committee member, or former director in the same document.

**Deterministic within-company canonical key:** normalized legal/proxy headline name + company ticker. Normalize Unicode apostrophes/whitespace, remove honorifics and professional suffixes (`Dr.`, `Ph.D.`, `Jr.`, `III`) into separate fields, preserve middle initials, and retain raw aliases. Resolve a shortened/surname-only form only when exactly one current board candidate in that company/proxy year matches it.

**Ambiguity cases:** shared surnames on one board; father/son suffixes; changed surnames; initials-only tables; a director with multiple employer titles; names in shareholder proposals; duplicated profile/table/ballot occurrences; and genuinely different people with the same normalized name across companies. Cross-company merging should be conservative: only merge with two independent corroborators (full name + biography/employer, or a stable external identifier); otherwise create separate `PersonCandidate` records. This makes entity resolution low difficulty within one issuer/year, medium within an issuer over time, and high across issuers.

Recommended person fields: `person_id`, `canonical_display_name`, `given_name`, `middle_name_or_initial`, `family_name`, suffix, raw_aliases, resolution_scope, confidence. Model tenure separately as a dated `RoleAssignment`; never infer that a biography mention proves present service.

## 5. 8-K event taxonomy

The 8-Ks show SEC Item headings are stronger primary signals than prose. Corpus presence: Item 2.02 in 48 filings, Item 5.02 in 42, and Item 8.01 in 41. The table below gives candidate-event evidence, not a claim that every keyword hit is a separate event.

| Event type | Structural/trigger phrases | Evidence filings | Graph vertex and essential properties |
| --- | --- | ---: | --- |
| `EarningsRelease` | Item 2.02; “Results of Operations and Financial Condition”; “earnings release” | 48; phrase 10 | `CorporateEvent`: event_date, period, earnings_release_exhibit, guidance flag, metrics, Item 2.02 |
| `OfficerAppointmentOrDeparture` | Item 5.02; appointed/named/elected; CEO/CFO/title; resignation/retirement/termination | 42 Item 5.02; appointed 20; CEO 15; CFO 43 | `OfficerChangeEvent`: person, old/new role, effective_date, reason, compensation arrangement |
| `DirectorChange` | Item 5.02; director appointed/elected/resigned; committee assignment | within Item 5.02 | `BoardChangeEvent`: person, board/committee, effective_date, reason |
| `DividendDeclaration` | “declared a … dividend”, record date, payment date | 16 keyword-bearing filings | `DividendEvent`: share class, amount/currency per share, declaration/record/payment dates |
| `ShareRepurchase` | repurchase program; authorization; buyback | 12 | `RepurchaseEvent`: authorization amount, expiry, program status, shares/amount repurchased |
| `AcquisitionOrMerger` | acquisition/acquire; merger; definitive agreement | acquisition 16; merger 5; agreement 9 | `TransactionEvent`: target/counterparty, transaction type, announced/closed date, consideration, status |
| `JointVentureOrPartnership` | joint venture; collaboration; strategic partnership | joint venture 1 | `PartnershipEvent`: counterparties, scope, effective date, ownership/economics if disclosed |
| `Restructuring` | restructuring; workforce reduction; exit/impairment charges | 2 keyword-bearing filings | `RestructuringEvent`: program, affected scope, expected charges, timing |
| `LegalOrRegulatoryMatter` | legal proceedings; settlement; investigation; subpoena | 3 `legal proceedings` phrase hits | `LegalMatterEvent`: authority/court, matter type, status, amount, date |
| `MaterialAgreement` | Item 1.01; “material definitive agreement” | 9 phrase hits | `AgreementEvent`: parties, agreement class, effective/termination date, material terms |
| `OtherMaterialDisclosure` | Item 8.01; “Other Events” | 41 | `CorporateEvent` with `event_type=other` until evidence supports a subtype |

Every event requires `event_status` (announced/entered/effective/closed/terminated), explicit event vs filing date, Item, source filing/chunk, confidence, and party roles. Never create a dividend/acquisition edge merely because the word appears in an earnings exhibit.

## 6. Risk and topic taxonomy

Risk Factors are a section-scoped taxonomy, not just topics anywhere in a 10-K. Corpus-wide document presence confirms broad themes: cybersecurity 100/100; regulatory 100/100; competition 100/100; supply chain 95/100; inflation 95/100; tariffs 95/100; IP 94/100; human capital 93/100; geopolitical 90/100; climate change 87/100; data privacy 76/100; generative AI 44/100; semiconductor 27/100; foundry 11/100; GLP-1 6/100. These counts are corpus mentions, so they must be requalified to Item 1A before becoming `Risk` facts.

Recommended canonical `RiskTheme` hierarchy:

- `TechnologyAndSecurity`: cybersecurity, data privacy, AI/model risk, technology failure, IP.
- `MarketAndCommercial`: competition, demand/consumer behavior, pricing, product concentration, GLP-1 exposure.
- `OperationsAndSupplyChain`: suppliers, manufacturing, logistics, semiconductors/foundries, quality.
- `MacroeconomicAndGeopolitical`: inflation, interest rates, FX, tariffs/trade, geopolitical conflict.
- `RegulatoryAndLegal`: regulation/compliance, litigation, tax, healthcare/FDA, environmental/climate.
- `FinancialAndCapital`: liquidity, debt, credit, pensions, market risk.
- `PeopleAndGovernance`: human capital, executive succession, labor, internal controls.

Make a theme a vertex when it has stable semantics and enables intersections/trends (`Cybersecurity`, `Climate`, `GenerativeAI`, `SupplyChain`, `Foundry`, `GLP1`, `Regulation`). Keep an issuer-specific risk wording as a `RiskDisclosure` vertex linked to one or more themes; this preserves nuance and prevents false equivalence.

## 7. Graph-first opportunities and proposed knowledge graph

### First-class vertices

`Company`, `Filing`, `Section`, `SourceSpan`, `Period`, `MetricDefinition`, `MetricObservation`, `Person`, `PersonCandidate`, `Role`, `RoleAssignment`, `Board`, `Committee`, `AuditFirm`, `AuditEngagement`, `CorporateEvent`, `EventParty`, `RiskDisclosure`, `RiskTheme`, `Technology`, `Product`, `Segment`, `Organization`, `Location`, `Sector`.

### Essential edges

`Company-FILED→Filing`; `Filing-HAS_SECTION→Section`; `Section-HAS_EVIDENCE→SourceSpan`; `Company-REPORTED→MetricObservation`; `MetricObservation-OF_METRIC→MetricDefinition`; `MetricObservation-FOR_PERIOD→Period`; `Person-HELD→RoleAssignment-AT→Company`; `RoleAssignment-SERVED_ON→Board/Committee`; `Company-AUDITED_BY→AuditEngagement→AuditFirm`; `Company-DISCLOSED→CorporateEvent`; `EventParty-PARTICIPATED_IN→CorporateEvent`; `Company-DISCLOSED_RISK→RiskDisclosure-HAS_THEME→RiskTheme`; `Company-IN_SECTOR→Sector`.

All asserted edges need `filing_accession`, `source_span_id`, `extraction_method`, `confidence`, `reported_at`, and valid-time fields where relevant. This provenance is non-negotiable for citations and time-aware answers.

### Questions that should be graph-first, not vector-first

| Need | Retrieval/query pattern |
| --- | --- |
| Companies sharing an auditor, risk theme, technology, or director | two-hop intersection: entity ← relationship ← company; group/count distinct company |
| CFO/CEO/board roster as of a date | temporal traversal over `RoleAssignment` filtered by valid interval; then fetch evidence |
| Dividends/buybacks/acquisitions in time order | company → event traversal, filter event type/status, sort event date |
| Metric comparison/ranking/trend | filter `MetricObservation` by canonical metric/scope/period/unit; aggregate/group/order numerically |
| Board/auditor changes following an event | temporal multi-hop from event to role/audit engagement, constrained by company/date |
| Sectors exposed to AI/foundry/GLP-1 themes | sector → companies → risk disclosures/themes; distinct count and evidence roll-up |
| Identify all issuers meeting multiple conditions | set intersection over typed edges, e.g. `uses foundry ∩ has cybersecurity risk ∩ sector=IT` |

Vector retrieval is still best for a narrative explanation, a quote, or a novel unmodeled concept. It should retrieve the cited `SourceSpan` after graph filtering, not replace period arithmetic, identity resolution, intersections, or temporal qualification.

## Suggested ingestion sequence (conceptual)

1. Validate manifest/file identity and create Company/Filing/Section/SourceSpan records.
2. Parse deterministic cover metadata and SEC Item/statement boundaries.
3. Extract table-aware metric observations; preserve raw labels/units and map only with context-aware canonical rules.
4. Localize current auditor opinion/signature and normalize firm with the guarded rules above.
5. In DEF 14A, build issuer-scoped person aliases, then role/board/committee assignments with proxy-year evidence.
6. In 8-K, classify by Item first, extract event parties/dates/status second, and retain ambiguous disclosures as `OtherMaterialDisclosure`.
7. In 10-K Item 1A, create `RiskDisclosure` instances and link them to one or more controlled themes.
8. Run deterministic reconciliation/quality checks: unique accession, date consistency, units, role interval conflicts, duplicate observations, and every fact’s evidence span.

This sequence is generalizable because it relies on SEC form structure, typed contexts, raw-label retention, and explicit provenance—not issuer-specific hardcoding.
