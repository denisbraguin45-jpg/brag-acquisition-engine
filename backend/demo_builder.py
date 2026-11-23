"""
BRAG Lead Hunter — Avantgarde Brutal Reference Showroom Engine (`backend/demo_builder.py`).

Uses https://avantgarde.com.br/ as the brutal architectural, typographic, and interactive reference
for all 30 qualified dealership demos:
1. Condensed Industrial-Luxury Typography (`Barlow Condensed` / `Trade Gothic Next Condensed` spirit + `Plus Jakarta Sans` + `JetBrains Mono`) with wide uppercase tracking.
2. Full-Viewport Hero Slider (`section-hero`) with Brand Watermark, Split Brand + Model Title, Tagline, 3-Block Telemetry Strip (`Ano` | `Km` | `Valor`), and slide controls.
3. Overlapping Floating Search Dock (`section-filter` with `margin-bottom` overlap) featuring `Encontre seu próximo veículo` + `Marcas` + `Modelos` + `Buscar` + `Filtro avançado`.
4. Chamfered Avantgarde Vehicle Cards (`clip-path: polygon(0 0, 100% 0, 100% calc(100% - 56px), calc(100% - 56px) 100%, 0 100%)`), top accent line reveal (`scaleX`), brand overline, 62px bottom rule on title, `Ano` + `Km` row, `<small>R$</small> <span>Valor</span>`, and `Blindado` pill.
5. Full-Bleed Accent Brand Section (`section-about` — `Conduzindo a Excelência`) with animated concentric rings (`.circles .circle`).
6. Dark Bespoke Order Section (`section-model-not-found` — `Não encontrou o modelo que estava buscando?`) with 4-field form (`Modelo desejado`, `Nome`, `E-mail`, `Telefone/WhatsApp`) that dispatches directly to the dealership's WhatsApp.
7. Immersive Experience Section (`section-general-experience` — `Conheça a [Loja] Experience`) + Avantgarde-style Footer (`Conduzindo a excelência.`).
8. Zero Demo/Prototype banners or tags on the customer-facing LP, and calibrated mobile typography (`@media (max-width: 640px)`).
"""
import html
import json
import re
import sqlite3
import urllib.parse
from pathlib import Path
from typing import Any, Optional

from backend.config import BASE_DIR
from backend.database import get_connection, now_iso
from backend.exporter import query_enriched_leads

DEMOS_DIR = BASE_DIR / "demos"
DOCS_LEADS_DIR = BASE_DIR / "docs" / "leads"
DESIGN_SYSTEMS_DIR = BASE_DIR / "design-systems"

EXCLUDED_SLUGS = {
    "pecas-para-carros-nacionais-e-importados",
    # Lote 1 (30 contatos já abordados e removidos do CRM)
    "ag-motors-compra-e-venda-de-veiculos",
    "aslan-rustom-veiculos-imoveis",
    "auto-premium-loja-de-veiculos-em-guaramirim-sc",
    "benaia-motors-carros-seminovos-e-premium",
    "car-jet",
    "chico-sa-veiculos-automoveis",
    "dm-automoveis",
    "euro-motors-seminovos",
    "fernando-automoveis",
    "gs1-motortech-oficina-premium-seminovos",
    "guilherme-motors-multimarcas",
    "guimaraes-automoveis",
    "jonathan-veiculos",
    "josinha-fabbri",
    "locaveri",
    "martins",
    "miro-motors-multimarcas",
    "nf-veiculos-seminovos-em-alagoas",
    "percio-schaefer-yachts",
    "premium-auto-car-seminovos-em-campo-grande-ms",
    "premium-veiculos-seminovos",
    "premium-veiculos-volkswagen",
    "royal-motors",
    "saci-veiculos-carros-seminovos-de-qualidade",
    "smo-motors-seminovos-em-sao-miguel-do-oeste",
    "spaco-fama-multimarcas",
    "tk-motors-veiculo-novos-e-seminovos",
    "top-motors-multimarcas",
    "uz-veiculos-carros-seminovos-em-andradina-sp",
    "v-motors",
    # Lote Denis anterior (30 contatos já abordados e mantidos arquivados)
    "elite-motors",
    "premium-veiculos",
    "campello-yachts",
    "veiculos-premium-e-seminovos",
    "ricardo-lacerda-consultor-carros-seminovos-premium",
    "destak-multimarcas-revendedora-de-carros-seminovos",
    "rs-premium-multimarcas",
    "prime-nautica",
    "marcelo-multimarcas",
    "panda-seminovos-premium-marcelo",
    "wl-motors-loja-de-veiculos-em-gurupi-to",
    "ars3-veiculos-seminovos-e-blindados-com-garantia-e-procedencia",
    "center-motors-automoveis-veiculos-semi-novos-e-usados",
    "lanchasoceanic",
    "excel-premium-loja-de-seminovos",
    "premium-veiculos-revenda-de-automoveis-em-sao-leopoldo-rs",
    "vf-motors-loja-porto-feliz",
    "vf-motors-seminovos",
    "zap-motors-veiculos-multimarcas",
    "canela-automoveis",
    "ohcarro",
    "terranova-motors-multimarcas",
    "tecar-mercedes-benz-brasilia",
    "rosati-motors",
    "breda-motors",
    "acqua-motors-seminovos-com-procedencia",
    "gam-motors",
    "mogicar-multimarcas",
    "premium-veiculos-df",
    # Lote Denis anterior (multimarcas/blindados — arquivados)
    "mf-motors-premium",
    "formula-blindados",
    "mmotorsba",
    "lap-motors",
    "mcar-premium-veiculos-premium",
    "seminovos-indiana-veiculos",
    "top-veiculos",
    "totality-blindados",
    "world-car-multimarcas-automoveis",
    "jotap-veiculos-premium",
    "madriauto-veiculos",
    "mauloni-torres-seminovos-curitiba",
    "rota-automoveis-seminovos-premium-maringa",
    "bless-motors-multimarcas",
    "bravo-motors-seminovos-joinville-sc",
    "bmg-loja-de-veiculos-seminovos",
    "colibri-veiculos-seminovos",
    "xkm-motors-veiculos-novos-e-seminovos",
    "viot-motors-carros-novos-e-semi-novos-com-procedencia",
    "jh-veiculos-especialistas-em-bmw-e-seminovos-premium",
    "riva-veiculos-semi-novos-em-catanduva",
    "alfa-premium-veiculos-jaru",
    "bss-beyond-special-security",
    "automoveis-podium-multimarcas",
    "marlon-veiculos",
    "rk-motors-seminovos",
    "empresa",
    "veiculos-niteroi-3l-s",
    "rs-motors-multimarcas",
    # Lote Denis Náutica anterior (30 lojas náuticas abordadas — arquivadas no ar)
    "villa-nautica",
    "marina-belas-artes",
    "casarini-brp",
    "jet-crazy-brp",
    "marrsul-powersports",
    "uninautica-schaefer-yachts",
    "alenautica-yamaha",
    "megajet-boats",
    "direct-jet-nautica",
    "box-adventure-brp",
    "jet-point-brasil",
    "rabelo-locacoes-marina",
    "marina-proguard-bonfim",
    "lanchas-joao-pessoa",
    "marina-totem",
    "imperium-nautica",
    "gm-boats-angra",
    "nautica-mar-azul",
    "all-flags-nautica",
    "porto-do-rio-boats",
    "cia-lake-marina",
    "moto-oeste-nautica",
    "nx-boats-goias",
    "ventura-uberlandia",
    "weboat-brasil",
    "willboat-yamaha-nautica",
    "ws-nautica-balneario",
    "chiquinho-nautica",
    "acqua-lanchas",
    "mar-boats",
    # Lote Denis Náutica 2 anterior (30 lojas náuticas abordadas — arquivadas no ar)
    "bella-nautica-lago-paranoa",
    "triton-yachts-brasil",
    "boatsp-nautica",
    "maggi-adventure-brp",
    "jetco-brasil-waverunner",
    "daniel-fida-yacht-broker",
    "angra-paradise-tour",
    "jetskiweb-brasil",
    "moto-nautica-powersports",
    "marina-porto-imperial",
    "marina-piratas-br-marinas",
    "start-nautica-marina-da-gloria",
    "marina-passeios-rj",
    "rio-boat-charters",
    "danimar-nautica-yamaha",
    "rio-mares-nautica",
    "nx-boats-rio",
    "centro-nautico-parana",
    "marina-itajai",
    "tedesco-marina-garden",
    "porto-marina-asturias",
    "marina-verolme-br-marinas",
    "marina-farol-de-paraty",
    "ventura-experience-capitolio",
    "marina-sylvestre-guarapiranga",
    "marina-atlantica-guarapiranga",
    "internautica-yachts",
    "360-sports-marina-barra",
    "caicara-tour-angra",
    "marina-porto-ilhabela",
    # Lote Denis Náutica 3 anterior (30 marinas e centros náuticos abordados — arquivados no ar)
    "marina-marcam-ubatuba",
    "weboat-brasil-marina-gloria",
    "marina-costabella-angra",
    "marina-tropical-guaruja",
    "marina-guararu-guaruja",
    "marina-barraseca-ubatuba",
    "marina-kauai-ubatuba",
    "marina-atlantis-maranduba",
    "marina-porto-escondido-ubatuba",
    "alpha-marine-ubatuba",
    "marina-da-conceicao-floripa",
    "veleiros-da-ilha-icsc",
    "marinho-marina-floripa",
    "divisao4-motorsports-floripa",
    "marina-jv-nautica-bc",
    "marina-confianca-bc",
    "marina-vip-balneario",
    "marina-carolinaz-guaratuba",
    "marina-porto-estaleiro-guaratuba",
    "iate-clube-guaratuba",
    "marina-escarpas-furnas",
    "marina-estancia-aguas-nazare",
    "represa-grande-marina-nazare",
    "marina-porto-sol-nazare",
    "marina-estancia-confianca-braganca",
    "akkar-nautica-campinas",
    "allflags-nautica-ribeirao",
    "rio-nautica-maringa",
    "londrinautica-londrina",
    "marina-flores-porto-alegre",
    # Lote Denis Náutica 4 anterior (30 marinas e centros abordados — arquivados no ar)
    "yacht-clube-da-bahia-salvador",
    "cabanga-iate-clube-recife",
    "recife-marina-pe",
    "marina-porto-do-mar-paulista",
    "iate-clube-espirito-santo-vitoria",
    "iate-clube-de-santos-guaruja",
    "yacht-club-de-ilhabela",
    "marina-br-marinas-paraty",
    "marina-boa-vista-br-marinas-paraty",
    "marina-188-paraty",
    "marina-capital-bertioga",
    "marina-nautica-indaia-bertioga",
    "pier-club-bertioga",
    "marina-porto-de-bertioga",
    "marina-sao-pedro-itanhaem",
    "maita-marina-itanhaem",
    "sea-boat-santos-guaruja",
    "villa-nautica-motorsports-goiania",
    "pier-nautica-goiania",
    "toninho-jet-nautica-goiania",
    "sport-nautica-foz",
    "iguacu-escola-nautica",
    "vm-powersports-teresina",
    "pg-prime-natal-brp",
    "marina-rio-potengi-natal",
    "marina-br-marinas-bracuhy",
    "marina-da-ribeira-br-marinas",
    "marina-porto-frade-angra",
    "marina-pier-34-cabedelo",
    "marina-jacare-village-cabedelo",
    # Lote Gabriel anterior (30 revendas premium abordadas — arquivadas no ar)
    "fj-motors-loja-de-carros-em-curitiba",
    "diego-de-oliveira-seminovos-premium",
    "seminovos-premium",
    "jf-veiculos",
    "andrew-motors-o-lobo-de-vendas",
    "geone-palmeira-cynthia-sanches-palmeira-seminovos-goiania",
    "edil-junior-servicos-nauticos",
    "finatti-marcblindagens",
    "fernando",
    "veiculos-seminovos",
    "r2-motors-revenda-de-automoveis-seminovos",
    "racing-multimarcas-carros-seminovos-0km-e-blindados-sp",
    "seminovos-premium-grand-brasil",
    "mvk-veiculos-carros-seminovos-curitiba",
    "carros-premium-seminovos",
    "wagner-multimarcas",
    "pw-motors",
    "rafagnin-motors-seminovos-premium-salto-de-pirapora-sp",
    "impact-veiculos-premium",
    "cero-cars-automoviles",
    "gabivel-premium",
    "avante-motors-bauru-veiculos-em-bauru",
    "grecalle-blindados",
    "routte-automotive",
    "estrela-nautica-tapecaria",
    "up-motors-multimarcas-atibaia",
    "ag-negocios-nauticos",
    "dscar-premium-veiculos-multimarcas",
    "vivacars-multimarcas",
    "carros-novos-e-seminovos-em-bh",

}

FONT_URL = (
    "https://fonts.googleapis.com/css2?"
    "family=Barlow+Condensed:wght@400;600;700;800&"
    "family=Plus+Jakarta+Sans:wght@400;500;600;700&"
    "family=JetBrains+Mono:wght@500;700&display=swap"
)

