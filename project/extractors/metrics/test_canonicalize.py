import unittest
from canonicalize import MetricCanonicalizer

class TestMetricCanonicalizer(unittest.TestCase):
    def setUp(self):
        self.c = MetricCanonicalizer()
        
    def test_income_statement(self):
        # Revenue variants
        self.assertEqual(self.c.canonicalize("Revenue", "IncomeStatement"), "Revenue")
        self.assertEqual(self.c.canonicalize("Net Sales", "IncomeStatement"), "Revenue")
        self.assertEqual(self.c.canonicalize("Total Revenues", "IncomeStatement"), "Revenue")
        
        # Profit variants
        self.assertEqual(self.c.canonicalize("Gross Profit", "IncomeStatement"), "Gross Profit")
        self.assertEqual(self.c.canonicalize("Gross Margin", "IncomeStatement"), "Gross Margin")
        
        # Check they don't map to each other
        self.assertNotEqual(self.c.canonicalize("Gross Margin", "IncomeStatement"), "Gross Profit")
        
    def test_unknown(self):
        self.assertIsNone(self.c.canonicalize("Random Metric", "IncomeStatement"))
        self.assertIsNone(self.c.canonicalize("Revenue", "BalanceSheet"))

if __name__ == '__main__':
    unittest.main()
