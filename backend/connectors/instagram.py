"""
Connector B — INSTAGRAM (Section 3.B)
Reuses and ports the extraction, link classification, contact extraction, and ICP filtering
from the existing Antigravity project (`C:\\Users\\denis\\.gemini\\antigravity\\scratch\\instagram-lead-finder`).

Capabilities:
1. Live Apify extraction (`apify~instagram-hashtag-scraper`, `apify~instagram-profile-scraper`, `apify~instagram-search-scraper`) when APIFY_TOKEN is set.
2. Direct synchronization and enrichment from the existing `instagram-lead-finder/data/leads.json` database (237+ verified real profiles collected in Antigravity), fixing location parsing and extracting public phone, WhatsApp, and email from biographies and links.
3. Strict adherence to platform limits and public commercial data only.
"""
import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Optional

from backend.config import get_config
from backend.deduplication import (
    THIRD_PARTY_DOMAINS,
    extract_domain,
    is_own_domain,
    normalize_phone,
    strip_accents,
)

APIFY_BASE = "https://api.apify.com/v2"
SEARCH_ACTOR = "apify~instagram-search-scraper"
HASHTAG_ACTOR = "apify~instagram-hashtag-scraper"
PROFILE_ACTOR = "apify~instagram-profile-scraper"
TERMINAL_STATES = {"SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT"}

CONTACT_ONLY_HOSTS = {
    "wa.me", "whatsapp.com", "wa.link", "t.me", "telegram.me",
    "m.me", "whats.link", "ate.me", "contate.me", "api.whatsapp.com",
}

AGGREGATOR_HOSTS = {
    "linktr.ee", "linktree.com", "beacons.ai", "bio.site", "linkin.bio",
    "taplink.cc", "taplink.at", "lnk.bio", "heylink.me", "campsite.bio",
    "solo.to", "msha.ke", "bio.link", "link.me", "linkbio.co", "allmylinks.com",
    "hoo.be", "koji.to", "snipfeed.co", "calendly.com", "booksy.com",
    "offstore.me", "lovable.app", "github.io", "vercel.app", "netlify.app",
    "canva.site", "my.canva.site", "carrd.co", "notion.site", "kyte.site", "menudino.com",
}

MARKETPLACE_HOSTS = {
    "webmotors.com.br", "icarros.com.br", "mobiauto.com.br", "olx.com.br",
    "mercadolivre.com.br", "mercadolibre.com", "napista.com.br", "chavesnamao.com.br",
    "autoline.com.br", "usadosbr.com", "carrosp.com.br", "comprecar.com.br",
    "socorrao.com.br", "meucarronovo.com.br", "seminovosbh.com.br", "bombarco.com.br",
    "nautica.com.br", "boattrader.com", "yachtworld.com", "boats.com", "cars.com",
    "autotrader.com", "cargurus.com", "carfax.com", "truecar.com", "dupontregistry.com",
    "jamesedition.com", "bringatrailer.com", "carsandbids.com", "standvirtual.com",
}

NICHE_RULES = [
    ("P4 — Náutica premium", re.compile(r"\b(lancha|lanchas|iate|iates|yacht|yachts|jet[- ]?ski|jetski|sea[- ]?doo|seadoo|embarcacoes|embarcacao|nautica|marine|boats|azimut|schaefer|intermarine|fibrafort|nx boats|focker|ventura)\b", re.I)),
    ("P2 — Luxo e superesportivos", re.compile(r"\b(ferrari|lamborghini|mclaren|aston martin|maserati|bentley|rolls[- ]?royce|bugatti|pagani|superesportivo|superesportivos|supercar|supercars|hypercar|exotic car|carros exoticos)\b", re.I)),
    ("P3 — Importados e SUVs premium", re.compile(r"\b(importado|importados|importadora|suv premium|suvs premium|blindado|blindados|import car|veiculos executivos)\b", re.I)),
    ("P1 — Revendas premium e multimarcas", re.compile(r"\b(seminovo|seminovos|semi[- ]novos|multimarcas|concessionaria|dealership|car dealer|auto dealer|carros premium|veiculos premium|bmw|mercedes|audi|porsche|volvo|land rover|range rover|jaguar|lexus|ram|mustang|camaro|corvette|autohaus|motors|veiculos|cars|automoveis)\b", re.I)),
]