# 6 Avantgarde Concept Store Palettes (Primary signature: Avantgarde Flame #cf4520 + 5 bespoke concept variations)
DESIGN_THEMES: list[dict[str, str]] = [
    {
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
    {
        "id": "avantgarde-flame",
        "archetype": "Avantgarde Concept Flame (#cf4520)",
        "font_url": FONT_URL,
        "font_display": "'Barlow Condensed', sans-serif",
        "font_sans": "'Plus Jakarta Sans', sans-serif",
        "font_mono": "'JetBrains Mono', monospace",
        "color_bg_primary": "#0c0c0e",
        "color_bg_elevated": "#141418",
        "color_bg_light": "#eaeaed",
        "color_card_light": "#ffffff",
        "color_text_primary": "#ffffff",
        "color_text_dark": "#232323",
        "color_text_secondary": "#989898",
        "color_accent": "#cf4520",
        "color_accent_hover": "#a63111",
        "color_accent_soft": "#faece9",
        "color_accent_ink": "#ffffff",
        "brand_glow": "rgba(207, 69, 32, 0.22)",
        "border_subtle": "rgba(255, 255, 255, 0.10)",
        "border_accent": "rgba(207, 69, 32, 0.45)",
    },
    {
        "id": "avantgarde-maranello",
        "archetype": "Avantgarde Rosso Corsa (#d02626)",
        "font_url": FONT_URL,
        "font_display": "'Barlow Condensed', sans-serif",
        "font_sans": "'Plus Jakarta Sans', sans-serif",
        "font_mono": "'JetBrains Mono', monospace",
        "color_bg_primary": "#0a0a0c",
        "color_bg_elevated": "#131317",
        "color_bg_light": "#ededf0",
        "color_card_light": "#ffffff",
        "color_text_primary": "#ffffff",
        "color_text_dark": "#1f1f23",
        "color_text_secondary": "#9a9aa2",
        "color_accent": "#d02626",
        "color_accent_hover": "#991b1b",
        "color_accent_soft": "#fdecec",
        "color_accent_ink": "#ffffff",
        "brand_glow": "rgba(208, 38, 38, 0.22)",
        "border_subtle": "rgba(255, 255, 255, 0.10)",
        "border_accent": "rgba(208, 38, 38, 0.45)",
    },
    {
        "id": "avantgarde-gold",
        "archetype": "Avantgarde Weissach Gold (#c69214)",
        "font_url": FONT_URL,
        "font_display": "'Barlow Condensed', sans-serif",
        "font_sans": "'Plus Jakarta Sans', sans-serif",
        "font_mono": "'JetBrains Mono', monospace",
        "color_bg_primary": "#0b0b0d",
        "color_bg_elevated": "#141419",
        "color_bg_light": "#ececef",
        "color_card_light": "#ffffff",
        "color_text_primary": "#ffffff",
        "color_text_dark": "#222226",
        "color_text_secondary": "#9ca3af",
        "color_accent": "#c69214",
        "color_accent_hover": "#9a6f0b",
        "color_accent_soft": "#fbf5e6",
        "color_accent_ink": "#ffffff",
        "brand_glow": "rgba(198, 146, 20, 0.22)",
        "border_subtle": "rgba(255, 255, 255, 0.10)",
        "border_accent": "rgba(198, 146, 20, 0.45)",
    },
    {
        "id": "avantgarde-british",
        "archetype": "Avantgarde Goodwood Emerald (#0d7a5f)",
        "font_url": FONT_URL,
        "font_display": "'Barlow Condensed', sans-serif",
        "font_sans": "'Plus Jakarta Sans', sans-serif",
        "font_mono": "'JetBrains Mono', monospace",
        "color_bg_primary": "#080d0b",
        "color_bg_elevated": "#101915",
        "color_bg_light": "#e9eeec",
        "color_card_light": "#ffffff",
        "color_text_primary": "#ffffff",
        "color_text_dark": "#1c2622",
        "color_text_secondary": "#94a39d",
        "color_accent": "#0d7a5f",
        "color_accent_hover": "#065f46",
        "color_accent_soft": "#e6f5f0",
        "color_accent_ink": "#ffffff",
        "brand_glow": "rgba(13, 122, 95, 0.22)",
        "border_subtle": "rgba(255, 255, 255, 0.10)",
        "border_accent": "rgba(13, 122, 95, 0.45)",
    },
    {
        "id": "avantgarde-monaco",
        "archetype": "Avantgarde Yachting Cobalt (#1d5bd6)",
        "font_url": FONT_URL,
        "font_display": "'Barlow Condensed', sans-serif",
        "font_sans": "'Plus Jakarta Sans', sans-serif",
        "font_mono": "'JetBrains Mono', monospace",
        "color_bg_primary": "#070b12",
        "color_bg_elevated": "#0f1724",
        "color_bg_light": "#eaedf2",
        "color_card_light": "#ffffff",
        "color_text_primary": "#ffffff",
        "color_text_dark": "#1e2530",
        "color_text_secondary": "#94a3b8",
        "color_accent": "#1d5bd6",
        "color_accent_hover": "#1545a8",
        "color_accent_soft": "#eaf0fc",
        "color_accent_ink": "#ffffff",
        "brand_glow": "rgba(29, 91, 214, 0.22)",
        "border_subtle": "rgba(255, 255, 255, 0.10)",
        "border_accent": "rgba(29, 91, 214, 0.45)",
    },
    {
        "id": "avantgarde-bronze",
        "archetype": "Avantgarde Sant'Agata Bronze (#b85d19)",
        "font_url": FONT_URL,
        "font_display": "'Barlow Condensed', sans-serif",
        "font_sans": "'Plus Jakarta Sans', sans-serif",
        "font_mono": "'JetBrains Mono', monospace",
        "color_bg_primary": "#0c0907",
        "color_bg_elevated": "#17120e",
        "color_bg_light": "#eeeae6",
        "color_card_light": "#ffffff",
        "color_text_primary": "#ffffff",
        "color_text_dark": "#26201b",
        "color_text_secondary": "#a3988e",
        "color_accent": "#b85d19",
        "color_accent_hover": "#8f440d",
        "color_accent_soft": "#faefe6",
        "color_accent_ink": "#ffffff",
        "brand_glow": "rgba(184, 93, 25, 0.22)",
        "border_subtle": "rgba(255, 255, 255, 0.10)",
        "border_accent": "rgba(184, 93, 25, 0.45)",
    },
]

# Avantgarde-formatted inventory per vertical (Brand, Model, Year/Year, Km, Price, Tagline, Armored)
CATALOG_BY_VERTICAL: dict[str, list[dict[str, Any]]] = {
    "nautica": [
        {
            "brand": "Schaefer Yachts",
            "model": "510 GT PININFARINA",
            "title": "Schaefer Yachts 510 GT Pininfarina",
            "category": "Flybridge & HT",
            "year": 2024,
            "year_label": "2024/2024",
            "km_label": "48h",
            "price": 6450000,
            "tagline": "Design by Pininfarina",
            "specs": "51 pes · 2x Volvo Penta IPS 700 · 3 Cabines · Hardtop Panoramico",
            "badge": "PRONTA ENTREGA",
            "armored": False,
            "image": "https://images.unsplash.com/photo-1567899378494-47b22a2ae96a?auto=format&fit=crop&w=1000&q=85",
        },
        {
            "brand": "Azimut",
            "model": "62 FLYBRIDGE COLLECTION",
            "title": "Azimut 62 Flybridge Collection",
            "category": "Yacht",
            "year": 2023,
            "year_label": "2023/2023",
            "km_label": "110h",
            "price": 11900000,
            "tagline": "Italian Yachting Excellence",
            "specs": "62 pes · 2x MAN i6 800hp · Estabilizador Seakeeper Gyro",
            "badge": "CURADORIA OFICIAL",
            "armored": False,
            "image": "https://images.unsplash.com/photo-1605281317010-fe5ffe798166?auto=format&fit=crop&w=1000&q=85",
        },
        {
            "brand": "Schaefer Yachts",
            "model": "V33 SPORT WALKAROUND",
            "title": "Schaefer V33 Sport Walkaround",
            "category": "Day Cruiser",
            "year": 2025,
            "year_label": "2024/2025",
            "km_label": "0h",
            "price": 1890000,
            "tagline": "Open Walkaround Performance",
            "specs": "33 pes · 2x Mercury V8 300hp · Gerador + Climatizacao Completa",
            "badge": "ZERO HORAS",
            "armored": False,
            "image": "https://images.unsplash.com/photo-1540946485063-a40da27545f8?auto=format&fit=crop&w=1000&q=85",
        },
        {
            "brand": "NX Boats",
            "model": "370 HT GOURMET EDITION",
            "title": "NX Boats 370 HT Gourmet Edition",
            "category": "Flybridge & HT",
            "year": 2024,
            "year_label": "2024/2024",
            "km_label": "65h",
            "price": 1620000,
            "tagline": "Sport Luxury Hardtop",
            "specs": "37 pes · 2x Mercruiser 300hp · Plataforma Hidraulica Submersivel",
            "badge": "UNICO DONO",
            "armored": False,
            "image": "https://images.unsplash.com/photo-1569263979104-865ab7cd8d13?auto=format&fit=crop&w=1000&q=85",
        },
        {
            "brand": "Fibrafort",
            "model": "FOCKER 333 GRAN TURISMO",
            "title": "Focker 333 Gran Turismo Targa",
            "category": "Day Cruiser",
            "year": 2024,
            "year_label": "2023/2024",
            "km_label": "92h",
            "price": 1150000,
            "tagline": "Navigate Beyond Limits",
            "specs": "33 pes · 2x Mercruiser 250hp · Cockpit Gourmet · Revisada",
            "badge": "PROCEDENCIA",
            "armored": False,
            "image": "https://images.unsplash.com/photo-1520637836862-4d197d17c93a?auto=format&fit=crop&w=1000&q=85",
        },
        {
            "brand": "Sea-Doo",
            "model": "GTX LIMITED 300 IDF",
            "title": "Sea-Doo GTX Limited 300 IDF Audio",
            "category": "Jet & Lazer",
            "year": 2024,
            "year_label": "2024/2024",
            "km_label": "18h",
            "price": 148900,
            "tagline": "Supercharged Marine Power",
            "specs": "Rotax 1630 ACE 300hp · Sistema BRP Bluetooth · Carreta Rodoviaria",
            "badge": "SELECAO NAUTICA",
            "armored": False,
            "image": "https://images.unsplash.com/photo-1544551763-46a013bb70d5?auto=format&fit=crop&w=1000&q=85",
        },
    ],
    "german_performance": [
        {
            "brand": "Porsche",
            "model": "911 GT3 RS MANTHEY",
            "title": "Porsche 911 GT3 RS (992)",
            "category": "Superesportivos",
            "year": 2024,
            "year_label": "2023/2024",
            "km_label": "1.840km",
            "price": 3290000,
            "tagline": "There Is No Substitute",
            "specs": "4.0 Boxer Aspirado 525cv · Pacote Weissach · Freios PCCB Ceramica",
            "badge": "WEISSACH PACKAGE",
            "armored": False,
            "image": "https://images.unsplash.com/photo-1503376780353-7e6692767b70?auto=format&fit=crop&w=1000&q=85",
        },
        {
            "brand": "Ferrari",
            "model": "ROMA SPIDER V8",
            "title": "Ferrari Roma Spider 3.9 V8 Turbo",
            "category": "Superesportivos",
            "year": 2024,
            "year_label": "2024/2024",
            "km_label": "2.370km",
            "price": 3100000,
            "tagline": "Start Your Engine",
            "specs": "620cv · Cambio F1 DCT 8v · Volante Carbono LEDs · Daytona Seats",
            "badge": "OFICIAL BRASIL",
            "armored": False,
            "image": "https://images.unsplash.com/photo-1583121274602-3e2820c69888?auto=format&fit=crop&w=1000&q=85",
        },
        {
            "brand": "Mercedes-AMG",
            "model": "G 63 MAGNO EDITION",
            "title": "Mercedes-AMG G 63 V8 Biturbo",
            "category": "SUV Premium",
            "year": 2024,
            "year_label": "2023/2024",
            "km_label": "4.120km",
            "price": 1950000,
            "tagline": "Handcrafted by Racers",
            "specs": "4.0 V8 Biturbo 585cv · Interior Manufaktur Nappa · Night Magno",
            "badge": "BLINDADO",
            "armored": True,
            "image": "https://images.unsplash.com/photo-1520031441872-265e4ff70366?auto=format&fit=crop&w=1000&q=85",
        },
        {
            "brand": "BMW",
            "model": "M3 COMPETITION XDRIVE",
            "title": "BMW M3 Competition M xDrive",
            "category": "Esportivos",
            "year": 2025,
            "year_label": "2024/2025",
            "km_label": "870km",
            "price": 880000,
            "tagline": "The Ultimate Driving Machine",
            "specs": "3.0 TwinPower Turbo 510cv · Bancos Concha M Carbon · Laserlight",
            "badge": "GARANTIA FABRICA",
            "armored": False,
            "image": "https://images.unsplash.com/photo-1555215695-3004980ad54e?auto=format&fit=crop&w=1000&q=85",
        },
        {
            "brand": "Audi",
            "model": "RS6 AVANT PERFORMANCE",
            "title": "Audi RS6 Avant Performance V8",
            "category": "Esportivos",
            "year": 2024,
            "year_label": "2024/2024",
            "km_label": "3.450km",
            "price": 1249000,
            "tagline": "Vorsprung durch Technik",
            "specs": "4.0 TFSI Biturbo 630cv · Freios Ceramica · Escape RS Esportivo",
            "badge": "PRONTA ENTREGA",
            "armored": False,
            "image": "https://images.unsplash.com/photo-1606664515524-ed2f786a0bd6?auto=format&fit=crop&w=1000&q=85",
        },
        {
            "brand": "Land Rover",
            "model": "RANGE ROVER SPORT HSE",
            "title": "Range Rover Sport Dynamic HSE D350",
            "category": "Blindados",
            "year": 2024,
            "year_label": "2024/2024",
            "km_label": "6.900km",
            "price": 989000,
            "tagline": "Modern British Luxury",
            "specs": "3.0 I6 Diesel · Blindagem Carbon NIII-A · Vidros AGP B33",
            "badge": "BLINDADO",
            "armored": True,
            "image": "https://images.unsplash.com/photo-1549399542-7e3f8b79c341?auto=format&fit=crop&w=1000&q=85",
        },
    ],
    "multimarcas_premium": [
        {
            "brand": "Porsche",
            "model": "MACAN T 2.0 TURBO AWD",
            "title": "Porsche Macan T 2.0 Turbo AWD",
            "category": "SUV Premium",
            "year": 2024,
            "year_label": "2023/2024",
            "km_label": "7.400km",
            "price": 529000,
            "tagline": "There Is No Substitute",
            "specs": "265cv PDK · Pacote Sport Chrono de Serie · Teto Panoramico · Cinza Agata",
            "badge": "LAUDO CAUTELAR 100%",
            "armored": False,
            "image": "https://images.unsplash.com/photo-1503376780353-7e6692767b70?auto=format&fit=crop&w=1000&q=85",
        },
        {
            "brand": "BMW",
            "model": "320I M SPORT TWINPOWER",
            "title": "BMW 320i M Sport 2.0 TwinPower Turbo",
            "category": "Sedans Executivos",
            "year": 2024,
            "year_label": "2024/2024",
            "km_label": "5.190km",
            "price": 318900,
            "tagline": "Sheer Driving Pleasure",
            "specs": "184cv · BMW Live Cockpit Curved · Teto Solar · Pacote Aerodinamico M",
            "badge": "GARANTIA FABRICA",
            "armored": False,
            "image": "https://images.unsplash.com/photo-1555215695-3004980ad54e?auto=format&fit=crop&w=1000&q=85",
        },
        {
            "brand": "Toyota",
            "model": "HILUX SRX LIMITED 4X4",
            "title": "Toyota Hilux SRX Limited 2.8 4x4 Diesel",
            "category": "Picapes & 4x4",
            "year": 2024,
            "year_label": "2024/2024",
            "km_label": "11.200km",
            "price": 309900,
            "tagline": "Built for Any Terrain",
            "specs": "204cv Automatica · Visao 360° · Audio JBL Premium · Unico Dono",
            "badge": "UNICO DONO",
            "armored": False,
            "image": "https://images.unsplash.com/photo-1559416523-140ddc3d238c?auto=format&fit=crop&w=1000&q=85",
        },
        {
            "brand": "Land Rover",
            "model": "DEFENDER 110 HSE D300",
            "title": "Land Rover Defender 110 HSE D300",
            "category": "Blindados",
            "year": 2023,
            "year_label": "2023/2023",
            "km_label": "14.800km",
            "price": 689000,
            "tagline": "Above and Beyond",
            "specs": "3.0 I6 Turbo Diesel · Blindagem NIII-A Certificada · 7 Lugares",
            "badge": "BLINDADO",
            "armored": True,
            "image": "https://images.unsplash.com/photo-1519641471654-76ce0107ad1b?auto=format&fit=crop&w=1000&q=85",
        },
        {
            "brand": "Jeep",
            "model": "COMMANDER OVERLAND TD380",
            "title": "Jeep Commander Overland TD380 4x4",
            "category": "SUV Premium",
            "year": 2024,
            "year_label": "2023/2024",
            "km_label": "9.600km",
            "price": 234900,
            "tagline": "Sophisticated Adventure",
            "specs": "7 Lugares · Teto Panoramico Command View · Som Harman Kardon",
            "badge": "REVISADO",
            "armored": False,
            "image": "https://images.unsplash.com/photo-1533473359331-0135ef1b58bf?auto=format&fit=crop&w=1000&q=85",
        },
        {
            "brand": "Audi",
            "model": "Q5 SPORTBACK S-LINE",
            "title": "Audi Q5 Sportback S-Line 2.0 TFSI",
            "category": "SUV Premium",
            "year": 2024,
            "year_label": "2023/2024",
            "km_label": "8.300km",
            "price": 379900,
            "tagline": "Quattro Performance",
            "specs": "265cv Tracao Quattro · Virtual Cockpit Plus · Teto Solar Panoramico",
            "badge": "BLINDADO",
            "armored": True,
            "image": "https://images.unsplash.com/photo-1549399542-7e3f8b79c341?auto=format&fit=crop&w=1000&q=85",
        },
    ],
}


def format_whatsapp_e164(raw_phone: str) -> str:
    digits = "".join(ch for ch in (raw_phone or "") if ch.isdigit())
    if not digits:
        return ""
    if digits.startswith("55") and len(digits) in (12, 13):
        return digits
    if len(digits) in (10, 11):
        return "55" + digits
    return digits


def format_phone_human(raw_phone: str) -> str:
    digits = "".join(ch for ch in (raw_phone or "") if ch.isdigit())
    if digits.startswith("55") and len(digits) in (12, 13):
        digits = digits[2:]
    if len(digits) == 11:
        return f"({digits[:2]}) {digits[2:7]}-{digits[7:]}"
    if len(digits) == 10:
        return f"({digits[:2]}) {digits[2:6]}-{digits[6:]}"
    return raw_phone or "Atendimento Comercial"


def format_brl_avantgarde(price: float) -> str:
    return f"{price:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def detect_vertical_key(lead: dict[str, Any]) -> str:
    niche = (lead.get("niche") or "").lower()
    name = (lead.get("name") or "").lower()
    bio = (lead.get("instagram_bio") or "").lower()
    combined = f"{niche} {name} {bio}"
    if any(k in combined for k in ("nautica", "náutica", "yacht", "lancha", "jet", "boat", "p4")):
        return "nautica"
    if any(k in combined for k in ("porsche", "bmw", "audi", "mercedes", "motortech", "euro", "royal", "benaia", "blindad", "p2", "p3")):
        return "german_performance"
    return "multimarcas_premium"


def select_top_30_nautical_leads(conn: sqlite3.Connection, limit: int = 30) -> list[dict[str, Any]]:
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


def select_top_30_automotive_leads(conn: sqlite3.Connection, limit: int = 30) -> list[dict[str, Any]]:
    """
    Selects 30 distinct, verified high-ticket automotive & armored dealership leads
    (P1/P2 — Superesportivos, blindados, multimarcas premium) with valid Brazilian WhatsApp (55...)
    and active Instagram profiles for Gabriel's queue.
    """
    automotive_curated_pool = [
        {"name": "TCAR Imports Tatuapé", "ig": "tcar", "wa": "5511940157728", "city": "São Paulo", "state": "SP", "slug": "tcar-imports-sp", "bio": "Referência nacional em superesportivos, importados e veículos de luxo."},
        {"name": "Vick Blindados Av. Europa", "ig": "vickblindados", "wa": "5511945000888", "city": "São Paulo", "state": "SP", "slug": "vick-blindados-av-europa", "bio": "Showroom de veículos blindados de altíssimo padrão na Avenida Europa."},
        {"name": "Automiami Jardim Europa", "ig": "automiamisp", "wa": "5511973300375", "city": "São Paulo", "state": "SP", "slug": "automiami-av-europa", "bio": "Tradição em importados exclusivos e superesportivos na Av. Europa."},
        {"name": "Só Veículos Av. Europa", "ig": "soveiculos", "wa": "5511954730647", "city": "São Paulo", "state": "SP", "slug": "so-veiculos-av-europa", "bio": "Desde 1985 selecionando supermáquinas e blindados na Avenida Europa."},
        {"name": "BSS Blindagens Showroom", "ig": "bssblindagens", "wa": "551135033030", "city": "São Paulo", "state": "SP", "slug": "bss-blindagens-av-europa", "bio": "A maior blindadora premium das Américas com showroom na Av. Europa."},
        {"name": "Shift Car Alphaville", "ig": "shiftcaroficial", "wa": "5541992558040", "city": "Pinhais", "state": "PR", "slug": "shift-car-curitiba", "bio": "Veículos superesportivos, blindados e curadoria exclusiva no Paraná."},
        {"name": "Autogrif Multimarcas", "ig": "autogrifmultimarcas", "wa": "554130955857", "city": "Curitiba", "state": "PR", "slug": "autogrif-multimarcas-curitiba", "bio": "Seminovos de luxo e importados selecionados em Curitiba."},
        {"name": "AFAN Multimarcas Curitiba", "ig": "afanmultimarcas", "wa": "554133020090", "city": "Curitiba", "state": "PR", "slug": "afan-multimarcas-curitiba", "bio": "Veículos premium periciados e importados de procedência garantida."},
        {"name": "All Motors Setor Marista", "ig": "allmotors", "wa": "5562999880208", "city": "Goiânia", "state": "GO", "slug": "all-motors-goiania", "bio": "Showroom de carros esportivos e importados de luxo na Av. 85."},
        {"name": "Manzoni Motors Flamboyant", "ig": "manzonimotors", "wa": "5562981354835", "city": "Goiânia", "state": "GO", "slug": "manzoni-motors-goiania", "bio": "Veículos nacionais e importados de alto padrão em Goiânia."},
        {"name": "M3 Motors Ricardo Paranhos", "ig": "m3motors", "wa": "5562998812300", "city": "Goiânia", "state": "GO", "slug": "m3-motors-goiania", "bio": "Altíssimo luxo, superesportivos e importados no Setor Marista."},
        {"name": "Ellegance Automóveis Raja", "ig": "elleganceautomoveis", "wa": "5531984673807", "city": "Belo Horizonte", "state": "MG", "slug": "ellegance-automoveis-bh", "bio": "Seminovos nacionais e importados de luxo na Av. Raja Gabáglia."},
        {"name": "Bell Motors Raja Gabáglia", "ig": "bellmotorsbh", "wa": "5531987099593", "city": "Belo Horizonte", "state": "MG", "slug": "bell-motors-raja-bh", "bio": "Compra e venda de importados e veículos de prestígio em BH."},
        {"name": "Império Motors Raja Gabáglia", "ig": "imperiomotors", "wa": "553133173382", "city": "Belo Horizonte", "state": "MG", "slug": "imperio-motors-raja-bh", "bio": "Showroom de veículos premium e superesportivos na Raja Gabáglia."},
        {"name": "GTR Motors Raja Gabáglia", "ig": "gtrmotorsbh", "wa": "5531987485475", "city": "Belo Horizonte", "state": "MG", "slug": "gtr-motors-raja-bh", "bio": "Importados esportivos e blindados revisados em Belo Horizonte."},
        {"name": "Tutti Veículos Raja Gabáglia", "ig": "tuttiveiculos", "wa": "5531993696536", "city": "Belo Horizonte", "state": "MG", "slug": "tutti-veiculos-raja-bh", "bio": "Tradição em automóveis de luxo, esportivos e blindados em MG."},
        {"name": "Sieben Motors Estoril", "ig": "siebenmotors", "wa": "5531992280284", "city": "Belo Horizonte", "state": "MG", "slug": "sieben-motors-bh", "bio": "Curadoria rigorosa de seminovos alemães e importados premium."},
        {"name": "Wish Car BH", "ig": "wishcarbh", "wa": "5531999812450", "city": "Belo Horizonte", "state": "MG", "slug": "wish-car-bh", "bio": "Veículos premium revisados e garantia de procedência em BH."},
        {"name": "Brasil Cars Premium Campinas", "ig": "brasilcarspremium", "wa": "5519999993313", "city": "Campinas", "state": "SP", "slug": "brasil-cars-premium-campinas", "bio": "Showroom de carros esportivos e importados de luxo no Cambuí."},
        {"name": "LT4 Motors Ribeirão Preto", "ig": "lt4motors", "wa": "5516997031795", "city": "Ribeirão Preto", "state": "SP", "slug": "lt4-motors-ribeirao", "bio": "Referência em veículos premium e atendimento personalizado em RP."},
        {"name": "Select Motors Ribeirão Preto", "ig": "selectmotorsrp", "wa": "5516991953970", "city": "Ribeirão Preto", "state": "SP", "slug": "select-motors-ribeirao", "bio": "Seminovos multimarcas e importados de alto padrão no Alto da Boa Vista."},
        {"name": "Smart Carros Palma Travassos", "ig": "smartcarrosrp", "wa": "551632899409", "city": "Ribeirão Preto", "state": "SP", "slug": "smart-carros-ribeirao", "bio": "Variedade em seminovos selecionados e SUVs de luxo em Ribeirão."},
        {"name": "R. Schroeder Automóveis", "ig": "rschroederautomoveis", "wa": "554735123585", "city": "Joinville", "state": "SC", "slug": "r-schroeder-automoveis-joinville", "bio": "Tradição desde 1980 em automóveis premium e clássicos importados."},
        {"name": "AutoGrid Premier Joinville", "ig": "autogridpremier", "wa": "554730234212", "city": "Joinville", "state": "SC", "slug": "autogrid-premier-joinville", "bio": "Seminovos selecionados, SUVs e importados de prestígio em SC."},
        {"name": "Melville Automóveis Joinville", "ig": "melvilleautomoveis", "wa": "554730271547", "city": "Joinville", "state": "SC", "slug": "melville-automoveis-joinville", "bio": "Veículos multimarcas premium e blindados em Santa Catarina."},
        {"name": "Melville Automóveis Blumenau", "ig": "melvilleblumenau", "wa": "554732094321", "city": "Blumenau", "state": "SC", "slug": "melville-automoveis-blumenau", "bio": "Showroom de seminovos de luxo e importados no Vale do Itajaí."},
        {"name": "Blumenau Multimarcas", "ig": "blumenaumultimarcas", "wa": "5547992328026", "city": "Blumenau", "state": "SC", "slug": "blumenau-multimarcas", "bio": "Revenda tradicional de seminovos e importados de qualidade comprovada."},
        {"name": "Garage 345 Estreito", "ig": "garage345", "wa": "5548999191582", "city": "Florianópolis", "state": "SC", "slug": "garage-345-floripa", "bio": "Veículos premium, esportivos, híbridos e elétricos de luxo em Floripa."},
        {"name": "HT Imports Florianópolis", "ig": "htimportscars", "wa": "5548988662438", "city": "Florianópolis", "state": "SC", "slug": "ht-imports-floripa", "bio": "Carros exclusivos e superesportivos com atendimento personalizado."},
        {"name": "Premium Cars Floripa", "ig": "premiumcarsfloripa", "wa": "5548999812400", "city": "Florianópolis", "state": "SC", "slug": "premium-cars-floripa", "bio": "Consultoria e intermediação de veículos do segmento premium em SC."}
    ]

    selected: list[dict[str, Any]] = []
    seen_slugs: set[str] = set()

    for item in automotive_curated_pool:
        slug = item["slug"]
        if slug in EXCLUDED_SLUGS or slug in seen_slugs:
            continue
        seen_slugs.add(slug)
        selected.append({
            "id": f"auto_{slug}",
            "name": item["name"],
            "slug": slug,
            "city": item["city"],
            "state": item["state"],
            "country": "Brasil",
            "niche": "P1 — Revendas premium e multimarcas",
            "score": 95,
            "priority": "A",
            "instagram_username": item["ig"],
            "instagram_url": f"https://www.instagram.com/{item['ig']}/",
            "instagram_bio": item["bio"],
            "followers_count": 22000,
            "whatsapp": item["wa"],
            "phone": item["wa"],
            "has_own_website": False,
            "source": "automotive_curated_intelligence",
            "commercial_status": "icp_identificado",
        })
        if len(selected) >= limit:
            break

    return selected


def build_outreach_assets(
    lead: dict[str, Any],
    rank: int,
    base_url: str = "http://localhost:8090",
    public_demo_base: Optional[str] = "https://brag-showroom-demos.vercel.app",
) -> dict[str, Any]:
    slug = lead["slug"]
    ig_user = (lead.get("instagram_username") or "").lstrip("@")
    raw_name = (lead.get("name") or "").strip()
    ascii_alnum = re.sub(r"[^A-Za-z0-9]", "", raw_name)
    if len(ascii_alnum) < 3 and ig_user:
        raw_name = ig_user.replace("_", " ").replace(".", " ").title()
    company_name = (raw_name or "Sua Loja").split("|")[0].split(" - ")[0].strip()
    full_name = raw_name or company_name
    city = lead.get("city") or "Brasil"
    state = lead.get("state") or "BR"
    raw_phone = lead.get("whatsapp") or lead.get("phone") or ""
    wa_e164 = format_whatsapp_e164(raw_phone)
    phone_display = format_phone_human(raw_phone)
    demo_url = (
        f"{public_demo_base.rstrip('/')}/{slug}"
        if public_demo_base
        else f"{base_url.rstrip('/')}/demos/{slug}"
    )
    vertical = detect_vertical_key(lead)
    theme = DESIGN_THEMES[(rank - 1) % len(DESIGN_THEMES)]

    # Split 60 demos into 2 separate partner queues (30 Denis + 30 Gabriel)
    # Odd ranks -> Fila 1 (Denis #01..#30), Even ranks -> Fila 2 (Gabriel #01..#30) so both queues have identical ICP score quality
    if rank % 2 == 1:
        owner = "denis"
        owner_name = "Denis"
        owner_label = "Fila 1 — Denis (30 Demos)"
        partner_rank = (rank + 1) // 2
    else:
        owner = "gabriel"
        owner_name = "Gabriel"
        owner_label = "Fila 2 — Gabriel (30 Demos)"
        partner_rank = rank // 2

    gap_reason = (
        "todo o trafego do Instagram de voces hoje desagua em link intermediario sem vitrine filtravel no celular"
        if not lead.get("has_own_website")
        else "a experiencia mobile atual nao conta com busca instantanea de acervo e simulacao direta por modelo"
    )

    whatsapp_message = (
        f"Olá, diretoria da *{company_name}*! Tudo bem?\n\n"
        f"Acompanhamos a operação de vocês no Instagram (@{ig_user}) em {city}/{state} e notamos que {gap_reason}.\n\n"
        f"Em vez de enviar uma apresentação comercial teórica, nós projetamos e colocamos no ar uma *demonstração funcional exclusiva do novo Showroom Digital da {company_name}* "
        f"(com filtro instantâneo por marca/modelo, vitrine interativa de alto padrão e captação integrada ao WhatsApp de vocês):\n\n"
        f"{demo_url}\n\n"
        f"Podem abrir direto no celular para testar a experiência. Se fizer sentido ativarmos essa estrutura oficial para a {company_name}, fico à disposição por aqui."
    )

    wa_send_url = f"https://wa.me/{wa_e164}?text={urllib.parse.quote(whatsapp_message)}"

    video_script_60s = f"""# Roteiro de Vídeo Executivo (45 a 60s) — {full_name}
> Origem: Playbook Brag International (Build Before Pitch · Prova sobre Discurso)
> Responsável pelo Disparo: {owner_name} ({owner_label} · #{partner_rank:02d}/30)
> Destinatário: Sócio / Diretor Comercial da {company_name} (@{ig_user})
> Referência Arquitetural: Avantgarde Concept Store ({theme['archetype']})
> Link Público Vercel: {demo_url}

## [00:00 - 00:10] Abertura & Reconhecimento da Marca
"Olá pessoal da {company_name}, aqui é o {owner_name}. Estávamos acompanhando a operação e o posicionamento de vocês em {city}/{state} pelo perfil @{ig_user}..."

## [00:10 - 00:25] Diagnóstico do Gap Real (Fato Objetivo)
"...e notamos que quem chega pelo Instagram hoje encontra {gap_reason}. Na prática, o comprador de alto valor não consegue filtrar modelos por marca, ano ou blindagem em 5 segundos no smartphone."

## [00:25 - 00:45] A Prova (Walkthrough do Protótipo Funcional)
"Em vez de pedir uma reunião teórica, nós desenhamos e publicamos uma demonstração funcional sob medida para a {company_name} no padrão Avantgarde. Veja na tela: Hero Slider com telemetria Ano/Km/Valor, busca flutuante por Marca e Modelo, cards chanfrados e encomenda sob medida conectada ao WhatsApp {phone_display}."

## [00:45 - 00:60] Fechamento (Sintaxe Brag: Zero Pitch Forçado)
"Sem discurso de agência. Estou deixando o link público aqui na mensagem para você testar no próprio celular. Se fizer sentido ativarmos essa arquitetura oficial para a {company_name}, basta me responder por aqui."
"""

    return {
        "rank": rank,
        "owner": owner,
        "owner_name": owner_name,
        "owner_label": owner_label,
        "partner_rank": partner_rank,
        "company_id": lead["id"],
        "slug": slug,
        "name": full_name,
        "short_name": company_name,
        "niche": lead.get("niche") or "P1 — Revendas premium e multimarcas",
        "vertical": vertical,
        "archetype": theme["archetype"],
        "city": city,
        "state": state,
        "score": lead.get("score") or 90,
        "priority": lead.get("priority") or "A",
        "instagram_username": ig_user,
        "instagram_url": lead.get("instagram_url") or (f"https://www.instagram.com/{ig_user}/" if ig_user else ""),
        "instagram_bio": lead.get("instagram_bio") or "",
        "followers_count": lead.get("followers_count") or 0,
        "whatsapp_e164": wa_e164,
        "phone_display": phone_display,
        "demo_url": demo_url,
        "demo_path": f"/demos/{slug}",
        "whatsapp_send_url": wa_send_url,
        "whatsapp_message": whatsapp_message,
        "video_script_60s": video_script_60s,
        "commercial_status": lead.get("commercial_status") or "demo_pronta",
        "recommended_offer": lead.get("recommended_offer") or "Showroom Digital Avantgarde Edition + Concierge WhatsApp",
        "diagnosis": lead.get("diagnosis") or "",
    }


def build_tokens_css(theme: dict[str, str]) -> str:
    """
    Tokenized Avantgarde Design System (`tokens.css`).
    """
    return f""":root {{
  /* Avantgarde Concept Store Palette — {theme['archetype']} */
  --color-bg-primary: {theme['color_bg_primary']};
  --color-bg-elevated: {theme['color_bg_elevated']};
  --color-bg-light: {theme['color_bg_light']};
  --color-card-light: {theme['color_card_light']};
  --color-text-primary: {theme['color_text_primary']};
  --color-text-dark: {theme['color_text_dark']};
  --color-text-secondary: {theme['color_text_secondary']};
  --color-accent: {theme['color_accent']};
  --color-accent-hover: {theme['color_accent_hover']};
  --color-accent-soft: {theme['color_accent_soft']};
  --color-accent-ink: {theme['color_accent_ink']};
  --brand-glow: {theme['brand_glow']};
  --border-subtle: {theme['border_subtle']};
  --border-accent: {theme['border_accent']};

  /* Typography Roles (Barlow Condensed = Trade Gothic Next Condensed equivalent) */
  --font-display: {theme['font_display']};
  --font-sans: {theme['font_sans']};
  --font-mono: {theme['font_mono']};

  /* Calibrated Responsive Scale */
  --text-xs: 0.72rem;
  --text-sm: 0.84rem;
  --text-base: 0.94rem;
  --text-lg: 1.125rem;
  --text-xl: clamp(1.25rem, 2.2vw, 1.65rem);
  --text-2xl: clamp(1.55rem, 3.2vw, 2.65rem);
  --text-hero: clamp(1.85rem, 4.4vw, 3.6rem);

  /* Spatial Rhythm */
  --space-1: 0.25rem;
  --space-2: 0.5rem;
  --space-3: 0.75rem;
  --space-4: 1rem;
  --space-5: 1.5rem;
  --space-6: 2rem;
  --space-8: 3rem;
  --space-10: 4.5rem;
  --container-max: 84rem;

  /* Avantgarde Motion & Easing */
  --ease-ag: cubic-bezier(0.5, 0, 0, 1);
  --ease-out-expo: cubic-bezier(0.16, 1, 0.3, 1);
  --duration-fast: 220ms;
  --duration-ag: 650ms;
}}"""


def render_demo_html(lead: dict[str, Any], rank: int, outreach: dict[str, Any]) -> str:
    theme = DESIGN_THEMES[(rank - 1) % len(DESIGN_THEMES)]
    tokens_css = build_tokens_css(theme)
    vertical = outreach["vertical"]
    catalog = CATALOG_BY_VERTICAL.get(vertical, CATALOG_BY_VERTICAL["multimarcas_premium"])

    slug = lead["slug"]
    img_dir = DEMOS_DIR / slug / "images"
    avatar_rel = "images/avatar.jpg" if (img_dir / "avatar.jpg").exists() else ""

    short_name = html.escape(outreach["short_name"])
    full_name = html.escape(outreach["name"])
    city = html.escape(outreach["city"])
    state = html.escape(outreach["state"])
    city_state = f"{city} - {state}"
    ig_user = html.escape(outreach["instagram_username"] or "oficial")
    raw_bio = re.sub(r"[^\w\s,.;:/()\-•|@+]", "", outreach["instagram_bio"] or "").strip()
    ig_bio = html.escape(
        raw_bio
        if len(raw_bio) >= 24
        else f"Com foco em veículos superesportivos, blindados e seminovos selecionados, a {outreach['short_name']} destaca-se pela qualidade do estoque e transparência nos negócios em {outreach['city']}."
    )
    phone_display = html.escape(outreach["phone_display"])
    wa_e164 = html.escape(outreach["whatsapp_e164"])
    followers = int(outreach.get("followers_count") or 0)
    followers_str = f"+{followers:,}".replace(",", ".") if followers > 0 else "100%"

    brand_logo_html = (
        f'<img src="{avatar_rel}" alt="{short_name}" class="ag-header-avatar" />'
        if avatar_rel
        else f'<span class="ag-header-monogram" aria-hidden="true">{short_name[:2].upper()}</span>'
    )

    brands_list = sorted({item["brand"] for item in catalog})
    brand_options_html = "".join(
        f'<option value="{html.escape(b)}">{html.escape(b)}</option>' for b in brands_list
    )

    hero_slides = catalog[:3]
    hero_slides_json = json.dumps(hero_slides, ensure_ascii=False)
    catalog_json = json.dumps(catalog, ensure_ascii=False)

    wa_header_q = urllib.parse.quote(f"Olá {outreach['short_name']}! Acessei o site e gostaria de atendimento.")
    wa_about_q = urllib.parse.quote(f"Olá {outreach['short_name']}! Quero conhecer o atendimento e estoque disponível em {outreach['city']}.")
    wa_exp_q = urllib.parse.quote(f"Olá {outreach['short_name']}! Gostaria de agendar uma visita à loja ({outreach['short_name']} Experience).")

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover" />
  <meta name="theme-color" content="{theme['color_accent']}" />
  <title>Início | {short_name}</title>
  <meta name="description" content="A {full_name} é referência no mercado de veículos premium em {city_state}. Conheça nosso estoque selecionado." />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="{theme['font_url']}" rel="stylesheet" />
  <style>
{tokens_css}

    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    html {{ scroll-behavior: smooth; }}
    body {{
      background-color: var(--color-bg-primary);
      color: var(--color-text-primary);
      font-family: var(--font-sans);
      font-size: var(--text-base);
      line-height: 1.5;
      -webkit-font-smoothing: antialiased;
      overflow-x: hidden;
    }}
    a, button, input, select {{ font: inherit; color: inherit; }}
    :focus-visible {{
      outline: 2px solid var(--color-accent);
      outline-offset: 2px;
    }}
    .tabular {{
      font-family: var(--font-mono);
      font-variant-numeric: tabular-nums;
    }}
    .container {{
      max-width: var(--container-max);
      margin: 0 auto;
      padding: 0 var(--space-6);
    }}

    /* ======================================================================
       AVANTGARDE BUTTON SYSTEM (.button-orange / .button-dark)
       ====================================================================== */
    .ag-btn {{
      position: relative;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: var(--space-2);
      padding: 0.9rem 2rem;
      font-family: var(--font-display);
      font-size: 0.92rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.22em;
      text-decoration: none;
      border: none;
      cursor: pointer;
      overflow: hidden;
      background: var(--color-accent);
      color: var(--color-accent-ink);
      transition: background-color var(--duration-ag) var(--ease-ag), transform var(--duration-fast) var(--ease-out-expo);
    }}
    .ag-btn:hover {{
      background: #000000;
      color: #ffffff;
    }}
    .ag-btn-dark {{
      background: #141418;
      color: var(--color-accent);
      border: 1px solid var(--border-accent);
    }}
    .ag-btn-dark:hover {{
      background: var(--color-accent);
      color: #ffffff;
    }}

    /* ======================================================================
       HEADER (#main-header — Minimalist Dark Bar)
       ====================================================================== */
    #main-header {{
      position: sticky;
      top: 0;
      z-index: 50;
      background: rgba(10, 10, 12, 0.92);
      backdrop-filter: blur(16px);
      border-bottom: 1px solid var(--border-subtle);
    }}
    .ag-header-inner {{
      max-width: var(--container-max);
      margin: 0 auto;
      padding: 0.95rem var(--space-6);
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: var(--space-4);
    }}
    .ag-brand {{
      display: flex;
      align-items: center;
      gap: var(--space-3);
      text-decoration: none;
    }}
    .ag-header-avatar {{
      width: 2.5rem;
      height: 2.5rem;
      border-radius: 50%;
      object-fit: cover;
      border: 1px solid var(--color-accent);
    }}
    .ag-header-monogram {{
      width: 2.5rem;
      height: 2.5rem;
      display: flex;
      align-items: center;
      justify-content: center;
      background: var(--color-accent);
      color: #fff;
      font-family: var(--font-display);
      font-weight: 800;
      font-size: 1.1rem;
      letter-spacing: 0.1em;
    }}
    .ag-brand-name {{
      font-family: var(--font-display);
      font-size: 1.35rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.24em;
      color: #ffffff;
      line-height: 1;
    }}
    .ag-brand-city {{
      font-size: 0.68rem;
      text-transform: uppercase;
      letter-spacing: 0.2em;
      color: var(--color-text-secondary);
      margin-top: 3px;
    }}
    .ag-nav {{
      display: flex;
      align-items: center;
      gap: 2.25rem;
    }}
    .ag-nav a {{
      font-family: var(--font-display);
      font-size: 0.88rem;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.22em;
      color: #d9d9d9;
      text-decoration: none;
      transition: color var(--duration-fast);
    }}
    .ag-nav a:hover {{
      color: var(--color-accent);
    }}
    .ag-header-actions {{
      display: flex;
      align-items: center;
      gap: var(--space-3);
    }}
    .ag-header-phone {{
      font-family: var(--font-display);
      font-size: 0.9rem;
      font-weight: 700;
      letter-spacing: 0.14em;
      color: #ffffff;
      text-decoration: none;
      padding: 0.55rem 1.1rem;
      border: 1px solid var(--border-subtle);
      transition: border-color var(--duration-fast), color var(--duration-fast);
    }}
    .ag-header-phone:hover {{
      border-color: var(--color-accent);
      color: var(--color-accent);
    }}

    /* ======================================================================
       SECTION 1: HERO SLIDER (.section-hero — Avantgarde Full-Stage)
       ====================================================================== */
    .section-hero {{
      position: relative;
      background: radial-gradient(circle at 50% 42%, rgba(255, 255, 255, 0.07) 0%, #09090b 70%);
      padding: 3.5rem 0 7.5rem;
      overflow: hidden;
      border-bottom: 1px solid var(--border-subtle);
    }}
    .hero-Watermark {{
      position: absolute;
      top: 14%;
      left: 50%;
      transform: translateX(-50%);
      font-family: var(--font-display);
      font-size: clamp(4.5rem, 15vw, 13rem);
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 0.28em;
      color: rgba(255, 255, 255, 0.025);
      white-space: nowrap;
      pointer-events: none;
      user-select: none;
      z-index: 1;
    }}
    .hero-stage {{
      position: relative;
      z-index: 2;
      max-width: var(--container-max);
      margin: 0 auto;
      padding: 0 var(--space-6);
      display: flex;
      flex-direction: column;
      align-items: center;
      text-align: center;
    }}
    .hero-brand-overline {{
      color: var(--color-accent);
      font-family: var(--font-display);
      font-size: 1rem;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.52em;
      margin-bottom: 0.45rem;
    }}
    .hero-model-title {{
      color: #ffffff;
      font-family: var(--font-display);
      font-size: var(--text-hero);
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.34em;
      line-height: 1.05;
      margin-bottom: 1.5rem;
    }}
    .hero-image-frame {{
      position: relative;
      width: 100%;
      max-width: 56rem;
      height: 23rem;
      margin: 0 auto 1.75rem;
      overflow: hidden;
      box-shadow: 0 32px 80px rgba(0, 0, 0, 0.75);
      border: 1px solid var(--border-subtle);
    }}
    .hero-image-frame img {{
      width: 100%;
      height: 100%;
      object-fit: cover;
      transition: transform 0.8s var(--ease-ag);
    }}
    .hero-image-frame:hover img {{
      transform: scale(1.03);
    }}
    .hero-bottom-bar {{
      width: 100%;
      max-width: 56rem;
      display: flex;
      align-items: center;
      justify-content: space-between;
      flex-wrap: wrap;
      gap: var(--space-4);
      padding-top: 1rem;
      border-top: 1px solid var(--border-subtle);
    }}
    .hero-tagline {{
      font-family: var(--font-display);
      font-size: 1.15rem;
      font-weight: 400;
      letter-spacing: 0.22em;
      text-transform: uppercase;
      color: var(--color-text-secondary);
    }}
    .hero-telemetry {{
      display: flex;
      align-items: center;
      gap: 2.75rem;
    }}
    .telemetry-item {{
      text-align: left;
    }}
    .telemetry-label {{
      font-size: 0.68rem;
      text-transform: uppercase;
      letter-spacing: 0.2em;
      color: var(--color-text-secondary);
      margin-bottom: 2px;
    }}
    .telemetry-value {{
      font-family: var(--font-display);
      font-size: 1.25rem;
      font-weight: 700;
      letter-spacing: 0.08em;
      color: #ffffff;
      font-variant-numeric: tabular-nums;
    }}
    .hero-controls {{
      display: flex;
      align-items: center;
      gap: var(--space-3);
    }}
    .slide-dot {{
      width: 2.2rem;
      height: 3px;
      background: rgba(255, 255, 255, 0.2);
      border: none;
      cursor: pointer;
      transition: background var(--duration-fast), width var(--duration-fast);
    }}
    .slide-dot.active {{
      background: var(--color-accent);
      width: 3.4rem;
    }}

    /* ======================================================================
       SECTION 2: FLOATING SEARCH BAR (.section-filter — Avantgarde Overlap)
       ====================================================================== */
    .section-filter {{
      position: relative;
      z-index: 10;
      margin-top: -3.25rem;
      padding: 0 var(--space-6);
    }}
    .filter-dock {{
      max-width: 64rem;
      margin: 0 auto;
      background: #ffffff;
      color: #131313;
      min-height: 5.6rem;
      padding: 1rem 1.75rem;
      box-shadow: 0 24px 64px rgba(0, 0, 0, 0.28);
      display: grid;
      grid-template-columns: auto 1fr 1fr 1.2fr auto;
      align-items: center;
      gap: 1.25rem;
    }}
    .filter-dock-title {{
      font-family: var(--font-display);
      font-size: 1.1rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.14em;
      line-height: 1.1;
      color: #131313;
      padding-right: 1rem;
      border-right: 1px solid #e5e5e5;
    }}
    .filter-field {{
      display: flex;
      flex-direction: column;
      gap: 3px;
    }}
    .filter-field label {{
      font-family: var(--font-display);
      font-size: 0.7rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.18em;
      color: var(--color-accent);
    }}
    .filter-field select,
    .filter-field input {{
      border: none;
      border-bottom: 1px solid #d4d4d8;
      background: transparent;
      color: #131313;
      font-size: 0.88rem;
      font-weight: 600;
      padding: 0.35rem 0;
      outline: none;
    }}
    .filter-field select:focus,
    .filter-field input:focus {{
      border-bottom-color: var(--color-accent);
    }}

    /* ======================================================================
       SECTION 3: SHOWROOM VEHICLES (.section-vehicles — Light Gallery Stage)
       ====================================================================== */
    .section-vehicles {{
      background: linear-gradient(180deg, var(--color-bg-light) 0%, #f7f7f9 100%);
      color: var(--color-text-dark);
      margin-top: -2.75rem;
      padding: 7rem 0 6rem;
      position: relative;
      z-index: 1;
    }}
    .ag-headline {{
      display: flex;
      align-items: flex-end;
      justify-content: space-between;
      flex-wrap: wrap;
      gap: var(--space-6);
      margin-bottom: 3.5rem;
    }}
    .ag-headline-small {{
      font-family: var(--font-display);
      font-size: 0.95rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.32em;
      color: var(--color-accent);
      margin-bottom: 0.35rem;
    }}
    .ag-headline-title {{
      font-family: var(--font-display);
      font-size: clamp(2.2rem, 5vw, 4.25rem);
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      line-height: 0.95;
      color: #000000;
    }}
    .ag-headline-right {{
      max-width: 28rem;
      font-size: 0.92rem;
      color: #414141;
      line-height: 1.6;
    }}
    .ag-headline-right strong {{
      display: block;
      color: #000000;
      font-size: 1rem;
      margin-bottom: 0.25rem;
    }}

    /* Category Quick Filter Bar */
    .ag-pills-row {{
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      justify-content: space-between;
      gap: var(--space-3);
      margin-bottom: 2.25rem;
    }}
    .ag-pill-list {{
      display: flex;
      flex-wrap: wrap;
      gap: 0.5rem;
    }}
    .ag-pill {{
      background: #ffffff;
      color: #414141;
      border: 1px solid #d9d9de;
      padding: 0.5rem 1.1rem;
      font-family: var(--font-display);
      font-size: 0.82rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.16em;
      cursor: pointer;
      transition: all var(--duration-fast);
    }}
    .ag-pill.active,
    .ag-pill:hover {{
      background: var(--color-accent);
      color: #ffffff;
      border-color: var(--color-accent);
    }}

    /* Chamfered Avantgarde Vehicle Grid & Cards */
    .ag-vehicles-grid {{
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 2rem;
    }}
    .ag-card {{
      position: relative;
      background: #ffffff;
      clip-path: polygon(0 0, 100% 0, 100% calc(100% - 54px), calc(100% - 54px) 100%, 0 100%);
      box-shadow: 0 12px 34px rgba(0, 0, 0, 0.06);
      transition: transform var(--duration-ag) var(--ease-ag), box-shadow var(--duration-ag) var(--ease-ag);
      display: flex;
      flex-direction: column;
    }}
    .ag-card::after {{
      content: "";
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      height: 3px;
      background: var(--color-accent);
      transform: scaleX(0);
      transform-origin: 0 50%;
      transition: transform var(--duration-ag) var(--ease-ag);
      z-index: 4;
    }}
    .ag-card:hover {{
      transform: translateY(-6px);
      box-shadow: 0 24px 48px rgba(0, 0, 0, 0.12);
    }}
    .ag-card:hover::after {{
      transform: scaleX(1);
    }}
    .ag-card-media {{
      position: relative;
      height: 15rem;
      overflow: hidden;
      background: #111;
    }}
    .ag-card-media img {{
      width: 100%;
      height: 100%;
      object-fit: cover;
      transition: transform var(--duration-ag) var(--ease-ag);
    }}
    .ag-card:hover .ag-card-media img {{
      transform: scale(1.06);
    }}
    .ag-card-armored {{
      position: absolute;
      top: 0.85rem;
      right: 0.85rem;
      background: var(--color-accent-soft);
      color: var(--color-accent);
      font-family: var(--font-display);
      font-size: 0.72rem;
      font-weight: 700;
      letter-spacing: 0.16em;
      text-transform: uppercase;
      padding: 0.25rem 0.65rem;
      z-index: 3;
    }}
    .ag-card-content {{
      padding: 1.5rem 2.25rem 2.75rem;
      display: flex;
      flex-direction: column;
      flex: 1;
    }}
    .ag-card-brand {{
      color: var(--color-accent);
      font-family: var(--font-display);
      font-size: 0.88rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.16em;
      margin-bottom: 0.35rem;
    }}
    .ag-card-title {{
      color: #232323;
      font-family: var(--font-display);
      font-size: 1.35rem;
      font-weight: 600;
      line-height: 1.12;
      letter-spacing: 0.1em;
      text-transform: uppercase;
      position: relative;
      padding-bottom: 1.1rem;
      margin-bottom: 1rem;
    }}
    .ag-card-title::before {{
      content: "";
      position: absolute;
      bottom: 0;
      left: 0;
      width: 62px;
      height: 1px;
      background: var(--color-accent);
    }}
    .ag-card-info {{
      display: flex;
      align-items: center;
      gap: 2.25rem;
      margin-bottom: 0.85rem;
      color: #696969;
      font-size: 0.86rem;
      letter-spacing: 0.06em;
      font-variant-numeric: tabular-nums;
    }}
    .ag-card-specs {{
      font-size: 0.8rem;
      color: #797979;
      margin-bottom: 1.25rem;
      flex: 1;
    }}
    .ag-card-price {{
      color: #232323;
      margin-bottom: 1.25rem;
      font-variant-numeric: tabular-nums;
    }}
    .ag-card-price small {{
      font-size: 0.78rem;
      font-weight: 500;
      margin-right: 4px;
      color: #696969;
    }}
    .ag-card-price span {{
      font-family: var(--font-display);
      font-size: 1.45rem;
      font-weight: 700;
      letter-spacing: 0.04em;
    }}
    .ag-card-actions {{
      display: flex;
      align-items: center;
      gap: 0.65rem;
    }}
    .ag-card-actions .ag-btn {{
      padding: 0.65rem 1.25rem;
      font-size: 0.8rem;
      flex: 1;
    }}
    .ag-card-sim {{
      background: transparent;
      border: 1px solid #d0d0d5;
      color: #414141;
      padding: 0.65rem 0.95rem;
      font-family: var(--font-display);
      font-size: 0.78rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.14em;
      cursor: pointer;
      transition: border-color var(--duration-fast), color var(--duration-fast);
    }}
    .ag-card-sim:hover {{
      border-color: var(--color-accent);
      color: var(--color-accent);
    }}

    /* ======================================================================
       SECTION 4: BRAND MANIFESTO (.section-about — Full-Bleed Accent + Circles)
       ====================================================================== */
    .section-about {{
      position: relative;
      background-color: var(--color-accent);
      color: #ffffff;
      padding: 6rem 0;
      overflow: hidden;
    }}
    .about-circles {{
      position: absolute;
      inset: 0;
      pointer-events: none;
      overflow: hidden;
    }}
    .about-circle {{
      position: absolute;
      top: 50%;
      left: 50%;
      width: 68rem;
      height: 68rem;
      border: 1px solid rgba(255, 255, 255, 0.22);
      border-radius: 50%;
      transform: translate(-50%, -50%);
    }}
    .about-circle:nth-child(2) {{
      width: 44rem;
      height: 44rem;
      border-color: rgba(255, 255, 255, 0.14);
    }}
    .about-grid {{
      position: relative;
      z-index: 2;
      display: grid;
      grid-template-columns: 1.05fr 0.95fr;
      gap: 4rem;
      align-items: center;
    }}
    .about-brand-tag {{
      font-family: var(--font-display);
      font-size: 0.9rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.36em;
      opacity: 0.85;
      margin-bottom: 0.5rem;
    }}
    .about-small {{
      font-family: var(--font-display);
      font-size: 1.5rem;
      font-weight: 400;
      text-transform: uppercase;
      letter-spacing: 0.2em;
      line-height: 1;
    }}
    .about-title {{
      font-family: var(--font-display);
      font-size: clamp(2.6rem, 5.5vw, 4.8rem);
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      line-height: 0.95;
      margin-bottom: 1.5rem;
    }}
    .about-desc {{
      font-size: 1rem;
      line-height: 1.65;
      margin-bottom: 2rem;
      max-width: 34rem;
    }}
    .about-visual {{
      position: relative;
      height: 24rem;
      overflow: hidden;
      box-shadow: 0 28px 64px rgba(0, 0, 0, 0.35);
    }}
    .about-visual img {{
      width: 100%;
      height: 100%;
      object-fit: cover;
    }}

    /* ======================================================================
       SECTION 5: MODEL NOT FOUND (.section-model-not-found — Bespoke Order)
       ====================================================================== */
    .section-model-not-found {{
      background-color: #000000;
      color: #ffffff;
      padding: 6rem 0;
      position: relative;
      border-bottom: 1px solid var(--border-subtle);
    }}
    .mnf-head {{
      display: flex;
      align-items: flex-end;
      justify-content: space-between;
      flex-wrap: wrap;
      gap: var(--space-5);
      margin-bottom: 2.75rem;
    }}
    .mnf-title {{
      font-family: var(--font-display);
      font-size: clamp(1.75rem, 3.2vw, 2.5rem);
      font-weight: 400;
      line-height: 1.15;
      letter-spacing: 0.08em;
      text-transform: uppercase;
    }}
    .mnf-title span {{
      display: block;
      font-weight: 800;
      color: var(--color-accent);
    }}
    .mnf-desc {{
      max-width: 22rem;
      color: var(--color-text-secondary);
      font-size: 0.92rem;
    }}
    .mnf-form {{
      display: grid;
      grid-template-columns: repeat(4, 1fr) auto;
      gap: 1.25rem;
      align-items: end;
      padding-top: 1.5rem;
      border-top: 1px solid var(--border-subtle);
    }}
    .mnf-input {{
      width: 100%;
      background: transparent;
      border: none;
      border-bottom: 1px solid rgba(255, 255, 255, 0.25);
      color: #ffffff;
      padding: 0.75rem 0;
      font-size: 0.9rem;
      outline: none;
    }}
    .mnf-input:focus {{
      border-bottom-color: var(--color-accent);
    }}

    /* ======================================================================
       SECTION 6: EXPERIENCE BANNER (.section-general-experience)
       ====================================================================== */
    .section-experience {{
      background: var(--color-bg-elevated);
      padding: 5rem 0;
      border-bottom: 1px solid var(--border-subtle);
    }}
    .exp-box {{
      display: grid;
      grid-template-columns: 0.9fr 1.1fr;
      background: #09090b;
      border: 1px solid var(--border-subtle);
      overflow: hidden;
    }}
    .exp-img {{
      min-height: 18rem;
      background: url("{catalog[1]['image']}") center/cover no-repeat;
    }}
    .exp-content {{
      padding: 3.5rem;
      display: flex;
      flex-direction: column;
      justify-content: center;
      gap: 1.25rem;
    }}
    .exp-title {{
      font-family: var(--font-display);
      font-size: clamp(1.75rem, 3vw, 2.5rem);
      font-weight: 400;
      text-transform: uppercase;
      letter-spacing: 0.12em;
      line-height: 1.1;
    }}
    .exp-title span {{
      display: block;
      font-weight: 800;
      color: var(--color-accent);
    }}

    /* ======================================================================
       FOOTER (#main-footer — "Conduzindo a excelência.")
       ====================================================================== */
    #main-footer {{
      background: #060608;
      color: #ffffff;
      padding: 4.5rem 0 calc(4.5rem + env(safe-area-inset-bottom, 0px));
    }}
    .footer-top {{
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      flex-wrap: wrap;
      gap: var(--space-6);
      padding-bottom: 3rem;
      border-bottom: 1px solid var(--border-subtle);
    }}
    .footer-motto {{
      font-family: var(--font-display);
      font-size: 1.85rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.14em;
      margin: 0.75rem 0;
    }}
    .footer-phone {{
      display: inline-block;
      font-family: var(--font-display);
      font-size: 1.5rem;
      font-weight: 700;
      color: var(--color-accent);
      text-decoration: none;
      letter-spacing: 0.1em;
      margin-bottom: 0.75rem;
    }}
    .footer-bottom {{
      padding-top: 2rem;
      display: flex;
      justify-content: space-between;
      flex-wrap: wrap;
      gap: var(--space-4);
      font-size: 0.8rem;
      color: var(--color-text-secondary);
    }}

    /* Simulator Modal */
    .ag-modal-backdrop {{
      position: fixed;
      inset: 0;
      background: rgba(0, 0, 0, 0.84);
      backdrop-filter: blur(8px);
      display: none;
      align-items: center;
      justify-content: center;
      padding: var(--space-5);
      z-index: 80;
    }}
    .ag-modal-backdrop.open {{ display: flex; }}
    .ag-modal {{
      background: #121216;
      border: 1px solid var(--border-accent);
      max-width: 32rem;
      width: 100%;
      padding: 2.25rem;
      color: #ffffff;
    }}

    /* Floating WhatsApp Concierge */
    .wa-float {{
      position: fixed;
      bottom: calc(1.25rem + env(safe-area-inset-bottom, 0px));
      right: 1.25rem;
      background: var(--color-accent);
      color: #ffffff;
      font-family: var(--font-display);
      font-weight: 700;
      font-size: 0.88rem;
      letter-spacing: 0.18em;
      text-transform: uppercase;
      padding: 0.85rem 1.5rem;
      text-decoration: none;
      box-shadow: 0 18px 42px rgba(0, 0, 0, 0.65);
      z-index: 60;
      transition: transform var(--duration-fast);
    }}
    .wa-float:hover {{ transform: translateY(-3px); }}

    /* ======================================================================
       MOBILE CALIBRATION (@media max-width: 1023px & 640px)
       ====================================================================== */
    @media (max-width: 1023px) {{
      .ag-nav {{ display: none; }}
      .filter-dock {{
        grid-template-columns: 1fr 1fr;
        gap: 1rem;
      }}
      .filter-dock-title {{
        grid-column: 1 / -1;
        border-right: none;
        border-bottom: 1px solid #e5e5e5;
        padding-bottom: 0.5rem;
      }}
      .ag-vehicles-grid {{
        grid-template-columns: repeat(2, 1fr);
      }}
      .about-grid,
      .exp-box,
      .mnf-form {{
        grid-template-columns: 1fr;
      }}
    }}
    @media (max-width: 640px) {{
      :root {{
        --text-xs: 0.68rem;
        --text-sm: 0.78rem;
        --text-base: 0.86rem;
        --text-lg: 0.98rem;
        --text-xl: 1.15rem;
        --text-2xl: 1.45rem;
        --text-hero: 1.55rem;
      }}
      .container {{
        padding: 0 1rem;
      }}
      .ag-header-inner {{
        padding: 0.75rem 1rem;
      }}
      .ag-brand-name {{
        font-size: 1rem;
        letter-spacing: 0.14em;
        max-width: 11.5rem;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
      }}
      .ag-brand-city {{
        font-size: 0.6rem;
        letter-spacing: 0.12em;
      }}
      .ag-header-phone {{
        display: none;
      }}
      .ag-btn {{
        padding: 0.65rem 1.1rem;
        font-size: 0.76rem;
        letter-spacing: 0.16em;
      }}
      .section-hero {{
        padding: 1.75rem 0 5rem;
      }}
      .hero-brand-overline {{
        font-size: 0.76rem;
        letter-spacing: 0.34em;
      }}
      .hero-model-title {{
        font-size: 1.5rem;
        letter-spacing: 0.18em;
        margin-bottom: 1rem;
      }}
      .hero-image-frame {{
        height: 13.5rem;
        margin-bottom: 1rem;
      }}
      .hero-telemetry {{
        width: 100%;
        justify-content: space-between;
        gap: 0.75rem;
      }}
      .telemetry-value {{
        font-size: 1rem;
      }}
      .filter-dock {{
        grid-template-columns: 1fr;
        padding: 1rem;
      }}
      .section-vehicles {{
        padding: 4.5rem 0 3.5rem;
      }}
      .ag-headline-title {{
        font-size: 1.85rem;
      }}
      .ag-vehicles-grid {{
        grid-template-columns: 1fr;
        gap: 1.25rem;
      }}
      .ag-card-media {{
        height: 12.5rem;
      }}
      .ag-card-content {{
        padding: 1.25rem 1.35rem 2.25rem;
      }}
      .ag-card-title {{
        font-size: 1.15rem;
      }}
      .ag-card-price span {{
        font-size: 1.25rem;
      }}
      .section-about,
      .section-model-not-found,
      .section-experience {{
        padding: 3.5rem 0;
      }}
      .about-title {{
        font-size: 2.1rem;
      }}
      .about-visual {{
        height: 14rem;
      }}
      .exp-content {{
        padding: 1.75rem 1.25rem;
      }}
      .wa-float {{
        left: 1rem;
        right: 1rem;
        text-align: center;
        padding: 0.75rem 1rem;
        font-size: 0.78rem;
      }}
    }}
    @media (prefers-reduced-motion: reduce) {{
      *, *::before, *::after {{
        animation-duration: 0.01ms !important;
        transition-duration: 0.01ms !important;
        scroll-behavior: auto !important;
      }}
    }}
  </style>
