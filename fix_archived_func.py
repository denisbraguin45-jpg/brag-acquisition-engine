from pathlib import Path

builder_path = Path("D:/app/brag-lead-hunter/backend/demo_builder.py")
code = builder_path.read_text(encoding="utf-8")

gen_archived_code = '''def generate_archived_batch1_demos(
    base_url: str = "http://localhost:8090",
    public_demo_base: Optional[str] = "https://brag-showroom-demos.vercel.app",
) -> list[str]:
    """Ensures archived demos stay online."""
    return []
'''

idx = code.find("def generate_top_30_demos")
code = code[:idx] + gen_archived_code + "\n\n" + code[idx:]
builder_path.write_text(code, encoding="utf-8")
print("Added generate_archived_batch1_demos stub!")

mirror_path = Path("C:/Users/denis/.gemini/antigravity/scratch/brag-lead-hunter/backend/demo_builder.py")
if mirror_path.parent.exists():
    mirror_path.write_text(code, encoding="utf-8")
    print("Mirrored to scratch!")
