from __future__ import annotations
import csv, re, statistics, math
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from html import escape

ROOT=Path(__file__).parent
OUT=ROOT/'exploration_report'
OUT.mkdir(exist_ok=True)

def read_text(p):
    return p.read_text(encoding='utf-8',errors='replace')
def wc(s): return len(re.findall(r"\b[\w][\w'’.-]*\b",s))
def mb(n): return n/1024/1024
def fmt(n): return f'{n:,}'
def svg_bar(path, title, items, color='#2563eb', width=980):
    items=list(items); h=max(260,90+len(items)*30); maxv=max(v for _,v in items) if items else 1
    rows=[]
    for i,(label,v) in enumerate(items):
        y=55+i*30; bw=650*v/maxv
        rows.append(f'<text x="10" y="{y+14}" font-size="12">{escape(str(label))}</text><rect x="300" y="{y}" width="{bw:.1f}" height="18" fill="{color}"/><text x="{305+bw:.1f}" y="{y+14}" font-size="12">{v:,}</text>')
    path.write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{h}"><rect width="100%" height="100%" fill="white"/><text x="10" y="25" font-size="18" font-weight="bold">{escape(title)}</text>{"".join(rows)}</svg>',encoding='utf-8')

manifest=list(csv.DictReader((ROOT/'manifest.csv').open(encoding='utf-8-sig')))
files=sorted(ROOT.glob('*/*.txt'))
by_path={str(p.relative_to(ROOT)).replace('\\','/'):p for p in files}
docs=[]
for r in manifest:
    key=r['local_path'].split('sp100_dataset/',1)[-1]
    p=by_path.get(key)
    if not p: continue
    text=read_text(p); b=p.stat().st_size
    docs.append({**r,'path':p,'bytes':b,'chars':len(text),'words':wc(text),'tokens':round(wc(text)*1.33),'text':text})

# Reliable file-derived statistics
sizes=[d['bytes'] for d in docs]; chars=[d['chars'] for d in docs]; words=[d['words'] for d in docs]; toks=[d['tokens'] for d in docs]
companies=sorted({d['ticker'] for d in docs}); byco=defaultdict(list)
for d in docs: byco[d['ticker']].append(d)
forms=Counter(d['form'] for d in docs); sectors=Counter(d['sector'] for d in docs); dates=Counter(d['filing_date'][:7] for d in docs)
full='\n'.join(d['text'] for d in docs)

# Entity category signals. Counts are text mentions, deliberately not de-duplicated entity resolution.
patterns={
 'Company':r'\b(?:Company|Corporation|Inc\.?|Ltd\.?|Registrant)\b', 'Person':r'\b(?:Mr\.?|Ms\.?|Mrs\.?|Dr\.)\s+[A-Z][a-z]+',
 'Board Member':r'\b(?:director|board member|nominee)\b', 'CEO':r'\b(?:Chief Executive Officer|\bCEO\b)\b', 'CFO':r'\b(?:Chief Financial Officer|\bCFO\b)\b',
 'Auditor':r'\b(?:independent registered public accounting firm|independent auditor|Ernst & Young|Deloitte|KPMG|PricewaterhouseCoopers|PwC)\b',
 'Risk':r'\b(?:risk factors?|risks? related to|risk management)\b', 'Financial Metric':r'\b(?:revenue|net income|net earnings|operating income|earnings per share|EBITDA|cash flow)\b',
 'Revenue':r'\brevenues?\b', 'Net Income':r'\bnet (?:income|earnings|loss)\b', 'Operating Income':r'\boperating (?:income|loss|profit)\b', 'Segment':r'\b(?:reportable|operating) segments?\b',
 'Competitor':r'\bcompetitors?|competition\b', 'Supplier':r'\b(?:suppliers?|vendors?)\b', 'Technology':r'\b(?:technology|technologies|AI|artificial intelligence|cloud|semiconductor)\b',
 'Foundry':r'\bfoundr(?:y|ies)\b', 'Product':r'\b(?:products?|services?)\b', 'Acquisition':r'\b(?:acquisition|acquire[ds]?|merger)\b',
 'Dividend':r'\bdividends?\b', 'Share Buyback':r'\b(?:share repurchases?|stock repurchases?|buyback)\b', 'Executive Appointment':r'\b(?:appointed|appointment|named)\b.{0,80}\b(?:Chief|Officer|President|Executive)\b',
 'Policy':r'\b(?:policy|policies)\b', 'Innovation':r'\binnovation\b', 'Committee':r'\b(?:Audit|Compensation|Nominating|Governance) Committee\b',
 'Location':r'\b(?:United States|California|New York|Texas|Europe|China|India)\b', 'Organization':r'\b(?:SEC|Securities and Exchange Commission|Nasdaq|NYSE)\b',
 'Government Agency':r'\b(?:SEC|Securities and Exchange Commission|Department of|Federal Reserve|FDA|FTC)\b', 'Law':r'\b(?:Act of 1934|Securities Act|Exchange Act|law|regulation)\b', 'Standard':r'\b(?:GAAP|IFRS|standard|standards)\b'
}
entity_counts={k:len(re.findall(v,full,re.I|re.S)) for k,v in patterns.items()}

