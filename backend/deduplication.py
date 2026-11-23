"""
Deduplication System (Section 6).
Unique identification across:
1. Normalized phone (last 10-11 digits or international E.164 digits)
2. Website domain (excluding third-party aggregators/marketplaces/socials)
3. Instagram username (lowercase without @)
4. Normalized commercial name + location

Never allows the same company to be added repeatedly.
When new data arrives, updates the existing record and preserves history.
"""
import json
import re
import sqlite3
import unicodedata
from typing import Any, Optional
from urllib.parse import urlparse

from backend.database import new_id, now_iso, row_to_dict

THIRD_PARTY_DOMAINS = {
    "linktr.ee", "linktree.com", "beacons.ai", "bio.site", "linkin.bio",
    "taplink.cc", "taplink.at", "lnk.bio", "heylink.me", "campsite.bio",
    "solo.to", "msha.ke", "bio.link", "link.me", "linkbio.co", "allmylinks.com",
    "hoo.be", "koji.to", "snipfeed.co", "calendly.com", "booksy.com",
    "offstore.me", "lovable.app", "github.io", "vercel.app", "netlify.app",
    "canva.site", "my.canva.site", "carrd.co", "notion.site", "kyte.site",
    "menudino.com", "webmotors.com.br", "icarros.com.br", "mobiauto.com.br",
    "olx.com.br", "mercadolivre.com.br", "mercadolibre.com", "napista.com.br",
    "chavesnamao.com.br", "autoline.com.br", "usadosbr.com", "carrosp.com.br",
    "comprecar.com.br", "socorrao.com.br", "meucarronovo.com.br",
    "seminovosbh.com.br", "bombarco.com.br", "nautica.com.br", "boattrader.com",
    "yachtworld.com", "boats.com", "cars.com", "autotrader.com", "cargurus.com",
    "carfax.com", "truecar.com", "dupontregistry.com", "jamesedition.com",
    "bringatrailer.com", "carsandbids.com", "standvirtual.com", "piscapisca.pt",
    "instagram.com", "facebook.com", "fb.com", "fb.me", "youtube.com",
    "youtu.be", "tiktok.com", "twitter.com", "x.com", "linkedin.com",
    "pinterest.com", "threads.net", "threads.com", "g.page", "maps.app.goo.gl",
    "goo.gl", "forms.gle", "maps.google.com", "google.com", "google.com.br",
    "g.co", "share.google", "negocio.site", "yelp.com", "apontador.com.br",
    "guiamais.com.br", "wa.me", "whatsapp.com", "api.whatsapp.com", "wa.link",
    "t.me", "telegram.me", "whats.link", "bit.ly", "tinyurl.com", "cutt.ly",
    "encurtador.com.br",
}


def strip_accents(text: str) -> str:
    if not text:
        return ""
    norm = unicodedata.normalize("NFD", str(text))
    return "".join(c for c in norm if unicodedata.category(c) != "Mn")


def normalize_slug(text: str) -> str:
    clean = strip_accents(text).lower()
    clean = re.sub(r"[^a-z0-9]+", "-", clean).strip("-")
    return clean or "empresa"


def normalize_phone(phone: Optional[str]) -> str:
    if not phone:
        return ""
    digits = re.sub(r"\D+", "", str(phone))
    if not digits:
        return ""
    # Remove leading 00 or 55 if Brazilian 12/13 digits so local (11) 98888-7777 matches +55 11 98888-7777
    if len(digits) in (12, 13) and digits.startswith("55"):
        digits = digits[2:]
    elif len(digits) == 11 and digits.startswith("1") and digits[2] != "9":
        # US number 1 + 10 digits (where 3rd digit is not Brazilian mobile '9')
        digits = digits[1:]
    if len(digits) < 8:
        return ""
    return digits


