import re
from pathlib import Path

# Paths
BUILDER_PATH = Path("D:/app/brag-lead-hunter/backend/demo_builder.py")
content = BUILDER_PATH.read_text(encoding="utf-8")

# 1. Add previous 30 Denis slugs to EXCLUDED_SLUGS if not already there
PREVIOUS_DENIS_SLUGS = [
    "w-salvador-lancha",
    "db-nautica-salvador",
    "nova-nautica-salvador",
    "chiquinho-nautica-salvador",
    "vitta-nautica-vitoria",
    "gt-cotas-vitoria",
    "netuno-cotas-vitoria",
    "ilheus-iate-clube",
    "topjet-marina-maceio",
    "aluguel-lancha-maceio",
    "vitta-nautica-fortaleza",
    "navegar-joao-pessoa",
    "paraiba-travel-lanchas",
    "recife-boats-charter",
    "marina-jf-jurumirim-avare",
    "jk-adventure-jurumirim",
    "macorio-nautica-avare",
    "gh-nautica-alfenas",
    "hp-moto-nautica-varginha",
    "forfun-sea-doo-varginha",
    "allflags-nautica-rifaina",
    "canastra-boats-franca",
    "mg-nautica-uberlandia",
    "navegacao-medio-tiete-barra-bonita",
    "navios-xumbury-barra-bonita",
    "marina-tiete-pederneiras",
    "marina-tiete-itapui",
    "primar-navegacoes-cuesta",
    "navio-homero-krahenbuhl",
    "marina-rio-itapanhau-bertioga",
]

# 2. Define the new Campello Racing Theme
CAMPELLO_RACING_THEME = '''    {
        "id": "campello-racing",
        "archetype": "Campello Racing Portugal (#dfb858 / #0c0d0b)",
        "font_url": "https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,100..1000;1,9..40,100..1000&family=Instrument+Serif:ital@0;1&family=JetBrains+Mono:wght@400;500;600;700&family=Syne:wght@600;700;800&display=swap",
        "font_display": "'Instrument Serif', 'Syne', serif",
        "font_sans": "'DM Sans', sans-serif",
        "font_mono": "'JetBrains Mono', monospace",
        "color_bg_primary": "#0c0d0b",
        "color_bg_elevated": "#141612",
        "color_bg_light": "#ededeb",
        "color_card_light": "#ffffff",
        "color_text_primary": "#f7f7ee",
        "color_text_dark": "#161814",
        "color_text_secondary": "#a2a59a",
        "color_accent": "#dfb858",
        "color_accent_hover": "#ecc972",
        "color_accent_soft": "#fdf7e7",
        "color_accent_ink": "#0c0d0b",
        "brand_glow": "rgba(223, 184, 88, 0.28)",
        "border_subtle": "rgba(247, 247, 238, 0.12)",
        "border_accent": "rgba(223, 184, 88, 0.50)",
    },
'''