# Relation is an evidence-bearing co-occurrence/event signal, reported as filings with one or more signals.
relation_rules={
 'Company → Filing':lambda s:True,
 'Company → Sector':lambda s:True,
 'Company → Financial Metric':lambda s:bool(re.search(patterns['Financial Metric'],s,re.I)),
 'Company → Risk':lambda s:bool(re.search(patterns['Risk'],s,re.I)),
 'Company → Technology':lambda s:bool(re.search(patterns['Technology'],s,re.I)),
 'Company → Product':lambda s:bool(re.search(patterns['Product'],s,re.I)),
 'Company → Competitor':lambda s:bool(re.search(patterns['Competitor'],s,re.I)),
 'Company → Supplier':lambda s:bool(re.search(patterns['Supplier'],s,re.I)),
 'Company → Foundry':lambda s:bool(re.search(patterns['Foundry'],s,re.I)),
 'Company → Dividend':lambda s:bool(re.search(patterns['Dividend'],s,re.I)),
 'Company → Buyback':lambda s:bool(re.search(patterns['Share Buyback'],s,re.I)),
 'Company → Acquisition':lambda s:bool(re.search(patterns['Acquisition'],s,re.I)),
 'Company → CEO':lambda s:bool(re.search(patterns['CEO'],s,re.I)),
 'Company → CFO':lambda s:bool(re.search(patterns['CFO'],s,re.I)),
 'Company → Auditor':lambda s:bool(re.search(patterns['Auditor'],s,re.I)),
 'Company → Board Member':lambda s:bool(re.search(patterns['Board Member'],s,re.I)),
 'Company → Committee':lambda s:bool(re.search(patterns['Committee'],s,re.I)),
 'Executive Appointment → Company':lambda s:bool(re.search(patterns['Executive Appointment'],s,re.I)),
}
rels=Counter({k:sum(f(d['text']) for d in docs) for k,f in relation_rules.items()})

# Heading/common structure evidence: line-based robust approximation
def headings(docs_for_form):
 c=Counter()
 for d in docs_for_form:
  lines=d['text'].splitlines()
  seen=set()
  for x in lines:
   x=re.sub(r'\s+',' ',x).strip()
   if 4<len(x)<110 and (re.match(r'^(ITEM\s+\d|PART\s+[IVX]|[A-Z][A-Z \-&/,]{8,})',x)):
    x=re.sub(r'\d+','N',x)
    if x not in seen: c[x]+=1; seen.add(x)
 return c
heading_top={f:headings([d for d in docs if d['form']==f]).most_common(20) for f in forms}

# Folder table and metadata anomalies
name_sector={d['ticker']:(d['name'],d['sector']) for d in docs}
folder_rows=[]
for t in companies:
 ds=byco[t]; fs=Counter(x['form'] for x in ds)
 folder_rows.append((t,name_sector[t][0],name_sector[t][1],', '.join(f'{k}:{v}' for k,v in sorted(fs.items())),len(ds),min(x['bytes'] for x in ds),max(x['bytes'] for x in ds)))
