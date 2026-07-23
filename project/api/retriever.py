import re
from typing import Dict, Any
from project.api.graph_client import SecGraphClient

class IntentRouter:
    """
    Abstract intent router that can be replaced with an LLM implementation later.
    Currently uses regex heuristics to map a question to a graph query.
    """
    def route(self, question: str) -> Dict[str, Any]:
        question = question.lower()
        
        # 1. Company Snapshot
        if "snapshot" in question or "overview" in question or "summary" in question:
            ticker = self._extract_ticker(question)
            return {"intent": "company_snapshot", "params": {"ticker": ticker}}
            
        # 2. Metric History
        if "history" in question or "over time" in question or "trend" in question:
            ticker = self._extract_ticker(question)
            metric = self._extract_metric(question)
            return {"intent": "metric_history", "params": {"ticker": ticker, "metric": metric}}
            
        # 3. Filing Lookup
        if "filing" in question and bool(re.search(r'\d{10}-\d{2}-\d{6}', question)):
            accession = re.search(r'\d{10}-\d{2}-\d{6}', question).group(0)
            return {"intent": "filing_lookup", "params": {"accession": accession}}
            
        # 4. Metric Lookup
        if "metric" in question or "revenue" in question or "income" in question or "asset" in question:
            ticker = self._extract_ticker(question)
            period = self._extract_period(question)
            return {"intent": "metric_lookup", "params": {"ticker": ticker, "period": period}}
            
        # 5. Event Lookup
        if "event" in question or "vote" in question or "director" in question or "board" in question:
            ticker = self._extract_ticker(question)
            return {"intent": "event_lookup", "params": {"ticker": ticker}}
            
        return {"intent": "unknown", "params": {}}
        
    def _extract_ticker(self, question: str) -> str:
        # Simple heuristic: look for known tickers or uppercase words.
        # Hardcoding AMGN for demo purposes if AMGN is mentioned.
        if "amgn" in question or "amgen" in question:
            return "AMGN"
        if "csco" in question or "cisco" in question:
            return "CSCO"
        return "AMGN" # Fallback
        
    def _extract_metric(self, question: str) -> str:
        if "revenue" in question: return "Revenue"
        if "net income" in question: return "Net Income"
        if "asset" in question: return "Total Assets"
        return "Revenue"
        
    def _extract_period(self, question: str) -> str:
        if "2023" in question: return "FY2023"
        if "2024" in question: return "FY2024"
        if "2025" in question: return "FY2025"
        return "FY2025"

class GraphRetriever:
    def __init__(self, client: SecGraphClient, router: IntentRouter):
        self.client = client
        self.router = router
        
    def retrieve_evidence(self, question: str) -> Dict[str, Any]:
        """
        Takes a natural language question, routes it to an intent,
        executes the corresponding graph query, and returns JSON evidence.
        """
        plan = self.router.route(question)
        intent = plan.get("intent")
        params = plan.get("params", {})
        
        evidence = {"intent_detected": intent, "params": params, "data": None}
        
        try:
            if intent == "company_snapshot":
                evidence["data"] = self.client.get_company_snapshot(params.get("ticker"))
            elif intent == "metric_history":
                evidence["data"] = self.client.get_metric_history(params.get("ticker"), params.get("metric"))
            elif intent == "filing_lookup":
                evidence["data"] = self.client.get_filing_evidence(params.get("accession"))
            elif intent == "metric_lookup":
                evidence["data"] = self.client.list_company_metrics(params.get("ticker"), params.get("period"))
            elif intent == "event_lookup":
                evidence["data"] = self.client.list_company_events(params.get("ticker"))
            else:
                evidence["error"] = "Could not map question to a known intent."
        except Exception as e:
            evidence["error"] = str(e)
            
        return evidence

if __name__ == "__main__":
    HOST = "https://tg-3210492c-7ad0-452c-ba1d-f36374050e8e.tg-2635877100.i.tgcloud.io"
    PASSWORD = "wMmlUI4V7iI40P59"
    client = SecGraphClient(host=HOST, password=PASSWORD)
    router = IntentRouter()
    retriever = GraphRetriever(client, router)
    
    questions = [
        "Give me a snapshot of AMGN",
        "What is the revenue history for CSCO?",
        "What happened in filing 0000318154-26-000097?"
    ]
    
    import json
    for q in questions:
        print(f"\\nQuestion: {q}")
        res = retriever.retrieve_evidence(q)
        print(json.dumps(res, indent=2)[:500] + "...\\n[TRUNCATED]")
