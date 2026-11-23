from backend import demo_builder
import inspect

source = inspect.getsource(demo_builder.render_hub_index_html)
idx = source.find('partner-switcher')
print(source[idx:idx+2500])
