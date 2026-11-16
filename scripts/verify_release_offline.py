from pathlib import Path
import hashlib, json, re
root=Path(__file__).resolve().parents[1]
files=[p for p in root.rglob('*') if p.is_file() and p.name!='RELEASE_MANIFEST.json']
leaks=[]
for p in files:
 text=p.read_text(encoding='utf-8',errors='ignore')
 if re.search(r'C:[\\/]Users[\\/]|sk-[A-Za-z0-9]{20,}|ghp_[A-Za-z0-9]{20,}',text): leaks.append(str(p.relative_to(root)))
print(json.dumps({'files':len(files),'leaks':leaks},indent=2))
raise SystemExit(1 if leaks else 0)
