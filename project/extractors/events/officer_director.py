import re

class OfficerDirectorExtractor:
    def extract(self, accession, parsed_filing):
        observations = []
        form = parsed_filing.get("form")
        
        # Officer/Director changes are primarily in 8-K under Item 5.02
        if form == "8-K":
            for idx, section in enumerate(parsed_filing.get("sections", [])):
                text = section.get("text", "")
                
                # Check if this section is Item 5.02 or has content about Officer/Director changes
                has_item = re.search(r'Item\s+5\.02', text, re.IGNORECASE)
                
                content_patterns = [
                    r'Retirement of.*(Chief|President|Officer|Director)',
                    r'Departure of.*(Chief|President|Officer|Director)',
                    r'Appointment of.*(Chief|President|Officer|Director)',
                    r'Election of.*Director',
                    r'Chief Financial Officer',
                    r'Chief Executive Officer'
                ]
                has_content = any(re.search(p, text, re.IGNORECASE) for p in content_patterns)
                
                if has_item or has_content:
                    observations.append({
                        "rule": "RULE_005",
                        "confidence": "high",
                        "source_spans": [f"section_{idx}"],
                        "filing_accession": accession,
                        "data": {
                            "event_type": "OfficerDirectorChange",
                            "description": "Departure, Election, or Appointment of Directors/Officers"
                        }
                    })
                    break
                    
        return observations
