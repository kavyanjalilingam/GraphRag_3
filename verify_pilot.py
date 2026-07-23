import csv
import os
from collections import defaultdict

manifest_path = "manifest.csv"
pilot_tickers = {"AMGN", "CAT", "CSCO", "COP", "DIS"}

def verify_pilot():
    filings = defaultdict(list)
    accessions = set()
    
    with open(manifest_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["ticker"] in pilot_tickers:
                filings[row["ticker"]].append(row)
                
    all_readable = True
    unique_accessions = True
    
    print(f"Verified companies: {len(filings)}")
    for ticker in pilot_tickers:
        ticker_filings = filings[ticker]
        print(f"{ticker}: {len(ticker_filings)} filings")
        for f_row in ticker_filings:
            acc = f_row["accession"]
            if acc in accessions:
                print(f"DUPLICATE ACCESSION: {acc}")
                unique_accessions = False
            accessions.add(acc)
            
            # verify readable
            local_path = f_row["local_path"]
            # local_path is relative to sp100_dataset folder but it contains sp100_dataset prefix.
            # Example: sp100_dataset/AAPL/8-K_2026-04-30.txt
            # Since we are inside sp100_dataset, we can just strip the prefix or adjust path.
            adjusted_path = local_path.replace("sp100_dataset/", "")
            
            if not os.path.exists(adjusted_path):
                print(f"FILE MISSING: {adjusted_path}")
                all_readable = False
            else:
                try:
                    with open(adjusted_path, "r", encoding="utf-8") as file:
                        _ = file.read(100) # Read small chunk
                except Exception as e:
                    print(f"FILE UNREADABLE: {adjusted_path} ({e})")
                    all_readable = False
                    
    if all_readable and unique_accessions and len(filings) == 5 and all(len(filings[t]) == 4 for t in pilot_tickers):
        print("✅ Pilot corpus verification PASSED")
    else:
        print("❌ Pilot corpus verification FAILED")

if __name__ == "__main__":
    verify_pilot()
