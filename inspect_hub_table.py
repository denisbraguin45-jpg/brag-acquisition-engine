from backend import demo_builder
import inspect

source = inspect.getsource(demo_builder.render_hub_index_html)
idx = source.find('<table')
print(source[idx:idx+1500])
