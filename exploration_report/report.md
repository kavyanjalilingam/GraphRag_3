# TigerGraph GraphRAG Round 3 — Dataset Exploration

Generated from the local corpus on 2026-07-24 22:50. This is an exploratory, read-only audit; it does not build a pipeline. Entity and relation totals are transparent rule-based **mention/evidence counts** over extracted text, not a claim of perfect named-entity resolution. Token counts use the stated approximation (English words × 1.33), not an actual GPT tokenizer.

## Executive summary

The corpus contains **100 companies and 400 matched filings**, not 401: the manifest and filesystem each contain 400 filing text files. It is highly regular—normally one 10-K, two 8-Ks, and one DEF 14A per issuer—making form-aware extraction and metadata filters unusually effective. The important graph joins are issuer ↔ filing ↔ period, people/roles, governance, auditors, events, metrics, products/technologies, and risk themes. GraphRAG should add real value for temporal/cross-filing and cross-company joins; conventional retrieval remains preferable for quoting a single narrative passage.

## 1. Dataset statistics

| Measure | Value |
| --- | --- |
| Companies | 100 |
| Manifest rows | 400 |
| On-disk documents matched to manifest | 400 |
| Average documents/company | 4.00 |
| Smallest company folder | COST (4 documents; 0.34 MB) |
| Largest company folder | TSLA (4 documents; 1.59 MB) |
| Smallest document | COP\8-K_2026-06-23.txt (2,528 bytes) |
| Largest document | TSLA\DEF14A_2025-09-17.txt (1,259,690 bytes) |
| Filing corpus size | 85.71 MB |
| Total source dataset size (filings + manifest) | 85.79 MB |
| Average document size | 224,688 bytes |
| Median document size | 44,080 bytes |
| Total characters | 86,990,830 |
| Total words | 13,061,684 |
| Estimated GPT tokens (words × 1.33) | 17,372,043 |
| Average tokens/document | 43,430 |
| Median tokens/document | 8,527 |
| Minimum tokens/document | 476 |
| Maximum tokens/document | 243,769 |

Filing-type distribution:

| Form | Filings | Share |
| --- | --- | --- |
| 10-K | 100 | 25.0% |
| 8-K | 200 | 50.0% |
| DEF 14A | 100 | 25.0% |

## 2. Manifest analysis

Columns: `ticker, name, sector, form, filing_date, accession, source_url, local_path, status`.

| Check | Result |
| --- | --- |
| Missing values | ticker: 0; name: 0; sector: 0; form: 0; filing_date: 0; accession: 0; source_url: 0; local_path: 0; status: 0 |
| Exact duplicate rows | 0 |
| Duplicate accession numbers | 0 |
| Duplicate filing keys (ticker, form, date) | 3 |
| Duplicate filing keys detail | ('CVX', '8-K', '2026-05-29') ×2; ('JPM', '8-K', '2026-07-14') ×2; ('PFE', '8-K', '2026-06-18') ×2 |
| Date coverage | 2025-07-21 to 2026-07-15 |
| Path reconciliation | 0 manifest rows lack a matched file |

| Sector | Filings | Companies |
| --- | --- | --- |
| Communication Services | 32 | 8 |
| Consumer Discretionary | 40 | 10 |
| Consumer Staples | 36 | 9 |
| Energy | 12 | 3 |
| Financials | 72 | 18 |
| Health Care | 60 | 15 |
| Industrials | 56 | 14 |
| Information Technology | 68 | 17 |
| Materials | 4 | 1 |
| Real Estate | 8 | 2 |
| Utilities | 12 | 3 |

Chart files: [companies per sector](companies_per_sector.svg), [filings per form](filings_per_form.svg), [filings over time](filings_over_time.svg).

## 3. Folder structure and anomalies

Expected folder pattern is `TICKER/{10-K, two 8-K, DEF14A}_YYYY-MM-DD[optional _2].txt`; folders are flat and every matched file is represented in the manifest. It is **not perfectly uniform**: 0 issuers deviate from the canonical 4-file/2-8-K pattern: none.