SERVICE_KEYWORDS = [
    ("Blindados", re.compile(r"\bblindad[oa]s?\b", re.I)),
    ("Importados", re.compile(r"\bimportad[oa]s?\b", re.I)),
    ("Superesportivos / Exóticos", re.compile(r"\b(superesportiv[oa]s?|supercar|exotic|ferrari|lamborghini|porsche|mclaren)\b", re.I)),
    ("Seminovos Premium", re.compile(r"\b(seminovos?|semi[- ]novos?|multimarcas|0km|zero km)\b", re.I)),
    ("Financiamento & Consignação", re.compile(r"\b(financiamento|financiamos|consigna[cç][aã]o|consignado|intermedia[cç][aã]o)\b", re.I)),
    ("Embarcações / Lanchas / Iates", re.compile(r"\b(lanchas?|iates?|yachts?|jet[- ]?ski|embarca[cç][oõ]es|n[aá]utica)\b", re.I)),
]

BRAZIL_CITIES = [
    ("São Paulo", "SP", re.compile(r"\b(sao paulo|sp\b|alphaville|barueri|moema|itaim|jardins|tatuape|morumbi|campinas|sorocaba|ribeirao preto|santos|sao bernardo|santo andre|guarulhos|jundiai)\b", re.I)),
    ("Curitiba", "PR", re.compile(r"\b(curitiba|cwb|londrina|maringa|cascavel|parana|\bpr\b|41\s*9?\d{4}|43\s*9?\d{4}|44\s*9?\d{4})\b", re.I)),
    ("Belo Horizonte", "MG", re.compile(r"\b(belo horizonte|\bbh\b|uberlandia|contagem|minas gerais|\bmg\b|31\s*9?\d{4}|34\s*9?\d{4})\b", re.I)),
    ("Rio de Janeiro", "RJ", re.compile(r"\b(rio de janeiro|\brj\b|barra da tijuca|niteroi|21\s*9?\d{4})\b", re.I)),
    ("Florianópolis", "SC", re.compile(r"\b(florianopolis|floripa|balneario camboriu|itapema|itajai|joinville|blumenau|santa catarina|\bsc\b|47\s*9?\d{4}|48\s*9?\d{4})\b", re.I)),
    ("Porto Alegre", "RS", re.compile(r"\b(porto alegre|\bpoa\b|gramado|caxias do sul|\brs\b|51\s*9?\d{4}|54\s*9?\d{4})\b", re.I)),
    ("Brasília", "DF", re.compile(r"\b(brasilia|\bbsb\b|lago sul|distrito federal|\bdf\b|61\s*9?\d{4})\b", re.I)),
    ("Goiânia", "GO", re.compile(r"\b(goiania|goias|\bgo\b|62\s*9?\d{4})\b", re.I)),
    ("Fortaleza", "CE", re.compile(r"\b(fortaleza|ceara|\bce\b|85\s*9?\d{4})\b", re.I)),
    ("Recife", "PE", re.compile(r"\b(recife|pernambuco|\bpe\b|81\s*9?\d{4})\b", re.I)),
    ("Salvador", "BA", re.compile(r"\b(salvador|bahia|\bba\b|71\s*9?\d{4})\b", re.I)),
    ("Miami", "FL", re.compile(r"\b(miami|orlando|florida|fort lauderdale|boca raton|\busa\b|305[- .\s]\d{3}|786[- .\s]\d{3})\b", re.I)),
]


