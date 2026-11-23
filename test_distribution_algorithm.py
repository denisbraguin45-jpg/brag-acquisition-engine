import json
from pathlib import Path
from collections import Counter

demos_dir = Path("D:/app/brag-lead-hunter/demos")
with open(demos_dir / "database_all_demos.json", "r", encoding="utf-8") as f:
    records = json.load(f)

# Sort all records by score descending, then priority A before B, then name
def sort_key(r):
    # Highest score first (-score)
    # Priority 'A' first
    prio_order = 0 if r.get("priority") == "A" else 1
    return (-r.get("score", 0), prio_order, r.get("name", ""))

sorted_records = sorted(records, key=sort_key)

# We want 400 valid leads
top_400 = sorted_records[:400]
print(f"Top 400 score range: {top_400[-1].get('score')} to {top_400[0].get('score')}")
print(f"Top 400 priorities: {Counter(r.get('priority') for r in top_400)}")

# Proportional distribution between Bruce and Gabriel
# Group into tiers: High (Score >= 95), Medium (Score 85-94), Low (Score < 85)
high = [r for r in top_400 if r.get("score", 0) >= 95]
med = [r for r in top_400 if 85 <= r.get("score", 0) < 95]
low = [r for r in top_400 if r.get("score", 0) < 85]

print(f"High potential (>=95): {len(high)}")
print(f"Medium potential (85-94): {len(med)}")
print(f"Low potential (<85): {len(low)}")
print(f"Sum: {len(high) + len(med) + len(low)}")

# Distribute alternately (serpentine / round-robin) in each tier
bruce = []
gabriel = []

for tier in [high, med, low]:
    for i, lead in enumerate(tier):
        # Alternate to keep exactly 50%
        if (len(bruce) <= len(gabriel) and len(bruce) < 200) or len(gabriel) == 200:
            bruce.append(lead)
        else:
            gabriel.append(lead)

print(f"Bruce leads: {len(bruce)}")
print(f"Gabriel leads: {len(gabriel)}")

bruce_high = sum(1 for r in bruce if r.get("score", 0) >= 95)
gabriel_high = sum(1 for r in gabriel if r.get("score", 0) >= 95)
bruce_med = sum(1 for r in bruce if 85 <= r.get("score", 0) < 95)
gabriel_med = sum(1 for r in gabriel if 85 <= r.get("score", 0) < 95)
bruce_low = sum(1 for r in bruce if r.get("score", 0) < 85)
gabriel_low = sum(1 for r in gabriel if r.get("score", 0) < 85)

print(f"Bruce distribution -> High: {bruce_high}, Med: {bruce_med}, Low: {bruce_low}")
print(f"Gabriel distribution -> High: {gabriel_high}, Med: {gabriel_med}, Low: {gabriel_low}")
