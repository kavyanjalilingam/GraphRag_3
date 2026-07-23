import re

class MetricCanonicalizer:
    def __init__(self):
        # A simple mapping for Income Statement metrics (RULE_006 context scoping)
        self.income_statement_aliases = {
            "revenue": "Revenue",
            "net sales": "Revenue",
            "total revenues": "Revenue",
            "total revenue": "Revenue",
            "product sales": "Revenue",
            "sales": "Revenue",
            "total sales and revenues": "Revenue",
            
            "gross profit": "Gross Profit",
            "gross margin": "Gross Margin", # Gross Margin must NEVER map to Gross Profit
            
            "operating income": "Operating Income",
            "income from operations": "Operating Income",
            "operating profit": "Operating Income",
            "operating income loss": "Operating Income",
            
            "net income": "Net Income",
            "net earnings": "Net Income",
            "net income loss": "Net Income",
            "profit of consolidated and affiliated companies": "Net Income",
            
            "basic earnings per share": "EPS Basic",
            "diluted earnings per share": "EPS Diluted",
            "basic eps": "EPS Basic",
            "diluted eps": "EPS Diluted",
            "net income per share basic": "EPS Basic",
            "net income per share diluted": "EPS Diluted"
        }
        
        self.balance_sheet_aliases = {
            "total assets": "Total Assets",
            "total liabilities": "Total Liabilities",
            "total stockholders equity": "Total Equity",
            "total shareholders equity": "Total Equity",
            "total equity": "Total Equity"
        }
        
        self.cash_flow_aliases = {
            "net cash provided by operating activities": "Operating Cash Flow",
            "net cash provided by operating activities continuing operations": "Operating Cash Flow",
            "net cash used in operating activities": "Operating Cash Flow",
            "net cash provided by used in operating activities": "Operating Cash Flow",
            
            "net cash used in investing activities": "Investing Cash Flow",
            "net cash provided by investing activities": "Investing Cash Flow",
            "net cash provided by used in investing activities": "Investing Cash Flow",
            
            "net cash used in financing activities": "Financing Cash Flow",
            "net cash provided by financing activities": "Financing Cash Flow",
            "net cash provided by used in financing activities": "Financing Cash Flow",
            
            "capital expenditures": "CapEx",
            "purchases of property plant and equipment": "CapEx",
            "additions to property plant and equipment": "CapEx"
        }
        
    def canonicalize(self, raw_label, statement_context):
        label_lower = raw_label.lower().strip()
        
        # Remove trailing periods, footnotes like (1)
        label_lower = re.sub(r'\(\d+\)', '', label_lower).strip()
        
        # Remove all punctuation and strange apostrophes
        label_lower = re.sub(r'[^\w\s]', '', label_lower)
        label_lower = re.sub(r'\s+', ' ', label_lower).strip()
        
        if statement_context == "IncomeStatement":
            return self.income_statement_aliases.get(label_lower, None)
        elif statement_context == "BalanceSheet":
            return self.balance_sheet_aliases.get(label_lower, None)
        elif statement_context == "CashFlow":
            return self.cash_flow_aliases.get(label_lower, None)
            
        return None