| Ticker | Company | Sector | Forms:count | Files | Min bytes | Max bytes |
| --- | --- | --- | --- | --- | --- | --- |
| AAPL | Apple Inc. | Information Technology | 10-K:1, 8-K:2, DEF 14A:1 | 4 | 3,671 | 301,187 |
| ABBV | AbbVie | Health Care | 10-K:1, 8-K:2, DEF 14A:1 | 4 | 7,013 | 428,027 |
| ABT | Abbott Laboratories | Health Care | 10-K:1, 8-K:2, DEF 14A:1 | 4 | 3,559 | 395,565 |
| ACN | Accenture | Information Technology | 10-K:1, 8-K:2, DEF 14A:1 | 4 | 3,545 | 386,558 |
| ADBE | Adobe Inc. | Information Technology | 10-K:1, 8-K:2, DEF 14A:1 | 4 | 7,888 | 478,738 |
| AIG | American International Group | Financials | 10-K:1, 8-K:2, DEF 14A:1 | 4 | 3,752 | 755,017 |
| AMD | Advanced Micro Devices | Information Technology | 10-K:1, 8-K:2, DEF 14A:1 | 4 | 8,660 | 481,254 |
| AMGN | Amgen | Health Care | 10-K:1, 8-K:2, DEF 14A:1 | 4 | 4,953 | 649,998 |
| AMT | American Tower | Real Estate | 10-K:1, 8-K:2, DEF 14A:1 | 4 | 4,538 | 561,007 |
| AMZN | Amazon | Consumer Discretionary | 10-K:1, 8-K:2, DEF 14A:1 | 4 | 6,649 | 311,617 |
| AVGO | Broadcom | Information Technology | 10-K:1, 8-K:2, DEF 14A:1 | 4 | 3,211 | 372,837 |
| AXP | American Express | Financials | 10-K:1, 8-K:2, DEF 14A:1 | 4 | 3,332 | 635,898 |
| BA | Boeing | Industrials | 10-K:1, 8-K:2, DEF 14A:1 | 4 | 3,144 | 426,879 |
| BAC | Bank of America | Financials | 10-K:1, 8-K:2, DEF 14A:1 | 4 | 7,749 | 901,124 |
| BKNG | Booking Holdings | Consumer Discretionary | 10-K:1, 8-K:2, DEF 14A:1 | 4 | 6,885 | 364,452 |
| BLK | BlackRock | Financials | 10-K:1, 8-K:2, DEF 14A:1 | 4 | 3,478 | 663,724 |
| BMY | Bristol Myers Squibb | Health Care | 10-K:1, 8-K:2, DEF 14A:1 | 4 | 5,276 | 538,622 |
| BNY | Bank of New York Mellon | Financials | 10-K:1, 8-K:2, DEF 14A:1 | 4 | 5,020 | 370,515 |
| BRK.B | Berkshire Hathaway (Class B) | Financials | 10-K:1, 8-K:2, DEF 14A:1 | 4 | 7,318 | 519,607 |
| C | Citigroup | Financials | 10-K:1, 8-K:2, DEF 14A:1 | 4 | 4,259 | 1,193,472 |
| CAT | Caterpillar Inc. | Industrials | 10-K:1, 8-K:2, DEF 14A:1 | 4 | 3,671 | 445,202 |
| CL | Colgate-Palmolive | Consumer Staples | 10-K:1, 8-K:2, DEF 14A:1 | 4 | 5,134 | 346,160 |
| CMCSA | Comcast | Communication Services | 10-K:1, 8-K:2, DEF 14A:1 | 4 | 3,622 | 406,680 |
| COF | Capital One | Financials | 10-K:1, 8-K:2, DEF 14A:1 | 4 | 4,705 | 891,049 |
| COP | ConocoPhillips | Energy | 10-K:1, 8-K:2, DEF 14A:1 | 4 | 2,528 | 528,089 |
| COST | Costco | Consumer Staples | 10-K:1, 8-K:2, DEF 14A:1 | 4 | 2,820 | 211,383 |
| CRM | Salesforce | Information Technology | 10-K:1, 8-K:2, DEF 14A:1 | 4 | 4,940 | 655,819 |
| CSCO | Cisco | Information Technology | 10-K:1, 8-K:2, DEF 14A:1 | 4 | 4,842 | 407,411 |
| CVS | CVS Health | Health Care | 10-K:1, 8-K:2, DEF 14A:1 | 4 | 3,722 | 770,966 |
| CVX | Chevron Corporation | Energy | 10-K:1, 8-K:2, DEF 14A:1 | 4 | 2,942 | 498,828 |
| DE | Deere & Company | Industrials | 10-K:1, 8-K:2, DEF 14A:1 | 4 | 3,774 | 513,129 |
| DHR | Danaher Corporation | Health Care | 10-K:1, 8-K:2, DEF 14A:1 | 4 | 6,671 | 493,073 |
| DIS | Walt Disney Company (The) | Communication Services | 10-K:1, 8-K:2, DEF 14A:1 | 4 | 3,455 | 452,669 |
| DUK | Duke Energy | Utilities | 10-K:1, 8-K:2, DEF 14A:1 | 4 | 5,512 | 1,061,513 |
| EMR | Emerson Electric | Industrials | 10-K:1, 8-K:2, DEF 14A:1 | 4 | 5,561 | 303,709 |
| FDX | FedEx | Industrials | 10-K:1, 8-K:2, DEF 14A:1 | 4 | 6,466 | 678,687 |
| GD | General Dynamics | Industrials | 10-K:1, 8-K:2, DEF 14A:1 | 4 | 2,978 | 316,212 |
| GE | GE Aerospace | Industrials | 10-K:1, 8-K:2, DEF 14A:1 | 4 | 4,823 | 425,159 |
| GILD | Gilead Sciences | Health Care | 10-K:1, 8-K:2, DEF 14A:1 | 4 | 4,532 | 487,215 |
| GM | General Motors | Consumer Discretionary | 10-K:1, 8-K:2, DEF 14A:1 | 4 | 3,421 | 460,405 |
| GOOGL | Alphabet Inc. (Class A) | Communication Services | 10-K:1, 8-K:2, DEF 14A:1 | 4 | 10,695 | 415,995 |
| GS | Goldman Sachs | Financials | 10-K:1, 8-K:2, DEF 14A:1 | 4 | 3,961 | 1,118,584 |
| HD | Home Depot | Consumer Discretionary | 10-K:1, 8-K:2, DEF 14A:1 | 4 | 3,596 | 418,070 |
| HON | Honeywell | Industrials | 10-K:1, 8-K:2, DEF 14A:1 | 4 | 11,040 | 519,965 |
| IBM | IBM | Information Technology | 10-K:1, 8-K:2, DEF 14A:1 | 4 | 6,061 | 431,791 |
| INTC | Intel | Information Technology | 10-K:1, 8-K:2, DEF 14A:1 | 4 | 5,468 | 524,937 |
| INTU | Intuit | Information Technology | 10-K:1, 8-K:2, DEF 14A:1 | 4 | 5,572 | 425,592 |
| ISRG | Intuitive Surgical | Health Care | 10-K:1, 8-K:2, DEF 14A:1 | 4 | 3,312 | 605,174 |
| JNJ | Johnson & Johnson | Health Care | 10-K:1, 8-K:2, DEF 14A:1 | 4 | 3,756 | 426,914 |
| JPM | JPMorgan Chase | Financials | 10-K:1, 8-K:2, DEF 14A:1 | 4 | 6,024 | 1,210,983 |
| KO | Coca-Cola Company (The) | Consumer Staples | 10-K:1, 8-K:2, DEF 14A:1 | 4 | 5,880 | 612,084 |
| LIN | Linde plc | Materials | 10-K:1, 8-K:2, DEF 14A:1 | 4 | 3,106 | 345,932 |
| LLY | Eli Lilly and Company | Health Care | 10-K:1, 8-K:2, DEF 14A:1 | 4 | 5,458 | 373,443 |
| LMT | Lockheed Martin | Industrials | 10-K:1, 8-K:2, DEF 14A:1 | 4 | 3,194 | 442,166 |
| LOW | Lowe's | Consumer Discretionary | 10-K:1, 8-K:2, DEF 14A:1 | 4 | 3,693 | 325,051 |
| MA | Mastercard | Financials | 10-K:1, 8-K:2, DEF 14A:1 | 4 | 5,141 | 458,049 |
| MCD | McDonald's | Consumer Discretionary | 10-K:1, 8-K:2, DEF 14A:1 | 4 | 3,498 | 287,013 |
| MDLZ | Mondelez International | Consumer Staples | 10-K:1, 8-K:2, DEF 14A:1 | 4 | 5,625 | 421,790 |
| MDT | Medtronic | Health Care | 10-K:1, 8-K:2, DEF 14A:1 | 4 | 4,657 | 495,784 |
| MET | MetLife | Financials | 10-K:1, 8-K:2, DEF 14A:1 | 4 | 4,563 | 1,138,645 |
| META | Meta Platforms | Communication Services | 10-K:1, 8-K:2, DEF 14A:1 | 4 | 6,924 | 522,806 |
| MMM | 3M | Industrials | 10-K:1, 8-K:2, DEF 14A:1 | 4 | 4,435 | 477,127 |
| MO | Altria | Consumer Staples | 10-K:1, 8-K:2, DEF 14A:1 | 4 | 4,303 | 513,352 |
| MRK | Merck & Co. | Health Care | 10-K:1, 8-K:2, DEF 14A:1 | 4 | 5,468 | 638,835 |
| MS | Morgan Stanley | Financials | 10-K:1, 8-K:2, DEF 14A:1 | 4 | 5,598 | 790,544 |
| MSFT | Microsoft | Information Technology | 10-K:1, 8-K:2, DEF 14A:1 | 4 | 3,108 | 439,123 |
| NEE | NextEra Energy | Utilities | 10-K:1, 8-K:2, DEF 14A:1 | 4 | 4,357 | 550,603 |
| NFLX | Netflix, Inc. | Communication Services | 10-K:1, 8-K:2, DEF 14A:1 | 4 | 3,808 | 279,511 |
| NKE | Nike, Inc. | Consumer Discretionary | 10-K:1, 8-K:2, DEF 14A:1 | 4 | 2,930 | 377,339 |
| NOW | ServiceNow | Information Technology | 10-K:1, 8-K:2, DEF 14A:1 | 4 | 6,730 | 464,453 |
| NVDA | Nvidia | Information Technology | 10-K:1, 8-K:2, DEF 14A:1 | 4 | 5,445 | 346,606 |
| ORCL | Oracle Corporation | Information Technology | 10-K:1, 8-K:2, DEF 14A:1 | 4 | 3,824 | 436,457 |
| PEP | PepsiCo | Consumer Staples | 10-K:1, 8-K:2, DEF 14A:1 | 4 | 4,601 | 429,410 |
| PFE | Pfizer | Health Care | 10-K:1, 8-K:2, DEF 14A:1 | 4 | 4,446 | 651,633 |
| PG | Procter & Gamble | Consumer Staples | 10-K:1, 8-K:2, DEF 14A:1 | 4 | 4,102 | 451,675 |
| PLTR | Palantir Technologies | Information Technology | 10-K:1, 8-K:2, DEF 14A:1 | 4 | 4,232 | 549,930 |
| PM | Philip Morris International | Consumer Staples | 10-K:1, 8-K:2, DEF 14A:1 | 4 | 4,444 | 546,768 |
| PYPL | PayPal | Financials | 10-K:1, 8-K:2, DEF 14A:1 | 4 | 7,402 | 557,951 |
| QCOM | Qualcomm | Information Technology | 10-K:1, 8-K:2, DEF 14A:1 | 4 | 3,766 | 550,027 |
| RTX | RTX Corporation | Industrials | 10-K:1, 8-K:2, DEF 14A:1 | 4 | 3,779 | 550,181 |
| SBUX | Starbucks | Consumer Discretionary | 10-K:1, 8-K:2, DEF 14A:1 | 4 | 4,189 | 410,511 |
| SCHW | Charles Schwab Corporation | Financials | 10-K:1, 8-K:2, DEF 14A:1 | 4 | 3,997 | 549,645 |
| SO | Southern Company | Utilities | 10-K:1, 8-K:2, DEF 14A:1 | 4 | 7,341 | 1,185,797 |
| SPG | Simon Property Group | Real Estate | 10-K:1, 8-K:2, DEF 14A:1 | 4 | 4,961 | 734,178 |
| T | AT&T | Communication Services | 10-K:1, 8-K:2, DEF 14A:1 | 4 | 6,755 | 419,658 |
| TGT | Target Corporation | Consumer Discretionary | 10-K:1, 8-K:2, DEF 14A:1 | 4 | 2,927 | 457,216 |
| TMO | Thermo Fisher Scientific | Health Care | 10-K:1, 8-K:2, DEF 14A:1 | 4 | 4,044 | 334,623 |
| TMUS | T-Mobile US | Communication Services | 10-K:1, 8-K:2, DEF 14A:1 | 4 | 5,838 | 556,861 |
| TSLA | Tesla, Inc. | Consumer Discretionary | 10-K:1, 8-K:2, DEF 14A:1 | 4 | 3,117 | 1,259,690 |
| TXN | Texas Instruments | Information Technology | 10-K:1, 8-K:2, DEF 14A:1 | 4 | 3,553 | 209,299 |
| UBER | Uber | Industrials | 10-K:1, 8-K:2, DEF 14A:1 | 4 | 5,558 | 616,001 |
| UNH | UnitedHealth Group | Health Care | 10-K:1, 8-K:2, DEF 14A:1 | 4 | 3,663 | 428,666 |
| UNP | Union Pacific Corporation | Industrials | 10-K:1, 8-K:2, DEF 14A:1 | 4 | 3,322 | 324,797 |
| UPS | United Parcel Service | Industrials | 10-K:1, 8-K:2, DEF 14A:1 | 4 | 3,425 | 445,994 |
| USB | U.S. Bancorp | Financials | 10-K:1, 8-K:2, DEF 14A:1 | 4 | 5,766 | 406,810 |
| V | Visa Inc. | Financials | 10-K:1, 8-K:2, DEF 14A:1 | 4 | 3,960 | 438,340 |
| VZ | Verizon | Communication Services | 10-K:1, 8-K:2, DEF 14A:1 | 4 | 5,396 | 459,020 |
| WFC | Wells Fargo | Financials | 10-K:1, 8-K:2, DEF 14A:1 | 4 | 4,977 | 537,245 |
| WMT | Walmart | Consumer Staples | 10-K:1, 8-K:2, DEF 14A:1 | 4 | 4,777 | 389,264 |
| XOM | ExxonMobil | Energy | 10-K:1, 8-K:2, DEF 14A:1 | 4 | 6,310 | 882,924 |

