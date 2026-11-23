from backend import demo_builder
import inspect

source = inspect.getsource(demo_builder.render_demo_html)
print(source[:1200])
