import os
import json
import csv
from dataclasses import asdict
from graph.schema import (
    Company, Filing, MetricDefinition, MetricObservation, CorporateEvent, 
    AuditFirm, Person, RoleAssignment, SourceSpan,
    FiledEdge, ReportsEdge, OfMetricEdge, DisclosesEdge, AuditedByEdge, RoleHeldEdge, HasEvidenceEdge, HasSpanEdge
)

def build():
    artifacts_dir = "artifacts"
    if not os.path.exists(artifacts_dir):
        return
        
    companies = {}
    filings = {}
    metric_defs = {}
    metric_obs = {}
    events = {}
    firms = {}
    people = {}
    roles = {}
    spans = {}
    
    e_filed = []
    e_reports = []
    e_of_metric = []
    e_discloses = []
    e_audited = []
    e_role = []
    e_evidence = []
    e_has_span = []
    seen_spans = set()
    
    for entry in os.listdir(artifacts_dir):
        d = os.path.join(artifacts_dir, entry)
        if not os.path.isdir(d): continue
        
        accession = entry
        ticker = "UNKNOWN"
        meta_path = os.path.join(d, "metadata.json")
        if os.path.exists(meta_path):
            with open(meta_path) as f:
                meta = json.load(f)
                ticker = meta.get("ticker", "UNKNOWN")
                companies[ticker] = Company(ticker=ticker, name=meta.get("registrant", ticker))
                filings[accession] = Filing(
                    accession=accession,
                    ticker=ticker,
                    form=meta.get("form", ""),
                    filing_date=meta.get("filing_date", ""),
                    event_date=meta.get("event_date", "")
                )
                e_filed.append(FiledEdge(company_id=ticker, filing_id=accession))
                
        metrics_path = os.path.join(d, "metrics.json")
        if os.path.exists(metrics_path):
            with open(metrics_path) as f:
                metrics = json.load(f)
                for m in metrics:
                    md = m["data"]
                    m_def = md["metric_definition"]
                    period = md["period"]
                    val = md["value"]
                    unit = md["unit"]
                    scope = md.get("statement", "Consolidated")
                    
                    metric_defs[m_def] = MetricDefinition(name=m_def)
                    obs_id = f"{ticker}|{m_def}|{period}|{unit}|{scope}"
                    
                    if obs_id not in metric_obs:
                        metric_obs[obs_id] = MetricObservation(
                            id=obs_id, ticker=ticker, accession=accession, period=period,
                            value=val, unit=unit, scope=scope, raw_label=md.get("raw_label", "")
                        )
                    
                    e_of_metric.append(OfMetricEdge(observation_id=obs_id, definition_id=m_def))
                    spans_str = ",".join(m.get("source_spans", []))
                    e_reports.append(ReportsEdge(
                        filing_id=accession, observation_id=obs_id, 
                        source_spans=spans_str, confidence=m.get("confidence", "")
                    ))
                    
                    for sp in m.get("source_spans", []):
                        span_id = f"{accession}|{sp}"
                        spans[span_id] = SourceSpan(id=span_id, accession=accession, span=sp)
                        e_evidence.append(HasEvidenceEdge(source_id=obs_id, target_id=span_id, span_id=sp))
                        if span_id not in seen_spans:
                            e_has_span.append(HasSpanEdge(filing_id=accession, span_id=span_id))
                            seen_spans.add(span_id)
                        
        events_path = os.path.join(d, "events.json")
        if os.path.exists(events_path):
            with open(events_path) as f:
                evs = json.load(f)
                for ev in evs:
                    ed = ev["data"]
                    ev_type = ed["event_type"]
                    date = ed.get("event_date", filings[accession].event_date if accession in filings else "")
                    ev_id = f"{ticker}|{ev_type}|{date}|{accession}"
                    
                    events[ev_id] = CorporateEvent(
                        id=ev_id, ticker=ticker, event_type=ev_type, date=date, 
                        accession=accession, description=ed.get("description", "")
                    )
                    
                    spans_str = ",".join(ev.get("source_spans", []))
                    e_discloses.append(DisclosesEdge(
                        filing_id=accession, event_id=ev_id,
                        source_spans=spans_str, confidence=ev.get("confidence", "")
                    ))
                    
                    for sp in ev.get("source_spans", []):
                        span_id = f"{accession}|{sp}"
                        spans[span_id] = SourceSpan(id=span_id, accession=accession, span=sp)
                        e_evidence.append(HasEvidenceEdge(source_id=ev_id, target_id=span_id, span_id=sp))
                        if span_id not in seen_spans:
                            e_has_span.append(HasSpanEdge(filing_id=accession, span_id=span_id))
                            seen_spans.add(span_id)
                        
        auditors_path = os.path.join(d, "auditors.json")
        if os.path.exists(auditors_path):
            with open(auditors_path) as f:
                auditors = json.load(f)
                for a in auditors:
                    firm = a["data"].get("auditor", "UNKNOWN")
                    firms[firm] = AuditFirm(name=firm)
                    
                    spans_str = ",".join(a.get("source_spans", []))
                    e_audited.append(AuditedByEdge(
                        company_id=ticker, firm_id=firm, filing_accession=accession,
                        source_spans=spans_str, confidence=a.get("confidence", "")
                    ))
                    
                    for sp in a.get("source_spans", []):
                        span_id = f"{accession}|{sp}"
                        spans[span_id] = SourceSpan(id=span_id, accession=accession, span=sp)
                        e_evidence.append(HasEvidenceEdge(source_id=ticker, target_id=span_id, span_id=sp))
                        if span_id not in seen_spans:
                            e_has_span.append(HasSpanEdge(filing_id=accession, span_id=span_id))
                            seen_spans.add(span_id)

    # Export to JSON
    os.makedirs("project/graph/output", exist_ok=True)
    nodes = {
        "Company": [asdict(v) for v in companies.values()],
        "Filing": [asdict(v) for v in filings.values()],
        "MetricDefinition": [asdict(v) for v in metric_defs.values()],
        "MetricObservation": [asdict(v) for v in metric_obs.values()],
        "CorporateEvent": [asdict(v) for v in events.values()],
        "AuditFirm": [asdict(v) for v in firms.values()],
        "SourceSpan": [asdict(v) for v in spans.values()]
    }
    edges = {
        "FILED": [asdict(e) for e in e_filed],
        "REPORTS": [asdict(e) for e in e_reports],
        "OF_METRIC": [asdict(e) for e in e_of_metric],
        "DISCLOSES": [asdict(e) for e in e_discloses],
        "AUDITED_BY": [asdict(e) for e in e_audited],
        "HAS_EVIDENCE": [asdict(e) for e in e_evidence],
        "HAS_SPAN": [asdict(e) for e in e_has_span]
    }
    
    with open("project/graph/output/vertices.json", "w") as f:
        json.dump(nodes, f, indent=2)
    with open("project/graph/output/edges.json", "w") as f:
        json.dump(edges, f, indent=2)
        
    # Export to CSV
    os.makedirs("project/graph/output/csv", exist_ok=True)
    for name, data in nodes.items():
        if not data: continue
        with open(f"project/graph/output/csv/{name}.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
            
    for name, data in edges.items():
        if not data: continue
        with open(f"project/graph/output/csv/{name}.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
            
    print(f"Generated {sum(len(v) for v in nodes.values())} nodes and {sum(len(e) for e in edges.values())} edges.")

if __name__ == "__main__":
    build()