## 4. Document structure

### 10-K

Cover page; Part I (Business, Risk Factors, Properties, Legal Proceedings); Part II (MD&A, market/equity disclosures); Part III (directors/executive compensation, often incorporated by reference to proxy); Part IV (exhibits); signatures; audited financial statements/notes. Tables recur for statements of operations, balance sheets, cash flows, equity, segments, commitments and valuation.

Common heading evidence (number of filings containing normalized heading):

| Heading | Filings |
| --- | --- |
| PART II | 79 |
| PART III | 79 |
| PART IV | 79 |
| SIGNATURES | 79 |
| PART I | 78 |
| UNITED STATES | 76 |
| SECURITIES AND EXCHANGE COMMISSION | 76 |
| DOCUMENTS INCORPORATED BY REFERENCE | 67 |
| TABLE OF CONTENTS | 49 |
| NOTES TO CONSOLIDATED FINANCIAL STATEMENTS | 40 |
| REPORT OF INDEPENDENT REGISTERED PUBLIC ACCOUNTING FIRM | 40 |
| CONSOLIDATED BALANCE SHEETS | 38 |

### 8-K

Cover page; one or more numbered Item sections; narrative disclosure; exhibits (often earnings release); signatures. Most common event-centric items are earnings/results, material agreements, departures/appointments, financial obligations, and shareholder matters. Formatting varies most because the form is event driven.

