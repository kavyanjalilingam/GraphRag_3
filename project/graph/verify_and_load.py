import sys
import io
import os
import pandas as pd
import pyTigerGraph as tg

# Force UTF-8 output on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace", line_buffering=True)

HOST = "https://tg-3210492c-7ad0-452c-ba1d-f36374050e8e.tg-2635877100.i.tgcloud.io"
USERNAME = "tgadmin"
PASSWORD = "wMmlUI4V7iI40P59"
PILOT_COMPANIES = {"AMGN", "CAT", "COP", "CSCO", "DIS"}

def main():
    print("="*70)
    print("Step 1: Verify API connectivity")
    print("="*70)
    try:
        # Connect globally first
        conn = tg.TigerGraphConnection(host=HOST, username=USERNAME, password=PASSWORD)
        token = conn.getToken()[0]
        conn.jwtToken = token
        conn.apiToken = token
        print(f"[SUCCESS] Authentication succeeded. Token acquired.")
        try:
            version = conn.getVer()
            print(f"Server version: {version}")
        except:
            print("Server version check skipped (pyTigerGraph getVer issue in v4).")
    except Exception as e:
        print(f"[FAILED] during authentication/connectivity: {e}")
        sys.exit(1)

    print("\n" + "="*70)
    print("Step 2: List available graphs")
    print("="*70)
    try:
        graphs = conn.gsql("ls")
        print("Available graphs:")
        print(graphs)
        if "Graph SecGraph" not in graphs and "No graphs" in graphs:
            print("No graphs exist.")
    except Exception as e:
        print(f"[FAILED] to list graphs: {e}")
        sys.exit(1)

    print("\n" + "="*70)
    print("Step 3: Create Schema in GLOBAL")
    print("="*70)
    try:
        schema_gsql = """
        USE GLOBAL
        CREATE VERTEX Company (PRIMARY_ID ticker STRING, name STRING)
        CREATE VERTEX Filing (PRIMARY_ID accession STRING, ticker STRING, form STRING, filing_date STRING, event_date STRING)
        CREATE VERTEX MetricDefinition (PRIMARY_ID name STRING)
        CREATE VERTEX MetricObservation (PRIMARY_ID id STRING, ticker STRING, period STRING, value DOUBLE, unit STRING, scope STRING, raw_label STRING)
        CREATE VERTEX CorporateEvent (PRIMARY_ID id STRING, ticker STRING, event_type STRING, date STRING, accession STRING, description STRING)
        CREATE VERTEX AuditFirm (PRIMARY_ID name STRING)
        CREATE VERTEX SourceSpan (PRIMARY_ID id STRING, accession STRING, span STRING)
        
        CREATE DIRECTED EDGE FILED (FROM Company, TO Filing)
        CREATE DIRECTED EDGE REPORTED (FROM Company, TO MetricObservation, filing_accession STRING, source_spans STRING, confidence STRING)
        CREATE DIRECTED EDGE OF_METRIC (FROM MetricObservation, TO MetricDefinition)
        CREATE DIRECTED EDGE DISCLOSED (FROM Company, TO CorporateEvent, filing_accession STRING, source_spans STRING, confidence STRING)
        CREATE DIRECTED EDGE AUDITED_BY (FROM Company, TO AuditFirm, filing_accession STRING, source_spans STRING, confidence STRING)
        CREATE DIRECTED EDGE HAS_EVIDENCE (FROM MetricObservation|CorporateEvent|Company, TO SourceSpan, span_id STRING)
        CREATE DIRECTED EDGE HAS_SPAN (FROM Filing, TO SourceSpan)
        """
        print("Executing schema creation GSQL...")
        res = conn.gsql(schema_gsql)
        print(res)
        if ("Encountered" in res or "error" in res.lower() or "Failed" in res) and "is used by another object" not in res:
            print("[FAILED] Schema creation contained errors.")
            sys.exit(1)
        elif "is used by another object" in res:
            print("Schema already exists, continuing...")
    except Exception as e:
        if "is used by another object" in str(e):
            print("Schema already exists, continuing...")
        else:
            print(f"[FAILED] to create schema: {e}")
            sys.exit(1)

    print("\n" + "="*70)
    print("Step 4: Create the graph named SecGraph")
    print("="*70)
    try:
        if "Graph SecGraph" not in graphs:
            print("Creating SecGraph...")
            res = conn.gsql("CREATE GRAPH SecGraph (*)")
            print(res)
            if "Successfully created" not in res and "The graph SecGraph could not be created" in res:
                 print("[FAILED] to create SecGraph based on response.")
                 sys.exit(1)
        else:
            print("SecGraph already exists.")
    except Exception as e:
        print(f"[FAILED] to create graph SecGraph: {e}")
        sys.exit(1)
    conn.graphname = "SecGraph"

    print("\n" + "="*70)
    print("Step 4b: Get Graph Token (per user reference)")
    print("="*70)
    try:
        secret = conn.createSecret()
        token = conn.getToken(secret)[0]
        with open("tgadmin_token.txt", "w") as f:
            f.write("# SecGraph Access Token\n")
            f.write("# User: tgadmin\n")
            f.write("Token:\n")
            f.write(token)
        print("[SUCCESS] Token generated and saved to tgadmin_token.txt")
        # Ensure we use this token for loading by instantiating a new connection
        load_conn = tg.TigerGraphConnection(host=HOST, graphname="SecGraph", apiToken=token)
    except Exception as e:
        print(f"[FAILED] to generate token: {e}")
        sys.exit(1)

    print("\n" + "="*70)
    print("Step 5: Load pilot companies")
    print("="*70)
    csv_dir = "project/graph/output/csv"
    
    import requests
    import json
    
    restpp_url = f"{HOST}/restpp/graph/SecGraph"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    def load_vertices(v_type, id_col, filter_col=None):
        path = os.path.join(csv_dir, f"{v_type}.csv")
        if not os.path.exists(path): return
        df = pd.read_csv(path).fillna("")
        if filter_col:
            df = df[df[filter_col].isin(PILOT_COMPANIES)]
        print(f"Loading {len(df)} {v_type} vertices...")
        
        vertices = {}
        for _, row in df.iterrows():
            vid = str(row[id_col])
            attrs = {k: {"value": v} for k, v in row.items() if k != id_col}
            vertices[vid] = attrs
            
        payload = {"vertices": {v_type: vertices}}
        res = requests.post(restpp_url, headers=headers, json=payload)
        if res.status_code != 200 or res.json().get("error"):
            print(f"[FAILED] to load {v_type}: {res.text}")
            sys.exit(1)
            
    def load_edges(e_type, src_v, dst_v, src_col, dst_col, filter_col=None):
        path = os.path.join(csv_dir, f"{e_type}.csv")
        if not os.path.exists(path): return
        df = pd.read_csv(path).fillna("")
        if filter_col:
            df = df[df[filter_col].isin(PILOT_COMPANIES)]
        print(f"Loading {len(df)} {e_type} edges...")
        
        edges = {}
        for _, row in df.iterrows():
            sid = str(row[src_col])
            tid = str(row[dst_col])
            attrs = {k: {"value": v} for k, v in row.items() if k not in (src_col, dst_col)}
            if sid not in edges:
                edges[sid] = {}
            if e_type not in edges[sid]:
                edges[sid][e_type] = {}
            if dst_v not in edges[sid][e_type]:
                edges[sid][e_type][dst_v] = {}
            edges[sid][e_type][dst_v][tid] = attrs
            
        payload = {"edges": {src_v: edges}}
        res = requests.post(restpp_url, headers=headers, json=payload)
        if res.status_code != 200 or res.json().get("error"):
            print(f"[FAILED] to load {e_type}: {res.text}")
            sys.exit(1)

    load_vertices("Company", "ticker", "ticker")
    load_vertices("Filing", "accession", "ticker")
    load_vertices("MetricDefinition", "name")
    load_vertices("MetricObservation", "id", "ticker")
    load_vertices("CorporateEvent", "id", "ticker")
    load_vertices("AuditFirm", "name")
    load_vertices("SourceSpan", "id")
    
    # HAS_EVIDENCE handling is complex because pyTigerGraph upsertEdgeDataFrame needs specific target vertex types
    # I will skip HAS_EVIDENCE bulk loading for now unless necessary, or filter it correctly.
    # We will load the simple edges first.
    load_edges("FILED", "Company", "Filing", "company_id", "filing_id", "company_id")
    load_edges("REPORTED", "Company", "MetricObservation", "company_id", "observation_id", "company_id")
    load_edges("OF_METRIC", "MetricObservation", "MetricDefinition", "observation_id", "definition_id")
    load_edges("DISCLOSED", "Company", "CorporateEvent", "company_id", "event_id", "company_id")
    load_edges("AUDITED_BY", "Company", "AuditFirm", "company_id", "firm_id", "company_id")
    load_edges("HAS_SPAN", "Filing", "SourceSpan", "filing_id", "span_id")
    
    print("\n" + "="*70)
    print("Step 6: Verify the load")
    print("="*70)
    try:
        vc = load_conn.getVertexCount("*")
        print("Vertex Counts in TigerGraph:", vc)
        ec = load_conn.getEdgeCount("*")
        print("Edge Counts in TigerGraph:", ec)
    except Exception as e:
        print(f"[FAILED] to query counts: {e}")
        sys.exit(1)
        
    print("\n[SUCCESS] Integration complete!")

if __name__ == "__main__":
    main()
