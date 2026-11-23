import sys
from backend import demo_builder

print("Total themes in DESIGN_THEMES:", len(demo_builder.DESIGN_THEMES))
for t in demo_builder.DESIGN_THEMES:
    print(t["id"], t["archetype"])
