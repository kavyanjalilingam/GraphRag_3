import json
import os
from extractors.events.shareholder_vote import ShareholderVoteExtractor
from extractors.events.officer_director import OfficerDirectorExtractor
from extractors.events.other_events import OtherEventsExtractor

def main():
    extractors = [
        ShareholderVoteExtractor(),
        OfficerDirectorExtractor(),
        OtherEventsExtractor()
    ]
    
    if not os.path.exists("artifacts"):
        return
        
    for entry in os.listdir("artifacts"):
        d = os.path.join("artifacts", entry)
        if not os.path.isdir(d):
            continue
            
        parsed_path = os.path.join(d, "parsed.json")
        if not os.path.exists(parsed_path):
            continue
            
        with open(parsed_path, "r", encoding="utf-8") as f:
            parsed = json.load(f)
            
        accession = entry
        
        metadata_path = os.path.join(d, "metadata.json")
        ticker = "UNKNOWN"
        form = "UNKNOWN"
        event_date = None
        if os.path.exists(metadata_path):
            with open(metadata_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
                ticker = meta.get("ticker", "UNKNOWN")
                form = meta.get("form", "UNKNOWN")
                event_date = meta.get("event_date", None)
                
        print(f"Extracting events for {accession} ({ticker} {form})")
        
        observations = []
        for ext in extractors:
            obs = ext.extract(accession, parsed)
            for o in obs:
                # Inject event_date from metadata if not present
                if "event_date" not in o["data"] and event_date:
                    o["data"]["event_date"] = event_date
            observations.extend(obs)
            
        # Deduplicate
        unique_obs = []
        seen = set()
        for obs in observations:
            key = (obs["data"]["event_type"], obs["data"].get("event_date"))
            if key not in seen:
                seen.add(key)
                unique_obs.append(obs)
            else:
                for existing in unique_obs:
                    if (existing["data"]["event_type"], existing["data"].get("event_date")) == key:
                        existing["source_spans"].extend(x for x in obs["source_spans"] if x not in existing["source_spans"])
                        break
                        
        events_path = os.path.join(d, "events.json")
        with open(events_path, "w", encoding="utf-8") as f:
            json.dump(unique_obs, f, indent=2)

if __name__ == "__main__":
    main()
