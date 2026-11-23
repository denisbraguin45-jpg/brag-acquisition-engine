import json
from pathlib import Path
from collections import Counter

demos_dir = Path("D:/app/brag-lead-hunter/demos")
with open(demos_dir / "database_all_demos.json", "r", encoding="utf-8") as f:
    records = json.load(f)

print(f"Total records: {len(records)}")

# Check duplicates by slug, name, phone, etc.
slug_counts = Counter(r.get("slug") for r in records)
phone_counts = Counter(r.get("whatsapp_e164") for r in records if r.get("whatsapp_e164"))
name_counts = Counter(r.get("name") for r in records)

print(f"Unique slugs: {len(slug_counts)}")
print(f"Unique phones: {len(phone_counts)}")
print(f"Unique names: {len(name_counts)}")

# Priorities & scores
priorities = Counter(r.get("priority") for r in records)
scores = [r.get("score", 0) for r in records]
print(f"Priorities: {priorities}")
print(f"Score min: {min(scores)}, max: {max(scores)}, avg: {sum(scores)/len(scores):.1f}")

# Owners currently
owners = Counter(r.get("owner") for r in records)
print(f"Current owners: {owners}")
