import sys
import io
import os
import pyTigerGraph as tg

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace", line_buffering=True)

HOST = "https://tg-3210492c-7ad0-452c-ba1d-f36374050e8e.tg-2635877100.i.tgcloud.io"
USERNAME = "tgadmin"
PASSWORD = "wMmlUI4V7iI40P59"

queries = {
    "get_filing": """
CREATE OR REPLACE QUERY get_filing(VERTEX<Filing> f) FOR GRAPH SecGraph {
  Start = {f};
  PRINT Start;
}
""",
    "list_company_filings": """
CREATE OR REPLACE QUERY list_company_filings(VERTEX<Company> comp) FOR GRAPH SecGraph {
  Start = {comp};
  Result = SELECT t FROM Start:s -(FILED:e)-> Filing:t;
  PRINT Result;
}
""",
    "list_company_metrics": """
CREATE OR REPLACE QUERY list_company_metrics(VERTEX<Company> comp, STRING period_param) FOR GRAPH SecGraph {
  Start = {comp};
  Filings = SELECT t FROM Start:s -(FILED:e)-> Filing:t;
  Metrics = SELECT t FROM Filings:s -(REPORTS:e)-> MetricObservation:t WHERE t.period == period_param;
  PRINT Metrics;
}
""",
    "list_company_events": """
CREATE OR REPLACE QUERY list_company_events(VERTEX<Company> comp) FOR GRAPH SecGraph {
  Start = {comp};
  Filings = SELECT t FROM Start:s -(FILED:e)-> Filing:t;
  Events = SELECT t FROM Filings:s -(DISCLOSES:e)-> CorporateEvent:t;
  PRINT Events;
}
""",
    "get_metric_history": """
CREATE OR REPLACE QUERY get_metric_history(VERTEX<Company> comp, VERTEX<MetricDefinition> metric_def) FOR GRAPH SecGraph {
  Start = {comp};
  Filings = SELECT t FROM Start:s -(FILED:e)-> Filing:t;
  Metrics = SELECT t FROM Filings:s -(REPORTS:e)-> MetricObservation:t;
  MatchedMetrics = SELECT s FROM Metrics:s -(OF_METRIC:e)-> MetricDefinition:d WHERE d == metric_def;
  PRINT MatchedMetrics;
}
""",
    "get_filing_evidence": """
CREATE OR REPLACE QUERY get_filing_evidence(VERTEX<Filing> f) FOR GRAPH SecGraph {
  Start = {f};
  Metrics = SELECT t FROM Start:s -(REPORTS:e)-> MetricObservation:t;
  Events = SELECT t FROM Start:s -(DISCLOSES:e)-> CorporateEvent:t;
  Spans = SELECT t FROM Start:s -(HAS_SPAN:e)-> SourceSpan:t;
  PRINT Start, Metrics, Events, Spans;
}
""",
    "get_event_evidence": """
CREATE OR REPLACE QUERY get_event_evidence(VERTEX<CorporateEvent> ev) FOR GRAPH SecGraph {
  Start = {ev};
  Spans = SELECT t FROM Start:s -(HAS_EVIDENCE:e)-> SourceSpan:t;
  PRINT Start, Spans;
}
""",
    "get_sources_for_metric": """
CREATE OR REPLACE QUERY get_sources_for_metric(VERTEX<MetricObservation> obs) FOR GRAPH SecGraph {
  Start = {obs};
  Spans = SELECT t FROM Start:s -(HAS_EVIDENCE:e)-> SourceSpan:t;
  PRINT Start, Spans;
}
""",
    "get_company_snapshot": """
CREATE OR REPLACE QUERY get_company_snapshot(VERTEX<Company> comp) FOR GRAPH SecGraph {
  Start = {comp};
  Filings = SELECT t FROM Start:s -(FILED:e)-> Filing:t ORDER BY t.filing_date DESC LIMIT 5;
  Events = SELECT t FROM Filings:s -(DISCLOSES:e)-> CorporateEvent:t ORDER BY t.date DESC LIMIT 5;
  Metrics = SELECT t FROM Filings:s -(REPORTS:e)-> MetricObservation:t LIMIT 10;
  PRINT Start, Filings, Events, Metrics;
}
"""
}

def main():
    print("Connecting to TigerGraph...")
    conn = tg.TigerGraphConnection(host=HOST, username=USERNAME, password=PASSWORD, graphname="SecGraph")
    conn.jwtToken = conn.getToken()[0]
    
    os.makedirs("project/query", exist_ok=True)
    
    gsql_block = "USE GRAPH SecGraph\n"
    for q_name, q_body in queries.items():
        with open(f"project/query/{q_name}.gsql", "w") as f:
            f.write(f"USE GRAPH SecGraph\n{q_body}")
        gsql_block += q_body + "\n"
        
    gsql_block += f"INSTALL QUERY {','.join(queries.keys())}\n"
    
    print("Deploying and installing queries (this may take a few minutes)...")
    res = conn.gsql(gsql_block)
    print(res)
    print("Done!")

if __name__ == "__main__":
    main()
