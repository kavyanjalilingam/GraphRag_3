import json

def validate_graph():
    with open("project/graph/output/vertices.json") as f:
        nodes = json.load(f)
    with open("project/graph/output/edges.json") as f:
        edges = json.load(f)
        
    passed = True
    
    # Check unique vertex IDs
    vertex_ids = set()
    for ntype, items in nodes.items():
        for item in items:
            if ntype == "Filing":
                vid = item["accession"]
            elif ntype == "Company":
                vid = item["ticker"]
            elif ntype == "MetricDefinition" or ntype == "AuditFirm":
                vid = item["name"]
            else:
                vid = item["id"]
            if not vid:
                print(f"FAILED: Vertex missing ID in {ntype}")
                passed = False
            if vid in vertex_ids:
                print(f"FAILED: Duplicate vertex ID {vid} in {ntype}")
                passed = False
            vertex_ids.add(vid)
            
    # Referential integrity checks
    metric_defs = {n["name"] for n in nodes.get("MetricDefinition", [])}
    filings = {n["accession"] for n in nodes.get("Filing", [])}
    spans = {n["id"] for n in nodes.get("SourceSpan", [])}
    companies = {n["ticker"] for n in nodes.get("Company", [])}
    
    for obs in nodes.get("MetricObservation", []):
        if obs["metric"] not in metric_defs:
            print(f"FAILED: MetricObservation {obs['id']} references unknown metric {obs['metric']}")
            passed = False
            
    for ev in nodes.get("CorporateEvent", []):
        if ev["accession"] not in filings:
            print(f"FAILED: CorporateEvent {ev['id']} references unknown filing {ev['accession']}")
            passed = False
            
    for edge in edges.get("HAS_EVIDENCE", []):
        if edge["target_id"] not in spans:
            print(f"FAILED: HAS_EVIDENCE edge references unknown span {edge['target_id']}")
            passed = False
            
    for edge in edges.get("REPORTED", []):
        if edge["company_id"] not in companies:
            print(f"FAILED: REPORTED edge references unknown company {edge['company_id']}")
            passed = False
            
    if passed:
        print("PASSED Graph Validation")

if __name__ == "__main__":
    validate_graph()