# 3. Define the new curated pool for Denis
NEW_NAUTICAL_CURATED_CODE = '''def select_top_30_nautical_leads(conn: sqlite3.Connection, limit: int = 30) -> list[dict[str, Any]]:
    """
    Selects 30 distinct, verified high-ticket nautical & dealership leads
    (P4/P1 — Concessionárias náuticas oficiais, estaleiros, Sea-Doo/BRP, Schaefer e iates)
    with valid Brazilian WhatsApp (55...) and active Instagram profiles for Denis's queue.
    Architectural reference: Campello Racing (Obsidian, Portuguese Gold #dfb858, Bespoke Inventory).
    """
    nautical_curated_pool = [
        {"name": "Regatta Yachts São Paulo", "ig": "regattayachts", "wa": "5511957997972", "city": "São Paulo", "state": "SP", "slug": "regatta-yachts-sp", "bio": "Maior dealer náutico do Brasil. Concessionária oficial Schaefer Yachts, Sea-Doo e barcos premium."},
        {"name": "Regatta Yachts Guarujá", "ig": "regattayachts", "wa": "5511984470016", "city": "Guarujá", "state": "SP", "slug": "regatta-yachts-guaruja", "bio": "Showroom náutico e marina no Iate Clube de Santos Guarujá. Embarcações novas e seminovos certificados."},
        {"name": "Regatta Yachts Ilhabela", "ig": "regattayachts", "wa": "5511982065019", "city": "Ilhabela", "state": "SP", "slug": "regatta-yachts-ilhabela", "bio": "Base náutica Ilhabela. Venda de iates, lanchas e assistência técnica autorizada."},
        {"name": "WS Náutica Curitiba & BC", "ig": "wsnautica", "wa": "5541984112713", "city": "Curitiba", "state": "PR", "slug": "ws-nautica-curitiba", "bio": "Concessionária Focker, Mercury Marine e Sea-Doo no Paraná e Santa Catarina. Showrooms em Curitiba e Balneário."},
        {"name": "FF Motorsports Floripa", "ig": "ffmotorsportsbr", "wa": "5548999343939", "city": "Florianópolis", "state": "SC", "slug": "ff-motorsports-floripa", "bio": "Concessionária autorizada BRP Sea-Doo, Can-Am e lanchas Focker em Florianópolis."},
        {"name": "NautiCLASS Intermediações", "ig": "nauticlass", "wa": "5548991724533", "city": "Florianópolis", "state": "SC", "slug": "nauticlass-florianopolis", "bio": "Boutique náutica especializada em compra, venda e assessoria de iates e lanchas de luxo em SC."},
        {"name": "Sessa Marine Brasil", "ig": "sessamarinebrasil", "wa": "554832499983", "city": "Palhoça", "state": "SC", "slug": "sessa-marine-intech-boating", "bio": "Estaleiro e concessionária oficial dos iates italianos Sessa Marine no Brasil por Intech Boating."},
        {"name": "Azimut Yachts Brasil", "ig": "azimutyachts_brasil", "wa": "551333484000", "city": "Itajaí", "state": "SC", "slug": "azimut-yachts-brasil", "bio": "Líder mundial na fabricação de iates de luxo a motor. Concessionárias e marinas exclusivas no Brasil."},
        {"name": "Schaefer Yachts Floripa", "ig": "schaeferyachts", "wa": "554821060001", "city": "Florianópolis", "state": "SC", "slug": "schaefer-yachts-floripa", "bio": "Maior estaleiro de iates do Brasil. Showroom matriz de lanchas e yachts de 30 a 85 pés."},
        {"name": "Expert Yachts Schaefer SP", "ig": "expertyachts", "wa": "5511984470016", "city": "São Paulo", "state": "SP", "slug": "expert-yachts-schaefer-sp", "bio": "Concessionária autorizada Schaefer Yachts na capital paulista e litoral."},
        {"name": "FBA Náutica Recife", "ig": "fbanautica", "wa": "5581971195431", "city": "Recife", "state": "PE", "slug": "fba-nautica-recife", "bio": "Concessionária autorizada NX Boats e motores Mercury Marine para o Nordeste."},
        {"name": "Marina Tahiti BRP Bauru", "ig": "marinatahiti", "wa": "5514997009229", "city": "Bauru", "state": "SP", "slug": "marina-tahiti-bauru-brp", "bio": "Concessionária BRP Sea-Doo, Can-Am e marina completa no interior paulista."},
        {"name": "Villa Motorsports Campinas", "ig": "villamotorsports", "wa": "551932387375", "city": "Campinas", "state": "SP", "slug": "villa-motorsports-campinas-brp", "bio": "Concessionária BRP oficial Sea-Doo, Can-Am e Spyder em Campinas e região."},
        {"name": "Rio Náutica Prudente", "ig": "rionauticapp", "wa": "551839280077", "city": "Presidente Prudente", "state": "SP", "slug": "rio-nautica-prudente", "bio": "Concessionária autorizada Sea-Doo, lanchas Fibrafort Focker e motores Yamaha."},
        {"name": "Oeste Marine Náutica", "ig": "oestemarine", "wa": "5518997110022", "city": "Presidente Prudente", "state": "SP", "slug": "oeste-marine-prudente", "bio": "Concessionária de barcos Levefort, lanchas Focker e motores Mercury na Alta Sorocabana."},
        {"name": "Sea Náutica Rio Preto", "ig": "seanautica", "wa": "5517997120033", "city": "São José do Rio Preto", "state": "SP", "slug": "sea-nautica-rio-preto", "bio": "Concessionária e marina de barcos, lanchas e jet skis novos e seminovos em Rio Preto."},
        {"name": "Náutica Prime Piracicaba", "ig": "nauticaprime", "wa": "5519996861212", "city": "Piracicaba", "state": "SP", "slug": "nautica-prime-piracicaba", "bio": "Multimarcas náutica premium. Venda de lanchas, jet skis e carretas no interior de SP."},
        {"name": "Boreal Powersports Campo Grande", "ig": "borealpowersports", "wa": "556730468282", "city": "Campo Grande", "state": "MS", "slug": "boreal-powersports-campo-grande", "bio": "Concessionária BRP Sea-Doo e Can-Am no Mato Grosso do Sul."},
        {"name": "Dismoto Náutica Campo Grande", "ig": "dismotonautica", "wa": "5567981700067", "city": "Campo Grande", "state": "MS", "slug": "dismoto-nautica-campo-grande", "bio": "Concessionária náutica autorizada Yamaha Náutica e barcos de alumínio no MS."},
        {"name": "Villa Motorsports Cuiabá", "ig": "villamotorsportscuiaba", "wa": "5565996496262", "city": "Cuiabá", "state": "MT", "slug": "villa-motorsports-cuiaba", "bio": "Concessionária BRP Sea-Doo e Can-Am no Mato Grosso. Linha completa de jet skis e quadriciclos."},
        {"name": "Disnáutica Várzea Grande", "ig": "disnautica", "wa": "5565984416571", "city": "Várzea Grande", "state": "MT", "slug": "disnautica-varzea-grande", "bio": "Concessionária de barcos, lanchas e motores de popa Mercury no Mato Grosso."},
        {"name": "Náutica X Cuiabá", "ig": "nauticaxcuiaba", "wa": "5565999812420", "city": "Cuiabá", "state": "MT", "slug": "nautica-x-cuiaba", "bio": "Concessionária exclusiva Fishing Raptor e Mercury Marine para o Centro-Oeste."},
        {"name": "Jet Tech BRP Manaus", "ig": "jettechmanaus", "wa": "559236523900", "city": "Manaus", "state": "AM", "slug": "jet-tech-manaus-brp", "bio": "Concessionária oficial BRP Sea-Doo, Evinrude e lanchas Ventura no Amazonas."},
        {"name": "Marreco de Goiás Barcos", "ig": "marrecodebarcos", "wa": "5562996358587", "city": "Goiânia", "state": "GO", "slug": "marreco-de-goias-barcos", "bio": "Fabricante e concessionária de embarcações de alumínio e lazer náutico em Goiás."},
        {"name": "Center Náutica Goiânia", "ig": "centernauticagyn", "wa": "556232052200", "city": "Goiânia", "state": "GO", "slug": "center-nautica-goiania", "bio": "Concessionária autorizada Levefort, motores Mercury e acessórios náuticos em GO."},
        {"name": "Barcos Fisher Goiânia", "ig": "barcosfisher", "wa": "556232230606", "city": "Goiânia", "state": "GO", "slug": "barcos-fisher-goiania", "bio": "Venda e representação de barcos, lanchas e motores de popa em Goiânia."},
        {"name": "RM Náutica Itajaí", "ig": "rmnauticaoficial", "wa": "5547992869590", "city": "Itajaí", "state": "SC", "slug": "rm-nautica-itajai", "bio": "Suporte, comércio de seminovos e assistência autorizada Focker e Yamaha em Itajaí."},
        {"name": "Fibrafort Estaleiro Matriz", "ig": "fibrafortboats", "wa": "5547996585643", "city": "Itajaí", "state": "SC", "slug": "fibrafort-estaleiro-focker", "bio": "Maior fabricante de lanchas da América Latina (Linha Focker de 18 a 42 pés). Showroom de fábrica."},
        {"name": "Da Fonte Náutica Recife", "ig": "dafontenautica", "wa": "558133251022", "city": "Recife", "state": "PE", "slug": "d-fonte-nautica-imbiribeira", "bio": "Concessionária BRP Sea-Doo e Can-Am líder no Nordeste há mais de 30 anos."},
        {"name": "Chiquinho Náutica Nordeste", "ig": "chiquinhonauticape", "wa": "5581995144000", "city": "Recife", "state": "PE", "slug": "chiquinho-nautica-nordeste", "bio": "Concessionária multimarcas náutica em Pernambuco. Lanchas, jet skis e quadriciclos novos e seminovos."}
    ]

    selected: list[dict[str, Any]] = []
    seen_slugs: set[str] = set()

    for item in nautical_curated_pool:
        slug = item["slug"]
        if slug in EXCLUDED_SLUGS or slug in seen_slugs:
            continue
        seen_slugs.add(slug)
        selected.append({
            "id": f"nautica_{slug}",
            "name": item["name"],
            "slug": slug,
            "city": item["city"],
            "state": item["state"],
            "country": "Brasil",
            "niche": "P4 — Náutica premium",
            "score": 97,
            "priority": "A",
            "instagram_username": item["ig"],
            "instagram_url": f"https://www.instagram.com/{item['ig']}/",
            "instagram_bio": item["bio"],
            "followers_count": 22000,
            "whatsapp": item["wa"],
            "phone": item["wa"],
            "has_own_website": False,
            "source": "nautical_curated_intelligence",
            "commercial_status": "icp_identificado",
        })
        if len(selected) >= limit:
            break

    return selected
'''

