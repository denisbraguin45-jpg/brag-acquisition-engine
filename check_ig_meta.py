import urllib.request
import re

profiles = [
    'guilherme_motors_multimarcas',
    'uz_veiculos',
    'royalmotors_seminovos',
    'nf.veiculos.mcz',
    'vmotors.multimarcas',
    'miromotorsmultimarcas',
    'premium_autocar',
    'jatveiculos_premium',
    'mellomotorss',
    'roma.multimarcass',
    'automaxveiculosjoinville',
    'gatti_veiculospremium',
    'rajaseminovos',
    'v3motorsbr',
    'daluz_multimarcas'
]

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7'
}

for user in profiles:
    url = f'https://www.instagram.com/{user}/'
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=5) as resp:
            content = resp.read().decode('utf-8', errors='ignore')
            m_desc = re.search(r'<meta property="og:description" content="([^"]+)"', content)
            desc = m_desc.group(1) if m_desc else 'No desc'
            m_title = re.search(r'<meta property="og:title" content="([^"]+)"', content)
            title = m_title.group(1) if m_title else 'No title'
            print(f'User: @{user}')
            print(f'  Title: {title[:70]}')
            print(f'  Desc:  {desc[:120]}')
    except Exception as e:
        print(f'User: @{user} Error: {e}')
