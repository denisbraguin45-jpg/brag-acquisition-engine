from backend import demo_builder
import inspect

source = inspect.getsource(demo_builder.build_outreach_assets)
print(source[:2000])
