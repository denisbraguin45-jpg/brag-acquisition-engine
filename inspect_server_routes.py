from pathlib import Path

code = Path("D:/app/brag-lead-hunter/server.py").read_text(encoding="utf-8")
idx = code.find("/demos/manifest.json")
print(code[idx-100:idx+800])
