from backend import demo_builder
import inspect

source = inspect.getsource(demo_builder.render_hub_index_html)
# Let's find body start
idx = source.find('<body>')
print(source[idx:idx+2500])
