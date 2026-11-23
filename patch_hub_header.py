from pathlib import Path

builder_path = Path("D:/app/brag-lead-hunter/backend/demo_builder.py")
code = builder_path.read_text(encoding="utf-8")

old_header_right = '''      <div class="tabular" style="font-size:var(--text-xs);color:var(--color-emerald);text-align:right;">
        <div>60/60 SHOWROOMS ONLINE</div>
        <div style="color:var(--color-text-secondary);margin-top:2px;">30 DENIS · 30 GABRIEL</div>
      </div>'''

new_header_right = '''      <div style="display:flex;flex-direction:column;align-items:flex-end;gap:0.5rem;">
        <div class="tabular" style="font-size:var(--text-xs);color:var(--color-emerald);text-align:right;">
          <div>60/60 SHOWROOMS ONLINE</div>
          <div style="color:var(--color-text-secondary);margin-top:2px;">30 DENIS · 30 GABRIEL</div>
        </div>
        <a href="/demos/crm.html" class="btn-top btn-top-gold" style="text-decoration:none;font-size:0.8rem;padding:0.45rem 0.85rem;background:rgba(223,184,88,0.18);border:1px solid #dfb858;color:#f7f7ee;display:inline-flex;align-items:center;gap:6px;font-weight:700;">
          📂 CRM Completo (328 Demos)
        </a>
      </div>'''

if old_header_right in code:
    code = code.replace(old_header_right, new_header_right)
    builder_path.write_text(code, encoding="utf-8")
    print("Updated demo_builder.py with CRM button in hub header!")
    
    mirror_path = Path("C:/Users/denis/.gemini/antigravity/scratch/brag-lead-hunter/backend/demo_builder.py")
    if mirror_path.parent.exists():
        mirror_path.write_text(code, encoding="utf-8")
        print("Mirrored to scratch!")
else:
    print("Could not find old_header_right in demo_builder.py")