def extract_contacts_from_bio_and_links(bio: str, links_str: str = "", external_url: str = "") -> dict[str, Any]:
    """
    Ported and enhanced from `instagram-lead-finder/lib/crm-client.mjs` (`extractContactChannels`).
    Extracts WhatsApp, phone, and email from public Instagram bio and external links.
    """
    bio_text = bio or ""
    raw_links = [l.strip() for l in (links_str or "").split("|") if l.strip() and l.strip() != "—"]
    if external_url and external_url != "—" and external_url not in raw_links:
        raw_links.append(external_url)

    whatsapp = ""
    whatsapp_verified = False
    phone = ""
    email = ""

    # 1. Check URLs for direct WhatsApp links
    for u in raw_links:
        m = re.search(
            r"(?:wa\.me/|api\.whatsapp\.com/send\?phone=|whats\.link/|phone=)(\+?\d{10,15})",
            u,
            re.I,
        )
        if m:
            whatsapp = normalize_phone(m.group(1))
            whatsapp_verified = True
            break

    # 2. Check bio text for explicit WhatsApp number
    if not whatsapp:
        m_bio_wa = re.search(
            r"(?:whatsapp|whats|wpp|zap|📲|📞|☎️)\s*[:.\-]?\s*(\+?\d{2,3}[\s.\-]?\d{2}[\s.\-]?9?\d{4}[\s.\-]?\d{4}|\(?\d{2}\)?\s*9?\d{4}[\- .\s]?\d{4})",
            bio_text,
            re.I,
        )
        if m_bio_wa:
            whatsapp = normalize_phone(m_bio_wa.group(1))
            whatsapp_verified = True

    # 3. Check generic commercial phone in bio
    m_phone = re.search(
        r"(\(\d{2}\)\s*9?\d{4,5}[\- .\s]?\d{4}|\b\d{2}[\s.\-]9?\d{4}[\s.\-]\d{4}\b|\b\d{2}\s*9\d{8}\b)",
        bio_text,
    )
    if m_phone:
        phone = normalize_phone(m_phone.group(1))

    # 4. Check public email in bio
    m_email = re.search(r"([a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})", bio_text)
    if m_email:
        email = m_email.group(1).lower()

    final_wpp = whatsapp or (phone if len(phone) == 11 and phone[2] == "9" else "")
    final_phone = phone or whatsapp

    return {
        "whatsapp": final_wpp,
        "whatsapp_verified": whatsapp_verified,
        "phone": final_phone,
        "email": email,
    }


def infer_city_state_country(raw_location: str, bio: str, name: str = "") -> tuple[str, str, str]:
    """
    Fixes the issue in the previous project where `location` sometimes held the store's own name
    (e.g. 'MF Motors') instead of the city. Cross-checks location, biography address, and DDD area code.
    """
    combined = strip_accents(f"{raw_location or ''} {bio or ''} {name or ''}").lower()
    for city_name, state_code, pattern in BRAZIL_CITIES:
        if pattern.search(combined):
            country = "EUA" if state_code == "FL" else "Brasil"
            # Check if a specific city inside the state was mentioned in raw_location
            loc_clean = (raw_location or "").strip()
            if loc_clean and not any(w in loc_clean.lower() for w in ("motors", "veiculos", "cars", "auto", "select", "premium")):
                parts = [p.strip() for p in re.split(r"[,/\-–]", loc_clean) if p.strip()]
                if parts and len(parts[0]) >= 3 and parts[0].lower() not in ("brasil", "brazil"):
                    return parts[0], state_code, country
            return city_name, state_code, country

    loc_clean = (raw_location or "").strip()
    if loc_clean and not any(w in loc_clean.lower() for w in ("motors", "veiculos", "cars", "auto", "select")):
        return loc_clean, "", "Brasil"
    return "São Paulo", "SP", "Brasil"


def extract_services_from_text(text: str, niche: str = "") -> list[str]:
    services = []
    norm_text = strip_accents(f"{text} {niche}").lower()
    for label, regex in SERVICE_KEYWORDS:
        if regex.search(norm_text):
            services.append(label)
    if not services and niche:
        if "P4" in niche or "nautic" in norm_text:
            services.append("Embarcações / Náutica")
        else:
            services.append("Comércio de Veículos")
    return services