Common heading evidence (number of filings containing normalized heading):

| Heading | Filings |
| --- | --- |
| CURRENT REPORT | 186 |
| UNITED STATES | 184 |
| SECURITIES AND EXCHANGE COMMISSION | 183 |
| SIGNATURES | 111 |
| SIGNATURE | 71 |
| WASHINGTON, D.C. N | 41 |
| OF THE SECURITIES EXCHANGE ACT OF N | 20 |
| PURSUANT TO SECTION N OR N(d) | 12 |
| UNITED STATES SECURITIES AND EXCHANGE COMMISSION | 11 |
| SECURITIES EXCHANGE ACT OF N | 11 |
| WASHINGTON, DC N | 10 |
| EXHIBIT INDEX | 5 |

### DEF 14A

Schedule 14A cover; annual-meeting/voting instructions; proposals; board and director biographies; governance/committees; executive compensation (CD&A, pay tables); ownership; audit/auditor ratification; related-party and shareholder-proposal material. Tables recur for director/committee membership, ownership and compensation.

Common heading evidence (number of filings containing normalized heading):

| Heading | Filings |
| --- | --- |
| UNITED STATES | 99 |
| SECURITIES AND EXCHANGE COMMISSION | 99 |
| SCHEDULE NA | 93 |
| TABLE OF CONTENTS | 33 |
| EXECUTIVE COMPENSATION | 27 |
| CORPORATE GOVERNANCE | 25 |
| VOTE BY MAIL | 24 |
| CHECK THE APPROPRIATE BOX: | 23 |
| TO VOTE, MARK BLOCKS BELOW IN BLUE OR BLACK INK AS FOLLOWS: | 22 |
| PAYMENT OF FILING FEE (CHECK ALL BOXES THAT APPLY): | 22 |
| VOTE BY INTERNET | 21 |
| PAY VERSUS PERFORMANCE | 21 |



