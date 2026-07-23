import csv
import json
import os
from collections import defaultdict

def reconcile_manifest(manifest_path, artifacts_dir, pilot_tickers):
    discrepancies = []
    
    # 1. Load manifest and find duplicates
    manifest_rows = []
    seen_keys = set()
    accession_map = {}
    
    with open(manifest_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["ticker"] in pilot_tickers:
                manifest_rows.append(row)
                acc = row["accession"]
                accession_map[acc] = row
                
                key = (row["ticker"], row["form"], row["filing_date"])
                if key in seen_keys:
                    discrepancies.append({
                        "severity": "Warning",
                        "type": "duplicate_key",
                        "message": f"Duplicate (ticker, form, filing_date) key found: {key}"
                    })
                seen_keys.add(key)
                
    # 2. Compare extracted metadata against manifest
    for acc, manifest_row in accession_map.items():
        meta_path = os.path.join(artifacts_dir, acc, "metadata.json")
        if not os.path.exists(meta_path):
            discrepancies.append({
                "severity": "Error",
                "type": "missing_metadata",
                "message": f"Missing metadata.json for accession {acc}"
            })
            continue
            
        with open(meta_path, "r", encoding="utf-8") as mf:
            meta = json.load(mf)
            
        # Check Accession
        if meta.get("accession") != acc:
            discrepancies.append({
                "severity": "Error",
                "type": "accession_mismatch",
                "message": f"Accession mismatch: {acc} != {meta.get('accession')}"
            })
            
        # Check Ticker
        if meta.get("ticker") != manifest_row["ticker"]:
            discrepancies.append({
                "severity": "Error",
                "type": "ticker_mismatch",
                "message": f"Ticker mismatch for {acc}: {manifest_row['ticker']} != {meta.get('ticker')}"
            })
            
        # Check Form
        if meta.get("form") != manifest_row["form"]:
            discrepancies.append({
                "severity": "Error",
                "type": "form_mismatch",
                "message": f"Form mismatch for {acc}: {manifest_row['form']} != {meta.get('form')}"
            })
            
        # Check Filing Date
        if meta.get("filing_date") != manifest_row["filing_date"]:
            discrepancies.append({
                "severity": "Error",
                "type": "filing_date_mismatch",
                "message": f"Filing date mismatch for {acc}: {manifest_row['filing_date']} != {meta.get('filing_date')}"
            })
            
        # Check Name Normalization
        meta_name = meta.get("registrant_name", "").strip().upper()
        man_name = manifest_row["name"].strip().upper()
        
        # Simple name comparison warning (ignoring 'INC.', 'CORPORATION' differences or just exact match)
        if meta_name != man_name and meta_name not in man_name and man_name not in meta_name:
            discrepancies.append({
                "severity": "Warning",
                "type": "name_normalization",
                "message": f"Registrant name differs for {acc}: Manifest='{manifest_row['name']}', Extracted='{meta.get('registrant_name')}'"
            })
            
    return discrepancies

if __name__ == "__main__":
    discrepancies = reconcile_manifest("../manifest.csv", "../artifacts", {"AMGN", "CAT", "CSCO", "COP", "DIS"})
    for d in discrepancies:
        print(f"[{d['severity']}] {d['type']}: {d['message']}")