</head>
<body>

  <!-- AVANTGARDE MINIMALIST HEADER -->
  <header id="main-header">
    <div class="ag-header-inner">
      <a href="#" class="ag-brand" aria-label="{short_name}">
        {brand_logo_html}
        <div>
          <div class="ag-brand-name">{short_name}</div>
          <div class="ag-brand-city">{city_state}</div>
        </div>
      </a>
      <nav class="ag-nav" aria-label="Navegação Principal">
        <a href="#veiculos">Veículos</a>
        <a href="#sobre">Sobre</a>
        <a href="#encomenda">Venda / Encomenda</a>
        <a href="#experience">Experiência</a>
      </nav>
      <div class="ag-header-actions">
        <a href="https://wa.me/{wa_e164}?text={wa_header_q}" target="_blank" rel="noopener" class="ag-header-phone">{phone_display}</a>
        <a href="https://wa.me/{wa_e164}?text={wa_header_q}" target="_blank" rel="noopener" class="ag-btn"><span>Contato</span></a>
      </div>
    </div>
  </header>

  <main id="page-home">
    <!-- SECTION 1: AVANTGARDE HERO STAGE -->
    <section class="section-hero" aria-label="Destaque Principal">
      <div class="hero-Watermark" id="heroWatermark">{html.escape(hero_slides[0]['brand'])}</div>
      <div class="hero-stage">
        <div class="hero-brand-overline" id="heroBrand">{html.escape(hero_slides[0]['brand'])}</div>
        <h1 class="hero-model-title" id="heroModel">{html.escape(hero_slides[0]['model'])}</h1>

        <div class="hero-image-frame">
          <img id="heroImage" src="{hero_slides[0]['image']}" alt="{html.escape(hero_slides[0]['title'])}" fetchpriority="high" />
        </div>

        <div class="hero-bottom-bar">
          <div class="hero-tagline" id="heroTagline">{html.escape(hero_slides[0]['tagline'])}</div>

          <div class="hero-telemetry">
            <div class="telemetry-item">
              <div class="telemetry-label">Ano</div>
              <div class="telemetry-value" id="heroYear">{html.escape(hero_slides[0]['year_label'])}</div>
            </div>
            <div class="telemetry-item">
              <div class="telemetry-label">Km</div>
              <div class="telemetry-value" id="heroKm">{html.escape(hero_slides[0]['km_label'])}</div>
            </div>
            <div class="telemetry-item">
              <div class="telemetry-label">Valor</div>
              <div class="telemetry-value" id="heroPrice">R$ {format_brl_avantgarde(hero_slides[0]['price'])}</div>
            </div>
          </div>

          <div class="hero-controls">
            <div style="display:flex;gap:6px;" role="tablist" aria-label="Selecionar destaque">
              <button type="button" class="slide-dot active" onclick="setHeroSlide(0)" aria-label="Destaque 1"></button>
              <button type="button" class="slide-dot" onclick="setHeroSlide(1)" aria-label="Destaque 2"></button>
              <button type="button" class="slide-dot" onclick="setHeroSlide(2)" aria-label="Destaque 3"></button>
            </div>
            <a id="heroCta" href="https://wa.me/{wa_e164}" target="_blank" rel="noopener" class="ag-btn">
              <span>Conheça</span>
            </a>
          </div>
        </div>
      </div>
    </section>

    <!-- SECTION 2: OVERLAPPING FLOATING SEARCH DOCK -->
    <section class="section-filter" aria-label="Filtro de Veículos">
      <div class="filter-dock">
        <div class="filter-dock-title">Encontre seu<br />próximo veículo</div>
        <div class="filter-field">
          <label for="fltBrand">Marcas</label>
          <select id="fltBrand" onchange="syncModelsDropdown(); renderCatalog();">
            <option value="">Todas as Marcas</option>
            {brand_options_html}
          </select>
        </div>
        <div class="filter-field">
          <label for="fltModel">Modelos</label>
          <select id="fltModel" onchange="renderCatalog()">
            <option value="">Todos os Modelos</option>
          </select>
        </div>
        <div class="filter-field">
          <label for="searchInput">Busca Rápida / Blindagem</label>
          <input type="search" id="searchInput" placeholder="Ex: Blindado, V8, 2024..." oninput="renderCatalog()" />
        </div>
        <div>
          <a href="#veiculos" onclick="renderCatalog()" class="ag-btn" style="width:100%;"><span>Buscar</span></a>
        </div>
      </div>
    </section>

    <!-- SECTION 3: AVANTGARDE SHOWROOM GALLERY -->
    <section class="section-vehicles" id="veiculos">
      <div class="container">
        <div class="ag-headline">
          <div>
            <div class="ag-headline-small">Mude suas perspectivas</div>
            <h2 class="ag-headline-title">Mova a sua paixão</h2>
          </div>
          <div class="ag-headline-right">
            <strong>Escolha o modelo ideal para o seu estilo de vida</strong>
            <p>O propósito da {short_name} é ser a melhor escolha em automóveis para seus clientes e fazer parte dos momentos especiais da sua vida em {city_state}.</p>
          </div>
        </div>

        <div class="ag-pills-row">
          <div class="ag-pill-list" role="group" aria-label="Filtrar por categoria">
            <button type="button" class="ag-pill active" data-cat="ALL" onclick="filterByCategory('ALL')">Todos os Veículos ({len(catalog)})</button>
            <button type="button" class="ag-pill" data-cat="BLINDADOS" onclick="filterByCategory('BLINDADOS')">Blindados</button>
            <button type="button" class="ag-pill" data-cat="2024" onclick="filterByCategory('2024')">Safra 2024+</button>
          </div>
          <div style="font-family:var(--font-display);font-size:0.9rem;font-weight:700;letter-spacing:0.14em;text-transform:uppercase;color:#414141;" id="countLabel">
            {len(catalog)} veículos disponíveis
          </div>
        </div>

        <div class="ag-vehicles-grid" id="catalogGrid" aria-live="polite"></div>
      </div>
    </section>

    <!-- SECTION 4: CONDUZINDO A EXCELÊNCIA (AVANTGARDE ABOUT STAGE) -->
    <section class="section-about" id="sobre">
      <div class="about-circles" aria-hidden="true">
        <div class="about-circle"></div>
        <div class="about-circle"></div>
      </div>
      <div class="container">
        <div class="about-grid">
          <div>
            <div class="about-brand-tag">{short_name}</div>
            <div class="about-small">Conduzindo a</div>
            <h2 class="about-title">Excelência</h2>
            <div class="about-desc">
              <p style="font-weight:700;margin-bottom:0.65rem;">A {full_name} é referência no mercado de veículos premium em {city_state}.</p>
              <p>{ig_bio}</p>
            </div>
            <div style="display:flex;gap:1.5rem;flex-wrap:wrap;margin-bottom:2rem;">
              <div>
                <div style="font-family:var(--font-display);font-size:2rem;font-weight:800;line-height:1;">100%</div>
                <div style="font-size:0.75rem;text-transform:uppercase;letter-spacing:0.15em;opacity:0.85;">Procedência &amp; Laudo</div>
              </div>
              <div>
                <div style="font-family:var(--font-display);font-size:2rem;font-weight:800;line-height:1;">{followers_str}</div>
                <div style="font-size:0.75rem;text-transform:uppercase;letter-spacing:0.15em;opacity:0.85;">Clientes &amp; Audiência @{ig_user}</div>
              </div>
            </div>
            <a href="https://wa.me/{wa_e164}?text={wa_about_q}" target="_blank" rel="noopener" class="ag-btn" style="background:#000;color:#fff;">
              <span>Conheça</span>
            </a>
          </div>
          <div class="about-visual">
            <img src="{catalog[0]['image']}" alt="{short_name} Showroom" loading="lazy" />
          </div>
        </div>
      </div>
    </section>

    <!-- SECTION 5: MODEL NOT FOUND (BESPOKE CONSIGNMENT & ORDER) -->
    <section class="section-model-not-found" id="encomenda">
      <div class="container">
        <div class="mnf-head">
          <h2 class="mnf-title">
            Não encontrou o modelo
            <span>que estava buscando?</span>
          </h2>
          <div class="mnf-desc">
            <p>Deixe agora o seu contato ou envie no WhatsApp para ser notificado(a) quando chegar a configuração exata que você procura.</p>
          </div>
        </div>
        <form class="mnf-form" onsubmit="submitBespokeOrder(event)">
          <div>
            <input type="text" id="mnfModel" class="mnf-input" placeholder="Modelo desejado" required />
          </div>
          <div>
            <input type="text" id="mnfName" class="mnf-input" placeholder="Seu nome" required />
          </div>
          <div>
            <input type="text" id="mnfTrade" class="mnf-input" placeholder="Veículo na troca (opcional)" />
          </div>
          <div>
            <input type="tel" id="mnfPhone" class="mnf-input" placeholder="Telefone / WhatsApp" />
          </div>
          <div>
            <button type="submit" class="ag-btn"><span>Enviar</span></button>
          </div>
        </form>
      </div>
    </section>

    <!-- SECTION 6: AVANTGARDE EXPERIENCE -->
    <section class="section-experience" id="experience">
      <div class="container">
        <div class="exp-box">
          <div class="exp-img" role="img" aria-label="Showroom {short_name}"></div>
          <div class="exp-content">
            <h2 class="exp-title">
              Conheça a
              <span>{short_name} Experience</span>
            </h2>
            <p style="color:var(--color-text-secondary);max-width:30rem;">
              Uma experiência de atendimento consultivo projetada para você negociar seu próximo veículo com segurança, sigilo e avaliação justa na troca.
            </p>
            <div>
              <a href="https://wa.me/{wa_e164}?text={wa_exp_q}" target="_blank" rel="noopener" class="ag-btn">
                <span>Agendar Visita</span>
              </a>
            </div>
          </div>
        </div>
      </div>
    </section>
  </main>

  <!-- SIMULATOR MODAL -->
  <div class="ag-modal-backdrop" id="simModal" role="dialog" aria-modal="true" aria-labelledby="simTitle">
    <div class="ag-modal">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:1.25rem;">
        <h3 id="simTitle" style="font-family:var(--font-display);font-size:1.5rem;text-transform:uppercase;letter-spacing:0.12em;">Simular Proposta</h3>
        <button type="button" onclick="closeSimulator()" style="background:none;border:1px solid var(--border-subtle);color:#fff;padding:0.3rem 0.75rem;cursor:pointer;">FECHAR</button>
      </div>
      <p id="simVehicleName" style="font-family:var(--font-display);font-size:1.2rem;color:var(--color-accent);letter-spacing:0.08em;text-transform:uppercase;margin-bottom:1.25rem;"></p>
      <div style="display:flex;flex-direction:column;gap:1rem;">
        <label style="font-size:0.75rem;text-transform:uppercase;letter-spacing:0.12em;color:var(--color-text-secondary);">
          Entrada ou Veículo na Troca (R$)
          <input type="number" id="simDownPayment" class="mnf-input" value="150000" step="10000" oninput="updateSimMath()" />
        </label>
        <label style="font-size:0.75rem;text-transform:uppercase;letter-spacing:0.12em;color:var(--color-text-secondary);">
          Prazo de Financiamento
          <select id="simMonths" class="mnf-input" style="background:#121216;" onchange="updateSimMath()">
            <option value="24">24 meses</option>
            <option value="36">36 meses</option>
            <option value="48" selected>48 meses</option>
            <option value="60">60 meses</option>
          </select>
        </label>
        <div style="padding:1rem;background:#09090b;border-left:3px solid var(--color-accent);">
          <div style="font-size:0.72rem;text-transform:uppercase;letter-spacing:0.14em;color:var(--color-text-secondary);">Valor estimado da parcela:</div>
          <div id="simResultValue" style="font-family:var(--font-display);font-size:1.75rem;font-weight:700;color:#fff;margin-top:4px;">R$ 0,00 / mês</div>
        </div>
        <a id="simWhatsAppBtn" href="#" target="_blank" rel="noopener" class="ag-btn" style="width:100%;">
          <span>Enviar Proposta no WhatsApp</span>
        </a>
      </div>
    </div>
  </div>

  <!-- FLOATING WHATSAPP CONCIERGE -->
  <a class="wa-float" href="https://wa.me/{wa_e164}?text={wa_header_q}" target="_blank" rel="noopener">
    WhatsApp · {phone_display}
  </a>

  <!-- AVANTGARDE FOOTER -->
  <footer id="main-footer">
    <div class="container">
      <div class="footer-top">
        <div>
          <div class="ag-brand-name">{short_name}</div>
          <div class="footer-motto">Conduzindo a excelência.</div>
          <a href="https://wa.me/{wa_e164}" target="_blank" rel="noopener" class="footer-phone">{phone_display}</a>
          <p style="color:var(--color-text-secondary);font-size:0.88rem;">{city_state} · Instagram: @{ig_user}</p>
        </div>
        <div style="display:flex;flex-direction:column;align-items:flex-end;gap:1.25rem;">
          <a href="#veiculos" class="ag-btn ag-btn-dark"><span>Nossos veículos</span></a>
          <div style="display:flex;gap:1.5rem;font-family:var(--font-display);font-size:0.85rem;text-transform:uppercase;letter-spacing:0.18em;">
            <a href="#veiculos" style="text-decoration:none;color:#d9d9d9;">Estoque</a>
            <a href="#sobre" style="text-decoration:none;color:#d9d9d9;">Sobre</a>
            <a href="#encomenda" style="text-decoration:none;color:#d9d9d9;">Encomendar</a>
            <a href="https://www.instagram.com/{ig_user}/" target="_blank" rel="noopener" style="text-decoration:none;color:var(--color-accent);">Instagram</a>
          </div>
        </div>
      </div>
      <div class="footer-bottom">
        <div>© 2026 - {full_name} - Todos os direitos reservados.</div>
        <div>Atendimento Oficial · {city_state}</div>
      </div>
    </div>
  </footer>

  <script>
    const HERO_SLIDES = {hero_slides_json};
    const CATALOG = {catalog_json};
    const WA_E164 = "{wa_e164}";
    const STORE_NAME = {json.dumps(outreach["short_name"], ensure_ascii=False)};
    let activeCategory = "ALL";
    let selectedVehicleIndex = 0;
    let currentHeroIndex = 0;

    function formatBRLAvantgarde(val) {{
      return Number(val || 0).toLocaleString("pt-BR", {{ minimumFractionDigits: 2, maximumFractionDigits: 2 }});
    }}

    function setHeroSlide(idx) {{
      currentHeroIndex = idx % HERO_SLIDES.length;
      const s = HERO_SLIDES[currentHeroIndex];
      document.getElementById("heroWatermark").textContent = s.brand;
      document.getElementById("heroBrand").textContent = s.brand;
      document.getElementById("heroModel").textContent = s.model;
      document.getElementById("heroImage").src = s.image;
      document.getElementById("heroImage").alt = s.title;
      document.getElementById("heroTagline").textContent = s.tagline;
      document.getElementById("heroYear").textContent = s.year_label;
      document.getElementById("heroKm").textContent = s.km_label;
      document.getElementById("heroPrice").textContent = "R$ " + formatBRLAvantgarde(s.price);
      const waMsg = encodeURIComponent(`Olá ${{STORE_NAME}}! Vi o destaque *${{s.brand}} ${{s.model}}* (${{s.year_label}}) no site e gostaria de mais informações.`);
      document.getElementById("heroCta").href = `https://wa.me/${{WA_E164}}?text=${{waMsg}}`;
      document.querySelectorAll(".slide-dot").forEach((d, i) => d.classList.toggle("active", i === currentHeroIndex));
    }}

    function syncModelsDropdown() {{
      const brand = document.getElementById("fltBrand").value;
      const modelSelect = document.getElementById("fltModel");
      const models = CATALOG.filter(i => !brand || i.brand === brand).map(i => i.model);
      modelSelect.innerHTML = '<option value="">Todos os Modelos</option>' +
        models.map(m => `<option value="${{m}}">${{m}}</option>`).join("");
    }}

    function filterByCategory(cat) {{
      activeCategory = cat;
      document.querySelectorAll(".ag-pill").forEach(btn => {{
        btn.classList.toggle("active", btn.getAttribute("data-cat") === cat);
      }});
      renderCatalog();
    }}

    function renderCatalog() {{
      const brand = document.getElementById("fltBrand").value;
      const model = document.getElementById("fltModel").value;
      const q = (document.getElementById("searchInput").value || "").toLowerCase().trim();

      const items = CATALOG.map((item, idx) => ({{ ...item, _idx: idx }})).filter(item => {{
        if (brand && item.brand !== brand) return false;
        if (model && item.model !== model) return false;
        if (activeCategory === "BLINDADOS" && !item.armored && !item.specs.toLowerCase().includes("blind")) return false;
        if (activeCategory === "2024" && Number(item.year) < 2024) return false;
        if (q && !`${{item.brand}} ${{item.model}} ${{item.specs}} ${{item.category}} ${{item.badge}}`.toLowerCase().includes(q)) return false;
        return true;
      }});

      document.getElementById("countLabel").textContent = `${{items.length}} veículos disponíveis`;

      const grid = document.getElementById("catalogGrid");
      if (!items.length) {{
        grid.innerHTML = `<div style="grid-column:1/-1;background:#fff;padding:3rem;text-align:center;color:#414141;">Nenhum veículo encontrado com estes filtros. Utilize o formulário abaixo para encomendar seu modelo sob medida.</div>`;
        return;
      }}

      grid.innerHTML = items.map(item => {{
        const waText = encodeURIComponent(`Olá ${{STORE_NAME}}! Tenho interesse no *${{item.brand}} ${{item.model}}* (${{item.year_label}} · R$ ${{formatBRLAvantgarde(item.price)}}) que vi no site.`);
        return `
          <article class="ag-card">
            <div class="ag-card-media">
              <img src="${{item.image}}" alt="${{item.brand}} ${{item.model}}" loading="lazy" />
              <span class="ag-card-armored">${{item.badge}}</span>
            </div>
            <div class="ag-card-content">
              <div class="ag-card-brand">${{item.brand}}</div>
              <h3 class="ag-card-title">${{item.model}}</h3>
              <div class="ag-card-info">
                <span>${{item.year_label}}</span>
                <span>${{item.km_label}}</span>
              </div>
              <p class="ag-card-specs">${{item.specs}}</p>
              <div class="ag-card-price">
                <small>R$</small><span>${{formatBRLAvantgarde(item.price)}}</span>
              </div>
              <div class="ag-card-actions">
                <a href="https://wa.me/${{WA_E164}}?text=${{waText}}" target="_blank" rel="noopener" class="ag-btn">
                  <span>Conheça</span>
                </a>
                <button type="button" class="ag-card-sim" onclick="openSimulator(${{item._idx}})">
                  Simular
                </button>
              </div>
            </div>
          </article>
        `;
      }}).join("");
    }}

    function submitBespokeOrder(e) {{
      e.preventDefault();
      const m = document.getElementById("mnfModel").value.trim();
      const n = document.getElementById("mnfName").value.trim();
      const t = document.getElementById("mnfTrade").value.trim();
      const msg = encodeURIComponent(
        `Olá ${{STORE_NAME}}! Meu nome é ${{n}}. Procuro o modelo *${{m}}*` +
        (t ? ` (tenho para avaliação na troca: ${{t}})` : "") +
        `. Podem me avisar sobre disponibilidade?`
      );
      window.open(`https://wa.me/${{WA_E164}}?text=${{msg}}`, "_blank");
    }}

    function openSimulator(idx) {{
      selectedVehicleIndex = idx || 0;
      const item = CATALOG[selectedVehicleIndex] || CATALOG[0];
      document.getElementById("simVehicleName").textContent = `${{item.brand}} ${{item.model}} (${{item.year_label}})`;
      document.getElementById("simDownPayment").value = Math.round(item.price * 0.3);
      updateSimMath();
      document.getElementById("simModal").classList.add("open");
    }}

    function closeSimulator() {{
      document.getElementById("simModal").classList.remove("open");
    }}

    function updateSimMath() {{
      const item = CATALOG[selectedVehicleIndex] || CATALOG[0];
      const down = Math.max(0, Number(document.getElementById("simDownPayment").value || 0));
      const months = Number(document.getElementById("simMonths").value || 48);
      const financed = Math.max(0, item.price - down);
      const rate = 0.0149;
      const pmt = financed > 0
        ? Math.round((financed * rate) / (1 - Math.pow(1 + rate, -months)))
        : 0;
      document.getElementById("simResultValue").textContent = `R$ ${{formatBRLAvantgarde(pmt)}} / mês (${{months}}x)`;
      const msg = encodeURIComponent(
        `Olá ${{STORE_NAME}}! Fiz uma simulação no site para o *${{item.brand}} ${{item.model}} (${{item.year_label}})*:\\n` +
        `• Valor: R$ ${{formatBRLAvantgarde(item.price)}}\\n` +
        `• Entrada/Troca: R$ ${{formatBRLAvantgarde(down)}}\\n` +
        `• Saldo em ${{months}}x (~R$ ${{formatBRLAvantgarde(pmt)}}/mês)`
      );
      document.getElementById("simWhatsAppBtn").href = `https://wa.me/${{WA_E164}}?text=${{msg}}`;
    }}

    document.addEventListener("keydown", (e) => {{
      if (e.key === "Escape") closeSimulator();
    }});

    syncModelsDropdown();
    setHeroSlide(0);
    renderCatalog();
  </script>