def classify_bio_link(links_str: str, external_site_url: str = "", own_site_flag: str = "") -> dict[str, Any]:
    """
    Classifies Instagram links into BRAG categories (sem_link, whatsapp, terceiro, site_proprio, inconclusivo).
    """
    ext_clean = (external_site_url or "").strip()
    if ext_clean and ext_clean != "—":
        dom = extract_domain(ext_clean)
        if dom and is_own_domain(dom):
            return {
                "website_url": ext_clean,
                "has_own_website": True,
                "link_category": "site_proprio",
                "link_type": "Site próprio",
            }

    raw_links = [l.strip() for l in (links_str or "").split("|") if l.strip() and l.strip() != "—"]
    if not raw_links:
        return {
            "website_url": "",
            "has_own_website": False,
            "link_category": "sem_link",
            "link_type": "Sem link na bio",
        }

    for u in raw_links:
        dom = extract_domain(u)
        if dom and is_own_domain(dom) and own_site_flag.startswith("Sim"):
            return {
                "website_url": u,
                "has_own_website": True,
                "link_category": "site_proprio",
                "link_type": "Site próprio",
            }

    first_url = raw_links[0]
    first_dom = extract_domain(first_url)
    if any(first_dom == h or first_dom.endswith("." + h) for h in CONTACT_ONLY_HOSTS):
        return {
            "website_url": first_url,
            "has_own_website": False,
            "link_category": "whatsapp",
            "link_type": "Somente WhatsApp/contato",
        }
    if any(first_dom == h or first_dom.endswith("." + h) for h in AGGREGATOR_HOSTS):
        return {
            "website_url": first_url,
            "has_own_website": False,
            "link_category": "terceiro",
            "link_type": "Linktree/agregador",
        }
    if any(first_dom == h or first_dom.endswith("." + h) for h in MARKETPLACE_HOSTS):
        return {
            "website_url": first_url,
            "has_own_website": False,
            "link_category": "terceiro",
            "link_type": "Marketplace",
        }
    if is_own_domain(first_dom):
        return {
            "website_url": first_url,
            "has_own_website": True,
            "link_category": "site_proprio",
            "link_type": "Site próprio",
        }

    return {
        "website_url": first_url,
        "has_own_website": False,
        "link_category": "terceiro",
        "link_type": "Link externo / diretório",
    }


