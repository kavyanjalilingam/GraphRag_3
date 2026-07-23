import csv
import json
import os
from collections import defaultdict
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from parser.manifest import reconcile_manifest
from extractors.auditors import resolve_auditor

def run_manifest_reconciliation(pilot_tickers, manifest_path):
    discrepancies = reconcile_manifest(manifest_path, "artifacts", pilot_tickers)
    errors = [d for d in discrepancies if d['severity'] == 'Error']
    warnings = [d for d in discrepancies if d['severity'] == 'Warning']
    
    for w in warnings:
        print(f"[Warning] {w['type']}: {w['message']}")
        
    for e in errors:
        print(f"[Error] {e['type']}: {e['message']}")
        
    if errors:
        print("FAILED Manifest Reconciliation")
        return False
    print("PASSED Manifest Reconciliation")
    return True

def run_parser_validation(pilot_tickers, manifest_path):
    # Verify all 20 have parsed.json, and CSCO exposes 2.02 and 2.05
    all_present = True
    csco_valid = False
    
    with open(manifest_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["ticker"] in pilot_tickers:
                acc = row["accession"]
                parsed_path = os.path.join("artifacts", acc, "parsed.json")
                if not os.path.exists(parsed_path):
                    print(f"FAILED Parser Validation: Missing {parsed_path}")
                    all_present = False
                    continue
                
                # specific check for CSCO
                if row["ticker"] == "CSCO" and row["form"] == "8-K":
                    with open(parsed_path, "r", encoding="utf-8") as pf:
                        parsed = json.load(pf)
                        items = [s.get("item") for s in parsed.get("sections", []) if "item" in s]
                        if "2.02" in items and "2.05" in items:
                            csco_valid = True
                            
    if not all_present:
        return False
    if not csco_valid:
        print("FAILED Parser Validation: CSCO missing Item 2.02 or 2.05")
        return False
        
    print("PASSED Parser Validation")
    return True

def run_auditor_validation(pilot_tickers):
    passed = True
    
    for ticker in pilot_tickers:
        fixture_path = os.path.join("fixtures", ticker, "auditor.json")
        if not os.path.exists(fixture_path):
            print(f"FAILED Auditor Validation: Missing fixture for {ticker}")
            passed = False
            continue
            
        with open(fixture_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        resolved = data.get("resolved", {})
        candidates = data.get("candidates", [])
        
        # Provenance completeness check
        required_fields = ["auditor", "confidence", "source_type", "source_spans", "filing_accession", "extraction_rule"]
        for field in required_fields:
            if not resolved.get(field) or resolved.get(field) == "unknown":
                print(f"FAILED Auditor Provenance Check for {ticker}: Missing {field}")
                passed = False
                
        # Auditor disagreement warning
        unique_candidate_auditors = {c["auditor"] for c in candidates if c.get("auditor") != "unknown"}
        if len(unique_candidate_auditors) > 1:
            print(f"[Warning] auditor_disagreement: Multiple different auditor candidates found for {ticker}: {unique_candidate_auditors}")
                
    # Synthetic Precedence Test
    synthetic_candidates = [
        {"auditor": "Deloitte & Touche LLP", "source_type": "def14a_ratification", "confidence": "high"},
        {"auditor": "Ernst & Young LLP", "source_type": "audit_signature", "confidence": "high"}
    ]
    
    resolved = resolve_auditor(synthetic_candidates)
    if resolved["auditor"] != "Ernst & Young LLP":
        print(f"FAILED Synthetic Precedence Test: Selected {resolved['auditor']} instead of Ernst & Young LLP")
        passed = False
        
    if passed:
        print("PASSED Auditor Validation (including precedence and provenance checks)")
    return passed

def main():
    manifest_path = "../manifest.csv"
    pilot_tickers = {"AMGN", "CAT", "CSCO", "COP", "DIS"}
    
    b = run_parser_validation(pilot_tickers, manifest_path)
    c = run_manifest_reconciliation(pilot_tickers, manifest_path)
    d = run_auditor_validation(pilot_tickers)
    
    if b and c and d:
        print("\nAll Validations PASSED.")
    else:
        print("\nSome Validations FAILED.")

if __name__ == "__main__":
    main()
