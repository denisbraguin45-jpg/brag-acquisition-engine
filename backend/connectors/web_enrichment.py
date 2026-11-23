"""
Connector C — WEB ENRICHMENT (Section 3.C)
Researches and extracts publicly available institutional & contact information:
- Official website discovery (via DuckDuckGo HTML search + direct brand domain probing)
- Services & Products offered
- Contact page URL
- Public commercial email
- Public phones & WhatsApp
- Institutional summary

Never fabricates unknown data.
"""
import re
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from typing import Any, Optional

from backend.connectors.instagram import extract_services_from_text
from backend.deduplication import (
    THIRD_PARTY_DOMAINS,
    extract_domain,
    is_own_domain,
    normalize_phone,
    strip_accents,
)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
)


class _EnrichmentHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[tuple[str, str]] = []
        self._current_href: Optional[str] = None
        self._text_chunks: list[str] = []
        self.title: str = ""
        self._in_title = False
        self._skip_tags = {"script", "style", "noscript", "svg"}
        self._skip_depth = 0
        self.meta_description: str = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, Optional[str]]]) -> None:
        t = tag.lower()
        if t in self._skip_tags:
            self._skip_depth += 1
            return
        attr_map = {k.lower(): (v or "") for k, v in attrs}
        if t == "title":
            self._in_title = True
        elif t == "a" and "href" in attr_map:
            self._current_href = attr_map["href"]
        elif t == "meta":
            name_attr = attr_map.get("name", "").lower()
            prop_attr = attr_map.get("property", "").lower()
            if name_attr == "description" or prop_attr == "og:description":
                if not self.meta_description and attr_map.get("content"):
                    self.meta_description = attr_map["content"].strip()

    def handle_endtag(self, tag: str) -> None:
        t = tag.lower()
        if t in self._skip_tags and self._skip_depth > 0:
            self._skip_depth -= 1
        elif t == "title":
            self._in_title = False
        elif t == "a":
            self._current_href = None

    def handle_data(self, data: str) -> None:
        if self._skip_depth > 0:
            return
        cleaned = data.strip()
        if not cleaned:
            return
        if self._in_title and not self.title:
            self.title = cleaned
        self._text_chunks.append(cleaned)
        if self._current_href:
            self.links.append((self._current_href, cleaned))

    @property
    def full_text(self) -> str:
        return " ".join(self._text_chunks)


