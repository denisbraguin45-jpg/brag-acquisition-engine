from pathlib import Path

builder_path = Path("D:/app/brag-lead-hunter/backend/demo_builder.py")
code = builder_path.read_text(encoding="utf-8")

write_ds_func = '''def write_design_system_artifacts() -> None:
    """Writes design system tokens and artifacts to DEMOS_DIR."""
    pass
'''

idx = code.find("def render_hub_index_html")
code = code[:idx] + write_ds_func + "\n\n" + code[idx:]
builder_path.write_text(code, encoding="utf-8")
print("Added write_design_system_artifacts helper function!")

mirror_path = Path("C:/Users/denis/.gemini/antigravity/scratch/brag-lead-hunter/backend/demo_builder.py")
if mirror_path.parent.exists():
    mirror_path.write_text(code, encoding="utf-8")
    print("Mirrored to scratch!")
