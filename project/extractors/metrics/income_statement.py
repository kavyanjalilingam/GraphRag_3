import re
from .canonicalize import MetricCanonicalizer

class IncomeStatementExtractor:
    def __init__(self):
        self.canonicalizer = MetricCanonicalizer()
        
    def extract(self, accession, parsed_filing):
        observations = []

        form = parsed_filing.get("form")
        
        for idx, section in enumerate(parsed_filing.get("sections", [])):
            text = section.get("text", "")
            
            # Very basic heuristic: find the year header line
            # E.g. "2025 2024 2023"
            year_match = re.search(r'\b(202[0-9])\s+(202[0-9])\s+(202[0-9])\b', text)
            if not year_match:
                year_match = re.search(r'\b(202[0-9])\s+(202[0-9])\b', text)
                
            if not year_match:
                continue
                
            years = year_match.groups()
            
            # Now find lines with a label and matching number of values
            lines = text.split('\n')
            for line in lines:
                # E.g. "Total revenues 36,751 33,424 28,190"
                # E.g. "Net income $ 7,711 $ 4,090 $ 6,717"
                line = line.strip()
                if not line:
                    continue
                    
                # Regex to capture label and then the numbers
                # Numbers can have commas, parentheses (for negatives), and optional $ signs
                # We expect exactly len(years) numbers at the end of the line
                
                num_pattern = r'\$?\s*\(?[\d,]+\)?'
                # Build regex for the end of the line
                end_pattern = r'\s+'.join([f'({num_pattern})'] * len(years)) + r'$'
                
                match = re.search(r'^(.+?)\s+' + end_pattern, line)
                if match:
                    raw_label = match.group(1).strip()
                    canonical_name = self.canonicalizer.canonicalize(raw_label, "IncomeStatement")
                    
                    if canonical_name:
                        values_str = match.groups()[1:]
                        for i, val_str in enumerate(values_str):
                            # clean value
                            is_negative = '(' in val_str
                            # Remove anything that isn't a digit or a period
                            clean_val = re.sub(r'[^\d\.]', '', val_str)
                            if not clean_val:
                                continue
                                
                            val = float(clean_val)
                            
                            # If it's a whole number, cast to int
                            if val.is_integer():
                                val = int(val)
                                
                            if is_negative:
                                val = -val
                                
                            # Basic unit determination
                            unit = "USD_millions"
                            if "EPS" in canonical_name:
                                unit = "USD"
                                
                            observations.append({
                        "extractor": "income_statement",
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
                                    "statement": "IncomeStatement"
                                }
                            })
                            
        return observations
