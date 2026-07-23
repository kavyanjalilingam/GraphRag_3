import csv
import json
import os
import sys

from extractors.metadata import extract_metadata

def main():
    manifest_path = "../manifest.csv"
    pilot_tickers = {"AMGN", "CAT", "CSCO", "COP", "DIS"}
    
    with open(manifest_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["ticker"] in pilot_tickers:
                acc = row["accession"]
                parsed_json_path = os.path.join("artifacts", acc, "parsed.json")
                
                if os.path.exists(parsed_json_path):
                    print(f"Extracting metadata for {acc}...")
                    
                    try:
                        metadata = extract_metadata(parsed_json_path, row)
                        
                        out_path = os.path.join("artifacts", acc, "metadata.json")
                        with open(out_path, "w", encoding="utf-8") as out_f:
                            json.dump(metadata, out_f, indent=2)
                            
                    except Exception as e:
                        print(f"Failed metadata for {acc}: {e}")

if __name__ == "__main__":
    main()
