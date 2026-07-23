import re
import json

CANONICAL_NAMES = {
    "AMGN": "Amgen Inc.",
    "CAT": "Caterpillar Inc.",
    "CSCO": "Cisco Systems, Inc.",
    "COP": "ConocoPhillips",
    "DIS": "The Walt Disney Company"
}

def extract_metadata(parsed_json_path, manifest_info):
    with open(parsed_json_path, 'r', encoding='utf-8') as f:
        parsed = json.load(f)
        
    form = parsed["form"]
    ticker = manifest_info.get("ticker")
    cover_text = ""
    for sec in parsed["sections"]:
        if sec.get("type") == "Cover":
            cover_text = sec.get("text", "")
            break
            
    # Registrant Name
    raw_name = manifest_info.get("name", "Unknown")
    lines = [line.strip() for line in cover_text.split('\n') if line.strip()]
    for i, line in enumerate(lines):
        if "(Exact name of" in line or "(EXACT NAME OF" in line.upper():
            if i > 0:
                raw_name = lines[i-1]
                # If we only grabbed 'INC.', grab the line before it as well
                if raw_name.upper() in ["INC.", "INC", "CORP.", "CORP", "CORPORATION", "COMPANY"] and i > 1:
                    raw_name = lines[i-2] + " " + raw_name
            break
            
    event_date = None
    if form == "8-K":
        match = re.search(r'Date of Report[^\n:]*:\s*(.+)', cover_text, re.IGNORECASE)
        if match:
            event_date = match.group(1).strip()
            
    fiscal_year_end = None
    if form == "10-K":
        match = re.search(r'For the fiscal year ended\s*(.+)', cover_text, re.IGNORECASE)
        if match:
            fiscal_year_end = match.group(1).strip()

    metadata = {
        "ticker": ticker,
        "form": form,
        "accession": manifest_info.get("accession"),
        "filing_date": manifest_info.get("filing_date"),
        "raw_registrant_name": raw_name,
        "registrant_name": CANONICAL_NAMES.get(ticker, raw_name),
    }
    
    if event_date:
        metadata["event_date"] = event_date
    if fiscal_year_end:
        metadata["fiscal_year_end"] = fiscal_year_end
        
    return metadata
