import os
import requests
import urllib.parse

class SecGraphClient:
    def __init__(self, host: str, username: str = "tgadmin", password: str = "", graphname: str = "SecGraph"):
        self.host = host.rstrip('/')
        self.graphname = graphname
        
        token_file = "tgadmin_token.txt"
        if os.path.exists(token_file):
            with open(token_file, "r") as f:
                lines = f.readlines()
                self.api_token = lines[-1].strip()
        elif os.path.exists("../tgadmin_token.txt"):
            with open("../tgadmin_token.txt", "r") as f:
                lines = f.readlines()
                self.api_token = lines[-1].strip()
        else:
            raise Exception("tgadmin_token.txt not found. Cannot authenticate REST queries.")

    def _run_query(self, query_name: str, params: dict = None):
        url = f"{self.host}/restpp/query/{self.graphname}/{query_name}"
        headers = {"Authorization": f"Bearer {self.api_token}"}
        if params:
            query_string = urllib.parse.urlencode(params)
            url = f"{url}?{query_string}"
            
        res = requests.get(url, headers=headers)
        if res.status_code != 200:
            raise Exception(f"Query {query_name} failed: {res.status_code} - {res.text}")
            
        json_res = res.json()
        if json_res.get("error"):
            raise Exception(f"Query error: {json_res.get('message')}")
            
        return json_res.get("results", [])

    def get_filing(self, accession: str):
        return self._run_query("get_filing", params={"f": accession})
        
    def list_company_filings(self, ticker: str):
        return self._run_query("list_company_filings", params={"comp": ticker})
        
    def list_company_metrics(self, ticker: str, period: str):
        return self._run_query("list_company_metrics", params={"comp": ticker, "period_param": period})
        
    def list_company_events(self, ticker: str):
        return self._run_query("list_company_events", params={"comp": ticker})
        
    def get_metric_history(self, ticker: str, metric_name: str):
        return self._run_query("get_metric_history", params={"comp": ticker, "metric_def": metric_name})
        
    def get_filing_evidence(self, accession: str):
        return self._run_query("get_filing_evidence", params={"f": accession})
        
    def get_event_evidence(self, event_id: str):
        return self._run_query("get_event_evidence", params={"ev": event_id})
        
    def get_sources_for_metric(self, observation_id: str):
        return self._run_query("get_sources_for_metric", params={"obs": observation_id})
        
    def get_company_snapshot(self, ticker: str):
        return self._run_query("get_company_snapshot", params={"comp": ticker})

if __name__ == "__main__":
    HOST = "https://tg-3210492c-7ad0-452c-ba1d-f36374050e8e.tg-2635877100.i.tgcloud.io"
    PASSWORD = "wMmlUI4V7iI40P59"
    client = SecGraphClient(host=HOST, password=PASSWORD)
    
    print("Testing get_company_snapshot for 'AMGN'...")
    res = client.get_company_snapshot("AMGN")
    print(res)
