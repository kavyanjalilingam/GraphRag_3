import re
import json
import os

def detect_form(text):
    head = text[:2000].upper()
    if "FORM 8-K" in head:
        return "8-K"
    elif "FORM 10-K" in head:
        return "10-K"
    elif "SCHEDULE 14A" in head or "DEF 14A" in head or "DEF14A" in head:
        return "DEF 14A"
    return "UNKNOWN"

def split_sections(text, form):
    sections = []
    
    if form == "8-K":
        pattern = re.compile(r'^(Item\s+\d\.\d{2})\.?\s*(.*)$|^(SIGNATURES?)\s*$', re.MULTILINE | re.IGNORECASE)
    elif form == "10-K":
        pattern = re.compile(r'^(PART\s+[IVX]+)\s*(.*)$|^(Item\s+\d+[A-Z]?)\.?\s*(.*)$|^(SIGNATURES?)\s*$', re.MULTILINE | re.IGNORECASE)
    elif form == "DEF 14A":
        pattern = re.compile(r'^(PROPOSAL\s+\d+)\s*(.*)$|^(Item\s+\d+)\.?\s*(.*)$|^(SIGNATURES?)\s*$', re.MULTILINE | re.IGNORECASE)
    else:
        pattern = re.compile(r'^(Item\s+\d+)\.?\s*(.*)$|^(SIGNATURES?)\s*$', re.MULTILINE | re.IGNORECASE)
        
    # Find all matches
    matches = list(pattern.finditer(text))
    
    if matches:
        first_match_start = matches[0].start()
        sections.append({
            "type": "Cover",
            "text": text[:first_match_start].strip()
        })
        
        for i, match in enumerate(matches):
            start = match.start()  # We want the full text of the section or just the body?
            # actually we can just store the body
            body_start = match.end()
            end = matches[i+1].start() if i + 1 < len(matches) else len(text)
            
            # Extract heading info
            heading = ""
            for g in match.groups():
                if g:
                    heading = g.strip()
                    break
                    
            sec = {}
            upper_heading = heading.upper()
            if upper_heading.startswith("ITEM"):
                sec["item"] = heading[4:].strip()
                if sec["item"].endswith('.'):
                    sec["item"] = sec["item"][:-1]
            elif upper_heading.startswith("SIGNATURE"):
                sec["type"] = "Signature"
            elif upper_heading.startswith("PART"):
                sec["part"] = heading[4:].strip()
            elif upper_heading.startswith("PROPOSAL"):
                sec["proposal"] = heading[8:].strip()
            else:
                sec["type"] = heading
                
            sec["text"] = text[body_start:end].strip()
            sections.append(sec)
    else:
        sections.append({
            "type": "Cover",
            "text": text.strip()
        })
        
    return sections

def parse_filing(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        text = f.read()
    
    form = detect_form(text)
    sections = split_sections(text, form)
    
    return {
        "form": form,
        "sections": sections
    }

def main():
    import sys
    if len(sys.argv) > 1:
        filepath = sys.argv[1]
        out = parse_filing(filepath)
        print(json.dumps({
            "form": out["form"],
            "sections": [{k: v for k, v in s.items() if k != "text"} for s in out["sections"]]
        }, indent=2))

if __name__ == "__main__":
    main()
