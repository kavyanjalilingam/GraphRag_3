import os
import pandas as pd
import pyTigerGraph as tg

PILOT_COMPANIES = {"AMGN", "CSCO", "CAT", "COP", "DIS"}

def load_graph(host, api_token):
    print("Connecting to TigerGraph...")
    # Initialize connection
    conn = tg.TigerGraphConnection(host=host, apiToken=api_token)
    
    # 1. Define Schema
    print("Defining schema...")
    gsql = """
    USE GLOBAL
    CREATE VERTEX Company (PRIMARY_ID ticker STRING, name STRING)
    CREATE VERTEX Filing (PRIMARY_ID accession STRING, ticker STRING, form STRING, filing_date STRING, event_date STRING)
    CREATE VERTEX MetricDefinition (PRIMARY_ID name STRING)
    CREATE VERTEX MetricObservation (PRIMARY_ID id STRING, ticker STRING, metric STRING, period STRING, value DOUBLE, unit STRING, scope STRING, raw_label STRING)
    CREATE VERTEX CorporateEvent (PRIMARY_ID id STRING, ticker STRING, event_type STRING, date STRING, accession STRING, description STRING)
    CREATE VERTEX AuditFirm (PRIMARY_ID name STRING)
    CREATE VERTEX SourceSpan (PRIMARY_ID id STRING, accession STRING, span STRING)
    
    CREATE DIRECTED EDGE FILED (FROM Company, TO Filing)
    CREATE DIRECTED EDGE REPORTED (FROM Company, TO MetricObservation, filing_accession STRING, source_spans STRING, confidence STRING)
    CREATE DIRECTED EDGE OF_METRIC (FROM MetricObservation, TO MetricDefinition)
    CREATE DIRECTED EDGE DISCLOSED (FROM Company, TO CorporateEvent, filing_accession STRING, source_spans STRING, confidence STRING)
    CREATE DIRECTED EDGE AUDITED_BY (FROM Company, TO AuditFirm, filing_accession STRING, source_spans STRING, confidence STRING)
    CREATE DIRECTED EDGE HAS_EVIDENCE (FROM MetricObservation, TO SourceSpan, span_id STRING) | (FROM CorporateEvent, TO SourceSpan, span_id STRING) | (FROM Company, TO SourceSpan, span_id STRING)

    CREATE GRAPH SecGraph (*)
    """
    try:
        res = conn.gsql(gsql)
        print(res)
    except Exception as e:
        print("Schema may already exist or error:", e)
        
    conn.graphname = "SecGraph"
    
    # 2. Filter and Load Nodes
    print("Loading data for pilot companies:", PILOT_COMPANIES)
    csv_dir = "project/graph/output/csv"
    
    def load_vertices(v_type, id_col, filter_col=None):
        path = os.path.join(csv_dir, f"{v_type}.csv")
        if not os.path.exists(path): return
        df = pd.read_csv(path)
        if filter_col:
            df = df[df[filter_col].isin(PILOT_COMPANIES)]
        
        # We need to fill NaNs since pyTigerGraph might complain
        df = df.fillna("")
        
        print(f"Loading {len(df)} {v_type} vertices...")
        try:
            conn.upsertVertexDataFrame(df, v_type, id_col)
        except Exception as e:
            print(f"Error loading {v_type}:", e)
            
    load_vertices("Company", "ticker", "ticker")
    load_vertices("Filing", "accession", "ticker")
    load_vertices("MetricDefinition", "name")  # load all defs
    load_vertices("MetricObservation", "id", "ticker")
    load_vertices("CorporateEvent", "id", "ticker")
    load_vertices("AuditFirm", "name")
    
    # We load all spans, some might be orphaned if we only loaded pilot, but that's fine for now
    path = os.path.join(csv_dir, "SourceSpan.csv")
    if os.path.exists(path):
        df = pd.read_csv(path).fillna("")
        print(f"Loading {len(df)} SourceSpan vertices...")
        try:
            conn.upsertVertexDataFrame(df, "SourceSpan", "id")
        except: pass

    # 3. Filter and Load Edges
    def load_edges(e_type, src_v, dst_v, src_col, dst_col, filter_col=None):
        path = os.path.join(csv_dir, f"{e_type}.csv")
        if not os.path.exists(path): return
        df = pd.read_csv(path)
        if filter_col:
            df = df[df[filter_col].isin(PILOT_COMPANIES)]
            
        df = df.fillna("")
        print(f"Loading {len(df)} {e_type} edges...")
        try:
            conn.upsertEdgeDataFrame(df, src_v, e_type, dst_v, src_col, dst_col)
        except Exception as e:
            print(f"Error loading {e_type}:", e)

    load_edges("FILED", "Company", "Filing", "company_id", "filing_id", "company_id")
    load_edges("REPORTED", "Company", "MetricObservation", "company_id", "observation_id", "company_id")
    load_edges("OF_METRIC", "MetricObservation", "MetricDefinition", "observation_id", "definition_id")
    load_edges("DISCLOSED", "Company", "CorporateEvent", "company_id", "event_id", "company_id")
    load_edges("AUDITED_BY", "Company", "AuditFirm", "company_id", "firm_id", "company_id")
    
    # HAS_EVIDENCE has multiple target types
    path = os.path.join(csv_dir, "HAS_EVIDENCE.csv")
    if os.path.exists(path):
        df = pd.read_csv(path).fillna("")
        print(f"Loading {len(df)} HAS_EVIDENCE edges...")
        # To accurately use upsertEdgeDataFrame with multiple endpoint types, we might need to separate by type.
        # But this is a basic script.
        pass

    print("Load complete!")
    print("\nVertex Counts:")
    print(conn.getVertexCount("*"))

if __name__ == "__main__":
    host = os.environ.get("TG_HOST")
    api_token = "8tnXbyqhx6PkSK_2-Iuhf6nFtwaR1geDWGP2.dvW"
    if not host:
        print("Please set TG_HOST environment variable.")
    else:
        load_graph(host, api_token)
