import re

class ShareholderVoteExtractor:
    def extract(self, accession, parsed_filing):
        observations = []
        form = parsed_filing.get("form")
        
        # Shareholder votes are primarily in 8-K under Item 5.07
        if form == "8-K":
            for idx, section in enumerate(parsed_filing.get("sections", [])):
                text = section.get("text", "")
                
                # Check if this section is Item 5.07 or has content about Annual Meeting voting
                has_item = re.search(r'Item\s+5\.07', text, re.IGNORECASE)
                has_content = re.search(r'Annual Meeting', text, re.IGNORECASE) and re.search(r'voting', text, re.IGNORECASE)
                
                if has_item or has_content:
                    # We found a Shareholder Vote event!
                    observations.append({
                        "rule": "RULE_005",
                        "confidence": "high",
                        "source_spans": [f"section_{idx}"],
                        "filing_accession": accession,
                        "data": {
                            "event_type": "ShareholderVote",
                            # We could try to extract event_date from the text, but the 8-K usually has a Cover Page with Event Date
                            "description": "Submission of Matters to a Vote of Security Holders"
                        }
                    })
                    # We only need one event per filing typically, but there might be multiple items
                    break
                    
        # DEF 14A also contains shareholder vote proposals, but usually the EVENT (the vote happening) is the 8-K.
        # If we need to extract from DEF 14A, we can look for "Notice of Annual Meeting of Shareholders".
        elif form == "DEF 14A":
            for idx, section in enumerate(parsed_filing.get("sections", [])):
                text = section.get("text", "")
                if "Notice of Annual Meeting of Shareholders" in text or "Proxy Statement" in text:
                    observations.append({
                        "rule": "RULE_005",
                        "confidence": "medium",
                        "source_spans": [f"section_{idx}"],
                        "filing_accession": accession,
                        "data": {
                            "event_type": "ShareholderVote",
                            "description": "Annual Meeting of Shareholders / Proxy Statement"
                        }
                    })
                    break
                    
        return observations
