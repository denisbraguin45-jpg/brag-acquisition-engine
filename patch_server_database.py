from pathlib import Path

server_path = Path("D:/app/brag-lead-hunter/server.py")
code = server_path.read_text(encoding="utf-8")

old_block = '''            if path == "/demos/crm_all_leads.json":
                j_file = DEMOS_DIR / "crm_all_leads.json"
                if j_file.exists():
                    self._send_bytes(200, "application/json; charset=utf-8", j_file.read_bytes())
                else:
                    self._send_json(404, {"error": "crm_all_leads.json não encontrado"})
                return'''

new_block = '''            if path == "/demos/crm_all_leads.json":
                j_file = DEMOS_DIR / "crm_all_leads.json"
                if j_file.exists():
                    self._send_bytes(200, "application/json; charset=utf-8", j_file.read_bytes())
                else:
                    self._send_json(404, {"error": "crm_all_leads.json não encontrado"})
                return

            if path == "/demos/database_all_demos.json":
                db_file = DEMOS_DIR / "database_all_demos.json"
                if db_file.exists():
                    self._send_bytes(200, "application/json; charset=utf-8", db_file.read_bytes())
                else:
                    self._send_json(404, {"error": "database_all_demos.json não encontrado"})
                return'''

if old_block in code:
    code = code.replace(old_block, new_block)
    server_path.write_text(code, encoding="utf-8")
    print("Updated server.py with database_all_demos.json route!")
    mirror_path = Path("C:/Users/denis/.gemini/antigravity/scratch/brag-lead-hunter/server.py")
    if mirror_path.parent.exists():
        mirror_path.write_text(code, encoding="utf-8")
        print("Mirrored to scratch server.py!")
