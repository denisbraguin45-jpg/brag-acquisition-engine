import shutil
from pathlib import Path

SRC = Path("D:/app/brag-lead-hunter")
DST = Path("C:/Users/denis/.gemini/antigravity/scratch/brag-lead-hunter")

if not DST.exists():
    DST.mkdir(parents=True, exist_ok=True)

files_to_sync = [
    "server.py",
    "backend/sales_db.py",
    "backend/sales_distribution.py",
    "backend/sales_service.py",
    "backend/sales_ui.py",
    "demos/sales.html",
    "demos/index.html",
    "demos/sales_distribution_400.json",
]

for rel in files_to_sync:
    s = SRC / rel
    d = DST / rel
    if s.exists():
        d.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(s, d)
        print(f"Synced {rel} -> {d}")
    else:
        print(f"Source missing: {s}")

print("Mirroring completed successfully!")
