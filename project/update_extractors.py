import os
import re

for dir_path in ['extractors/events', 'extractors/metrics']:
    for f in os.listdir(dir_path):
        if not f.endswith('.py') or f == '__init__.py' or f == 'canonicalize.py' or f == 'test_canonicalize.py': continue
        p = os.path.join(dir_path, f)
        with open(p, 'r') as file:
            content = file.read()
        
        extractor_name = f.replace('.py', '')
        
        # We find observations.append({ and inject the extractor field
        new_content = re.sub(r'observations\.append\(\{', f'observations.append({{\n                        "extractor": "{extractor_name}",', content)
        
        with open(p, 'w') as file:
            file.write(new_content)
        print(f'Updated {f}')