def extract_domain(url: Optional[str]) -> str:
    if not url:
        return ""
    raw = str(url).strip()
    if raw in ("—", "-", "None", "null"):
        return ""
    if not re.match(r"^https?://", raw, re.I):
        raw = "https://" + raw
    try:
        parsed = urlparse(raw)
        host = (parsed.hostname or "").lower()
        if host.startswith("www."):
            host = host[4:]
        return host
    except Exception:
        return ""


def is_own_domain(domain: str) -> bool:
    if not domain or "." not in domain:
        return False
    for tp in THIRD_PARTY_DOMAINS:
        if domain == tp or domain.endswith("." + tp):
            return False
    return True


def normalize_username(username: Optional[str]) -> str:
    if not username:
        return ""
    u = str(username).strip().lstrip("@").lower()
    u = re.sub(r"[^a-z0-9._]", "", u)
    return u


def normalize_name_location(name: Optional[str], city: Optional[str] = "", region: Optional[str] = "") -> str:
    base_name = strip_accents(name or "").lower()
    # Strip common corporate suffixes for matching
    base_name = re.sub(r"\b(ltda|me|epp|s/a|sa|inc|llc|corp|oficial|official)\b", " ", base_name)
    base_name = re.sub(r"[^a-z0-9]+", "", base_name)
    loc = strip_accents(city or region or "").lower()
    loc = re.sub(r"[^a-z0-9]+", "", loc)
    if not base_name:
        return ""
    return f"{base_name}::{loc}" if loc else base_name


def find_existing_company(
    conn: sqlite3.Connection,
    name: str,
    city: str = "",
    region: str = "",
    phone: str = "",
    whatsapp: str = "",
    website_url: str = "",
    instagram_username: str = "",
) -> tuple[Optional[dict[str, Any]], str]:
    """
    Checks SQLite database for an existing company matching by:
    1. Instagram username
    2. Own website domain
    3. Normalized phone / WhatsApp
    4. Normalized commercial name + location
    Returns (company_dict, matched_by_reason) or (None, "").
    """
    ig_norm = normalize_username(instagram_username)
    if ig_norm:
        row = conn.execute(
            """
            SELECT c.* FROM COMPANIES c
            JOIN SOCIAL_PROFILES s ON s.company_id = c.id
            WHERE LOWER(s.username) = ?
            LIMIT 1
            """,
            (ig_norm,),
        ).fetchone()
        if row:
            return row_to_dict(row), f"instagram:{ig_norm}"

    domain = extract_domain(website_url)
    if domain and is_own_domain(domain):
        row = conn.execute(
            """
            SELECT c.* FROM COMPANIES c
            JOIN WEBSITES w ON w.company_id = c.id
            WHERE LOWER(w.domain) = ? AND w.is_own_domain = 1
            LIMIT 1
            """,
            (domain,),
        ).fetchone()
        if row:
            return row_to_dict(row), f"domain:{domain}"

    for raw_p in (whatsapp, phone):
        p_norm = normalize_phone(raw_p)
        if p_norm:
            row = conn.execute(
                """
                SELECT c.* FROM COMPANIES c
                JOIN CONTACTS ct ON ct.company_id = c.id
                WHERE ct.phone_normalized = ?
                LIMIT 1
                """,
                (p_norm,),
            ).fetchone()
            if row:
                return row_to_dict(row), f"phone:{p_norm}"

    name_loc = normalize_name_location(name, city, region)
    if name_loc:
        row = conn.execute(
            "SELECT * FROM COMPANIES WHERE normalized_name_loc = ? LIMIT 1",
            (name_loc,),
        ).fetchone()
        if row:
            return row_to_dict(row), f"name_location:{name_loc}"

        # Also check exact normalized name if location was empty on one side
        just_name = name_loc.split("::")[0]
        if len(just_name) >= 6:
            row2 = conn.execute(
                "SELECT * FROM COMPANIES WHERE normalized_name_loc = ? OR normalized_name_loc LIKE ? LIMIT 1",
                (just_name, f"{just_name}::%"),
            ).fetchone()
            if row2:
                existing_city = strip_accents(row2["city"] or "").lower()
                incoming_city = strip_accents(city or "").lower()
                if not existing_city or not incoming_city or existing_city == incoming_city:
                    return row_to_dict(row2), f"name:{just_name}"

    return None, ""


