from backend import demo_builder
import inspect

source = inspect.getsource(demo_builder.build_dashboard_html)
print(source[:1500])