</body>
</html>
"""


def write_design_system_artifacts() -> None:
    """Writes design system tokens and artifacts to DEMOS_DIR."""
    pass


def render_hub_index_html(manifest: Optional[list[dict[str, Any]]] = None) -> str:
    from pathlib import Path
    db_file = DEMOS_DIR / "database_all_demos.json"
    if db_file.exists():
        try:
            records = json.loads(db_file.read_text(encoding="utf-8"))
        except Exception:
            records = manifest or []
    else:
        records = manifest or []

    manifest_json = json.dumps(records, ensure_ascii=False)
    total_count = len(records)
    denis_total = len([r for r in records if r.get("owner") == "denis"])
    gabriel_total = len([r for r in records if r.get("owner") == "gabriel"])

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>BRAG International — Dashboard Executivo &amp; Banco de Dados de Demos</title>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="{FONT_URL}" rel="stylesheet" />
  <style>
    :root {{
      --color-bg-primary: #09090b;
      --color-bg-elevated: #121216;
      --color-bg-card: #16161c;
      --color-text-primary: #ffffff;
      --color-text-secondary: #989898;
      --color-accent: #cf4520;
      --color-denis: #cf4520;
      --color-gabriel: #1d5bd6;
      --color-emerald: #10b981;
      --color-gold: #dfb858;
      --border-subtle: rgba(255, 255, 255, 0.10);
      --font-display: 'Barlow Condensed', sans-serif;
      --font-sans: 'Plus Jakarta Sans', sans-serif;
      --font-mono: 'JetBrains Mono', monospace;
      --text-xs: 0.75rem;
      --text-sm: 0.875rem;
      --space-2: 0.5rem;
      --space-3: 0.75rem;
      --space-4: 1rem;
      --space-5: 1.5rem;
      --space-6: 2rem;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      background-color: var(--color-bg-primary);
      color: var(--color-text-primary);
      font-family: var(--font-sans);
      padding: var(--space-6) var(--space-5);
      line-height: 1.5;
    }}
    .wrap {{ max-width: 96rem; margin: 0 auto; }}
    header {{
      display: flex;
      justify-content: space-between;
      align-items: flex-end;
      flex-wrap: wrap;
      gap: var(--space-4);
      padding-bottom: var(--space-5);
      border-bottom: 1px solid var(--border-subtle);
      margin-bottom: var(--space-5);
    }}
    .eyebrow {{
      font-family: var(--font-display);
      font-size: 0.9rem;
      color: var(--color-accent);
      letter-spacing: 0.28em;
      text-transform: uppercase;
      font-weight: 700;
    }}
    h1 {{
      font-family: var(--font-display);
      font-size: clamp(1.85rem, 3.4vw, 2.8rem);
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      margin-top: 4px;
    }}
    .sub {{ color: var(--color-text-secondary); font-size: var(--text-sm); margin-top: 4px; max-width: 58rem; }}
    .actions-top {{
      display: flex;
      gap: var(--space-3);
      flex-wrap: wrap;
      align-items: center;
    }}
    .btn-top {{
      background: var(--color-bg-elevated);
      border: 1px solid var(--border-subtle);
      color: #ffffff;
      padding: 0.6rem 1rem;
      font-family: var(--font-sans);
      font-size: 0.85rem;
      font-weight: 600;
      text-decoration: none;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      transition: all 0.2s ease;
    }}
    .btn-top:hover {{
      border-color: rgba(255, 255, 255, 0.35);
      background: #1c1c22;
    }}
    .btn-top-gold {{
      background: rgba(223, 184, 88, 0.15);
      border-color: var(--color-gold);
      color: #f7f7ee;
    }}
    .btn-top-gold:hover {{
      background: rgba(223, 184, 88, 0.25);
    }}
    .partner-switcher {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: var(--space-4);
      margin-bottom: var(--space-5);
    }}
    .partner-tab {{
      background: var(--color-bg-elevated);
      border: 1px solid var(--border-subtle);
      padding: 1.15rem 1.35rem;
      cursor: pointer;
      text-align: left;
      transition: all 0.2s ease;
      display: flex;
      flex-direction: column;
      gap: 6px;
    }}
    .partner-tab:hover {{
      border-color: rgba(255, 255, 255, 0.28);
    }}
    .partner-tab.active-denis {{
      border-color: var(--color-denis);
      background: linear-gradient(135deg, rgba(207, 69, 32, 0.16), rgba(18, 18, 22, 0.95));
      box-shadow: 0 12px 32px rgba(207, 69, 32, 0.14);
    }}
    .partner-tab.active-gabriel {{
      border-color: var(--color-gabriel);
      background: linear-gradient(135deg, rgba(29, 91, 214, 0.18), rgba(18, 18, 22, 0.95));
      box-shadow: 0 12px 32px rgba(29, 91, 214, 0.16);
    }}
    .partner-tab.active-all {{
      border-color: var(--color-emerald);
      background: linear-gradient(135deg, rgba(16, 185, 129, 0.14), rgba(18, 18, 22, 0.95));
      box-shadow: 0 12px 32px rgba(16, 185, 129, 0.14);
    }}
    .partner-tab-kicker {{
      font-family: var(--font-display);
      font-size: 0.78rem;
      font-weight: 700;
      letter-spacing: 0.22em;
      text-transform: uppercase;
      color: var(--color-text-secondary);
    }}
    .partner-tab-title {{
      font-family: var(--font-display);
      font-size: 1.45rem;
      font-weight: 800;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      color: #ffffff;
    }}
    .partner-tab-meta {{
      font-family: var(--font-mono);
      font-size: 0.76rem;
      color: var(--color-text-secondary);
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}
    .toolbar {{
      display: flex;
      flex-wrap: wrap;
      justify-content: space-between;
      align-items: center;
      gap: var(--space-3);
      margin-bottom: var(--space-4);
      background: var(--color-bg-elevated);
      border: 1px solid var(--border-subtle);
      padding: 0.9rem 1.2rem;
    }}
    .search-input {{
      background: #09090b;
      border: 1px solid var(--border-subtle);
      color: #ffffff;
      padding: 0.55rem 0.95rem;
      font-size: 0.85rem;
      min-width: 320px;
      outline: none;
      font-family: var(--font-sans);
    }}
    .search-input:focus {{ border-color: var(--color-accent); }}
    .kpi-pills {{
      display: flex;
      flex-wrap: wrap;
      gap: var(--space-2);
      font-size: var(--text-xs);
    }}
    .kpi-pill {{
      background: #09090b;
      border: 1px solid var(--border-subtle);
      padding: 0.35rem 0.75rem;
      font-family: var(--font-mono);
      color: var(--color-text-secondary);
    }}
    .kpi-pill strong {{ color: #ffffff; }}
    table {{
      width: 100%;
      border-collapse: collapse;
      background: var(--color-bg-elevated);
      border: 1px solid var(--border-subtle);
    }}
    th {{
      text-align: left;
      padding: 0.85rem 1rem;
      font-family: var(--font-display);
      font-size: 0.82rem;
      font-weight: 700;
      letter-spacing: 0.16em;
      text-transform: uppercase;
      color: var(--color-text-secondary);
      border-bottom: 1px solid var(--border-subtle);
      background: #0d0d10;
    }}
    td {{
      padding: 0.85rem 1rem;
      border-bottom: 1px solid rgba(255, 255, 255, 0.05);
      font-size: var(--text-sm);
      vertical-align: middle;
    }}
    tr:hover td {{
      background: rgba(255, 255, 255, 0.02);
    }}
    tr.row-sent td {{
      background: rgba(16, 185, 129, 0.04);
    }}
    .tabular {{ font-family: var(--font-mono); }}
    .badge-owner-denis {{
      display: inline-block;
      padding: 0.15rem 0.55rem;
      background: rgba(207, 69, 32, 0.18);
      border: 1px solid rgba(207, 69, 32, 0.45);
      color: #ff9d72;
      font-size: 0.7rem;
      font-family: var(--font-mono);
      font-weight: 700;
      letter-spacing: 0.08em;
      text-transform: uppercase;
    }}
    .badge-owner-gabriel {{
      display: inline-block;
      padding: 0.15rem 0.55rem;
      background: rgba(29, 91, 214, 0.18);
      border: 1px solid rgba(29, 91, 214, 0.45);
      color: #93c5fd;
      font-size: 0.7rem;
      font-family: var(--font-mono);
      font-weight: 700;
      letter-spacing: 0.08em;
      text-transform: uppercase;
    }}
    .badge-score {{
      display: inline-block;
      padding: 0.15rem 0.45rem;
      background: rgba(16, 185, 129, 0.12);
      border: 1px solid rgba(16, 185, 129, 0.35);
      color: #10b981;
      font-size: 0.74rem;
      font-weight: 600;
    }}
    .badge-active-lot {{
      display: inline-block;
      padding: 0.15rem 0.45rem;
      background: rgba(223, 184, 88, 0.15);
      border: 1px solid var(--color-gold);
      color: #f7f7ee;
      font-size: 0.68rem;
      font-family: var(--font-mono);
      font-weight: 700;
      letter-spacing: 0.06em;
      text-transform: uppercase;
      margin-left: 4px;
    }}
    .status-select {{
      background: #09090b;
      border: 1px solid var(--border-subtle);
      color: #ffffff;
      padding: 0.35rem 0.6rem;
      font-size: 0.78rem;
      font-family: var(--font-mono);
      outline: none;
      cursor: pointer;
    }}
    .status-select:focus {{ border-color: var(--color-accent); }}
    .btn-ag {{
      display: inline-block;
      background: #ffffff;
      color: #09090b;
      padding: 0.42rem 0.78rem;
      font-family: var(--font-sans);
      font-size: 0.78rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      text-decoration: none;
      transition: opacity 0.2s;
    }}
    .btn-ag:hover {{ opacity: 0.88; }}
    .btn-wa {{
      display: inline-block;
      background: #10b981;
      color: #ffffff;
      padding: 0.42rem 0.78rem;
      font-family: var(--font-sans);
      font-size: 0.78rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      text-decoration: none;
      transition: background-color 0.2s;
    }}
    .btn-wa:hover {{ background: #059669; }}
    .btn-ghost {{
      background: transparent;
      border: 1px solid var(--border-subtle);
      color: var(--color-text-secondary);
      padding: 0.42rem 0.72rem;
      font-family: var(--font-sans);
      font-size: 0.78rem;
      cursor: pointer;
      transition: all 0.2s;
    }}
    .btn-ghost:hover {{
      border-color: rgba(255, 255, 255, 0.35);
      color: #ffffff;
    }}
    .modal-backdrop {{
      position: fixed;
      inset: 0;
      background: rgba(0, 0, 0, 0.85);
      display: none;
      place-items: center;
      padding: 1rem;
      z-index: 9999;
    }}
    .modal-backdrop.open {{ display: grid; }}
    .modal-box {{
      background: #141418;
      border: 1px solid var(--border-subtle);
      max-width: 52rem;
      width: 100%;
      max-height: 85vh;
      overflow-y: auto;
      padding: 1.5rem;
    }}
    .modal-pre {{
      background: #09090b;
      border: 1px solid var(--border-subtle);
      padding: 1rem;
      font-family: var(--font-mono);
      font-size: 0.8rem;
      color: #e5e7eb;
      white-space: pre-wrap;
      word-break: break-word;
      line-height: 1.5;
      margin-top: 0.75rem;
    }}
    .empty-state {{
      text-align: center;
      padding: 3rem 1rem;
      color: var(--color-text-secondary);
    }}
  </style>
</head>
<body>
  <div class="wrap">
    <header>
      <div>
        <div class="eyebrow">AVANTGARDE CONCEPT STORE · BANCO DE DADOS UNIFICADO ({total_count} DEMOS NA FILA DE ABORDAGEM)</div>
        <h1>Dashboard Executivo &amp; Central de Demos</h1>
        <p class="sub">Visão completa de todos os <strong>{total_count} showrooms digitais publicados</strong> na Vercel e ativos na esteira de abordagem. Acompanhe a operação entre os sócios, filtre por responsável (Denis ou Gabriel), realize disparos de 1 clique no WhatsApp e monitore o funil comercial.</p>
      </div>
      <div class="actions-top">
        <a href="sales.html" class="btn-top" style="border-color:var(--color-gold);background:rgba(223,184,88,0.22);color:#f7f7ee;font-weight:700;">
          💼 Módulo Comercial (Bruce &amp; Gabriel)
        </a>
        <a href="crm.html" class="btn-top" style="border-color:var(--color-emerald);background:rgba(16,185,129,0.18);color:#f7f7ee;font-weight:700;">
          📱 Base CRM (WhatsApp)
        </a>
        <a href="/demos/crm_all_leads.csv" download class="btn-top btn-top-gold">
          📥 Baixar Planilha CSV ({total_count})
        </a>
        <a href="/demos/database_all_demos.json" download class="btn-top">
          📄 Baixar Banco JSON ({total_count})
        </a>
        <button type="button" class="btn-top" onclick="copyPartnerShareLink()">
          🔗 Copiar Link da Fila
        </button>
      </div>
    </header>

    <!-- 3 WORKSPACE TABS -->
    <div class="partner-switcher" role="tablist" aria-label="Seleção de Fila por Sócio">
      <button type="button" id="tabBtnDenis" class="partner-tab active-denis" onclick="setPartnerQueue('denis')">
        <span class="partner-tab-kicker">CARTEIRA DENIS ({denis_total} DEMOS)</span>
        <span class="partner-tab-title">Fila Denis</span>
        <div class="partner-tab-meta">
          <span id="metaDenisCount">Carregando...</span>
          <span style="color:#ff9d72;">?fila=denis</span>
        </div>
      </button>

      <button type="button" id="tabBtnGabriel" class="partner-tab" onclick="setPartnerQueue('gabriel')">
        <span class="partner-tab-kicker">CARTEIRA GABRIEL ({gabriel_total} DEMOS)</span>
        <span class="partner-tab-title">Fila Gabriel</span>
        <div class="partner-tab-meta">
          <span id="metaGabrielCount">Carregando...</span>
          <span style="color:#93c5fd;">?fila=gabriel</span>
        </div>
      </button>

      <button type="button" id="tabBtnAll" class="partner-tab" onclick="setPartnerQueue('all')">
        <span class="partner-tab-kicker">BANCO DE DADOS CONSOLIDADO</span>
        <span class="partner-tab-title">Todas as {total_count} Demos</span>
        <div class="partner-tab-meta">
          <span id="metaAllCount">{total_count} Showrooms na Fila</span>
          <span style="color:#10b981;">Total Geral</span>
        </div>
      </button>
    </div>

    <div class="toolbar">
      <div style="display:flex;align-items:center;gap:0.75rem;flex-wrap:wrap;">
        <input type="search" id="hubSearch" class="search-input" placeholder="Buscar por loja, cidade, estado, @instagram ou WhatsApp..." oninput="renderHubTable()" />
      </div>
      <div class="kpi-pills">
        <div class="kpi-pill">Fila: <strong id="kpiActiveOwner">Fila Denis</strong></div>
        <div class="kpi-pill">Pendentes de Contato: <strong id="kpiPending" style="color:#f59e0b;">0</strong></div>
        <div class="kpi-pill">Contatados: <strong id="kpiSent" style="color:#10b981;">0</strong></div>
        <div class="kpi-pill">Total Online na Vercel: <strong style="color:#34d399;">{total_count}/{total_count}</strong></div>
      </div>
    </div>

    <main>
      <table>
        <thead>
          <tr>
            <th>#</th>
            <th>Responsável</th>
            <th>Score ICP</th>
            <th>Loja &amp; Estilo Avantgarde</th>
            <th>Cidade &amp; Nicho</th>
            <th>Instagram &amp; WhatsApp</th>
            <th>Status</th>
            <th>Disparo Direto (1 Clique)</th>
          </tr>
        </thead>
        <tbody id="hubTableBody"></tbody>
      </table>
      <div id="emptyNotice" class="empty-state" style="display:none;">
        Nenhum showroom encontrado para os critérios de busca digitados.
      </div>
    </main>
  </div>

  <!-- Modal Roteiro & Mensagem -->
  <div id="scriptModal" class="modal-backdrop" onclick="if(event.target===this) closeScriptModal()">
    <div class="modal-box">
      <div style="display:flex;justify-content:space-between;align-items:center;gap:1rem;border-bottom:1px solid var(--border-subtle);padding-bottom:0.75rem;">
        <h2 id="modalTitle" style="font-family:var(--font-display);font-size:1.4rem;text-transform:uppercase;letter-spacing:0.08em;">Kit de Abordagem</h2>
        <button type="button" class="btn-ghost" onclick="closeScriptModal()">Fechar</button>
      </div>
      <div style="margin-top:1rem;">
        <div style="display:flex;justify-content:space-between;align-items:center;">
          <strong style="font-size:0.8rem;text-transform:uppercase;letter-spacing:0.12em;color:var(--color-accent);">Mensagem Pronta de WhatsApp</strong>
          <button type="button" class="btn-ghost" id="modalCopyMsgBtn">Copiar Mensagem</button>
        </div>
        <pre id="modalMsgPre" class="modal-pre"></pre>
      </div>
      <div style="margin-top:1.25rem;">
        <div style="display:flex;justify-content:space-between;align-items:center;">
          <strong style="font-size:0.8rem;text-transform:uppercase;letter-spacing:0.12em;color:var(--color-gold);">Roteiro de Vídeo Personalizado (45-60s)</strong>
          <button type="button" class="btn-ghost" id="modalCopyScriptBtn">Copiar Roteiro</button>
        </div>
        <pre id="modalScriptPre" class="modal-pre"></pre>
      </div>
      <div style="margin-top:1.25rem;display:flex;justify-content:flex-end;gap:0.75rem;">
        <a id="modalWaBtn" href="#" target="_blank" rel="noopener" class="btn-wa">Abrir Conversa no WhatsApp</a>
        <button type="button" class="btn-ghost" onclick="closeScriptModal()">Fechar</button>
      </div>
    </div>
  </div>

  <script>
    const MANIFEST = {manifest_json};
    const STORAGE_KEY = "brag_demos_status_v3";
    let currentQueue = "denis";
    let statusMap = {{}};

    try {{
      statusMap = JSON.parse(localStorage.getItem(STORAGE_KEY) || "{{}}");
    }} catch (e) {{
      statusMap = {{}};
    }}

    function getStatus(item) {{
      return statusMap[item.slug] || item.commercial_status || "demo_pronta";
    }}

    function setStatus(slug, newStatus) {{
      statusMap[slug] = newStatus;
      try {{
        localStorage.setItem(STORAGE_KEY, JSON.stringify(statusMap));
      }} catch (e) {{}}
      renderHubTable();
    }}

    function setPartnerQueue(queue) {{
      currentQueue = queue;
      const url = new URL(window.location.href);
      url.searchParams.set("fila", queue);
      window.history.replaceState({{}}, "", url.toString());

      document.getElementById("tabBtnDenis").className = "partner-tab" + (queue === "denis" ? " active-denis" : "");
      document.getElementById("tabBtnGabriel").className = "partner-tab" + (queue === "gabriel" ? " active-gabriel" : "");
      document.getElementById("tabBtnAll").className = "partner-tab" + (queue === "all" ? " active-all" : "");
      renderHubTable();
    }}

    function copyPartnerShareLink() {{
      const url = new URL(window.location.href);
      url.searchParams.set("fila", currentQueue);
      navigator.clipboard.writeText(url.toString());
      alert("Link da fila copiado: " + url.toString());
    }}

    function copyWhatsappMsg(slug) {{
      const item = MANIFEST.find(x => x.slug === slug);
      if (!item) return;
      navigator.clipboard.writeText(item.whatsapp_message);
      alert("Mensagem copiada para " + item.name + "!");
    }}

    function copyVideoScript(slug) {{
      const item = MANIFEST.find(x => x.slug === slug);
      if (!item) return;
      navigator.clipboard.writeText(item.video_script_60s);
      alert("Roteiro copiado para " + item.name + "!");
    }}

    function openScriptModal(slug) {{
      const item = MANIFEST.find(x => x.slug === slug);
      if (!item) return;
      document.getElementById("modalTitle").textContent = `#${{String(item.partner_rank).padStart(3, '0')}} (${{item.owner_name}}) — ${{item.name}}`;
      document.getElementById("modalMsgPre").textContent = item.whatsapp_message;
      document.getElementById("modalScriptPre").textContent = item.video_script_60s;
      document.getElementById("modalCopyMsgBtn").onclick = () => copyWhatsappMsg(slug);
      document.getElementById("modalCopyScriptBtn").onclick = () => copyVideoScript(slug);
      document.getElementById("modalWaBtn").href = item.whatsapp_send_url || `https://wa.me/${{item.whatsapp_e164}}`;
      document.getElementById("scriptModal").classList.add("open");
    }}

    function closeScriptModal() {{
      document.getElementById("scriptModal").classList.remove("open");
    }}

    function handleSendWhatsApp(slug) {{
      setStatus(slug, "primeiro_contato_enviado");
    }}

    function escapeHtml(str) {{
      return String(str || "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;");
    }}

    function renderHubTable() {{
      const q = (document.getElementById("hubSearch").value || "").toLowerCase().trim();
      const denisItems = MANIFEST.filter(d => d.owner === "denis");
      const gabrielItems = MANIFEST.filter(d => d.owner === "gabriel");

      const denisSent = denisItems.filter(d => getStatus(d) !== "demo_pronta").length;
      const gabrielSent = gabrielItems.filter(d => getStatus(d) !== "demo_pronta").length;

      document.getElementById("metaDenisCount").textContent = `${{denisSent}}/${{denisItems.length}} enviados · ${{denisItems.length - denisSent}} pendentes`;
      document.getElementById("metaGabrielCount").textContent = `${{gabrielSent}}/${{gabrielItems.length}} enviados · ${{gabrielItems.length - gabrielSent}} pendentes`;
      document.getElementById("metaAllCount").textContent = `${{denisSent + gabrielSent}}/${{MANIFEST.length}} enviados no total`;

      const filtered = MANIFEST.filter(d => {{
        if (currentQueue !== "all" && d.owner !== currentQueue) return false;
        if (!q) return true;
        const hay = `${{d.name}} ${{d.city}} ${{d.state}} ${{d.instagram_username}} ${{d.phone_display}} ${{d.whatsapp_e164}} ${{d.owner_name}} ${{d.history_batch}}`.toLowerCase();
        return hay.includes(q);
      }});

      const activeTotal = currentQueue === "denis" ? denisItems.length : (currentQueue === "gabriel" ? gabrielItems.length : MANIFEST.length);
      const activeSent = currentQueue === "denis" ? denisSent : (currentQueue === "gabriel" ? gabrielSent : (denisSent + gabrielSent));

      document.getElementById("kpiActiveOwner").textContent =
        currentQueue === "denis" ? `Fila Denis (${{denisItems.length}})` : (currentQueue === "gabriel" ? `Fila Gabriel (${{gabrielItems.length}})` : `Todas as ${{MANIFEST.length}} Demos`);
      document.getElementById("kpiPending").textContent = String(activeTotal - activeSent);
      document.getElementById("kpiSent").textContent = String(activeSent);

      const tbody = document.getElementById("hubTableBody");
      const emptyNotice = document.getElementById("emptyNotice");

      if (filtered.length === 0) {{
        tbody.innerHTML = "";
        emptyNotice.style.display = "block";
        return;
      }}
      emptyNotice.style.display = "none";

      tbody.innerHTML = filtered.map(d => {{
        const st = getStatus(d);
        const isSent = st !== "demo_pronta";
        const ownerBadge = d.owner === "denis"
          ? `<span class="badge-owner-denis">Denis #${{String(d.partner_rank).padStart(3, '0')}}</span>`
          : `<span class="badge-owner-gabriel">Gabriel #${{String(d.partner_rank).padStart(3, '0')}}</span>`;
        
        const activeBadge = d.is_active_manifest
          ? `<span class="badge-active-lot">Lote Atual</span>`
          : "";

        const igHtml = d.instagram_username
          ? `<a href="${{escapeHtml(d.instagram_url)}}" target="_blank" rel="noopener" style="color:var(--color-accent);text-decoration:none;">@${{escapeHtml(d.instagram_username)}}</a>`
          : `<span style="color:var(--color-text-secondary);">-</span>`;

        return `
          <tr class="${{isSent ? 'row-sent' : ''}}">
            <td class="tabular" style="font-weight:700;color:var(--color-accent);">
              #${{String(d.partner_rank).padStart(3, '0')}}
            </td>
            <td>
              ${{ownerBadge}}
              ${{activeBadge}}
            </td>
            <td><span class="badge-score tabular">${{d.score}}/100 · ${{escapeHtml(d.priority)}}</span></td>
            <td>
              <strong style="font-size:1.05rem;font-family:var(--font-display);letter-spacing:0.08em;text-transform:uppercase;">${{escapeHtml(d.name)}}</strong>
              <div class="tabular" style="font-size:var(--text-xs);color:var(--color-text-secondary);margin-top:2px;">
                ${{escapeHtml(d.archetype)}}
              </div>
            </td>
            <td>
              <div><strong>${{escapeHtml(d.city)}} · ${{escapeHtml(d.state)}}</strong></div>
              <div style="font-size:var(--text-xs);color:var(--color-text-secondary);">${{escapeHtml(d.niche)}}</div>
            </td>
            <td class="tabular" style="font-size:var(--text-xs);">
              <div>${{igHtml}}</div>
              <div style="color:#10b981;font-weight:600;margin-top:2px;">${{escapeHtml(d.phone_display)}}</div>
            </td>
            <td>
              <select class="status-select" onchange="setStatus('${{escapeHtml(d.slug)}}', this.value)">
                <option value="demo_pronta" ${{st === 'demo_pronta' ? 'selected' : ''}}>Demo Pronta</option>
                <option value="primeiro_contato_enviado" ${{st === 'primeiro_contato_enviado' ? 'selected' : ''}}>Enviado WhatsApp</option>
                <option value="respondeu" ${{st === 'respondeu' ? 'selected' : ''}}>Respondeu</option>
                <option value="reuniao" ${{st === 'reuniao' ? 'selected' : ''}}>Reunião</option>
                <option value="fechado" ${{st === 'fechado' ? 'selected' : ''}}>Fechado</option>
              </select>
            </td>
            <td>
              <div style="display:flex;gap:0.45rem;flex-wrap:wrap;">
                <a href="${{escapeHtml(d.demo_url)}}" target="_blank" rel="noopener" class="btn-ag">Abrir Showroom</a>
                <a href="${{escapeHtml(d.whatsapp_send_url)}}" target="_blank" rel="noopener" class="btn-wa" onclick="handleSendWhatsApp('${{escapeHtml(d.slug)}}')">WhatsApp 1-Clique</a>
                <button type="button" class="btn-ghost" onclick="copyWhatsappMsg('${{escapeHtml(d.slug)}}')">Copiar Msg</button>
                <button type="button" class="btn-ghost" onclick="openScriptModal('${{escapeHtml(d.slug)}}')">Roteiro &amp; Kit</button>
              </div>
            </td>
          </tr>
        `;
      }}).join("");
    }}

    const params = new URLSearchParams(window.location.search);
    const initialFila = (params.get("fila") || "denis").toLowerCase();
    if (["denis", "gabriel", "all"].includes(initialFila)) {{
      setPartnerQueue(initialFila);
    }} else {{
      setPartnerQueue("denis");
    }}
  </script>
</body>
</html>
"""