Generalized template: `SEC cover/registrant metadata → form-specific sections and tables → exhibit references → signature(s)`. Preserve cover metadata and section boundaries, but treat duplicated headers, exchange listings, checkbox language, exhibits indexes, and signatures as low-value retrieval context.

## 5. Semantic content analysis

The following are automated text-mention counts (overlap is intentional: *Revenue* is also a *Financial Metric*). They are suitable for schema prioritization, not final facts; production should add NER, role extraction, entity resolution, and relation confidence.

| Entity category | Mentions |
| --- | --- |
| Company | 101081 |
| Product | 55114 |
| Board Member | 23166 |
| Financial Metric | 23070 |
| Person | 19916 |
| Technology | 19843 |
| Revenue | 18135 |
| Policy | 14442 |
| CEO | 13876 |
| Committee | 13268 |
| Location | 13108 |
| Standard | 12353 |
| Law | 12177 |
| Acquisition | 10949 |
| Organization | 8639 |
| Government Agency | 8595 |
| Dividend | 7282 |
| Risk | 6854 |
| Auditor | 6291 |
| Net Income | 4986 |
| Supplier | 3870 |
| Executive Appointment | 3694 |
| Competitor | 3644 |
| Operating Income | 2961 |
| CFO | 2655 |
| Innovation | 1797 |
| Share Buyback | 1658 |
| Segment | 1169 |
| Foundry | 281 |

