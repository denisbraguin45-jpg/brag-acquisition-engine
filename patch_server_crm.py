from pathlib import Path

server_path = Path("D:/app/brag-lead-hunter/server.py")
code = server_path.read_text(encoding="utf-8")

old_block = '''            if path == "/demos/manifest.json":
                m_file = DEMOS_DIR / "manifest.json"
                if not m_file.exists():
                    generate_top_30_demos()
                if m_file.exists():
                    self._send_bytes(200, "application/json; charset=utf-8", m_file.read_bytes())
                else:
                    self._send_json(404, {"error": "Manifest não encontrado"})
                return'''

new_block = '''            if path == "/demos/manifest.json":
                m_file = DEMOS_DIR / "manifest.json"
                if not m_file.exists():
                    generate_top_30_demos()
                if m_file.exists():
                    self._send_bytes(200, "application/json; charset=utf-8", m_file.read_bytes())
                else:
                    self._send_json(404, {"error": "Manifest não encontrado"})
                return

            if path == "/demos/crm.html":
                crm_file = DEMOS_DIR / "crm.html"
                if crm_file.exists():
                    self._send_bytes(200, "text/html; charset=utf-8", crm_file.read_bytes())
                else:
                    self._send_json(404, {"error": "crm.html não encontrado"})
                return

            if path == "/demos/crm_all_leads.json":
                j_file = DEMOS_DIR / "crm_all_leads.json"
                if j_file.exists():
                    self._send_bytes(200, "application/json; charset=utf-8", j_file.read_bytes())
                else:
                    self._send_json(404, {"error": "crm_all_leads.json não encontrado"})
                return

            if path == "/demos/crm_all_leads.csv":
                c_file = DEMOS_DIR / "crm_all_leads.csv"
                if c_file.exists():
                    self._send_bytes(200, "text/csv; charset=utf-8", c_file.read_bytes())
                else:
                    self._send_json(404, {"error": "crm_all_leads.csv não encontrado"})
                return'''

if old_block in code:
    code = code.replace(old_block, new_block)
    server_path.write_text(code, encoding="utf-8")
    print("Updated server.py with CRM static files routes!")
    mirror_path = Path("C:/Users/denis/.gemini/antigravity/scratch/brag-lead-hunter/server.py")
    if mirror_path.parent.exists():
        mirror_path.write_text(code, encoding="utf-8")
        print("Mirrored server.py to scratch!")
else:
    print("Warning: old_block not found in server.py")
