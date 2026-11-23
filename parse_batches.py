from backend import demo_builder
import inspect
import re

source = inspect.getsource(demo_builder)
# find EXCLUDED_SLUGS block
idx1 = source.find("EXCLUDED_SLUGS = {")
idx2 = source.find("}", idx1)
block = source[idx1:idx2]

batches = []
current_batch = "Outros"
current_slugs = []

for line in block.splitlines():
    line_s = line.strip()
    if line_s.startswith("#"):
        if current_slugs:
            batches.append((current_batch, current_slugs))
            current_slugs = []
        current_batch = line_s.lstrip("#").strip()
    elif line_s.startswith('"'):
        slug = line_s.replace('"', '').replace(',', '').strip()
        if slug and slug != "pecas-para-carros-nacionais-e-importados":
            current_slugs.append(slug)

if current_slugs:
    batches.append((current_batch, current_slugs))

print(f"Total batches detected in EXCLUDED_SLUGS: {len(batches)}")
for name, slugs in batches:
    print(f" - {name}: {len(slugs)} slugs")