Recurring classes: issuer/company, people and officers, directors/committees, auditors, financial metrics, segments, risks, products/technology/supply chain, capital allocation/events, regulations/standards, and organizations/locations.

## 6. Relationship discovery

Ranked by number of filings containing an evidence signal. These are candidate edge families, not individual edges; extract endpoint spans and provenance before graph loading.

| Candidate relationship | Evidence filings |
| --- | --- |
| Company → Filing | 400 |
| Company → Sector | 400 |
| Company → CFO | 259 |
| Company → Board Member | 259 |
| Company → Auditor | 257 |
| Company → Product | 228 |
| Company → Technology | 222 |
| Company → CEO | 221 |
| Company → Risk | 217 |
| Company → Acquisition | 215 |
| Company → Dividend | 214 |
| Company → Financial Metric | 213 |
| Company → Committee | 209 |
| Company → Competitor | 201 |
| Executive Appointment → Company | 201 |
| Company → Supplier | 186 |
| Company → Buyback | 177 |
| Company → Foundry | 16 |

## 7. Cross-document relationships

| Concept | Scope | Recommended representation |
| --- | --- | --- |
| Appointment, dividend, buyback, acquisition | temporal; company-level | Event vertex with effective/reported date and source filing |
| CEO/CFO, auditor, director, committee | company-level and temporal | Person/Organization ↔ Role/Service edge with start/end/provenance |
| Revenue, income, segment metrics | company-level, temporal, comparable cross-company | MetricObservation keyed by issuer, period, metric, units |
| Risks, climate, AI, GLP-1, foundries, competitors | filing-local evidence; cross-company/cross-sector themes | Topic/Risk/Technology vertices linked to evidence chunks |
| Products, suppliers, locations, policies | company-level; some cross-sector | canonical entity plus qualified edges |

