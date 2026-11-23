from backend import demo_builder
import inspect

source = inspect.getsource(demo_builder.generate_top_30_demos)
print(source[source.find("for p_rank, lead in enumerate(top_denis_30"):])
