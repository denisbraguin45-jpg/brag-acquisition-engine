import urllib.request
import re

def test_ddg(username):
    url = f"https://html.duckduckgo.com/html/?q=site:instagram.com/{username}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=5) as resp:
            content = resp.read().decode("utf-8", errors="ignore")
            snippets = re.findall(r'<a class="result__snippet"[^>]*>(.*?)</a>', content, re.DOTALL)
            clean = [re.sub(r'<[^>]+>', '', s).strip() for s in snippets]
            print(f"@{username}:")
            for c in clean[:2]:
                print(f"  {c}")
    except Exception as e:
        print(f"@{username} error: {e}")

test_ddg("guilherme_motors_multimarcas")
test_ddg("uz_veiculos")
test_ddg("vmotors.multimarcas")
