Round 3 — Evaluation Set v3 (50) · GraphRAG vs RAG token-reduction
Goal: measure token reduction of GraphRAG vs plain RAG. Questions are stratified by expected GraphRAG token benefit = hop depth × fan-out (how many of the ~300 docs a naive RAG must scan to answer exhaustively). Score each question on BOTH answer-correctness and tokens processed, for each approach.
Tiers: A single-hop controls (8, benefit Low) · B two-hop bridges (16, Med) · C multi-hop aggregation/intersection (20, High) · D cross-doc & temporal (6, Med–High).  ‡ = exhaustive keyword-sweep key; spot-check before final scoring.
Dataset is synthetic/future-dated; all answer keys were extracted from the filings, not real-world knowledge.
ID
Hop
Fan-out / benefit
Question
Source doc(s)
Answer key
Tier A — Single-hop controls (GraphRAG benefit: Low)
EQ01
1
single-doc · Low
Apple's total net sales for fiscal year 2025?
AAPL 10-K
$416,161M (~$416.2B)
EQ02
1
single-doc · Low
NVIDIA's total revenue for fiscal year 2026?
NVDA 10-K
$215,938M (~$215.9B)
EQ03
1
single-doc · Low
JPMorgan Chase's net income for FY ended Dec 31, 2025?
JPM 10-K
$57,048M (~$57.0B), down 2% YoY
EQ04
1
single-doc · Low
ExxonMobil's total revenues and other income for FY2025?
XOM 10-K
$332,238M (~$332.2B)
EQ05
1
single-doc · Low
Coca-Cola's net operating revenues for FY2025?
KO 10-K
$47,941M (~$47.9B)
EQ06
1
single-doc · Low
On what date does Microsoft's FY2025 end?
MSFT 10-K
June 30, 2025
EQ07
1
single-doc · Low
Who is Amazon's Chief Executive Officer?
AMZN DEF14A
Andrew R. Jassy
EQ08
1
single-doc · Low
Netflix relies on which cloud provider to operate its streaming service?
NFLX 10-K
Amazon Web Services (AWS)
Tier B — Two-hop bridges (GraphRAG benefit: Medium)
EQ09
2
few-docs · Med
The company that appointed John Ternus as CEO — what were its total net sales in FY2025?
AAPL 8-K 2026-04-20 + 10-K
Apple; $416,161M (~$416.2B)
EQ10
2
few-docs · Med
The company that agreed to acquire Apogee Therapeutics — who is its independent auditor?
ABBV 8-K 2026-06-22 + DEF14A
AbbVie; Ernst & Young LLP
EQ11
2
few-docs · Med
Besides Netflix, which company authorized a $25B share-repurchase program in 2026?
ADBE 8-K 2026-04-21
Adobe
EQ12
2
few-docs · Med
Company that formed a 50/50 joint venture with BT Group plc — who is its auditor?
VZ 8-K 2026-06-17 + DEF14A
Verizon; Ernst & Young LLP
EQ13
2
few-docs · Med
Which had the higher fiscal-year net income: JPMorgan Chase or ExxonMobil?
JPM & XOM 10-K
JPMorgan Chase ($57.0B vs ExxonMobil $28.8B)
EQ14
2
few-docs · Med
Which had the higher fiscal-year revenue: Walmart or Apple?
WMT & AAPL 10-K
Walmart ($713.2B vs Apple $416.2B)
EQ15
2
few-docs · Med
Which spent more on R&D in its latest fiscal year: Apple or NVIDIA?
AAPL & NVDA 10-K
Apple ($34.55B vs NVIDIA $18.50B)
EQ16
2
few-docs · Med
The company that appointed Jay Hoag as Chairman in 2026 — what share-repurchase amount did it authorize that year?
NFLX 8-K 2026-04-23 + DEF14A
Netflix; $25 billion
EQ17
2
few-docs · Med
Amgen named an incoming CFO in 2026 — who is he, and who is Amgen's auditor?
AMGN 8-K 2026-05-19 + DEF14A
Thomas Dittrich; Ernst & Young LLP
EQ18
2
few-docs · Med
Chevron's departing Chief Legal Officer (per its 2026 8-K) is whom, and who is Chevron's auditor?
CVX 8-K 2026-05-29_2 + DEF14A
R. Hewitt Pate; PricewaterhouseCoopers LLP
EQ19
2
few-docs · Med
AMD names which two companies as its principal competitors in Data Center and discrete graphics?
AMD 10-K
Intel and Nvidia
EQ20
2
corpus-scan · High
Which Deloitte-audited company had a fiscal year ending June 30, 2025?
DEF14A + 10-K
Microsoft
EQ21
2
few-docs · Med
In Apple's April 2026 8-K, who was appointed CEO, and what role will Tim Cook move into?
AAPL 8-K 2026-04-20
John Ternus appointed CEO; Tim Cook moves to Executive Chair of the Board
EQ22
2
single-doc · Med
AMD's new revolving credit facility (May 2026 8-K) names which bank as administrative agent, and which was agent on the facility it replaced?
AMD 8-K 2026-05-15
New: JPMorgan Chase Bank, N.A.; prior (Apr 2022): Wells Fargo Bank, N.A.
EQ23
2
corpus-scan · High
Among the companies that name TSMC as a foundry, which one had the highest fiscal-year revenue?
10-Ks (semis)
NVIDIA ($215.9B; vs AMD, AVGO, INTC, QCOM)
EQ24
2
few-docs · Med
By how much did Caterpillar raise its quarterly dividend (June 2026 8-K), and to what new amount?
CAT 8-K 2026-06-11
+$0.12, from $1.51 to $1.63/share
Tier C — Multi-hop aggregation / intersection (GraphRAG benefit: High)
EQ25
3+
corpus-scan · High
List all S&P-100 companies in the dataset audited by KPMG.
DEF14A (all 100)
ACN, ADBE, BNY, COST, EMR, GD, HD, PEP, PFE, V, WFC (11)
EQ26
3+
corpus-scan · High
Which companies in the dataset name TSMC as a foundry/manufacturing partner?
10-Ks
AMD, AVGO, INTC, NVDA, QCOM
EQ27
3+
corpus-scan · High
Two companies list Indra Nooyi as a member of their board — which two?
DEF14A (all)
Amazon (AMZN), Honeywell (HON)
EQ28
3+
corpus-scan · High
Ellen Kullman serves on the boards of which two dataset companies?
DEF14A (all)
Amgen (AMGN), Goldman Sachs (GS)
EQ29
3+
corpus-scan · High
F. William McNabb III is a director at which two dataset companies?
DEF14A (all)
IBM, UnitedHealth (UNH)
EQ30
3+
corpus-scan · High
Which Energy-sector companies discuss climate change as a risk factor in their 10-K?
10-Ks
Chevron (CVX), ExxonMobil (XOM), ConocoPhillips (COP)
EQ31
3+
corpus-scan · High
Which Utilities-sector companies address climate change in their 10-K?
10-Ks
Duke (DUK), NextEra (NEE), Southern (SO)
EQ32
3+
corpus-scan · High
Which Health-Care companies mention weight-loss / obesity (GLP-1) drugs in their 10-K?
10-Ks
ABBV, AMGN, CVS, ISRG, LLY, MDT, MRK, PFE ‡
EQ33
3+
corpus-scan · High
Besides health-care companies, which consumer companies flag GLP-1 / weight-loss drugs as a business risk?
10-Ks
KO, MCD, MDLZ, PEP, SBUX ‡
EQ34
3+
corpus-scan · High
Which companies declared a cash dividend via an 8-K in this dataset?
8-Ks (all)
AIG ($0.50), Caterpillar ($1.63), Costco ($1.47), Oracle ($1,625 pref.+common), P&G ‡
EQ35
3+
corpus-scan · High
Which companies authorized a $25 billion share-repurchase program via an 8-K?
8-Ks
Adobe, Netflix
EQ36
3+
corpus-scan · High
Which KPMG-audited companies are in the Consumer Staples sector?
DEF14A + sector
PepsiCo (PEP), Costco (COST)
EQ37
3+
corpus-scan · High
Which KPMG-audited companies are in the Financials sector?
DEF14A + sector
BNY Mellon (BNY), Wells Fargo (WFC); + Visa (V) if classed Financials
EQ38
3+
corpus-scan · High
Among the companies that name TSMC as a foundry, which are audited by Ernst & Young?
10-K ∩ DEF14A
AMD, INTC
EQ39
3+
corpus-scan · High
Among the companies that name TSMC as a foundry, which are audited by PricewaterhouseCoopers?
10-K ∩ DEF14A
AVGO, NVDA, QCOM
EQ40
3+
corpus-scan · High
Among Health-Care companies that mention obesity/weight-loss drugs, which are audited by Ernst & Young?
DEF14A ∩ 10-K
ABBV, AMGN, CVS, LLY
EQ41
3+
corpus-scan · High
Which Deloitte-audited companies are in the Health-Care sector?
DEF14A + sector
Bristol-Myers Squibb (BMY), UnitedHealth (UNH)
EQ42
3+
corpus-scan · High
Among the dataset's semiconductor and networking companies, which explicitly name NVIDIA as a competitor?
10-Ks
AMD, CSCO, INTC, QCOM
EQ43
3+
corpus-scan · High
Among companies that name NVIDIA as a competitor, which are audited by PricewaterhouseCoopers?
10-K ∩ DEF14A
CSCO, QCOM
EQ44
3+
corpus-scan · High
How many dataset companies does each Big Four firm audit?
DEF14A (all 100)
Ernst & Young 35, PwC 29, Deloitte 25, KPMG 11
Tier D — Cross-document & temporal (GraphRAG benefit: Med–High)
EQ45
2
few-docs · Med
Amgen's CFO transition (2026): when does the outgoing CFO retire, and when does the incoming CFO start?
AMGN 8-K 2026-05-19
Peter H. Griffith retires as CFO Aug 31, 2026 (EVP until Jan 31, 2027); Thomas Dittrich effective Sept 1, 2026
EQ46
3+
few-docs · High
Put these 2026 buyback authorizations in chronological order: Adobe $25B, Netflix +$25B, Accenture +$2B, Morgan Stanley $20B.
ADBE/NFLX/ACN/MS 8-Ks
Adobe (Apr 21) → Netflix (Apr 22) → Accenture (Jun 23) → Morgan Stanley (Jun 24)
EQ47
2
few-docs · Med
Apple filed two 8-Ks in April 2026 (Apr 20, Apr 30). What event does each report?
AAPL 8-Ks
Apr 20 = CEO transition (Ternus); Apr 30 = Q2 FY26 earnings / results of operations
EQ48
2
few-docs · Med
The company that expanded a productivity/restructuring program on April 30, 2026 — name it, its auditor, and the revised total pre-tax charge range.
CL 8-K 2026-05-01 + DEF14A
Colgate-Palmolive; PwC; revised to $350M–$550M
EQ49
2
few-docs · Med
Cisco's May 2026 restructuring 8-K funds which growth areas, and who is Cisco's auditor?
CSCO 8-K 2026-05-13 + DEF14A
Silicon, optics, security, and AI; PwC
EQ50
1
single-doc · Low
What quarterly cash dividend per share did Costco declare in its July 2026 8-K?
COST 8-K 2026-07-08
$1.47 per share


