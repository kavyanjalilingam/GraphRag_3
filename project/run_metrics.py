import json
import os
import glob
from extractors.metrics.income_statement import IncomeStatementExtractor
from extractors.metrics.balance_sheet import BalanceSheetExtractor
from extractors.metrics.cash_flow import CashFlowExtractor
from extractors.metrics.segments import SegmentMetricsExtractor

def main():
    extractors = [
        IncomeStatementExtractor(),
        BalanceSheetExtractor(),
        CashFlowExtractor(),
        SegmentMetricsExtractor()
    ]
    
    # Process all parsed filings in artifacts
    if not os.path.exists("artifacts"):
        return
        
    for entry in os.listdir("artifacts"):
        d = os.path.join("artifacts", entry)
        if not os.path.isdir(d):
            continue
        parsed_path = os.path.join(d, "parsed.json")
        if not os.path.exists(parsed_path):
            continue
            
        with open(parsed_path, "r", encoding="utf-8") as f:
            parsed = json.load(f)
            
        accession = entry
        
        metadata_path = os.path.join(d, "metadata.json")
        ticker = "UNKNOWN"
        form = "UNKNOWN"
        if os.path.exists(metadata_path):
            with open(metadata_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
                ticker = meta.get("ticker", "UNKNOWN")
                form = meta.get("form", "UNKNOWN")
                
        print(f"Extracting metrics for {accession} ({ticker} {form})")
        
        observations = []
        for ext in extractors:
            observations.extend(ext.extract(accession, parsed))
        
        # Deduplicate identically-keyed observations
        unique_obs = []
        seen = set()
        for obs in observations:
            key = (obs["data"]["metric_definition"], obs["data"]["period"], obs["data"]["statement"], obs["filing_accession"])
            if key not in seen:
                seen.add(key)
                unique_obs.append(obs)
            else:
                # Append source span if it's the same metric
                for existing in unique_obs:
                    if (existing["data"]["metric_definition"], existing["data"]["period"], existing["data"]["statement"], existing["filing_accession"]) == key:
                        existing["source_spans"].extend(x for x in obs["source_spans"] if x not in existing["source_spans"])
                        break
        
        metrics_path = os.path.join(d, "metrics.json")
        with open(metrics_path, "w", encoding="utf-8") as f:
            json.dump(unique_obs, f, indent=2)

if __name__ == "__main__":
    main()
