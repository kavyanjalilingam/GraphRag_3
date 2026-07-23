import csv
import json
import os
import sys

from parser.form_parser import parse_filing

def main():
    manifest_path = "../manifest.csv"
    pilot_tickers = {"AMGN", "CAT", "CSCO", "COP", "DIS"}
    
    with open(manifest_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["ticker"] in pilot_tickers:
                acc = row["accession"]
                local_path = row["local_path"]
                # Adjust path because we are inside project dir, and local_path has sp100_dataset/
                adjusted_path = os.path.join("..", local_path.replace("sp100_dataset/", ""))
                
                print(f"Parsing {adjusted_path}...")
                
                try:
                    out = parse_filing(adjusted_path)
                    
                    artifact_dir = os.path.join("artifacts", acc)
                    os.makedirs(artifact_dir, exist_ok=True)
                    
                    with open(os.path.join(artifact_dir, "parsed.json"), "w", encoding="utf-8") as out_f:
                        json.dump(out, out_f, indent=2)
                        
                except Exception as e:
                    print(f"Failed to parse {acc}: {e}")

if __name__ == "__main__":
    main()
