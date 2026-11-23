"""
Connector A — GOOGLE MAPS & PLACES (Section 3.A)
Searches for commercial establishments by niche and location:
- Commercial name
- Address
- Phone
- Website
- Reviews count & Rating
- Category
- Opening hours
- Coordinates & Location
- Establishment link

Strategy:
1. If GOOGLE_PLACES_API_KEY is configured in .env, uses official Google Places Text Search API (v1 / legacy json).
2. If GOOGLE_PLACES_API_KEY is not configured, transparently falls back to authorized open public geographical providers (OpenStreetMap Nominatim + Overpass API) combined with public web directory extraction, clearly recording `source` and `data_confidence` without inventing ratings or reviews.
"""
import json
import re
import time
import urllib.parse
import urllib.request
from typing import Any, Optional

from backend.config import get_config
from backend.deduplication import extract_domain, is_own_domain, strip_accents

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) BRAGLeadHunter/1.0"

# Mapping of BRAG niches to OSM tags & search terms
NICHE_OSM_QUERIES = {
    "P1": ["car", "car_dealership", "seminovos", "multimarcas", "veiculos"],
    "P2": ["car", "supercarros", "ferrari", "porsche", "lamborghini"],
    "P3": ["car", "importados", "blindados", "suv"],
    "P4": ["boat", "marine", "yacht", "lanchas", "nautica", "jetski"],
}


