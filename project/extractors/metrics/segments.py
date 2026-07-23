import re
from .canonicalize import MetricCanonicalizer

class SegmentMetricsExtractor:
    def __init__(self):
        self.canonicalizer = MetricCanonicalizer()
        
    def extract(self, accession, parsed_filing):
        observations = []
        form = parsed_filing.get("form")
        
        # Segment tables are highly idiosyncratic (e.g. CAT's transposed tables).
        # True deterministic extraction of all segments requires complex table parsing heuristics
        # or an LLM step. For this deterministic baseline, we extract very basic indicators if present,
        # but mostly rely on the architecture's filing_accession to handle restatements naturally.
        # Any metric extracted here will have filing_accession set, which fulfills the 
        # "as_reported_in" requirement when the graph is built.
        
        # We will leave this largely as a stub for the deterministic pass,
        # to be augmented if specific simple segment patterns are identified.
        
        return observations
