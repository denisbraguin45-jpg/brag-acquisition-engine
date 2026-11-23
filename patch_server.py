from pathlib import Path

server_file = Path("D:/app/brag-lead-hunter/server.py")
code = server_file.read_text(encoding="utf-8")

old_block = '''            if path.startswith("/demos/"):
                rel_parts = [p for p in path.split("/demos/")[1].split("/") if p and p != ".."]
                if not rel_parts:
                    self._send_json(404, {"error": "Demo não especificada"})
                    return'''

new_block = '''            if path == "/demos" or path == "/demos/":
                hub_file = DEMOS_DIR / "index.html"
                if not hub_file.exists():
                    generate_top_30_demos()
                if hub_file.exists():
                    self._send_bytes(200, "text/html; charset=utf-8", hub_file.read_bytes())
                else:
                    self._send_json(404, {"error": "Hub index não encontrado"})
                return

            if path == "/demos/manifest.json":
                m_file = DEMOS_DIR / "manifest.json"
                if not m_file.exists():
                    generate_top_30_demos()
                if m_file.exists():
                    self._send_bytes(200, "application/json; charset=utf-8", m_file.read_bytes())
                else:
                    self._send_json(404, {"error": "Manifest não encontrado"})
                return

            if path.startswith("/demos/"):
                rel_parts = [p for p in path.split("/demos/")[1].split("/") if p and p != ".."]
                if not rel_parts:
                    self._send_json(404, {"error": "Demo não especificada"})
                    return'''

if old_block in code:
    code = code.replace(old_block, new_block)
    server_file.write_text(code, encoding="utf-8")
    print("server.py updated successfully!")
    mirror_file = Path("C:/Users/denis/.gemini/antigravity/scratch/brag-lead-hunter/server.py")
    if mirror_file.parent.exists():
        mirror_file.write_text(code, encoding="utf-8")
        print("Mirrored server.py to scratch!")
else:
    print("Warning: old_block not found in server.py")
