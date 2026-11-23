from backend import demo_builder
import inspect

source = inspect.getsource(demo_builder.generate_top_30_demos)
# find how index.html is generated
idx = source.find("index.html")
if idx != -1:
    print(source[idx-200:idx+600])
