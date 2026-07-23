import os
import json
import csv
from collections import defaultdict
import shutil

def main():
    manifest_path = "../manifest.csv"
    pilot_tickers = {"AMGN", "CAT", "CSCO", "COP", "DIS"}
    
    metadata_fixtures = defaultdict(dict)
    
    with open(manifest_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            ticker = row["ticker"]
            if ticker in pilot_tickers:
                acc = row["accession"]
                metadata_path = os.path.join("artifacts", acc, "metadata.json")
                if os.path.exists(metadata_path):
                    with open(metadata_path, "r", encoding="utf-8") as mf:
                        metadata_fixtures[ticker][acc] = json.load(mf)
                        
    for ticker, data in metadata_fixtures.items():
        ticker_dir = os.path.join("fixtures", ticker)
        os.makedirs(ticker_dir, exist_ok=True)
        with open(os.path.join(ticker_dir, "metadata.json"), "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
            
        # Also copy auditor.json if it exists
        auditor_src = os.path.join("artifacts", ticker, "auditor.json")
        if os.path.exists(auditor_src):
            shutil.copy(auditor_src, os.path.join(ticker_dir, "auditor.json"))
            
    print("Fixtures rebuilt successfully.")

if __name__ == "__main__":
    main()