Document-local: a specific 8-K event narrative, a table cell, exhibit reference. Company-level: governance roster, operating segments, products, risk inventory. Cross-company: shared auditors, competitors, technologies, standards and agencies. Cross-sector: AI, regulation, climate, supply chain. Temporal: every filing/event/metric/role relationship should have filing date and reported/fiscal period.

## 8. Question complexity analysis

No official evaluation-question file or question list is present in the supplied workspace, so individual official questions cannot be labeled. Use this rubric to tag them when supplied:

| Question archetype | Tags | GraphRAG difficulty |
| --- | --- | --- |
| Locate a fact/quote in a filing | single document, entity lookup, citation-heavy | Easy |
| Compare metric or guidance across filings | multi-document, temporal, numerical/comparison | Medium |
| List a company’s CEO/CFO/auditor/directors | multi-document, multi-hop, citation-heavy | Medium |
| Find issuers sharing a risk/technology/auditor | multi-company, set intersection, aggregation | Hard for plain RAG; Medium for GraphRAG |
| Compare a theme across sectors and periods | cross-sector, temporal, aggregation, comparison | Hard |
| Trace appointment/acquisition → subsequent metrics/risk | multi-hop, temporal, numerical, citation-heavy | Hard |

## 9. Chunking recommendation

- **10-K:** section-aware 900–1,200 GPT-token chunks, 100–150-token overlap; keep financial tables and their captions/units intact.
- **8-K:** Item/exhibit-aware 450–750-token chunks, 75–100-token overlap; often one event can be one chunk.
- **DEF 14A:** proposal/governance/compensation-aware 700–1,000-token chunks, 100–150-token overlap; preserve each compensation/ownership table as an atomic structured object.

Semantic chunking should outperform fixed windows because SEC headings are dependable and table boundaries matter. Use a fixed-token fallback only for malformed/heading-poor text. Attach form, item/section, issuer, date, fiscal period, accession and page/line offsets to each chunk.

## 10. Recommended graph schema