def upsert_company_bundle(
    conn: sqlite3.Connection,
    payload: dict[str, Any],
) -> dict[str, Any]:
    """
    Upserts a company and its related CONTACTS, SOCIAL_PROFILES, and WEBSITES records.
    Preserves history in COMPANIES.history_log when updating an existing record.
    Returns {"company_id": ..., "status": "new" | "updated" | "duplicate", "matched_by": ...}
    """
    now = now_iso()
    name = (payload.get("name") or payload.get("instagram_username") or "Empresa").strip()
    city = (payload.get("city") or "").strip()
    region = (payload.get("region") or "").strip()
    phone_raw = (payload.get("phone") or "").strip()
    whatsapp_raw = (payload.get("whatsapp") or "").strip()
    email = (payload.get("email") or "").strip().lower()
    website_url = (payload.get("website_url") or "").strip()
    ig_user = normalize_username(payload.get("instagram_username"))
    source = (payload.get("source") or "manual").strip()
    confidence = (payload.get("confidence") or "high").strip()

    existing, matched_by = find_existing_company(
        conn,
        name=name,
        city=city,
        region=region,
        phone=phone_raw,
        whatsapp=whatsapp_raw,
        website_url=website_url,
        instagram_username=ig_user,
    )

    domain = extract_domain(website_url)
    own_domain_flag = 1 if (domain and is_own_domain(domain)) or payload.get("has_own_website") else 0
    has_ig_flag = 1 if ig_user or payload.get("has_instagram") else 0
    name_loc = normalize_name_location(name, city, region)
    slug = normalize_slug(name)

    services_list = payload.get("services_offered") or []
    if isinstance(services_list, str):
        services_list = [s.strip() for s in services_list.split(",") if s.strip()]

    if existing is None:
        company_id = new_id("comp")
        history_entry = [{"timestamp": now, "source": source, "action": "created"}]
        conn.execute(
            """
            INSERT INTO COMPANIES (
                id, slug, name, normalized_name_loc, country, state, city, region,
                address, niche, subniche, category, services_offered,
                google_rating, google_reviews_count, opening_hours, maps_url,
                latitude, longitude, has_own_website, has_instagram,
                commercial_status, source, data_confidence, discovered_at, updated_at, history_log
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                company_id,
                slug,
                name,
                name_loc,
                payload.get("country") or "Brasil",
                payload.get("state") or "",
                city,
                region,
                payload.get("address") or "",
                payload.get("niche") or "",
                payload.get("subniche") or "",
                payload.get("category") or "",
                json.dumps(services_list, ensure_ascii=False),
                payload.get("google_rating"),
                payload.get("google_reviews_count"),
                payload.get("opening_hours") or "",
                payload.get("maps_url") or "",
                payload.get("latitude"),
                payload.get("longitude"),
                own_domain_flag,
                has_ig_flag,
                payload.get("commercial_status") or "icp_identificado",
                source,
                confidence,
                payload.get("discovered_at") or now,
                now,
                json.dumps(history_entry, ensure_ascii=False),
            ),
        )
        record_status = "new"
    else:
        company_id = existing["id"]
        changes = []
        try:
            old_history = json.loads(existing.get("history_log") or "[]")
        except Exception:
            old_history = []

        try:
            old_services = json.loads(existing.get("services_offered") or "[]")
        except Exception:
            old_services = []
        merged_services = list(dict.fromkeys(old_services + services_list))
        if len(merged_services) > len(old_services):
            changes.append("services_offered")

        def pick_str(field_key: str, incoming_val: Any) -> str:
            inc = str(incoming_val or "").strip()
            old = str(existing.get(field_key) or "").strip()
            if inc and not old:
                changes.append(field_key)
                return inc
            return old or inc

        new_city = pick_str("city", city)
        new_state = pick_str("state", payload.get("state"))
        new_region = pick_str("region", region)
        new_address = pick_str("address", payload.get("address"))
        new_niche = pick_str("niche", payload.get("niche"))
        new_subniche = pick_str("subniche", payload.get("subniche"))
        new_cat = pick_str("category", payload.get("category"))
        new_hours = pick_str("opening_hours", payload.get("opening_hours"))
        new_maps = pick_str("maps_url", payload.get("maps_url"))

        new_rating = existing.get("google_rating")
        if payload.get("google_rating") is not None and new_rating is None:
            new_rating = payload.get("google_rating")
            changes.append("google_rating")

        new_reviews = existing.get("google_reviews_count")
        if payload.get("google_reviews_count") is not None and new_reviews is None:
            new_reviews = payload.get("google_reviews_count")
            changes.append("google_reviews_count")

        new_own_web = 1 if (existing.get("has_own_website") or own_domain_flag) else 0
        if new_own_web != existing.get("has_own_website"):
            changes.append("has_own_website")

        new_has_ig = 1 if (existing.get("has_instagram") or has_ig_flag) else 0
        if new_has_ig != existing.get("has_instagram"):
            changes.append("has_instagram")

        old_sources = [s.strip() for s in (existing.get("source") or "").split("+") if s.strip()]
        if source not in old_sources:
            old_sources.append(source)
            changes.append(f"source:{source}")
        merged_source = "+".join(old_sources)

        if changes:
            old_history.append({
                "timestamp": now,
                "source": source,
                "matched_by": matched_by,
                "updated_fields": changes,
            })
            conn.execute(
                """
                UPDATE COMPANIES SET
                    city = ?, state = ?, region = ?, address = ?,
                    niche = ?, subniche = ?, category = ?, services_offered = ?,
                    google_rating = ?, google_reviews_count = ?, opening_hours = ?,
                    maps_url = ?, has_own_website = ?, has_instagram = ?,
                    source = ?, updated_at = ?, history_log = ?
                WHERE id = ?
                """,
                (
                    new_city, new_state, new_region, new_address,
                    new_niche, new_subniche, new_cat, json.dumps(merged_services, ensure_ascii=False),
                    new_rating, new_reviews, new_hours,
                    new_maps, new_own_web, new_has_ig,
                    merged_source, now, json.dumps(old_history, ensure_ascii=False),
                    company_id,
                ),
            )
            record_status = "updated"
        else:
            record_status = "duplicate"

    # Upsert CONTACTS
    p_norm = normalize_phone(whatsapp_raw or phone_raw)
    if p_norm or email or payload.get("contact_page_url"):
        existing_ct = conn.execute(
            "SELECT * FROM CONTACTS WHERE company_id = ? LIMIT 1",
            (company_id,),
        ).fetchone()
        if existing_ct is None:
            conn.execute(
                """
                INSERT INTO CONTACTS (
                    id, company_id, phone_raw, phone_normalized, whatsapp,
                    whatsapp_verified, email, contact_page_url, source, confidence, collected_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    new_id("ct"),
                    company_id,
                    phone_raw or whatsapp_raw,
                    p_norm,
                    whatsapp_raw or p_norm,
                    1 if payload.get("whatsapp_verified") else 0,
                    email,
                    payload.get("contact_page_url") or "",
                    source,
                    confidence,
                    now,
                ),
            )
        else:
            new_p_raw = existing_ct["phone_raw"] or phone_raw or whatsapp_raw
            new_p_norm = existing_ct["phone_normalized"] or p_norm
            new_wpp = existing_ct["whatsapp"] or whatsapp_raw or p_norm
            new_wpp_v = 1 if (existing_ct["whatsapp_verified"] or payload.get("whatsapp_verified")) else 0
            new_email = existing_ct["email"] or email
            new_cpage = existing_ct["contact_page_url"] or payload.get("contact_page_url") or ""
            if (new_p_norm != existing_ct["phone_normalized"]) or (new_email != existing_ct["email"]):
                if record_status == "duplicate":
                    record_status = "updated"
            conn.execute(
                """
                UPDATE CONTACTS SET
                    phone_raw = ?, phone_normalized = ?, whatsapp = ?,
                    whatsapp_verified = ?, email = ?, contact_page_url = ?, collected_at = ?
                WHERE id = ?
                """,
                (new_p_raw, new_p_norm, new_wpp, new_wpp_v, new_email, new_cpage, now, existing_ct["id"]),
            )

    # Upsert SOCIAL_PROFILES
    if ig_user:
        existing_sp = conn.execute(
            "SELECT * FROM SOCIAL_PROFILES WHERE company_id = ? AND LOWER(username) = ? LIMIT 1",
            (company_id, ig_user),
        ).fetchone()
        if existing_sp is None:
            conn.execute(
                """
                INSERT INTO SOCIAL_PROFILES (
                    id, company_id, platform, username, profile_name, profile_url,
                    biography, external_url, public_phone, public_email, category,
                    followers_count, posts_count, latest_post_date, is_business_account,
                    activity_indicators, source, confidence, collected_at
                ) VALUES (?, ?, 'instagram', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    new_id("sp"),
                    company_id,
                    ig_user,
                    payload.get("profile_name") or name,
                    payload.get("profile_url") or f"https://www.instagram.com/{ig_user}",
                    payload.get("biography") or "",
                    payload.get("external_url") or "",
                    phone_raw or whatsapp_raw,
                    email,
                    payload.get("business_category") or payload.get("category") or "",
                    payload.get("followers_count"),
                    payload.get("posts_count"),
                    payload.get("latest_post_date") or "",
                    1 if payload.get("is_business_account", True) else 0,
                    payload.get("activity_indicators") or "",
                    source,
                    confidence,
                    now,
                ),
            )
            if record_status == "duplicate":
                record_status = "updated"
        else:
            conn.execute(
                """
                UPDATE SOCIAL_PROFILES SET
                    biography = COALESCE(NULLIF(?, ''), biography),
                    external_url = COALESCE(NULLIF(?, ''), external_url),
                    followers_count = COALESCE(?, followers_count),
                    posts_count = COALESCE(?, posts_count),
                    latest_post_date = COALESCE(NULLIF(?, ''), latest_post_date),
                    activity_indicators = COALESCE(NULLIF(?, ''), activity_indicators),
                    collected_at = ?
                WHERE id = ?
                """,
                (
                    payload.get("biography") or "",
                    payload.get("external_url") or "",
                    payload.get("followers_count"),
                    payload.get("posts_count"),
                    payload.get("latest_post_date") or "",
                    payload.get("activity_indicators") or "",
                    now,
                    existing_sp["id"],
                ),
            )

    # Upsert WEBSITES
    if website_url and website_url not in ("—", "-"):
        existing_web = conn.execute(
            "SELECT * FROM WEBSITES WHERE company_id = ? LIMIT 1",
            (company_id,),
        ).fetchone()
        if existing_web is None:
            conn.execute(
                """
                INSERT INTO WEBSITES (
                    id, company_id, url, domain, link_category, link_type,
                    is_own_domain, http_status, final_url, source, confidence, collected_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    new_id("web"),
                    company_id,
                    website_url,
                    domain or website_url,
                    payload.get("link_category") or ("site_proprio" if own_domain_flag else "terceiro"),
                    payload.get("link_type") or ("Site próprio" if own_domain_flag else "Link externo"),
                    own_domain_flag,
                    payload.get("http_status"),
                    payload.get("final_url") or website_url,
                    source,
                    confidence,
                    now,
                ),
            )
            if record_status == "duplicate":
                record_status = "updated"

    return {
        "company_id": company_id,
        "status": record_status,
        "matched_by": matched_by,
    }