def _http_get_json(url: str, headers: Optional[dict[str, str]] = None, timeout: float = 10.0) -> Any:
    req_headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    if headers:
        req_headers.update(headers)
    req = urllib.request.Request(url, headers=req_headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8", errors="ignore"))


def _http_post_json(url: str, payload: dict[str, Any], headers: Optional[dict[str, str]] = None, timeout: float = 12.0) -> Any:
    req_headers = {
        "User-Agent": USER_AGENT,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    if headers:
        req_headers.update(headers)
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=req_headers, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8", errors="ignore"))


def search_google_places_official(
    query: str,
    city: str,
    state: str,
    country: str,
    niche: str,
    subniche: str,
    api_key: str,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """
    Calls official Google Places API (New v1 places:searchText or TextSearch JSON).
    """
    full_query = " ".join(p for p in [query or subniche or niche, city, state, country] if p).strip()
    results: list[dict[str, Any]] = []

    # Try Places API v1 (places:searchText)
    try:
        field_mask = (
            "places.id,places.displayName,places.formattedAddress,"
            "places.nationalPhoneNumber,places.internationalPhoneNumber,"
            "places.websiteUri,places.rating,places.userRatingCount,"
            "places.primaryTypeDisplayName,places.regularOpeningHours,"
            "places.location,places.googleMapsUri"
        )
        resp = _http_post_json(
            "https://places.googleapis.com/v1/places:searchText",
            {"textQuery": full_query, "maxResultCount": min(limit, 20), "languageCode": "pt-BR"},
            headers={"X-Goog-Api-Key": api_key, "X-Goog-FieldMask": field_mask},
        )
        for p in resp.get("places", [])[:limit]:
            name = (p.get("displayName") or {}).get("text") or ""
            if not name:
                continue
            website = p.get("websiteUri") or ""
            domain = extract_domain(website)
            own_site = bool(domain and is_own_domain(domain))
            hours_list = (p.get("regularOpeningHours") or {}).get("weekdayDescriptions") or []
            loc = p.get("location") or {}
            phone = p.get("internationalPhoneNumber") or p.get("nationalPhoneNumber") or ""
            results.append({
                "name": name,
                "address": p.get("formattedAddress") or "",
                "city": city,
                "state": state,
                "country": country or "Brasil",
                "phone": phone,
                "whatsapp": phone if re.search(r"\b9\d{4}[- ]?\d{4}\b", phone) else "",
                "website_url": website,
                "has_own_website": own_site,
                "google_rating": p.get("rating"),
                "google_reviews_count": p.get("userRatingCount"),
                "category": (p.get("primaryTypeDisplayName") or {}).get("text") or niche,
                "niche": niche,
                "subniche": subniche,
                "opening_hours": " | ".join(hours_list[:3]),
                "latitude": loc.get("latitude"),
                "longitude": loc.get("longitude"),
                "maps_url": p.get("googleMapsUri") or "",
                "source": "google_places_api",
                "confidence": "high",
            })
        if results:
            return results
    except Exception:
        pass

    # Fallback to legacy Maps TextSearch API if v1 is not enabled on the key
    encoded_q = urllib.parse.quote(full_query)
    legacy_url = f"https://maps.googleapis.com/maps/api/place/textsearch/json?query={encoded_q}&language=pt-BR&key={api_key}"
    resp = _http_get_json(legacy_url)
    for item in resp.get("results", [])[:limit]:
        place_id = item.get("place_id")
        details = {}
        if place_id:
            try:
                det_url = (
                    "https://maps.googleapis.com/maps/api/place/details/json"
                    f"?place_id={place_id}&fields=name,formatted_address,formatted_phone_number,"
                    f"international_phone_number,website,rating,user_ratings_total,opening_hours,url,geometry,types"
                    f"&language=pt-BR&key={api_key}"
                )
                det_resp = _http_get_json(det_url)
                details = det_resp.get("result") or {}
            except Exception:
                details = {}

        name = details.get("name") or item.get("name") or ""
        if not name:
            continue
        website = details.get("website") or ""
        domain = extract_domain(website)
        own_site = bool(domain and is_own_domain(domain))
        phone = details.get("international_phone_number") or details.get("formatted_phone_number") or ""
        hours = (details.get("opening_hours") or {}).get("weekday_text") or []
        loc = ((item.get("geometry") or {}).get("location")) or {}
        maps_url = details.get("url") or (f"https://www.google.com/maps/place/?q=place_id:{place_id}" if place_id else "")

        results.append({
            "name": name,
            "address": details.get("formatted_address") or item.get("formatted_address") or "",
            "city": city,
            "state": state,
            "country": country or "Brasil",
            "phone": phone,
            "whatsapp": phone if re.search(r"\b9\d{4}[- ]?\d{4}\b", phone) else "",
            "website_url": website,
            "has_own_website": own_site,
            "google_rating": details.get("rating") or item.get("rating"),
            "google_reviews_count": details.get("user_ratings_total") or item.get("user_ratings_total"),
            "category": ", ".join((item.get("types") or [])[:2]) or niche,
            "niche": niche,
            "subniche": subniche,
            "opening_hours": " | ".join(hours[:3]),
            "latitude": loc.get("lat"),
            "longitude": loc.get("lng"),
            "maps_url": maps_url,
            "source": "google_places_api",
            "confidence": "high",
        })

    return results


def search_open_maps_public(
    query: str,
    city: str,
    state: str,
    country: str,
    niche: str,
    subniche: str,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """
    Authorized open geographic search via OpenStreetMap Overpass & Nominatim APIs.
    Extracts real commercial POIs with coordinates, address, phone, website, and opening hours.
    Does not invent Google ratings/reviews (leaves None when not from Google Places).
    """
    results: list[dict[str, Any]] = []
    seen_names: set[str] = set()

    # 1. Geocode city bounding box via Nominatim
    loc_query = ", ".join(p for p in [city, state, country or "Brasil"] if p)
    bbox = None
    if loc_query:
        try:
            nom_url = f"https://nominatim.openstreetmap.org/search?q={urllib.parse.quote(loc_query)}&format=json&limit=1"
            nom_data = _http_get_json(nom_url, timeout=8.0)
            if nom_data and isinstance(nom_data, list) and "boundingbox" in nom_data[0]:
                # Nominatim boundingbox is [south, north, west, east]
                bb = [float(x) for x in nom_data[0]["boundingbox"]]
                bbox = (bb[0], bb[2], bb[1], bb[3])  # (south, west, north, east) for Overpass
        except Exception:
            bbox = None

    # 2. Query Overpass API for commercial establishments in that bounding box
    if bbox:
        south, west, north, east = bbox
        niche_norm = strip_accents(f"{niche} {subniche} {query}").lower()
        is_nautic = any(w in niche_norm for w in ("lancha", "nautic", "iate", "boat", "jet", "marine", "p4"))
        shop_filter = '"shop"~"car|boat|marine|yacht|motorcycle"' if is_nautic else '"shop"="car"'
        overpass_q = f"""
        [out:json][timeout:12];
        (
          node[{shop_filter}]({south},{west},{north},{east});
          way[{shop_filter}]({south},{west},{north},{east});
        );
        out center {min(limit * 2, 50)};
        """
        try:
            ov_url = "https://overpass-api.de/api/interpreter?data=" + urllib.parse.quote(overpass_q.strip())
            ov_data = _http_get_json(ov_url, timeout=12.0)
            for el in ov_data.get("elements", []):
                tags = el.get("tags") or {}
                name = (tags.get("name") or tags.get("brand") or "").strip()
                if not name or name.lower() in seen_names:
                    continue
                seen_names.add(name.lower())

                lat = el.get("lat") or (el.get("center") or {}).get("lat")
                lon = el.get("lon") or (el.get("center") or {}).get("lon")
                street = tags.get("addr:street") or ""
                housenumber = tags.get("addr:housenumber") or ""
                suburb = tags.get("addr:suburb") or ""
                addr_city = tags.get("addr:city") or city
                address_parts = [p for p in [f"{street} {housenumber}".strip(), suburb, addr_city, state] if p]
                address = ", ".join(address_parts)

                phone = (
                    tags.get("contact:phone")
                    or tags.get("phone")
                    or tags.get("contact:mobile")
                    or tags.get("contact:whatsapp")
                    or ""
                )
                whatsapp = tags.get("contact:whatsapp") or (
                    phone if re.search(r"\b9\d{4}[- ]?\d{4}\b", phone) else ""
                )
                email = tags.get("contact:email") or tags.get("email") or ""
                website = tags.get("contact:website") or tags.get("website") or tags.get("url") or ""
                ig = tags.get("contact:instagram") or ""
                if ig and "instagram.com/" in ig:
                    ig = ig.rstrip("/").split("instagram.com/")[-1].split("?")[0]

                domain = extract_domain(website)
                own_site = bool(domain and is_own_domain(domain))
                maps_link = (
                    f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(name + ' ' + addr_city)}"
                    if name else ""
                )

                results.append({
                    "name": name,
                    "address": address,
                    "city": addr_city or city,
                    "state": state,
                    "country": country or "Brasil",
                    "phone": phone,
                    "whatsapp": whatsapp,
                    "email": email,
                    "instagram_username": ig,
                    "website_url": website,
                    "has_own_website": own_site,
                    "google_rating": None,
                    "google_reviews_count": None,
                    "category": tags.get("shop") or niche or "Automotivo / Concessionária",
                    "niche": niche or "P1 — Revendas premium e multimarcas",
                    "subniche": subniche,
                    "opening_hours": tags.get("opening_hours") or "",
                    "latitude": lat,
                    "longitude": lon,
                    "maps_url": maps_link,
                    "source": "maps_osm_overpass",
                    "confidence": "high",
                })
                if len(results) >= limit:
                    break
        except Exception:
            pass

    # 3. Also run Nominatim direct text search if more results needed
    if len(results) < limit:
        search_terms = [q for q in [query, subniche, "concessionaria veiculos", "seminovos", "multimarcas"] if q]
        for term in search_terms[:2]:
            if len(results) >= limit:
                break
            q_str = ", ".join(p for p in [term, city, state, country or "Brasil"] if p)
            try:
                nom_url = (
                    f"https://nominatim.openstreetmap.org/search?q={urllib.parse.quote(q_str)}"
                    f"&format=json&addressdetails=1&extratags=1&limit={limit}"
                )
                items = _http_get_json(nom_url, timeout=8.0)
                for it in items:
                    name = (it.get("name") or (it.get("display_name") or "").split(",")[0]).strip()
                    if not name or name.lower() in seen_names or name.lower() == city.lower():
                        continue
                    seen_names.add(name.lower())
                    extratags = it.get("extratags") or {}
                    addr = it.get("address") or {}
                    phone = extratags.get("contact:phone") or extratags.get("phone") or ""
                    website = extratags.get("contact:website") or extratags.get("website") or ""
                    domain = extract_domain(website)
                    own_site = bool(domain and is_own_domain(domain))
                    lat = float(it["lat"]) if "lat" in it else None
                    lon = float(it["lon"]) if "lon" in it else None
                    maps_link = f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(name + ' ' + city)}"

                    results.append({
                        "name": name,
                        "address": it.get("display_name") or "",
                        "city": addr.get("city") or addr.get("town") or city,
                        "state": addr.get("state") or state,
                        "country": addr.get("country") or country or "Brasil",
                        "phone": phone,
                        "whatsapp": extratags.get("contact:whatsapp") or "",
                        "website_url": website,
                        "has_own_website": own_site,
                        "google_rating": None,
                        "google_reviews_count": None,
                        "category": it.get("type") or niche,
                        "niche": niche or "P1 — Revendas premium e multimarcas",
                        "subniche": subniche,
                        "opening_hours": extratags.get("opening_hours") or "",
                        "latitude": lat,
                        "longitude": lon,
                        "maps_url": maps_link,
                        "source": "maps_nominatim",
                        "confidence": "medium",
                    })
                    if len(results) >= limit:
                        break
                time.sleep(0.5)
            except Exception:
                pass

    return results[:limit]


def search_maps_establishments(
    niche: str,
    subniche: str = "",
    city: str = "São Paulo",
    state: str = "SP",
    country: str = "Brasil",
    query: str = "",
    limit: int = 20,
    min_rating: Optional[float] = None,
    min_reviews: Optional[int] = None,
) -> dict[str, Any]:
    """
    Main entrypoint for Connector A (Google Maps).
    Uses Google Places API if GOOGLE_PLACES_API_KEY is present, otherwise OpenStreetMap Overpass/Nominatim.
    Applies rating/reviews filters when rating data is available.
    """
    cfg = get_config()
    api_key = cfg.get("google_places_api_key") or ""
    provider_used = "google_places_api" if api_key else "maps_osm_overpass"
    warning = None

    items: list[dict[str, Any]] = []
    if api_key:
        try:
            items = search_google_places_official(
                query=query,
                city=city,
                state=state,
                country=country,
                niche=niche,
                subniche=subniche,
                api_key=api_key,
                limit=limit,
            )
        except Exception as e:
            warning = f"Google Places API falhou ({e}); utilizando conector geográfico aberto (OSM Overpass/Nominatim)."
            provider_used = "maps_osm_overpass"

    if not items:
        items = search_open_maps_public(
            query=query,
            city=city,
            state=state,
            country=country,
            niche=niche,
            subniche=subniche,
            limit=limit,
        )

    # Filter by min_rating and min_reviews when present
    filtered: list[dict[str, Any]] = []
    for it in items:
        if min_rating is not None and it.get("google_rating") is not None:
            if float(it["google_rating"]) < float(min_rating):
                continue
        if min_reviews is not None and it.get("google_reviews_count") is not None:
            if int(it["google_reviews_count"]) < int(min_reviews):
                continue
        filtered.append(it)

    return {
        "provider": provider_used,
        "warning": warning,
        "count": len(filtered),
        "items": filtered,
    }
