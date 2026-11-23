from backend import demo_builder
import inspect

source = inspect.getsource(demo_builder.generate_top_30_demos)
# find all occurrences of index.html
import re
for m in re.finditer(r'index\.html', source):
    start = max(0, m.start() - 150)
    end = min(len(source), m.end() + 250)
    print("--- MATCH ---")
    print(source[start:end])