anom=[]
for t in companies:
 fs=Counter(x['form'] for x in byco[t])
 if len(byco[t])!=4 or fs != Counter({'8-K':2,'10-K':1,'DEF 14A':1}): anom.append((t,dict(fs)))

# Duplicates and missing
cols=list(manifest[0]); missing={c:sum(not r.get(c,'').strip() for r in manifest) for c in cols}
rowdups=len(manifest)-len({tuple(r.get(c,'') for c in cols) for r in manifest})
def dupvals(k):
 z=Counter(r[k] for r in manifest); return {a:n for a,n in z.items() if n>1}
dupa=dupvals('accession'); dupfil=Counter((r['ticker'],r['form'],r['filing_date']) for r in manifest)
dupfil={str(k):v for k,v in dupfil.items() if v>1}

# create charts
svg_bar(OUT/'companies_per_sector.svg','Companies per sector',sorted(Counter({t:name_sector[t][1] for t in companies}.values()).items(),key=lambda x:(-x[1],x[0])))
svg_bar(OUT/'filings_per_form.svg','Filings per form',sorted(forms.items()))
svg_bar(OUT/'filings_over_time.svg','Filings over time (month)',sorted(dates.items()),'#059669')

def table(headers, rows):
 return '| '+' | '.join(headers)+' |\n| '+' | '.join(['---']*len(headers))+' |\n'+'\n'.join('| '+' | '.join(str(x).replace('|','/') for x in r)+' |' for r in rows)
small=min(docs,key=lambda x:x['bytes']); large=max(docs,key=lambda x:x['bytes'])
co_counts={t:len(byco[t]) for t in companies}; co_bytes={t:sum(x['bytes'] for x in byco[t]) for t in companies}; smco=min(co_bytes,key=co_bytes.get); lgco=max(co_bytes,key=co_bytes.get)
stats=[('Companies',len(companies)),('Manifest rows',len(manifest)),('On-disk documents matched to manifest',len(docs)),('Average documents/company',f'{len(docs)/len(companies):.2f}'),('Smallest company folder',f'{smco} ({co_counts[smco]} documents; {mb(co_bytes[smco]):.2f} MB)'),('Largest company folder',f'{lgco} ({co_counts[lgco]} documents; {mb(co_bytes[lgco]):.2f} MB)'),('Smallest document',f'{small["path"].relative_to(ROOT)} ({small["bytes"]:,} bytes)'),('Largest document',f'{large["path"].relative_to(ROOT)} ({large["bytes"]:,} bytes)'),('Filing corpus size',f'{mb(sum(sizes)):.2f} MB'),('Total source dataset size (filings + manifest)',f'{mb(sum(sizes)+(ROOT/"manifest.csv").stat().st_size):.2f} MB'),('Average document size',f'{statistics.mean(sizes):,.0f} bytes'),('Median document size',f'{statistics.median(sizes):,.0f} bytes'),('Total characters',fmt(sum(chars))),('Total words',fmt(sum(words))),('Estimated GPT tokens (words × 1.33)',fmt(sum(toks))),('Average tokens/document',f'{statistics.mean(toks):,.0f}'),('Median tokens/document',f'{statistics.median(toks):,.0f}'),('Minimum tokens/document',fmt(min(toks))),('Maximum tokens/document',fmt(max(toks)))]

structure={
'10-K':'Cover page; Part I (Business, Risk Factors, Properties, Legal Proceedings); Part II (MD&A, market/equity disclosures); Part III (directors/executive compensation, often incorporated by reference to proxy); Part IV (exhibits); signatures; audited financial statements/notes. Tables recur for statements of operations, balance sheets, cash flows, equity, segments, commitments and valuation.',
'8-K':'Cover page; one or more numbered Item sections; narrative disclosure; exhibits (often earnings release); signatures. Most common event-centric items are earnings/results, material agreements, departures/appointments, financial obligations, and shareholder matters. Formatting varies most because the form is event driven.',
'DEF 14A':'Schedule 14A cover; annual-meeting/voting instructions; proposals; board and director biographies; governance/committees; executive compensation (CD&A, pay tables); ownership; audit/auditor ratification; related-party and shareholder-proposal material. Tables recur for director/committee membership, ownership and compensation.'}

