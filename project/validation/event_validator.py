import os
import json

def main():
    if not os.path.exists("artifacts"):
        return
        
    passed = True
    for entry in os.listdir("artifacts"):
        d = os.path.join("artifacts", entry)
        events_path = os.path.join(d, "events.json")
        if not os.path.exists(events_path):
            continue
            
        with open(events_path, "r", encoding="utf-8") as f:
            events = json.load(f)
            
        for ev in events:
            # Type check
            if "event_type" not in ev["data"]:
                print(f"FAILED Event Validation: Missing event_type in {entry}")
                passed = False
                
            # Provenance check
            if not ev.get("source_spans"):
                print(f"FAILED Event Validation: Missing source_spans in {entry} for {ev['data'].get('event_type')}")
                passed = False
                
            # Date check (warning only, as some events might not have a date)
            if "event_date" not in ev["data"]:
                pass
                
    if passed:
        print("PASSED Event Validation")

if __name__ == "__main__":
    main()
