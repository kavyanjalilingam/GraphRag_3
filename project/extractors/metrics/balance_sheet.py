import re
from .canonicalize import MetricCanonicalizer

class BalanceSheetExtractor:
    def __init__(self):
        self.canonicalizer = MetricCanonicalizer()
        
    def extract(self, accession, parsed_filing):
        observations = []

        form = parsed_filing.get("form")
        
        for idx, section in enumerate(parsed_filing.get("sections", [])):
            text = section.get("text", "")
            
            # Balance sheet usually has 2 years (e.g. 2025 2024)
            year_match = re.search(r'\b(202[0-9])\s+(202[0-9])\b', text)
            if not year_match:
                continue
                
            years = year_match.groups()
            
            lines = text.split('\n')
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                num_pattern = r'\$?\s*\(?[\d,]+\)?'
                end_pattern = r'\s+'.join([f'({num_pattern})'] * len(years)) + r'$'
                
                match = re.search(r'^(.+?)\s+' + end_pattern, line)
                if match:
                    raw_label = match.group(1).strip()
                    canonical_name = self.canonicalizer.canonicalize(raw_label, "BalanceSheet")
                    
                    if canonical_name:
                        values_str = match.groups()[1:]
                        for i, val_str in enumerate(values_str):
                            is_negative = '(' in val_str
                            clean_val = re.sub(r'[^\d\.]', '', val_str)
                            if not clean_val:
                                continue
                                
                            val = float(clean_val)
                            if val.is_integer():
                                val = int(val)
                                
                            if is_negative:
                                val = -val
                                
                            unit = "USD_millions"
                                
                            observations.append({
                        "extractor": "balance_sheet",
                                "rule": "RULE_006",
                                "confidence": "medium",
                                "source_spans": [f"section_{idx}"],
                                "filing_accession": accession,
                                "data": {
                                    "metric_definition": canonical_name,
                                    "raw_label": raw_label,
                                    "value": val,
                                    "unit": unit,
                                    "period": f"FY{years[i]}",
                                    "statement": "BalanceSheet"
                                }
                            })
                            
        return observations