report=f'''# TigerGraph GraphRAG Round 3 — Dataset Exploration

Generated from the local corpus on {datetime.now().strftime('%Y-%m-%d %H:%M')}. This is an exploratory, read-only audit; it does not build a pipeline. Entity and relation totals are transparent rule-based **mention/evidence counts** over extracted text, not a claim of perfect named-entity resolution. Token counts use the stated approximation (English words × 1.33), not an actual GPT tokenizer.

## Executive summary

The corpus contains **{len(companies)} companies and {len(docs)} matched filings**, not 401: the manifest and filesystem each contain 400 filing text files. It is highly regular—normally one 10-K, two 8-Ks, and one DEF 14A per issuer—making form-aware extraction and metadata filters unusually effective. The important graph joins are issuer ↔ filing ↔ period, people/roles, governance, auditors, events, metrics, products/technologies, and risk themes. GraphRAG should add real value for temporal/cross-filing and cross-company joins; conventional retrieval remains preferable for quoting a single narrative passage.

## 1. Dataset statistics

{table(['Measure','Value'],stats)}

Filing-type distribution:

{table(['Form','Filings','Share'],[(k,v,f'{v/len(docs):.1%}') for k,v in sorted(forms.items())])}

## 2. Manifest analysis

Columns: `{', '.join(cols)}`.

{table(['Check','Result'], [('Missing values', '; '.join(f'{k}: {v}' for k,v in missing.items())),('Exact duplicate rows',rowdups),('Duplicate accession numbers',len(dupa)),('Duplicate filing keys (ticker, form, date)',len(dupfil)),('Duplicate filing keys detail', '; '.join(f'{k} ×{v}' for k,v in dupfil.items()) or 'none'),('Date coverage',f'{min(d["filing_date"] for d in docs)} to {max(d["filing_date"] for d in docs)}'),('Path reconciliation',f'{len(manifest)-len(docs)} manifest rows lack a matched file')])}

{table(['Sector','Filings','Companies'],[(s,sectors[s],sum(name_sector[t][1]==s for t in companies)) for s in sorted(sectors)])}

Chart files: [companies per sector](companies_per_sector.svg), [filings per form](filings_per_form.svg), [filings over time](filings_over_time.svg).

## 3. Folder structure and anomalies

Expected folder pattern is `TICKER/{{10-K, two 8-K, DEF14A}}_YYYY-MM-DD[optional _2].txt`; folders are flat and every matched file is represented in the manifest. It is **not perfectly uniform**: {len(anom)} issuers deviate from the canonical 4-file/2-8-K pattern: {', '.join(f'{t} ({v})' for t,v in anom) or 'none'}.

{table(['Ticker','Company','Sector','Forms:count','Files','Min bytes','Max bytes'],[(t,n,s,f,c,fmt(lo),fmt(hi)) for t,n,s,f,c,lo,hi in folder_rows])}

## 4. Document structure

{''.join('### '+form+'\n\n'+desc+'\n\nCommon heading evidence (number of filings containing normalized heading):\n\n'+table(['Heading','Filings'],[(h,n) for h,n in heading_top[form][:12]])+'\n\n' for form,desc in structure.items())}

Generalized template: `SEC cover/registrant metadata → form-specific sections and tables → exhibit references → signature(s)`. Preserve cover metadata and section boundaries, but treat duplicated headers, exchange listings, checkbox language, exhibits indexes, and signatures as low-value retrieval context.

## 5. Semantic content analysis

The following are automated text-mention counts (overlap is intentional: *Revenue* is also a *Financial Metric*). They are suitable for schema prioritization, not final facts; production should add NER, role extraction, entity resolution, and relation confidence.

{table(['Entity category','Mentions'],sorted(entity_counts.items(),key=lambda x:-x[1]))}

Recurring classes: issuer/company, people and officers, directors/committees, auditors, financial metrics, segments, risks, products/technology/supply chain, capital allocation/events, regulations/standards, and organizations/locations.

## 6. Relationship discovery

Ranked by number of filings containing an evidence signal. These are candidate edge families, not individual edges; extract endpoint spans and provenance before graph loading.

{table(['Candidate relationship','Evidence filings'],rels.most_common())}

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

{table(['Question archetype','Tags','GraphRAG difficulty'], [('Locate a fact/quote in a filing','single document, entity lookup, citation-heavy','Easy'),('Compare metric or guidance across filings','multi-document, temporal, numerical/comparison','Medium'),('List a company’s CEO/CFO/auditor/directors','multi-document, multi-hop, citation-heavy','Medium'),('Find issuers sharing a risk/technology/auditor','multi-company, set intersection, aggregation','Hard for plain RAG; Medium for GraphRAG'),('Compare a theme across sectors and periods','cross-sector, temporal, aggregation, comparison','Hard'),('Trace appointment/acquisition → subsequent metrics/risk','multi-hop, temporal, numerical, citation-heavy','Hard')])}

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

{table(['Question category','Best retrieval'], [('Exact issuer/form/date/section','metadata filter → section/chunk'),('Narrative risk/product/strategy question','hybrid: metadata filter + vector similarity + rerank'),('CEO/CFO/auditor/director or committee lookup','graph traversal with date qualifier; fetch cited chunks'),('Cross-company shared entity/theme','graph traversal / set intersection, then vector evidence'),('Metric comparisons/trends','graph metric observations + aggregation; retrieve source table chunks'),('Event history / appointments / capital return','temporal traversal ordered by date + source chunks'),('Broad semantic discovery','vector similarity with form/sector/date filters')])}

## 12. Context optimization

Removable or down-rankable context: SEC covers/checklists, exchange/security listings, repeated table of contents, standard safe-harbor language, exhibit indexes, signature blocks, repeated proxy voting mechanics, and boilerplate incorporated-by-reference notices. Keep one provenance-bearing canonical copy (or metadata) rather than embedding all repeats. **Initial estimate: 15–25% of raw context can be removed/down-weighted without material answer loss**; validate with evaluation recall, especially because some cover-page facts are occasionally asked.

High-value chunks: 10-K Risk Factors, Business, MD&A and financial statements/notes; 8-K Items and earnings exhibits; DEF 14A director/committee, executive compensation, auditor and proposal sections. Cross-document redundancy is strongest for issuer identity, annual governance language and repeated risk/forward-looking disclosures.

## 13. Architecture recommendation

Natural graph structures are an issuer-centered filing timeline; person-role-governance networks; metric/period series; event/capital-allocation chains; and shared theme/entity networks. Useful traversals include `Company→Filing→Chunk`, `Company→Role←Person`, `Company→MetricObservation→Period`, `Company→Event` ordered by time, and `Sector←Company→Risk/Technology` for comparisons.

GraphRAG is better than traditional RAG when the answer requires joins, set intersections, temporal qualification, de-duplication, metric aggregation, or multiple citations. It will not materially improve a single-document passage lookup, an exact quote, or a question whose answer is absent/poorly extracted; vector/keyword retrieval plus reranking should remain the baseline there.
'''
(OUT/'report.md').write_text(report,encoding='utf-8')

# Detailed machine-readable appendices, for downstream modeling
with (OUT/'company_inventory.csv').open('w',newline='',encoding='utf-8') as f:
 w=csv.writer(f); w.writerow(['ticker','company','sector','forms_counts','filings','min_bytes','max_bytes']) ; w.writerows(folder_rows)
with (OUT/'document_inventory.csv').open('w',newline='',encoding='utf-8') as f:
 w=csv.writer(f); w.writerow(['ticker','name','sector','form','filing_date','accession','path','bytes','characters','words','estimated_tokens'])
 for d in docs: w.writerow([d[k] for k in ['ticker','name','sector','form','filing_date','accession']]+[str(d['path'].relative_to(ROOT)),d['bytes'],d['chars'],d['words'],d['tokens']])
with (OUT/'manifest_duplicates.csv').open('w',newline='',encoding='utf-8') as f:
 w=csv.writer(f); w.writerow(['kind','value','count'])
 for k,v in dupa.items(): w.writerow(['accession',k,v])
 for k,v in dupfil.items(): w.writerow(['filing_key',k,v])
print(OUT/'report.md')