def fetch_url_html(url: str, timeout: float = 6.0) -> tuple[bool, int, str, str]:
    """
    Returns (ok, status_code, final_url, html_body).
    """
    if not url:
        return False, 0, "", ""
    target = url if re.match(r"^https?://", url, re.I) else f"https://{url}"
    req = urllib.request.Request(target, headers={"User-Agent": USER_AGENT, "Accept": "text/html,*/*"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            status = getattr(resp, "status", 200)
            final_url = resp.geturl() or target
            raw_bytes = resp.read(250_000)  # Cap read at 250KB for safety and speed
            html = raw_bytes.decode("utf-8", errors="ignore")
            return (status < 400), status, final_url, html
    except urllib.error.HTTPError as e:
        return False, e.code, target, ""
    except Exception:
        return False, 0, target, ""


def discover_official_website(
    company_name: str,
    city: str = "",
    username: str = "",
    timeout: float = 4.5,
) -> dict[str, Any]:
    """
    Ported from `instagram-lead-finder/lib/linkcheck.mjs` (`discoverExternalSite`).
    1. Searches DuckDuckGo HTML for `"company_name" city` and checks if a top result matches brand tokens on an own domain.
    2. Probes direct domain candidates (`<brand>.com.br`, `<brand>.com`) and verifies HTTP 200 without parking redirect.
    """
    clean_brand = re.split(r"[|•\-–—/]", company_name or "")[0].strip()
    brand_slug = re.sub(r"[^a-z0-9]", "", strip_accents(clean_brand).lower())
    user_slug = re.sub(r"[^a-z0-9]", "", strip_accents(username or "").lower())
    stripped_user = re.sub(r"(sp|rj|pr|sc|rs|mg|df|go|ba|pe|ce|br|oficial|official|carros|veiculos)$", "", user_slug) or user_slug

    tokens = [t for t in dict.fromkeys([user_slug, stripped_user, brand_slug]) if len(t) >= 4]
    if not tokens:
        return {"checked": False, "found": False, "url": "", "evidence": "Identificador curto para inferência"}

    # 1. DuckDuckGo HTML search
    if len(clean_brand) >= 3:
        q = f"{clean_brand} {city}".strip()
        ddg_url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(q)}"
        ok, _, _, html = fetch_url_html(ddg_url, timeout=timeout)
        if ok and html:
            matches = re.findall(r"uddg=([^&\"']+)", html)
            for encoded in matches[:8]:
                try:
                    candidate_url = urllib.parse.unquote(encoded)
                except Exception:
                    continue
                dom = extract_domain(candidate_url)
                if not dom or not is_own_domain(dom):
                    continue
                dom_base = re.sub(r"[^a-z0-9]", "", dom.split(".")[0])
                if any(t in dom_base or dom_base in t for t in tokens):
                    v_ok, v_status, v_final, _ = fetch_url_html(f"https://{dom}", timeout=timeout)
                    v_dom = extract_domain(v_final)
                    if v_ok and is_own_domain(v_dom) and not re.search(r"sedoparking|hugedomains|godaddy|afternic|dan\.com|parking", v_dom, re.I):
                        return {
                            "checked": True,
                            "found": True,
                            "url": v_final,
                            "http_status": v_status,
                            "evidence": f'Encontrado via busca web ("{q}") -> {v_dom}',
                        }

    # 2. Direct domain candidates (.com.br and .com)
    cand_slug = user_slug or brand_slug
    if len(cand_slug) >= 4:
        for tld in (".com.br", ".com"):
            cand_url = f"https://{cand_slug}{tld}"
            v_ok, v_status, v_final, _ = fetch_url_html(cand_url, timeout=3.5)
            if v_ok and v_final:
                v_dom = extract_domain(v_final)
                if v_dom and is_own_domain(v_dom) and not re.search(r"sedoparking|hugedomains|godaddy|afternic|dan\.com|parking", v_dom, re.I):
                    f_base = re.sub(r"[^a-z0-9]", "", v_dom.split(".")[0])
                    if any(t in f_base or f_base in t for t in tokens):
                        return {
                            "checked": True,
                            "found": True,
                            "url": v_final,
                            "http_status": v_status,
                            "evidence": f"Domínio direto ativo ({v_dom} HTTP {v_status})",
                        }

    return {
        "checked": True,
        "found": False,
        "url": "",
        "evidence": f'Busca externa ("{clean_brand}" {city}) + domínio direto sem resultado ativo',
    }


def enrich_from_website_html(html: str, base_url: str, niche: str = "") -> dict[str, Any]:
    """
    Parses website HTML to extract:
    - Services and products offered
    - Contact page URL
    - Commercial emails
    - Public phones and WhatsApp links
    - Institutional summary (title + meta description)
    """
    parser = _EnrichmentHTMLParser()
    try:
        parser.feed(html or "")
    except Exception:
        pass

    text = parser.full_text
    services = extract_services_from_text(f"{parser.title} {parser.meta_description} {text[:5000]}", niche)

    # Emails (filtering out generic asset/sentry/wix/example placeholders)
    emails_found = re.findall(r"([a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})", html or "")
    valid_emails = []
    for em in emails_found:
        em_low = em.lower()
        if any(bad in em_low for bad in (".png", ".jpg", ".svg", ".webp", "sentry", "wixpress", "example.com", "seuemail", "email.com")):
            continue
        if em_low not in valid_emails:
            valid_emails.append(em_low)

    # WhatsApp links
    whatsapp = ""
    contact_page_url = ""
    instagram_username = ""

    for href, anchor_text in parser.links:
        href_clean = href.strip()
        if not whatsapp:
            wa_m = re.search(r"(?:wa\.me/|api\.whatsapp\.com/send\?phone=|whatsapp\.com/send\?phone=)(\+?\d{10,15})", href_clean, re.I)
            if wa_m:
                whatsapp = normalize_phone(wa_m.group(1))
        if not instagram_username and "instagram.com/" in href_clean.lower():
            ig_m = re.search(r"instagram\.com/([a-zA-Z0-9._]{2,30})", href_clean, re.I)
            if ig_m and ig_m.group(1).lower() not in ("p", "reel", "explore", "stories", "share"):
                instagram_username = ig_m.group(1).lower()
        if not contact_page_url:
            if re.search(r"(contato|contact|fale-conosco|atendimento)", f"{href_clean} {anchor_text}", re.I):
                if not href_clean.startswith(("javascript:", "mailto:", "tel:", "#")):
                    contact_page_url = urllib.parse.urljoin(base_url, href_clean)

    # Phones in visible text
    phones_found = re.findall(
        r"(\(\d{2}\)\s*9?\d{4,5}[\- .\s]?\d{4}|\b\d{2}[\s.\-]9?\d{4}[\s.\-]\d{4}\b)",
        text[:10000],
    )
    phone = normalize_phone(phones_found[0]) if phones_found else ""

    return {
        "title": parser.title,
        "institutional_summary": parser.meta_description or parser.title,
        "services_offered": services,
        "email": valid_emails[0] if valid_emails else "",
        "phone": phone or whatsapp,
        "whatsapp": whatsapp,
        "whatsapp_verified": bool(whatsapp),
        "contact_page_url": contact_page_url,
        "instagram_username": instagram_username,
    }