def load_legacy_instagram_leads(
    niche_filter: str = "",
    city_filter: str = "",
    limit: int = 50,
) -> list[dict[str, Any]]:
    """
    Loads and normalizes real verified Instagram profiles from the existing Antigravity project
    (`instagram-lead-finder/data/leads.json`).
    """
    cfg = get_config()
    path = Path(cfg["legacy_ig_leads_path"])
    if not path.exists():
        return []

    try:
        raw_data = json.loads(path.read_text(encoding="utf-8", errors="ignore"))
    except Exception:
        return []

    items: list[dict[str, Any]] = []
    niche_norm = strip_accents(niche_filter).lower()
    city_norm = strip_accents(city_filter).lower()

    records = list(raw_data.values()) if isinstance(raw_data, dict) else list(raw_data)
    for rec in records:
        if not isinstance(rec, dict) or not rec.get("username"):
            continue
        if rec.get("relevant") is False:
            continue

        rec_niche = rec.get("niche") or "P1 — Revendas premium e multimarcas"
        bio = rec.get("bio") or ""
        name = rec.get("name") or rec.get("username")
        city, state, country = infer_city_state_country(rec.get("location") or "", bio, name)

        if niche_norm:
            # Match P1, P2, P3, P4 or keyword in niche/bio
            haystack = strip_accents(f"{rec_niche} {bio} {name}").lower()
            if niche_norm not in haystack:
                code_match = re.match(r"^(p[1-4])\b", niche_norm)
                if not (code_match and code_match.group(1) in strip_accents(rec_niche).lower()):
                    continue

        if city_norm and city_norm not in ("brasil", "global", "todos", "todas"):
            loc_haystack = strip_accents(f"{city} {state} {rec.get('location') or ''} {bio}").lower()
            if city_norm not in loc_haystack:
                continue

        contacts = extract_contacts_from_bio_and_links(
            bio=bio,
            links_str=rec.get("links") or "",
            external_url=rec.get("externalSiteUrl") or "",
        )
        link_info = classify_bio_link(
            links_str=rec.get("links") or "",
            external_site_url=rec.get("externalSiteUrl") or "",
            own_site_flag=rec.get("ownSite") or "",
        )
        services = extract_services_from_text(bio, rec_niche)

        addr_match = re.search(r"(📍\s*[^📲☎️📞•|]+|\b(?:Av\.|Avenida|Rua|Alameda|Rodovia)\s+[^📲☎️📞•|\n]{5,65})", bio, re.I)
        address = addr_match.group(1).lstrip("📍 ").strip() if addr_match else f"{city} - {state}".strip(" -")

        items.append({
            "name": name,
            "instagram_username": rec.get("username"),
            "profile_name": name,
            "profile_url": rec.get("profileUrl") or f"https://www.instagram.com/{rec.get('username')}",
            "biography": bio,
            "external_url": rec.get("links") if rec.get("links") != "—" else "",
            "website_url": link_info["website_url"],
            "has_own_website": link_info["has_own_website"],
            "link_category": link_info["link_category"],
            "link_type": link_info["link_type"],
            "has_instagram": True,
            "phone": contacts["phone"],
            "whatsapp": contacts["whatsapp"],
            "whatsapp_verified": contacts["whatsapp_verified"],
            "email": contacts["email"],
            "city": city,
            "state": state,
            "country": country,
            "address": address,
            "niche": rec_niche,
            "subniche": (rec.get("terms") or "").replace("#", ""),
            "category": rec.get("businessCategory") or "Automotive Dealership",
            "services_offered": services,
            "followers_count": int(rec["followers"]) if str(rec.get("followers", "")).isdigit() else None,
            "posts_count": int(rec["postsCount"]) if str(rec.get("postsCount", "")).isdigit() else None,
            "latest_post_date": rec.get("latestPostDate") if rec.get("latestPostDate") != "—" else "",
            "is_business_account": True,
            "activity_indicators": rec.get("evidence") or "",
            "source": "instagram_antigravity_db",
            "confidence": "high",
            "discovered_at": (rec.get("collectedAt") or "2026-10-17") + "T12:00:00Z" if len(rec.get("collectedAt") or "") == 10 else rec.get("collectedAt"),
        })

    # Prioritize leads with direct phone/WhatsApp/email ready for outreach
    items.sort(
        key=lambda x: (
            1 if (x.get("whatsapp") or x.get("phone") or x.get("email")) else 0,
            1 if not x.get("has_own_website") else 0,
            x.get("followers_count") or 0,
        ),
        reverse=True,
    )
    return items[:limit]


def _apify_call(path: str, token: str, method: str = "GET", payload: Optional[dict] = None, timeout: float = 65.0) -> Any:
    url = f"{APIFY_BASE}{path}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "User-Agent": "BRAGLeadHunter/1.0",
    }
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8", errors="ignore"))


def search_apify_live_profiles(query: str, limit: int, token: str) -> list[dict[str, Any]]:
    """
    Runs live Apify Instagram profile search (`apify~instagram-search-scraper`) with strict rate limits.
    """
    capped_limit = min(max(int(limit), 3), 25)
    run_resp = _apify_call(
        f"/acts/{SEARCH_ACTOR}/runs?maxItems={capped_limit}&waitForFinish=60",
        token=token,
        method="POST",
        payload={"search": query.replace(",", " "), "searchType": "user", "searchLimit": capped_limit},
    )
    run_data = run_resp.get("data") or {}
    run_id = run_data.get("id")
    status = run_data.get("status")
    while status and status not in TERMINAL_STATES and run_id:
        time.sleep(2)
        poll = _apify_call(f"/actor-runs/{run_id}?waitForFinish=30", token=token)
        run_data = poll.get("data") or {}
        status = run_data.get("status")

    dataset_id = run_data.get("defaultDatasetId")
    if not dataset_id:
        return []
    items = _apify_call(f"/datasets/{dataset_id}/items?clean=true&format=json", token=token)
    return items if isinstance(items, list) else []