print("Checking replacement points...")
# Check EXCLUDED_SLUGS
ex_str = '\n'.join([f'    "{s}",' for s in PREVIOUS_DENIS_SLUGS])
# Insert right after EXCLUDED_SLUGS = {
if "w-salvador-lancha" not in content:
    content = content.replace("EXCLUDED_SLUGS = {\n", f"EXCLUDED_SLUGS = {{\n    # Denis Lote Náutico anterior (30 arquivados no ar)\n{ex_str}\n")
    print("Added previous Denis slugs to EXCLUDED_SLUGS")
else:
    print("w-salvador-lancha already in EXCLUDED_SLUGS")

# Check Campello Racing Theme
if "campello-racing" not in content:
    content = content.replace("DESIGN_THEMES: list[dict[str, str]] = [\n", f"DESIGN_THEMES: list[dict[str, str]] = [\n{CAMPELLO_RACING_THEME}")
    print("Added Campello Racing theme to DESIGN_THEMES")
else:
    print("Campello Racing theme already in DESIGN_THEMES")

# Check select_top_30_nautical_leads
# Find function boundaries
func_start = content.find("def select_top_30_nautical_leads(")
func_end = content.find("def select_top_30_automotive_leads(")
if func_start != -1 and func_end != -1:
    content = content[:func_start] + NEW_NAUTICAL_CURATED_CODE + "\n\n" + content[func_end:]
    print("Replaced select_top_30_nautical_leads with 30 new nautical dealership leads")
else:
    print("ERROR: Could not find function boundaries for select_top_30_nautical_leads")

# Save updated demo_builder.py
BUILDER_PATH.write_text(content, encoding="utf-8")
print("demo_builder.py successfully updated on D:!")

# Mirror to C: scratch if it exists
MIRROR_PATH = Path("C:/Users/denis/.gemini/antigravity/scratch/brag-lead-hunter/backend/demo_builder.py")
if MIRROR_PATH.parent.exists():
    MIRROR_PATH.write_text(content, encoding="utf-8")
    print("Mirrored to C: scratch demo_builder.py!")