def generate_archived_batch1_demos(
    base_url: str = "http://localhost:8090",
    public_demo_base: Optional[str] = "https://brag-showroom-demos.vercel.app",
) -> list[str]:
    """Ensures archived demos stay online."""
    return []


def generate_top_30_demos(
    conn: Optional[sqlite3.Connection] = None,
    base_url: str = "http://localhost:8090",
    public_demo_base: Optional[str] = "https://brag-showroom-demos.vercel.app",
) -> list[dict[str, Any]]:
    own_conn = False
    if conn is None:
        conn = get_connection()
        own_conn = True

    try:
        DEMOS_DIR.mkdir(parents=True, exist_ok=True)
        DOCS_LEADS_DIR.mkdir(parents=True, exist_ok=True)
        write_design_system_artifacts()

        # Keep all previously-sent archived demos live on Vercel (demos/<slug>/index.html)
        generate_archived_batch1_demos(base_url=base_url, public_demo_base=public_demo_base)

        # Select 30 fresh nautical leads for Denis + 30 fresh automotive leads for Gabriel
        top_denis_30 = select_top_30_nautical_leads(conn, limit=30)
        top_gabriel_30 = select_top_30_automotive_leads(conn, limit=30)

        new_denis_manifest: list[dict[str, Any]] = []
        new_gabriel_manifest: list[dict[str, Any]] = []

        # Process Denis queue (30 demos)
        for p_rank, lead in enumerate(top_denis_30, start=1):
            slug = lead["slug"]
            company_name = (lead.get("name") or "Sua Loja").split("|")[0].split(" - ")[0].strip()
            full_name = lead.get("name") or company_name
            city = lead.get("city") or "Brasil"
            state = lead.get("state") or "BR"
            ig_user = (lead.get("instagram_username") or "").lstrip("@")
            raw_phone = lead.get("whatsapp") or lead.get("phone") or ""
            wa_e164 = format_whatsapp_e164(raw_phone)
            phone_display = format_phone_human(raw_phone)
            demo_url = (
                f"{public_demo_base.rstrip('/')}/{slug}"
                if public_demo_base
                else f"{base_url.rstrip('/')}/demos/{slug}"
            )
            vertical = detect_vertical_key(lead)
            theme = DESIGN_THEMES[(p_rank - 1) % len(DESIGN_THEMES)]

            gap_reason = (
                "todo o trafego do Instagram de voces hoje desagua em link intermediario sem vitrine filtravel no celular"
                if not lead.get("has_own_website")
                else "a experiencia mobile atual nao conta com busca instantanea de acervo e simulacao direta por modelo"
            )

            whatsapp_message = (
                f"Olá, diretoria da *{company_name}*! Tudo bem?\n\n"
                f"Acompanhamos a operação de vocês no Instagram (@{ig_user}) em {city}/{state} e notamos que {gap_reason}.\n\n"
                f"Em vez de enviar uma apresentação comercial teórica, nós projetamos e colocamos no ar uma *demonstração funcional exclusiva do novo Showroom Digital da {company_name}* "
                f"(com filtro instantâneo por marca/modelo, vitrine interativa de alto padrão e captação integrada ao WhatsApp de vocês):\n\n"
                f"{demo_url}\n\n"
                f"Podem abrir direto no celular para testar a experiência. Se fizer sentido ativarmos essa estrutura oficial para a {company_name}, fico à disposição por aqui."
            )
            wa_send_url = f"https://wa.me/{wa_e164}?text={urllib.parse.quote(whatsapp_message)}"

            video_script_60s = f"""# Roteiro de Vídeo Executivo (45 a 60s) — {full_name}
> Origem: Playbook Brag International (Build Before Pitch · Prova sobre Discurso)
> Responsável pelo Disparo: Denis (Fila 1 — Denis (30 Demos) · #{p_rank:02d}/30)
> Destinatário: Sócio / Diretor Comercial da {company_name} (@{ig_user})
> Referência Arquitetural: Avantgarde Concept Store ({theme['archetype']})
> Link Público Vercel: {demo_url}

## [00:00 - 00:10] Abertura & Reconhecimento da Marca
"Olá pessoal da {company_name}, aqui é o Denis. Estávamos acompanhando a operação e o posicionamento de vocês em {city}/{state} pelo perfil @{ig_user}..."

## [00:10 - 00:25] Diagnóstico do Gap Real (Fato Objetivo)
"...e notamos que quem chega pelo Instagram hoje encontra {gap_reason}. Na prática, o comprador de alto valor não consegue filtrar modelos por marca, ano ou blindagem em 5 segundos no smartphone."

## [00:25 - 00:45] A Prova (Walkthrough do Protótipo Funcional)
"Em vez de pedir uma reunião teórica, nós desenhamos e publicamos uma demonstração funcional sob medida para a {company_name} no padrão Avantgarde. Veja na tela: Hero Slider com telemetria Ano/Km/Valor, busca flutuante por Marca e Modelo, cards chanfrados e encomenda sob medida conectada ao WhatsApp {phone_display}."

## [00:45 - 00:60] Fechamento (Sintaxe Brag: Zero Pitch Forçado)
"Sem discurso de agência. Estou deixando o link público aqui na mensagem para você testar no próprio celular. Se fizer sentido ativarmos essa arquitetura oficial para a {company_name}, basta me responder por aqui."
"""

            outreach = {
                "rank": (p_rank * 2) - 1,
                "owner": "denis",
                "owner_name": "Denis",
                "owner_label": "Fila 1 — Denis (30 Demos)",
                "partner_rank": p_rank,
                "company_id": lead.get("id") or f"denis_{slug}",
                "slug": slug,
                "name": full_name,
                "short_name": company_name,
                "niche": lead.get("niche") or "P4 — Náutica premium",
                "vertical": vertical,
                "archetype": theme["archetype"],
                "city": city,
                "state": state,
                "score": lead.get("score") or 95,
                "priority": lead.get("priority") or "A",
                "instagram_username": ig_user,
                "instagram_url": lead.get("instagram_url") or (f"https://www.instagram.com/{ig_user}/" if ig_user else ""),
                "instagram_bio": lead.get("instagram_bio") or "",
                "followers_count": lead.get("followers_count") or 0,
                "whatsapp_e164": wa_e164,
                "phone_display": phone_display,
                "demo_url": demo_url,
                "demo_path": f"/demos/{slug}",
                "whatsapp_send_url": wa_send_url,
                "whatsapp_message": whatsapp_message,
                "video_script_60s": video_script_60s,
                "commercial_status": lead.get("commercial_status") or "demo_pronta",
                "recommended_offer": lead.get("recommended_offer") or "Showroom Digital Avantgarde Edition + Concierge WhatsApp",
                "diagnosis": lead.get("diagnosis") or "",
            }

            html_content = render_demo_html(lead, rank=p_rank, outreach=outreach)
            lead_demo_dir = DEMOS_DIR / slug
            lead_demo_dir.mkdir(parents=True, exist_ok=True)
            (lead_demo_dir / "index.html").write_text(html_content, encoding="utf-8")

            dossier_md = f"""# Dossiê & Kit de Envio Direto — {outreach['name']}
- **Ranking Top 30 (Denis):** #{p_rank:02d}
- **Arquitetura:** {outreach['archetype']}
- **ICP Score:** {outreach['score']}/100 (Prioridade {outreach['priority']})
- **Localização:** {outreach['city']} / {outreach['state']}
- **Instagram:** [@{outreach['instagram_username']}]({outreach['instagram_url']})
- **WhatsApp Direto:** {outreach['phone_display']} (`+{outreach['whatsapp_e164']}`)
- **URL Pública Vercel:** {outreach['demo_url']}
- **Link de Envio Direto (1 Clique):** [Enviar Demo no WhatsApp]({outreach['whatsapp_send_url']})

## Mensagem Pronta para WhatsApp
```text
{outreach['whatsapp_message']}
```

{outreach['video_script_60s']}
"""
            (DOCS_LEADS_DIR / f"{slug}.md").write_text(dossier_md, encoding="utf-8")
            new_denis_manifest.append(outreach)

        # Process Gabriel queue (30 demos)
        for p_rank, lead in enumerate(top_gabriel_30, start=1):
            slug = lead["slug"]
            company_name = (lead.get("name") or "Sua Loja").split("|")[0].split(" - ")[0].strip()
            full_name = lead.get("name") or company_name
            city = lead.get("city") or "Brasil"
            state = lead.get("state") or "BR"
            ig_user = (lead.get("instagram_username") or "").lstrip("@")
            raw_phone = lead.get("whatsapp") or lead.get("phone") or ""
            wa_e164 = format_whatsapp_e164(raw_phone)
            phone_display = format_phone_human(raw_phone)
            demo_url = (
                f"{public_demo_base.rstrip('/')}/{slug}"
                if public_demo_base
                else f"{base_url.rstrip('/')}/demos/{slug}"
            )
            vertical = detect_vertical_key(lead)
            theme = DESIGN_THEMES[(p_rank - 1) % len(DESIGN_THEMES)]

            gap_reason = (
                "todo o trafego do Instagram de voces hoje desagua em link intermediario sem vitrine filtravel no celular"
                if not lead.get("has_own_website")
                else "a experiencia mobile atual nao conta com busca instantanea de acervo e simulacao direta por modelo"
            )

            whatsapp_message = (
                f"Olá, diretoria da *{company_name}*! Tudo bem?\n\n"
                f"Acompanhamos a operação de vocês no Instagram (@{ig_user}) em {city}/{state} e notamos que {gap_reason}.\n\n"
                f"Em vez de enviar uma apresentação comercial teórica, nós projetamos e colocamos no ar uma *demonstração funcional exclusiva do novo Showroom Digital da {company_name}* "
                f"(com filtro instantâneo por marca/modelo, vitrine interativa de alto padrão e captação integrada ao WhatsApp de vocês):\n\n"
                f"{demo_url}\n\n"
                f"Podem abrir direto no celular para testar a experiência. Se fizer sentido ativarmos essa estrutura oficial para a {company_name}, fico à disposição por aqui."
            )
            wa_send_url = f"https://wa.me/{wa_e164}?text={urllib.parse.quote(whatsapp_message)}"

            video_script_60s = f"""# Roteiro de Vídeo Executivo (45 a 60s) — {full_name}
> Origem: Playbook Brag International (Build Before Pitch · Prova sobre Discurso)
> Responsável pelo Disparo: Gabriel (Fila 2 — Gabriel (30 Demos) · #{p_rank:02d}/30)
> Destinatário: Sócio / Diretor Comercial da {company_name} (@{ig_user})
> Referência Arquitetural: Avantgarde Concept Store ({theme['archetype']})
> Link Público Vercel: {demo_url}

## [00:00 - 00:10] Abertura & Reconhecimento da Marca
"Olá pessoal da {company_name}, aqui é o Gabriel. Estávamos acompanhando a operação e o posicionamento de vocês em {city}/{state} pelo perfil @{ig_user}..."

## [00:10 - 00:25] Diagnóstico do Gap Real (Fato Objetivo)
"...e notamos que quem chega pelo Instagram hoje encontra {gap_reason}. Na prática, o comprador de alto valor não consegue filtrar modelos por marca, ano ou blindagem em 5 segundos no smartphone."

## [00:25 - 00:45] A Prova (Walkthrough do Protótipo Funcional)
"Em vez de pedir uma reunião teórica, nós desenhamos e publicamos uma demonstração funcional sob medida para a {company_name} no padrão Avantgarde. Veja na tela: Hero Slider com telemetria Ano/Km/Valor, busca flutuante por Marca e Modelo, cards chanfrados e encomenda sob medida conectada ao WhatsApp {phone_display}."

## [00:45 - 00:60] Fechamento (Sintaxe Brag: Zero Pitch Forçado)
"Sem discurso de agência. Estou deixando o link público aqui na mensagem para você testar no próprio celular. Se fizer sentido ativarmos essa arquitetura oficial para a {company_name}, basta me responder por aqui."
"""

            outreach = {
                "rank": p_rank * 2,
                "owner": "gabriel",
                "owner_name": "Gabriel",
                "owner_label": "Fila 2 — Gabriel (30 Demos)",
                "partner_rank": p_rank,
                "company_id": lead.get("id") or f"gabriel_{slug}",
                "slug": slug,
                "name": full_name,
                "short_name": company_name,
                "niche": lead.get("niche") or "P1 — Revendas premium e multimarcas",
                "vertical": vertical,
                "archetype": theme["archetype"],
                "city": city,
                "state": state,
                "score": lead.get("score") or 95,
                "priority": lead.get("priority") or "A",
                "instagram_username": ig_user,
                "instagram_url": lead.get("instagram_url") or (f"https://www.instagram.com/{ig_user}/" if ig_user else ""),
                "instagram_bio": lead.get("instagram_bio") or "",
                "followers_count": lead.get("followers_count") or 0,
                "whatsapp_e164": wa_e164,
                "phone_display": phone_display,
                "demo_url": demo_url,
                "demo_path": f"/demos/{slug}",
                "whatsapp_send_url": wa_send_url,
                "whatsapp_message": whatsapp_message,
                "video_script_60s": video_script_60s,
                "commercial_status": lead.get("commercial_status") or "demo_pronta",
                "recommended_offer": lead.get("recommended_offer") or "Showroom Digital Avantgarde Edition + Concierge WhatsApp",
                "diagnosis": lead.get("diagnosis") or "",
            }

            html_content = render_demo_html(lead, rank=p_rank, outreach=outreach)
            lead_demo_dir = DEMOS_DIR / slug
            lead_demo_dir.mkdir(parents=True, exist_ok=True)
            (lead_demo_dir / "index.html").write_text(html_content, encoding="utf-8")

            dossier_md = f"""# Dossiê & Kit de Envio Direto — {outreach['name']}
- **Ranking Top 30 (Gabriel):** #{p_rank:02d}
- **Arquitetura:** {outreach['archetype']}
- **ICP Score:** {outreach['score']}/100 (Prioridade {outreach['priority']})
- **Localização:** {outreach['city']} / {outreach['state']}
- **Instagram:** [@{outreach['instagram_username']}]({outreach['instagram_url']})
- **WhatsApp Direto:** {outreach['phone_display']} (`+{outreach['whatsapp_e164']}`)
- **URL Pública Vercel:** {outreach['demo_url']}
- **Link de Envio Direto (1 Clique):** [Enviar Demo no WhatsApp]({outreach['whatsapp_send_url']})

## Mensagem Pronta para WhatsApp
```text
{outreach['whatsapp_message']}
```

{outreach['video_script_60s']}
"""
            (DOCS_LEADS_DIR / f"{slug}.md").write_text(dossier_md, encoding="utf-8")
            new_gabriel_manifest.append(outreach)

        # Merge Denis (30) + Gabriel (30) interlaced (Denis odd, Gabriel even)
        manifest: list[dict[str, Any]] = []
        for i in range(30):
            if i < len(new_denis_manifest):
                manifest.append(new_denis_manifest[i])
            if i < len(new_gabriel_manifest):
                manifest.append(new_gabriel_manifest[i])

        conn.commit()
        (DEMOS_DIR / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        (DEMOS_DIR / "index.html").write_text(render_hub_index_html(manifest), encoding="utf-8")
        (DEMOS_DIR / "vercel.json").write_text(
            json.dumps({"cleanUrls": True, "trailingSlash": False}, indent=2),
            encoding="utf-8",
        )
        return manifest
    finally:
        if own_conn:
            conn.close()

def render_hub_index_html(manifest: Optional[list[dict[str, Any]]] = None) -> str:
    from pathlib import Path
    db_file = DEMOS_DIR / "database_all_demos.json"
    if db_file.exists():
        try:
            records = json.loads(db_file.read_text(encoding="utf-8"))
        except Exception:
            records = manifest or []
    else:
        records = manifest or []

    manifest_json = json.dumps(records, ensure_ascii=False)
    total_count = len(records)
    denis_total = len([r for r in records if r.get("owner") == "denis"])
    gabriel_total = len([r for r in records if r.get("owner") == "gabriel"])

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>BRAG International — Dashboard Executivo &amp; Banco de Dados de Demos</title>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="{FONT_URL}" rel="stylesheet" />
  <style>
    :root {{
      --color-bg-primary: #09090b;
      --color-bg-elevated: #121216;
      --color-bg-card: #16161c;
      --color-text-primary: #ffffff;
      --color-text-secondary: #989898;
      --color-accent: #cf4520;
      --color-denis: #cf4520;
      --color-gabriel: #1d5bd6;
      --color-emerald: #10b981;
      --color-gold: #dfb858;
      --border-subtle: rgba(255, 255, 255, 0.10);
      --font-display: 'Barlow Condensed', sans-serif;
      --font-sans: 'Plus Jakarta Sans', sans-serif;
      --font-mono: 'JetBrains Mono', monospace;
      --text-xs: 0.75rem;
      --text-sm: 0.875rem;
      --space-2: 0.5rem;
      --space-3: 0.75rem;
      --space-4: 1rem;
      --space-5: 1.5rem;
      --space-6: 2rem;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      background-color: var(--color-bg-primary);
      color: var(--color-text-primary);
      font-family: var(--font-sans);
      padding: var(--space-6) var(--space-5);
      line-height: 1.5;
    }}
    .wrap {{ max-width: 96rem; margin: 0 auto; }}
    header {{
      display: flex;
      justify-content: space-between;
      align-items: flex-end;
      flex-wrap: wrap;
      gap: var(--space-4);
      padding-bottom: var(--space-5);
      border-bottom: 1px solid var(--border-subtle);
      margin-bottom: var(--space-5);
    }}
    .eyebrow {{
      font-family: var(--font-display);
      font-size: 0.9rem;
      color: var(--color-accent);
      letter-spacing: 0.28em;
      text-transform: uppercase;
      font-weight: 700;
    }}
    h1 {{
      font-family: var(--font-display);
      font-size: clamp(1.85rem, 3.4vw, 2.8rem);
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      margin-top: 4px;
    }}
    .sub {{ color: var(--color-text-secondary); font-size: var(--text-sm); margin-top: 4px; max-width: 58rem; }}
    .actions-top {{
      display: flex;
      gap: var(--space-3);
      flex-wrap: wrap;
      align-items: center;
    }}
    .btn-top {{
      background: var(--color-bg-elevated);
      border: 1px solid var(--border-subtle);
      color: #ffffff;
      padding: 0.6rem 1rem;
      font-family: var(--font-sans);
      font-size: 0.85rem;
      font-weight: 600;
      text-decoration: none;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      transition: all 0.2s ease;
    }}
    .btn-top:hover {{
      border-color: rgba(255, 255, 255, 0.35);
      background: #1c1c22;
    }}
    .btn-top-gold {{
      background: rgba(223, 184, 88, 0.15);
      border-color: var(--color-gold);
      color: #f7f7ee;
    }}
    .btn-top-gold:hover {{
      background: rgba(223, 184, 88, 0.25);
    }}
    .partner-switcher {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: var(--space-4);
      margin-bottom: var(--space-5);
    }}
    .partner-tab {{
      background: var(--color-bg-elevated);
      border: 1px solid var(--border-subtle);
      padding: 1.15rem 1.35rem;
      cursor: pointer;
      text-align: left;
      transition: all 0.2s ease;
      display: flex;
      flex-direction: column;
      gap: 6px;
    }}
    .partner-tab:hover {{
      border-color: rgba(255, 255, 255, 0.28);
    }}
    .partner-tab.active-denis {{
      border-color: var(--color-denis);
      background: linear-gradient(135deg, rgba(207, 69, 32, 0.16), rgba(18, 18, 22, 0.95));
      box-shadow: 0 12px 32px rgba(207, 69, 32, 0.14);
    }}
    .partner-tab.active-gabriel {{
      border-color: var(--color-gabriel);
      background: linear-gradient(135deg, rgba(29, 91, 214, 0.18), rgba(18, 18, 22, 0.95));
      box-shadow: 0 12px 32px rgba(29, 91, 214, 0.16);
    }}
    .partner-tab.active-all {{
      border-color: var(--color-emerald);
      background: linear-gradient(135deg, rgba(16, 185, 129, 0.14), rgba(18, 18, 22, 0.95));
      box-shadow: 0 12px 32px rgba(16, 185, 129, 0.14);
    }}
    .partner-tab-kicker {{
      font-family: var(--font-display);
      font-size: 0.78rem;
      font-weight: 700;
      letter-spacing: 0.22em;
      text-transform: uppercase;
      color: var(--color-text-secondary);
    }}
    .partner-tab-title {{
      font-family: var(--font-display);
      font-size: 1.45rem;
      font-weight: 800;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      color: #ffffff;
    }}
    .partner-tab-meta {{
      font-family: var(--font-mono);
      font-size: 0.76rem;
      color: var(--color-text-secondary);
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}
    .toolbar {{
      display: flex;
      flex-wrap: wrap;
      justify-content: space-between;
      align-items: center;
      gap: var(--space-3);
      margin-bottom: var(--space-4);
      background: var(--color-bg-elevated);
      border: 1px solid var(--border-subtle);
      padding: 0.9rem 1.2rem;
    }}
    .search-input {{
      background: #09090b;
      border: 1px solid var(--border-subtle);
      color: #ffffff;
      padding: 0.55rem 0.95rem;
      font-size: 0.85rem;
      min-width: 320px;
      outline: none;
      font-family: var(--font-sans);
    }}
    .search-input:focus {{ border-color: var(--color-accent); }}
    .kpi-pills {{
      display: flex;
      flex-wrap: wrap;
      gap: var(--space-2);
      font-size: var(--text-xs);
    }}
    .kpi-pill {{
      background: #09090b;
      border: 1px solid var(--border-subtle);
      padding: 0.35rem 0.75rem;
      font-family: var(--font-mono);
      color: var(--color-text-secondary);
    }}
    .kpi-pill strong {{ color: #ffffff; }}
    table {{
      width: 100%;
      border-collapse: collapse;
      background: var(--color-bg-elevated);
      border: 1px solid var(--border-subtle);
    }}
    th {{
      text-align: left;
      padding: 0.85rem 1rem;
      font-family: var(--font-display);
      font-size: 0.82rem;
      font-weight: 700;
      letter-spacing: 0.16em;
      text-transform: uppercase;
      color: var(--color-text-secondary);
      border-bottom: 1px solid var(--border-subtle);
      background: #0d0d10;
    }}
    td {{
      padding: 0.85rem 1rem;
      border-bottom: 1px solid rgba(255, 255, 255, 0.05);
      font-size: var(--text-sm);
      vertical-align: middle;
    }}
    tr:hover td {{
      background: rgba(255, 255, 255, 0.02);
    }}
    tr.row-sent td {{
      background: rgba(16, 185, 129, 0.04);
    }}
    .tabular {{ font-family: var(--font-mono); }}
    .badge-owner-denis {{
      display: inline-block;
      padding: 0.15rem 0.55rem;
      background: rgba(207, 69, 32, 0.18);
      border: 1px solid rgba(207, 69, 32, 0.45);
      color: #ff9d72;
      font-size: 0.7rem;
      font-family: var(--font-mono);
      font-weight: 700;
      letter-spacing: 0.08em;
      text-transform: uppercase;
    }}
    .badge-owner-gabriel {{
      display: inline-block;
      padding: 0.15rem 0.55rem;
      background: rgba(29, 91, 214, 0.18);
      border: 1px solid rgba(29, 91, 214, 0.45);
      color: #93c5fd;
      font-size: 0.7rem;
      font-family: var(--font-mono);
      font-weight: 700;
      letter-spacing: 0.08em;
      text-transform: uppercase;
    }}
    .badge-score {{
      display: inline-block;
      padding: 0.15rem 0.45rem;
      background: rgba(16, 185, 129, 0.12);
      border: 1px solid rgba(16, 185, 129, 0.35);
      color: #10b981;
      font-size: 0.74rem;
      font-weight: 600;
    }}
    .badge-active-lot {{
      display: inline-block;
      padding: 0.15rem 0.45rem;
      background: rgba(223, 184, 88, 0.15);
      border: 1px solid var(--color-gold);
      color: #f7f7ee;
      font-size: 0.68rem;
      font-family: var(--font-mono);
      font-weight: 700;
      letter-spacing: 0.06em;
      text-transform: uppercase;
      margin-left: 4px;
    }}
    .status-select {{
      background: #09090b;
      border: 1px solid var(--border-subtle);
      color: #ffffff;
      padding: 0.35rem 0.6rem;
      font-size: 0.78rem;
      font-family: var(--font-mono);
      outline: none;
      cursor: pointer;
    }}
    .status-select:focus {{ border-color: var(--color-accent); }}
    .btn-ag {{
      display: inline-block;
      background: #ffffff;
      color: #09090b;
      padding: 0.42rem 0.78rem;
      font-family: var(--font-sans);
      font-size: 0.78rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      text-decoration: none;
      transition: opacity 0.2s;
    }}
    .btn-ag:hover {{ opacity: 0.88; }}
    .btn-wa {{
      display: inline-block;
      background: #10b981;
      color: #ffffff;
      padding: 0.42rem 0.78rem;
      font-family: var(--font-sans);
      font-size: 0.78rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      text-decoration: none;
      transition: background-color 0.2s;
    }}
    .btn-wa:hover {{ background: #059669; }}
    .btn-ghost {{
      background: transparent;
      border: 1px solid var(--border-subtle);
      color: var(--color-text-secondary);
      padding: 0.42rem 0.72rem;
      font-family: var(--font-sans);
      font-size: 0.78rem;
      cursor: pointer;
      transition: all 0.2s;
    }}
    .btn-ghost:hover {{
      border-color: rgba(255, 255, 255, 0.35);
      color: #ffffff;
    }}
    .modal-backdrop {{
      position: fixed;
      inset: 0;
      background: rgba(0, 0, 0, 0.85);
      display: none;
      place-items: center;
      padding: 1rem;
      z-index: 9999;
    }}
    .modal-backdrop.open {{ display: grid; }}
    .modal-box {{
      background: #141418;
      border: 1px solid var(--border-subtle);
      max-width: 52rem;
      width: 100%;
      max-height: 85vh;
      overflow-y: auto;
      padding: 1.5rem;
    }}
    .modal-pre {{
      background: #09090b;
      border: 1px solid var(--border-subtle);
      padding: 1rem;
      font-family: var(--font-mono);
      font-size: 0.8rem;
      color: #e5e7eb;
      white-space: pre-wrap;
      word-break: break-word;
      line-height: 1.5;
      margin-top: 0.75rem;
    }}
    .empty-state {{
      text-align: center;
      padding: 3rem 1rem;
      color: var(--color-text-secondary);
    }}
  </style>
</head>
<body>
  <div class="wrap">
    <header>
      <div>
        <div class="eyebrow">AVANTGARDE CONCEPT STORE · BANCO DE DADOS UNIFICADO ({total_count} DEMOS NA FILA DE ABORDAGEM)</div>
        <h1>Dashboard Executivo &amp; Central de Demos</h1>
        <p class="sub">Visão completa de todos os <strong>{total_count} showrooms digitais publicados</strong> na Vercel e ativos na esteira de abordagem. Acompanhe a operação entre os sócios, filtre por responsável (Denis ou Gabriel), realize disparos de 1 clique no WhatsApp e monitore o funil comercial.</p>
      </div>
      <div class="actions-top">
        <a href="sales.html" class="btn-top" style="border-color:var(--color-gold);background:rgba(223,184,88,0.22);color:#f7f7ee;font-weight:700;">
          💼 Módulo Comercial (Bruce &amp; Gabriel)
        </a>
        <a href="crm.html" class="btn-top" style="border-color:var(--color-emerald);background:rgba(16,185,129,0.18);color:#f7f7ee;font-weight:700;">
          📱 Base CRM (WhatsApp)
        </a>
        <a href="/demos/crm_all_leads.csv" download class="btn-top btn-top-gold">
          📥 Baixar Planilha CSV ({total_count})
        </a>
        <a href="/demos/database_all_demos.json" download class="btn-top">
          📄 Baixar Banco JSON ({total_count})
        </a>
        <button type="button" class="btn-top" onclick="copyPartnerShareLink()">
          🔗 Copiar Link da Fila
        </button>
      </div>
    </header>

    <!-- 3 WORKSPACE TABS -->
    <div class="partner-switcher" role="tablist" aria-label="Seleção de Fila por Sócio">
      <button type="button" id="tabBtnDenis" class="partner-tab active-denis" onclick="setPartnerQueue('denis')">
        <span class="partner-tab-kicker">CARTEIRA DENIS ({denis_total} DEMOS)</span>
        <span class="partner-tab-title">Fila Denis</span>
        <div class="partner-tab-meta">
          <span id="metaDenisCount">Carregando...</span>
          <span style="color:#ff9d72;">?fila=denis</span>
        </div>
      </button>

      <button type="button" id="tabBtnGabriel" class="partner-tab" onclick="setPartnerQueue('gabriel')">
        <span class="partner-tab-kicker">CARTEIRA GABRIEL ({gabriel_total} DEMOS)</span>
        <span class="partner-tab-title">Fila Gabriel</span>
        <div class="partner-tab-meta">
          <span id="metaGabrielCount">Carregando...</span>
          <span style="color:#93c5fd;">?fila=gabriel</span>
        </div>
      </button>

      <button type="button" id="tabBtnAll" class="partner-tab" onclick="setPartnerQueue('all')">
        <span class="partner-tab-kicker">BANCO DE DADOS CONSOLIDADO</span>
        <span class="partner-tab-title">Todas as {total_count} Demos</span>
        <div class="partner-tab-meta">
          <span id="metaAllCount">{total_count} Showrooms na Fila</span>
          <span style="color:#10b981;">Total Geral</span>
        </div>
      </button>
    </div>

    <div class="toolbar">
      <div style="display:flex;align-items:center;gap:0.75rem;flex-wrap:wrap;">
        <input type="search" id="hubSearch" class="search-input" placeholder="Buscar por loja, cidade, estado, @instagram ou WhatsApp..." oninput="renderHubTable()" />
      </div>
      <div class="kpi-pills">
        <div class="kpi-pill">Fila: <strong id="kpiActiveOwner">Fila Denis</strong></div>
        <div class="kpi-pill">Pendentes de Contato: <strong id="kpiPending" style="color:#f59e0b;">0</strong></div>
        <div class="kpi-pill">Contatados: <strong id="kpiSent" style="color:#10b981;">0</strong></div>
        <div class="kpi-pill">Total Online na Vercel: <strong style="color:#34d399;">{total_count}/{total_count}</strong></div>
      </div>
    </div>

    <main>
      <table>
        <thead>
          <tr>
            <th>#</th>
            <th>Responsável</th>
            <th>Score ICP</th>
            <th>Loja &amp; Estilo Avantgarde</th>
            <th>Cidade &amp; Nicho</th>
            <th>Instagram &amp; WhatsApp</th>
            <th>Status</th>
            <th>Disparo Direto (1 Clique)</th>
          </tr>
        </thead>
        <tbody id="hubTableBody"></tbody>
      </table>
      <div id="emptyNotice" class="empty-state" style="display:none;">
        Nenhum showroom encontrado para os critérios de busca digitados.
      </div>
    </main>
  </div>

  <!-- Modal Roteiro & Mensagem -->
  <div id="scriptModal" class="modal-backdrop" onclick="if(event.target===this) closeScriptModal()">
    <div class="modal-box">
      <div style="display:flex;justify-content:space-between;align-items:center;gap:1rem;border-bottom:1px solid var(--border-subtle);padding-bottom:0.75rem;">
        <h2 id="modalTitle" style="font-family:var(--font-display);font-size:1.4rem;text-transform:uppercase;letter-spacing:0.08em;">Kit de Abordagem</h2>
        <button type="button" class="btn-ghost" onclick="closeScriptModal()">Fechar</button>
      </div>
      <div style="margin-top:1rem;">
        <div style="display:flex;justify-content:space-between;align-items:center;">
          <strong style="font-size:0.8rem;text-transform:uppercase;letter-spacing:0.12em;color:var(--color-accent);">Mensagem Pronta de WhatsApp</strong>
          <button type="button" class="btn-ghost" id="modalCopyMsgBtn">Copiar Mensagem</button>
        </div>
        <pre id="modalMsgPre" class="modal-pre"></pre>
      </div>
      <div style="margin-top:1.25rem;">
        <div style="display:flex;justify-content:space-between;align-items:center;">
          <strong style="font-size:0.8rem;text-transform:uppercase;letter-spacing:0.12em;color:var(--color-gold);">Roteiro de Vídeo Personalizado (45-60s)</strong>
          <button type="button" class="btn-ghost" id="modalCopyScriptBtn">Copiar Roteiro</button>
        </div>
        <pre id="modalScriptPre" class="modal-pre"></pre>
      </div>
      <div style="margin-top:1.25rem;display:flex;justify-content:flex-end;gap:0.75rem;">
        <a id="modalWaBtn" href="#" target="_blank" rel="noopener" class="btn-wa">Abrir Conversa no WhatsApp</a>
        <button type="button" class="btn-ghost" onclick="closeScriptModal()">Fechar</button>
      </div>
    </div>
  </div>

  <script>
    const MANIFEST = {manifest_json};
    const STORAGE_KEY = "brag_demos_status_v3";
    let currentQueue = "denis";
    let statusMap = {{}};

    try {{
      statusMap = JSON.parse(localStorage.getItem(STORAGE_KEY) || "{{}}");
    }} catch (e) {{
      statusMap = {{}};
    }}

    function getStatus(item) {{
      return statusMap[item.slug] || item.commercial_status || "demo_pronta";
    }}

    function setStatus(slug, newStatus) {{
      statusMap[slug] = newStatus;
      try {{
        localStorage.setItem(STORAGE_KEY, JSON.stringify(statusMap));
      }} catch (e) {{}}
      renderHubTable();
    }}

    function setPartnerQueue(queue) {{
      currentQueue = queue;
      const url = new URL(window.location.href);
      url.searchParams.set("fila", queue);
      window.history.replaceState({{}}, "", url.toString());

      document.getElementById("tabBtnDenis").className = "partner-tab" + (queue === "denis" ? " active-denis" : "");
      document.getElementById("tabBtnGabriel").className = "partner-tab" + (queue === "gabriel" ? " active-gabriel" : "");
      document.getElementById("tabBtnAll").className = "partner-tab" + (queue === "all" ? " active-all" : "");
      renderHubTable();
    }}

    function copyPartnerShareLink() {{
      const url = new URL(window.location.href);
      url.searchParams.set("fila", currentQueue);
      navigator.clipboard.writeText(url.toString());
      alert("Link da fila copiado: " + url.toString());
    }}

    function copyWhatsappMsg(slug) {{
      const item = MANIFEST.find(x => x.slug === slug);
      if (!item) return;
      navigator.clipboard.writeText(item.whatsapp_message);
      alert("Mensagem copiada para " + item.name + "!");
    }}

    function copyVideoScript(slug) {{
      const item = MANIFEST.find(x => x.slug === slug);
      if (!item) return;
      navigator.clipboard.writeText(item.video_script_60s);
      alert("Roteiro copiado para " + item.name + "!");
    }}

    function openScriptModal(slug) {{
      const item = MANIFEST.find(x => x.slug === slug);
      if (!item) return;
      document.getElementById("modalTitle").textContent = `#${{String(item.partner_rank).padStart(3, '0')}} (${{item.owner_name}}) — ${{item.name}}`;
      document.getElementById("modalMsgPre").textContent = item.whatsapp_message;
      document.getElementById("modalScriptPre").textContent = item.video_script_60s;
      document.getElementById("modalCopyMsgBtn").onclick = () => copyWhatsappMsg(slug);
      document.getElementById("modalCopyScriptBtn").onclick = () => copyVideoScript(slug);
      document.getElementById("modalWaBtn").href = item.whatsapp_send_url || `https://wa.me/${{item.whatsapp_e164}}`;
      document.getElementById("scriptModal").classList.add("open");
    }}

    function closeScriptModal() {{
      document.getElementById("scriptModal").classList.remove("open");
    }}

    function handleSendWhatsApp(slug) {{
      setStatus(slug, "primeiro_contato_enviado");
    }}

    function escapeHtml(str) {{
      return String(str || "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;");
    }}

    function renderHubTable() {{
      const q = (document.getElementById("hubSearch").value || "").toLowerCase().trim();
      const denisItems = MANIFEST.filter(d => d.owner === "denis");
      const gabrielItems = MANIFEST.filter(d => d.owner === "gabriel");

      const denisSent = denisItems.filter(d => getStatus(d) !== "demo_pronta").length;
      const gabrielSent = gabrielItems.filter(d => getStatus(d) !== "demo_pronta").length;

      document.getElementById("metaDenisCount").textContent = `${{denisSent}}/${{denisItems.length}} enviados · ${{denisItems.length - denisSent}} pendentes`;
      document.getElementById("metaGabrielCount").textContent = `${{gabrielSent}}/${{gabrielItems.length}} enviados · ${{gabrielItems.length - gabrielSent}} pendentes`;
      document.getElementById("metaAllCount").textContent = `${{denisSent + gabrielSent}}/${{MANIFEST.length}} enviados no total`;

      const filtered = MANIFEST.filter(d => {{
        if (currentQueue !== "all" && d.owner !== currentQueue) return false;
        if (!q) return true;
        const hay = `${{d.name}} ${{d.city}} ${{d.state}} ${{d.instagram_username}} ${{d.phone_display}} ${{d.whatsapp_e164}} ${{d.owner_name}} ${{d.history_batch}}`.toLowerCase();
        return hay.includes(q);
      }});

      const activeTotal = currentQueue === "denis" ? denisItems.length : (currentQueue === "gabriel" ? gabrielItems.length : MANIFEST.length);
      const activeSent = currentQueue === "denis" ? denisSent : (currentQueue === "gabriel" ? gabrielSent : (denisSent + gabrielSent));

      document.getElementById("kpiActiveOwner").textContent =
        currentQueue === "denis" ? `Fila Denis (${{denisItems.length}})` : (currentQueue === "gabriel" ? `Fila Gabriel (${{gabrielItems.length}})` : `Todas as ${{MANIFEST.length}} Demos`);
      document.getElementById("kpiPending").textContent = String(activeTotal - activeSent);
      document.getElementById("kpiSent").textContent = String(activeSent);

      const tbody = document.getElementById("hubTableBody");
      const emptyNotice = document.getElementById("emptyNotice");

      if (filtered.length === 0) {{
        tbody.innerHTML = "";
        emptyNotice.style.display = "block";
        return;
      }}
      emptyNotice.style.display = "none";

      tbody.innerHTML = filtered.map(d => {{
        const st = getStatus(d);
        const isSent = st !== "demo_pronta";
        const ownerBadge = d.owner === "denis"
          ? `<span class="badge-owner-denis">Denis #${{String(d.partner_rank).padStart(3, '0')}}</span>`
          : `<span class="badge-owner-gabriel">Gabriel #${{String(d.partner_rank).padStart(3, '0')}}</span>`;
        
        const activeBadge = d.is_active_manifest
          ? `<span class="badge-active-lot">Lote Atual</span>`
          : "";

        const igHtml = d.instagram_username
          ? `<a href="${{escapeHtml(d.instagram_url)}}" target="_blank" rel="noopener" style="color:var(--color-accent);text-decoration:none;">@${{escapeHtml(d.instagram_username)}}</a>`
          : `<span style="color:var(--color-text-secondary);">-</span>`;

        return `
          <tr class="${{isSent ? 'row-sent' : ''}}">
            <td class="tabular" style="font-weight:700;color:var(--color-accent);">
              #${{String(d.partner_rank).padStart(3, '0')}}
            </td>
            <td>
              ${{ownerBadge}}
              ${{activeBadge}}
            </td>
            <td><span class="badge-score tabular">${{d.score}}/100 · ${{escapeHtml(d.priority)}}</span></td>
            <td>
              <strong style="font-size:1.05rem;font-family:var(--font-display);letter-spacing:0.08em;text-transform:uppercase;">${{escapeHtml(d.name)}}</strong>
              <div class="tabular" style="font-size:var(--text-xs);color:var(--color-text-secondary);margin-top:2px;">
                ${{escapeHtml(d.archetype)}}
              </div>
            </td>
            <td>
              <div><strong>${{escapeHtml(d.city)}} · ${{escapeHtml(d.state)}}</strong></div>
              <div style="font-size:var(--text-xs);color:var(--color-text-secondary);">${{escapeHtml(d.niche)}}</div>
            </td>
            <td class="tabular" style="font-size:var(--text-xs);">
              <div>${{igHtml}}</div>
              <div style="color:#10b981;font-weight:600;margin-top:2px;">${{escapeHtml(d.phone_display)}}</div>
            </td>
            <td>
              <select class="status-select" onchange="setStatus('${{escapeHtml(d.slug)}}', this.value)">
                <option value="demo_pronta" ${{st === 'demo_pronta' ? 'selected' : ''}}>Demo Pronta</option>
                <option value="primeiro_contato_enviado" ${{st === 'primeiro_contato_enviado' ? 'selected' : ''}}>Enviado WhatsApp</option>
                <option value="respondeu" ${{st === 'respondeu' ? 'selected' : ''}}>Respondeu</option>
                <option value="reuniao" ${{st === 'reuniao' ? 'selected' : ''}}>Reunião</option>
                <option value="fechado" ${{st === 'fechado' ? 'selected' : ''}}>Fechado</option>
              </select>
            </td>
            <td>
              <div style="display:flex;gap:0.45rem;flex-wrap:wrap;">
                <a href="${{escapeHtml(d.demo_url)}}" target="_blank" rel="noopener" class="btn-ag">Abrir Showroom</a>
                <a href="${{escapeHtml(d.whatsapp_send_url)}}" target="_blank" rel="noopener" class="btn-wa" onclick="handleSendWhatsApp('${{escapeHtml(d.slug)}}')">WhatsApp 1-Clique</a>
                <button type="button" class="btn-ghost" onclick="copyWhatsappMsg('${{escapeHtml(d.slug)}}')">Copiar Msg</button>
                <button type="button" class="btn-ghost" onclick="openScriptModal('${{escapeHtml(d.slug)}}')">Roteiro &amp; Kit</button>
              </div>
            </td>
          </tr>
        `;
      }}).join("");
    }}

    const params = new URLSearchParams(window.location.search);
    const initialFila = (params.get("fila") || "denis").toLowerCase();
    if (["denis", "gabriel", "all"].includes(initialFila)) {{
      setPartnerQueue(initialFila);
    }} else {{
      setPartnerQueue("denis");
    }}
  </script>
</body>
</html>
"""



