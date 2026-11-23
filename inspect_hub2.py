from backend import demo_builder
import inspect

source = inspect.getsource(demo_builder.render_hub_index_html)
print(source[1500:3500])
