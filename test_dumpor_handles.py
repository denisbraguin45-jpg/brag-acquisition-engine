import urllib.request, json, time, re

handles_to_test = [
    'gatti_veiculospremium',
    'automaxveiculosjoinville',
    'brotherveiculospremium',
    'deocarsellection',
    'richird_hunter',
    'rajaseminovos',
    'mellomotorss',
    'stiloautomoveis',
    'equatorial_motors',
    'barao.autocars',
    'roma.multimarcass',
    'easymotors_',
    'okmultimarcas_bh',
    'happyboat.oficial',
    'paganinimotors.oficial',
    'premiumveiculoss',
    'premiummultimarcaspp',
    'daluz_multimarcas',
    'reinaldocostaconsultor',
    'jatveiculos_premium',
    'vcar_veiculos_premium',
    'caju.multimarcas',
    'showroommultimarcass',
    'ammotorsbelem',
    'jfmotorsppta',
    'mvmotors_tte',
    'v3motorsbr',
    'mg_seminovos_sc401',
    'seminovos.sagapremium'
]

results = {}
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

for h in handles_to_test:
    url = f"https://dumpor.io/v/{h}"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            content = resp.read().decode('utf-8', errors='ignore')
            # Look for post dates or text in dumpor
            # Dumpor posts usually have time tags or "days ago" or "weeks ago" or dates
            dates = re.findall(r'(\d+\s+(?:days?|weeks?|months?|hours?)\s+ago)', content, re.IGNORECASE)
            # title
            title = re.search(r'<title>(.*?)</title>', content)
            t_str = title.group(1) if title else ''
            results[h] = {
                'status': resp.status,
                'title': t_str[:60],
                'dates_found': dates[:3],
                'active': len(dates) > 0
            }
            print(f"[{resp.status}] @{h}: found {len(dates)} recent posts ({dates[:2]})")
    except Exception as e:
        print(f"[ERR] @{h}: {e}")
        results[h] = {'status': 'err', 'error': str(e)}
    time.sleep(0.5)

with open('D:/app/brag-lead-hunter/dumpor_results.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=2, ensure_ascii=False)
