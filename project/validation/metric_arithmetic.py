import json
import os
import glob

def validate_metrics():
    passed = True
    
    artifact_dirs = [d for d in os.listdir("artifacts") if os.path.isdir(os.path.join("artifacts", d))]
    
    for entry in artifact_dirs:
        d = os.path.join("artifacts", entry)
        metrics_path = os.path.join(d, "metrics.json")
        if not os.path.exists(metrics_path):
            continue
            
        with open(metrics_path, "r", encoding="utf-8") as f:
            metrics = json.load(f)
            
        # Group by period and statement
        by_period = {}
        for m in metrics:
            p = m["data"]["period"]
            if p not in by_period:
                by_period[p] = {}
                
            name = m["data"]["metric_definition"]
            # Detect duplicates
            if name in by_period[p]:
                # If they have the same value, it's just multiple mentions
                if by_period[p][name]["value"] != m["data"]["value"]:
                    print(f"FAILED Metric Validation: Contradictory {name} for {p} in {entry}: {by_period[p][name]['value']} vs {m['data']['value']}")
                    passed = False
            else:
                by_period[p][name] = m["data"]
                
        # Basic arithmetic checks for IncomeStatement
        for p, metrics_dict in by_period.items():
            revenue = metrics_dict.get("Revenue")
            net_income = metrics_dict.get("Net Income")
            
            # 1. Net Income should not be > Revenue (sanity check)
            if revenue and net_income:
                if net_income["value"] > revenue["value"] and revenue["value"] > 0:
                    print(f"FAILED Metric Validation: Net Income ({net_income['value']}) > Revenue ({revenue['value']}) for {p} in {entry}")
                    passed = False
                    
            assets = metrics_dict.get("Total Assets")
            equity = metrics_dict.get("Total Equity")
            liabilities = metrics_dict.get("Total Liabilities")
            
            # 2. Equity should not be > Assets (unless negative, but usually Assets > Equity)
            if assets and equity:
                if equity["value"] > assets["value"] and assets["value"] > 0:
                    print(f"FAILED Metric Validation: Equity ({equity['value']}) > Assets ({assets['value']}) for {p} in {entry}")
                    passed = False
            for name, m_data in metrics_dict.items():
                if "EPS" in name:
                    # EPS is usually small (e.g., $1.00 - $100.00)
                    # We extracted EPS as int, meaning $14.33 became 14. We should probably parse floats
                    pass

    return passed

if __name__ == "__main__":
    if validate_metrics():
        print("PASSED Metric Validation")