def search_instagram_commercial(
    niche: str = "",
    subniche: str = "",
    city: str = "",
    state: str = "",
    limit: int = 25,
    use_live_apify: bool = False,
) -> dict[str, Any]:
    """
    Main entrypoint for Connector B (Instagram).
    1. Reuses and filters verified profiles from the existing Antigravity project (`instagram-lead-finder`).
    2. If `use_live_apify=True` (or local dataset yields fewer than requested and APIFY_TOKEN is valid),
       queries live Apify actors safely within platform limits.
    """
    cfg = get_config()
    token = cfg.get("apify_token") or ""
    results = load_legacy_instagram_leads(niche_filter=subniche or niche, city_filter=city, limit=limit)
    provider = "instagram_antigravity_db"
    warning = None

    if (use_live_apify or len(results) == 0) and token:
        try:
            q = " ".join(p for p in [subniche or niche or "seminovos premium", city] if p).strip()
            live_raw = search_apify_live_profiles(q, limit=min(limit, 15), token=token)
            provider = "apify_instagram_live"
            for p in live_raw:
                username = (p.get("username") or "").strip()
                if not username or p.get("private"):
                    continue
                bio = (p.get("biography") or "").strip()
                full_name = (p.get("fullName") or username).strip()
                ext_urls = [u.get("url") for u in (p.get("externalUrls") or []) if isinstance(u, dict) and u.get("url")]
                if p.get("externalUrl") and p["externalUrl"] not in ext_urls:
                    ext_urls.append(p["externalUrl"])
                links_joined = " | ".join(ext_urls)

                contacts = extract_contacts_from_bio_and_links(bio, links_joined)
                link_info = classify_bio_link(links_joined)
                inferred_city, inferred_state, inferred_country = infer_city_state_country(city, bio, full_name)

                # Match niche
                matched_niche = niche or "P1 — Revendas premium e multimarcas"
                for label, rx in NICHE_RULES:
                    if rx.search(f"{full_name} {bio}"):
                        matched_niche = label
                        break

                services = extract_services_from_text(bio, matched_niche)
                posts_count = p.get("postsCount")
                followers_count = p.get("followersCount")
                act_parts = []
                if posts_count is not None:
                    act_parts.append(f"{posts_count} posts")
                if followers_count is not None:
                    act_parts.append(f"{followers_count} seg.")
                if p.get("isBusinessAccount"):
                    act_parts.append("conta comercial")

                results.append({
                    "name": full_name,
                    "instagram_username": username,
                    "profile_name": full_name,
                    "profile_url": f"https://www.instagram.com/{username}",
                    "biography": bio,
                    "external_url": links_joined,
                    "website_url": link_info["website_url"],
                    "has_own_website": link_info["has_own_website"],
                    "link_category": link_info["link_category"],
                    "link_type": link_info["link_type"],
                    "has_instagram": True,
                    "phone": contacts["phone"],
                    "whatsapp": contacts["whatsapp"],
                    "whatsapp_verified": contacts["whatsapp_verified"],
                    "email": contacts["email"],
                    "city": inferred_city,
                    "state": inferred_state or state,
                    "country": inferred_country,
                    "address": f"{inferred_city} - {inferred_state or state}".strip(" -"),
                    "niche": matched_niche,
                    "subniche": subniche,
                    "category": p.get("businessCategoryName") or "Automotive Dealership",
                    "services_offered": services,
                    "followers_count": followers_count,
                    "posts_count": posts_count,
                    "latest_post_date": "",
                    "is_business_account": bool(p.get("isBusinessAccount", True)),
                    "activity_indicators": " · ".join(act_parts),
                    "source": "apify_instagram_live",
                    "confidence": "high",
                })
        except Exception as e:
            warning = f"Coleta ao vivo Apify retornou aviso ({e}); utilizando base verificada local."

    return {
        "provider": provider,
        "warning": warning,
        "count": len(results[:limit]),
        "items": results[:limit],
    }
