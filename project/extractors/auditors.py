import re
import json

BIG_4_REGEX = re.compile(r'(PricewaterhouseCoopers\s*(?:LLP)?|Ernst\s*&\s*Young\s*(?:LLP)?|Deloitte\s*(?:&\s*Touche\s*)?(?:LLP)?|KPMG\s*(?:LLP)?)', re.IGNORECASE)

def normalize_auditor_name(name):
    name = name.strip()
    # capitalize appropriately
    if "pricewaterhouse" in name.lower():
        return "PricewaterhouseCoopers LLP"
    if "ernst" in name.lower():
        return "Ernst & Young LLP"
    if "deloitte" in name.lower():
        return "Deloitte & Touche LLP"
    if "kpmg" in name.lower():
        return "KPMG LLP"
    return name

def extract_candidates(accession, parsed_filing):
    candidates = []
    form = parsed_filing.get("form")
    sections = parsed_filing.get("sections", [])
    
    for idx, sec in enumerate(sections):
        text = sec.get("text", "")
        if not text:
            continue
            
        # 1. Audit Signature (10-K)
        if form == "10-K":
            sig_match = re.search(r'/s/\s*' + BIG_4_REGEX.pattern, text, re.IGNORECASE)
            if sig_match:
                candidates.append({
                    "auditor": normalize_auditor_name(sig_match.group(1)),
                    "confidence": "high",
                    "source_type": "audit_signature",
                    "source_span_id": f"section_{idx}",
                    "filing_accession": accession,
                    "extraction_rule": "RULE_004"
                })
                
        # 2. DEF14A Ratification
        if form == "DEF 14A":
            rat_match = re.search(r'(?:ratifi\w+|appointment).{0,200}?' + BIG_4_REGEX.pattern, text, re.IGNORECASE | re.DOTALL)
            if rat_match:
                candidates.append({
                    "auditor": normalize_auditor_name(rat_match.group(1)),
                    "confidence": "high",
                    "source_type": "def14a_ratification",
                    "source_span_id": f"section_{idx}",
                    "filing_accession": accession,
                    "extraction_rule": "RULE_004"
                })
                
        # 3. 8-K Vote (Item 5.07)
        if form == "8-K" and sec.get("item") == "5.07":
            vote_match = re.search(r'(?:ratifi\w+|appointment).{0,200}?' + BIG_4_REGEX.pattern, text, re.IGNORECASE | re.DOTALL)
            if vote_match:
                candidates.append({
                    "auditor": normalize_auditor_name(vote_match.group(1)),
                    "confidence": "high",
                    "source_type": "8k_vote",
                    "source_span_id": f"section_{idx}",
                    "filing_accession": accession,
                    "extraction_rule": "RULE_004"
                })
                
        # 4. Committee Selection
        # Must be in the exact same sentence to reduce false positives
        sentences = text.split('.')
        for sentence in sentences:
            s_lower = sentence.lower()
            if "audit committee" in s_lower:
                if "financial expert" in s_lower or "partner at" in s_lower or "served as" in s_lower:
                    continue
                auditor_match = BIG_4_REGEX.search(sentence)
                if auditor_match:
                    candidates.append({
                        "auditor": normalize_auditor_name(auditor_match.group(1)),
                        "confidence": "medium",
                        "source_type": "committee_selection",
                        "source_span_id": f"section_{idx}",
                        "filing_accession": accession,
                        "extraction_rule": "RULE_004"
                    })
                    break # only need one match per section
                
    return candidates

def deduplicate_candidates(candidates):
    seen = {}
    for c in candidates:
        key = (c["auditor"], c["source_type"], c["filing_accession"])
        if key not in seen:
            new_c = c.copy()
            new_c["source_spans"] = [new_c.pop("source_span_id")]
            seen[key] = new_c
        else:
            if c["source_span_id"] not in seen[key]["source_spans"]:
                seen[key]["source_spans"].append(c["source_span_id"])
    return list(seen.values())

def resolve_auditor(candidates):
    if not candidates:
        return {
            "auditor": "unknown",
            "confidence": "low",
            "source_type": "unknown",
            "source_spans": ["unknown"],
            "filing_accession": "unknown",
            "extraction_rule": "RULE_004"
        }
        
    PRECEDENCE = {
        "audit_signature": 1,
        "def14a_ratification": 2,
        "8k_vote": 3,
        "committee_selection": 4
    }
    
    candidates.sort(key=lambda c: PRECEDENCE.get(c["source_type"], 99))
    
    return candidates[0]

def extract_auditor_for_ticker(ticker, filings_dict):
    all_candidates = []
    for acc, parsed in filings_dict.items():
        all_candidates.extend(extract_candidates(acc, parsed))
        
    all_candidates = deduplicate_candidates(all_candidates)
    
    return resolve_auditor(all_candidates), all_candidates