**Vertices:** `Company`, `Filing`, `Chunk`, `Person`, `Role`, `Board/Committee`, `Auditor`, `Metric`, `MetricObservation`, `Risk`, `Technology`, `Product`, `Segment`, `Event`, `Organization`, `Location`, `LawOrStandard`, `Sector`, `Period`, `Table`.

**Essential edges:** `Company-FILED→Filing`, `Filing-CONTAINS→Chunk/Table`, `Company-IN_SECTOR→Sector`, `Person-HOLDS_ROLE_AT→Company`, `Person-SERVES_ON→Committee`, `Company-AUDITED_BY→Auditor`, `Company-REPORTS→MetricObservation`, `MetricObservation-FOR_METRIC→Metric`, `MetricObservation-FOR_PERIOD→Period`, `Company-HAS_RISK→Risk`, `Company-USES/DEVELOPS→Technology`, `Company-OFFERS→Product`, `Company-HAS_SEGMENT→Segment`, `Company-ANNOUNCED→Event`, and `Chunk-MENTIONS→entity`. Every claim edge needs `filing_id`, `chunk_id`, source span, extraction confidence, reported/effective date and validity interval when applicable.

**IDs/indexes:** Company=`ticker`; Filing=`accession` (fallback `ticker|form|date`); Chunk=`accession|section|ordinal`; person/org canonical IDs with alias table; metric observation=`ticker|metric|period|units|scope`. Index ticker, accession, form, sector, filing/effective/fiscal dates, normalized entity name, metric/period, event type, risk/technology. Vectorize `Chunk`, `Risk`, `Technology`, `Product`, `Event` narrative, and optionally `Metric` definitions—not bare filing headers or signatures. Keep `Filing`, `Period`, `Sector`, table metadata and provenance as metadata nodes/properties.

## 11. Retrieval strategy

| Question category | Best retrieval |
| --- | --- |
| Exact issuer/form/date/section | metadata filter → section/chunk |
| Narrative risk/product/strategy question | hybrid: metadata filter + vector similarity + rerank |
| CEO/CFO/auditor/director or committee lookup | graph traversal with date qualifier; fetch cited chunks |
| Cross-company shared entity/theme | graph traversal / set intersection, then vector evidence |
| Metric comparisons/trends | graph metric observations + aggregation; retrieve source table chunks |
| Event history / appointments / capital return | temporal traversal ordered by date + source chunks |
| Broad semantic discovery | vector similarity with form/sector/date filters |

## 12. Context optimization

Removable or down-rankable context: SEC covers/checklists, exchange/security listings, repeated table of contents, standard safe-harbor language, exhibit indexes, signature blocks, repeated proxy voting mechanics, and boilerplate incorporated-by-reference notices. Keep one provenance-bearing canonical copy (or metadata) rather than embedding all repeats. **Initial estimate: 15–25% of raw context can be removed/down-weighted without material answer loss**; validate with evaluation recall, especially because some cover-page facts are occasionally asked.

High-value chunks: 10-K Risk Factors, Business, MD&A and financial statements/notes; 8-K Items and earnings exhibits; DEF 14A director/committee, executive compensation, auditor and proposal sections. Cross-document redundancy is strongest for issuer identity, annual governance language and repeated risk/forward-looking disclosures.

## 13. Architecture recommendation

Natural graph structures are an issuer-centered filing timeline; person-role-governance networks; metric/period series; event/capital-allocation chains; and shared theme/entity networks. Useful traversals include `Company→Filing→Chunk`, `Company→Role←Person`, `Company→MetricObservation→Period`, `Company→Event` ordered by time, and `Sector←Company→Risk/Technology` for comparisons.

GraphRAG is better than traditional RAG when the answer requires joins, set intersections, temporal qualification, de-duplication, metric aggregation, or multiple citations. It will not materially improve a single-document passage lookup, an exact quote, or a question whose answer is absent/poorly extracted; vector/keyword retrieval plus reranking should remain the baseline there.
