import re

class OtherEventsExtractor:
    def extract(self, accession, parsed_filing):
        observations = []
        form = parsed_filing.get("form")
        
        if form == "8-K":
            for idx, section in enumerate(parsed_filing.get("sections", [])):
                text = section.get("text", "")
                
                # Item 1.01 Entry into a Material Definitive Agreement
                if re.search(r'Item\s+1\.01', text, re.IGNORECASE):
                    observations.append({
                        "extractor": "other_events",
                        "rule": "RULE_005",
                        "confidence": "high",
                        "source_spans": [f"section_{idx}"],
                        "filing_accession": accession,
                        "data": {
                            "event_type": "MaterialAgreement",
                            "description": "Entry into a Material Definitive Agreement"
                        }
                    })
                    
                # Item 2.01 Completion of Acquisition or Disposition of Assets
                if re.search(r'Item\s+2\.01', text, re.IGNORECASE) or re.search(r'Acquisition', text, re.IGNORECASE) and re.search(r'Item\s+8\.01', text, re.IGNORECASE):
                    # Sometimes acquisitions are announced in 8.01 Other Events
                    observations.append({
                        "extractor": "other_events",
                        "rule": "RULE_005",
                        "confidence": "high",
                        "source_spans": [f"section_{idx}"],
                        "filing_accession": accession,
                        "data": {
                            "event_type": "Acquisition",
                            "description": "Acquisition or Disposition of Assets"
                        }
                    })
                    
                # Item 2.02 Results of Operations and Financial Condition (Earnings)
                if re.search(r'Item\s+2\.02', text, re.IGNORECASE):
                    observations.append({
                        "extractor": "other_events",
                        "rule": "RULE_005",
                        "confidence": "high",
                        "source_spans": [f"section_{idx}"],
                        "filing_accession": accession,
                        "data": {
                            "event_type": "Earnings",
                            "description": "Results of Operations and Financial Condition"
                        }
                    })
                    
                # Dividends can be in 8.01 or 7.01
                if re.search(r'dividend', text, re.IGNORECASE) and (re.search(r'Item\s+8\.01', text, re.IGNORECASE) or re.search(r'Item\s+7\.01', text, re.IGNORECASE)):
                    observations.append({
                        "extractor": "other_events",
                        "rule": "RULE_005",
                        "confidence": "high",
                        "source_spans": [f"section_{idx}"],
                        "filing_accession": accession,
                        "data": {
                            "event_type": "Dividend",
                            "description": "Dividend Announcement"
                        }
                    })
                    
        return observations
