import csv
import json
import os
from collections import defaultdict
from extractors.auditors import extract_auditor_for_ticker

def main():
    manifest_path = "../manifest.csv"
    pilot_tickers = {"AMGN", "CAT", "CSCO", "COP", "DIS"}
    
    # group accessions by ticker
    ticker_accessions = defaultdict(list)
    with open(manifest_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["ticker"] in pilot_tickers:
                ticker_accessions[row["ticker"]].append(row["accession"])
                
    for ticker, accessions in ticker_accessions.items():
        filings_dict = {}
        for acc in accessions:
            parsed_path = os.path.join("artifacts", acc, "parsed.json")
            if os.path.exists(parsed_path):
                with open(parsed_path, "r", encoding="utf-8") as pf:
                    filings_dict[acc] = json.load(pf)
                    
        if filings_dict:
            resolved_auditor, all_candidates = extract_auditor_for_ticker(ticker, filings_dict)
            
            out_dir = os.path.join("artifacts", ticker)
            os.makedirs(out_dir, exist_ok=True)
            
            output = {
                "resolved": resolved_auditor,
                "candidates": all_candidates
            }
            
            out_path = os.path.join(out_dir, "auditor.json")
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(output, f, indent=2)
            print(f"Extracted auditor for {ticker}: {resolved_auditor.get('auditor')}")
            
if __name__ == "__main__":
    main()
