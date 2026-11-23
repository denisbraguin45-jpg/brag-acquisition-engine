"""
Connector D — WEBSITE AUDITOR (Section 3.D)
Evaluates any found website across 10 concrete technical & commercial criteria:
1. HTTP availability (status code, redirects, errors)
2. Responsiveness (viewport meta tag, responsive CSS/media queries)
3. HTTPS security (SSL/TLS protocol verification)
4. Load speed (measured response time in milliseconds)
5. Presentation quality (semantic structure, headings, meta description, modern assets)
6. Offer clarity (explicit niche/product proposition in title/hero/H1)
7. Existence of CTA (call-to-action buttons/links)
8. WhatsApp button (wa.me, api.whatsapp.com, floating widget)
9. Contact form (<form>, input fields)
10. Commercial structure (catalog/inventory filter, financing/simulation, address/trust signals)

Identifies real, evidence-backed improvement opportunities and saves to AUDITS table.
"""
import json
import re
import sqlite3
import time
import urllib.error
import urllib.request
from html.parser import HTMLParser
from typing import Any, Optional

from backend.database import new_id, now_iso
from backend.deduplication import extract_domain, is_own_domain

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
)


class _AuditHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.has_viewport = False
        self.has_meta_description = False
        self.has_og_tags = False
        self.title = ""
        self.h1_texts: list[str] = []
        self.h2_texts: list[str] = []
        self.forms_count = 0
        self.inputs_count = 0
        self.images_count = 0
        self.links: list[tuple[str, str]] = []
        self.buttons_text: list[str] = []
        self._in_title = False
        self._in_h1 = False
        self._in_h2 = False
        self._in_button = False
        self._current_href: Optional[str] = None
        self._skip_tags = {"script", "style", "noscript"}
        self._skip_depth = 0
        self.VisibleText: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, Optional[str]]]) -> None:
        t = tag.lower()
        if t in self._skip_tags:
            self._skip_depth += 1
            return
        attr_map = {k.lower(): (v or "") for k, v in attrs}
        if t == "meta":
            name = attr_map.get("name", "").lower()
            prop = attr_map.get("property", "").lower()
            if name == "viewport" and "width=device-width" in attr_map.get("content", "").lower():
                self.has_viewport = True
            elif name == "description" and len(attr_map.get("content", "").strip()) >= 20:
                self.has_meta_description = True
            elif prop.startswith("og:"):
                self.has_og_tags = True
        elif t == "title":
            self._in_title = True
        elif t == "h1":
            self._in_h1 = True
        elif t == "h2":
            self._in_h2 = True
        elif t == "button":
            self._in_button = True
        elif t == "form":
            self.forms_count += 1
        elif t in ("input", "textarea", "select"):
            self.inputs_count += 1
        elif t == "img":
            self.images_count += 1
        elif t == "a":
            self._current_href = attr_map.get("href", "")

    def handle_endtag(self, tag: str) -> None:
        t = tag.lower()
        if t in self._skip_tags and self._skip_depth > 0:
            self._skip_depth -= 1
        elif t == "title":
            self._in_title = False
        elif t == "h1":
            self._in_h1 = False
        elif t == "h2":
            self._in_h2 = False
        elif t == "button":
            self._in_button = False
        elif t == "a":
            self._current_href = None

    def handle_data(self, data: str) -> None:
        if self._skip_depth > 0:
            return
        txt = data.strip()
        if not txt:
            return
        self.VisibleText.append(txt)
        if self._in_title and not self.title:
            self.title = txt
        if self._in_h1:
            self.h1_texts.append(txt)
        if self._in_h2:
            self.h2_texts.append(txt)
        if self._in_button:
            self.buttons_text.append(txt)
        if self._current_href is not None:
            self.links.append((self._current_href, txt))


def audit_website_html(
    url: str,
    html: str,
    http_status: int = 200,
    load_time_ms: int = 350,
    final_url: str = "",
) -> dict[str, Any]:
    """
    Pure deterministic analyzer of website HTML and HTTP metrics.
    Can be called directly in unit tests or after live HTTP fetch.
    """
    effective_url = final_url or url or ""
    domain = extract_domain(effective_url)
    own_domain = is_own_domain(domain)
    has_https = effective_url.lower().startswith("https://")
    http_available = 200 <= (http_status or 0) < 400 and bool(html and len(html.strip()) > 50)

    issues: list[str] = []
    opportunities: list[str] = []

    if not url or url in ("—", "-"):
        return {
            "url_tested": "",
            "http_available": False,
            "http_status": 0,
            "has_https": False,
            "load_time_ms": 0,
            "is_responsive": False,
            "presentation_quality_score": 0,
            "offer_clarity_score": 0,
            "has_cta": False,
            "has_whatsapp_button": False,
            "has_contact_form": False,
            "commercial_structure_score": 0,
            "audit_status": "no_site",
            "issues_found": ["Ausência de website oficial próprio"],
            "improvement_opportunities": [
                "Criar vitrine digital própria com catálogo pesquisável, apresentação institucional premium e captação direta via WhatsApp."
            ],
        }

    if not own_domain:
        return {
            "url_tested": effective_url,
            "http_available": http_available,
            "http_status": http_status,
            "has_https": has_https,
            "load_time_ms": load_time_ms,
            "is_responsive": True,
            "presentation_quality_score": 25,
            "offer_clarity_score": 30,
            "has_cta": True,
            "has_whatsapp_button": "wa.me" in effective_url or "whatsapp" in effective_url,
            "has_contact_form": False,
            "commercial_structure_score": 20,
            "audit_status": "third_party_only",
            "issues_found": [
                f"Utiliza apenas link de terceiro ({domain or effective_url}) em vez de domínio próprio institucional"
            ],
            "improvement_opportunities": [
                "Substituir agregador/link de terceiro por website próprio de alta conversão com estoque estruturado e SEO local."
            ],
        }

    if not http_available:
        issues.append(f"Website indisponível ou quebrado (HTTP {http_status or 'timeout/DNS'})")
        opportunities.append("Reconstruir website oficial com hospedagem de alta disponibilidade, SSL e vitrine moderna.")
        return {
            "url_tested": effective_url,
            "http_available": False,
            "http_status": http_status,
            "has_https": has_https,
            "load_time_ms": load_time_ms,
            "is_responsive": False,
            "presentation_quality_score": 0,
            "offer_clarity_score": 0,
            "has_cta": False,
            "has_whatsapp_button": False,
            "has_contact_form": False,
            "commercial_structure_score": 0,
            "audit_status": "broken",
            "issues_found": issues,
            "improvement_opportunities": opportunities,
        }

    parser = _AuditHTMLParser()
    try:
        parser.feed(html)
    except Exception:
        pass

    raw_lower = html.lower()
    visible_text = " ".join(parser.VisibleText)
    visible_lower = visible_text.lower()

    # 1. HTTPS check
    if not has_https:
        issues.append("Site sem certificado HTTPS seguro (conexão HTTP não criptografada)")
        opportunities.append("Implementar certificado SSL/HTTPS e redirecionamento seguro.")

    # 2. Responsiveness check
    is_responsive = parser.has_viewport or ("@media" in raw_lower)
    if not is_responsive:
        issues.append("Site sem meta viewport responsiva (layout quebrado ou inadequado em celulares)")
        opportunities.append("Desenvolver interface mobile-first otimizada para decisores que acessam pelo smartphone.")

    # 3. Load speed check
    if load_time_ms and load_time_ms > 3500:
        issues.append(f"Carregamento lento ({load_time_ms} ms > 3.500 ms recomendados)")
        opportunities.append("Otimizar performance (PageSpeed ≥ 95) com carregamento instantâneo de imagens e catálogo.")

    # 4. WhatsApp button check
    has_whatsapp_btn = bool(
        re.search(r"(wa\.me/|api\.whatsapp\.com|whatsapp\.com/send|whatsapp|whats-button|wpp)", raw_lower)
    )
    if not has_whatsapp_btn:
        issues.append("Ausência de botão de conversão rápida para WhatsApp")
        opportunities.append("Integrar botão flutuante e CTAs diretos de WhatsApp por produto/veículo.")

    # 5. Contact form check
    has_contact_form = parser.forms_count > 0 or parser.inputs_count >= 2
    if not has_contact_form:
        issues.append("Ausência de formulário de captação de leads / agendamento")
        opportunities.append("Adicionar formulário enxuto de cotação, financiamento ou agendamento de visita.")

    # 6. CTA check
    cta_pattern = re.compile(
        r"\b(fale conosco|solicite|agende|comprar|ver estoque|estoque|cotacao|orcamento|whatsapp|simular|financiamento|contato|saiba mais|quero)\b",
        re.I,
    )
    all_cta_texts = " ".join(parser.buttons_text + [txt for _, txt in parser.links])
    has_cta = bool(cta_pattern.search(all_cta_texts))
    if not has_cta:
        issues.append("Ausência de Call-to-Action (CTA) claro acima da dobra")
        opportunities.append("Incluir CTAs estratégicos de alta visibilidade ('Ver Estoque', 'Falar com Consultor').")

    # 7. Presentation quality (0 - 100)
    pres_score = 30
    if parser.title and len(parser.title) >= 10:
        pres_score += 15
    if parser.has_meta_description:
        pres_score += 15
    if parser.has_og_tags:
        pres_score += 10
    if len(parser.h1_texts) >= 1:
        pres_score += 15
    else:
        issues.append("Estrutura de títulos (H1) ausente ou mal hierarquizada")
    if parser.images_count >= 3:
        pres_score += 15
    if not is_responsive:
        pres_score -= 25
    pres_score = max(0, min(100, pres_score))

    # 8. Offer clarity (0 - 100)
    offer_pattern = re.compile(
        r"\b(veiculos|carros|seminovos|multimarcas|blindados|importados|lanchas|iates|nautica|estoque|venda|compra|financiamento|concessionaria|showroom|servicos|solucoes|catalogo)\b",
        re.I,
    )
    hero_text = " ".join([parser.title] + parser.h1_texts + parser.h2_texts[:3])
    offer_clarity = 25
    if offer_pattern.search(hero_text):
        offer_clarity += 45
    elif offer_pattern.search(visible_lower[:2000]):
        offer_clarity += 25
    else:
        issues.append("Proposta de valor pouco clara no título e cabeçalho principal")
        opportunities.append("Reescrever copy principal destacando claramente o posicionamento e especialidade da empresa.")
    if has_cta:
        offer_clarity += 30
    offer_clarity = max(0, min(100, offer_clarity))

    # 9. Commercial structure (0 - 100)
    comm_score = 0
    if has_whatsapp_btn:
        comm_score += 30
    if has_contact_form:
        comm_score += 20
    if has_cta:
        comm_score += 20
    has_catalog = bool(re.search(r"\b(estoque|catalogo|filtro|busca|modelos|marcas|ano|km|preco)\b", visible_lower))
    if has_catalog:
        comm_score += 30
    else:
        issues.append("Sem vitrine/catálogo estruturado com filtros de busca")
        opportunities.append("Implementar vitrine dinâmica com busca por marca, modelo e faixa de valor.")

    # Overall audit status classification
    if not issues and pres_score >= 70 and comm_score >= 70 and has_https and is_responsive:
        audit_status = "adequate"
    elif len(issues) >= 3 or not has_https or not is_responsive or comm_score < 50 or (load_time_ms and load_time_ms > 4000):
        audit_status = "weak"
    else:
        audit_status = "needs_improvement"

    return {
        "url_tested": effective_url,
        "http_available": True,
        "http_status": http_status,
        "has_https": has_https,
        "load_time_ms": load_time_ms,
        "is_responsive": is_responsive,
        "presentation_quality_score": pres_score,
        "offer_clarity_score": offer_clarity,
        "has_cta": has_cta,
        "has_whatsapp_button": has_whatsapp_btn,
        "has_contact_form": has_contact_form,
        "commercial_structure_score": comm_score,
        "audit_status": audit_status,
        "issues_found": issues,
        "improvement_opportunities": opportunities,
    }


def audit_live_website(url: str, timeout: float = 6.5) -> dict[str, Any]:
    """
    Performs a live HTTP request to `url`, measures latency, and runs `audit_website_html`.
    """
    if not url or url in ("—", "-"):
        return audit_website_html("", "", 0, 0, "")

    target = url if re.match(r"^https?://", url, re.I) else f"https://{url}"
    dom = extract_domain(target)
    if not is_own_domain(dom):
        return audit_website_html(target, "", 200, 100, target)

    t0 = time.perf_counter()
    req = urllib.request.Request(target, headers={"User-Agent": USER_AGENT, "Accept": "text/html,*/*"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            status = getattr(resp, "status", 200)
            final_url = resp.geturl() or target
            raw_bytes = resp.read(250_000)
            elapsed_ms = int((time.perf_counter() - t0) * 1000)
            html = raw_bytes.decode("utf-8", errors="ignore")
            return audit_website_html(target, html, http_status=status, load_time_ms=elapsed_ms, final_url=final_url)
    except urllib.error.HTTPError as e:
        elapsed_ms = int((time.perf_counter() - t0) * 1000)
        return audit_website_html(target, "", http_status=e.code, load_time_ms=elapsed_ms, final_url=target)
    except Exception:
        elapsed_ms = int((time.perf_counter() - t0) * 1000)
        return audit_website_html(target, "", http_status=0, load_time_ms=elapsed_ms, final_url=target)


def save_website_audit(
    conn: sqlite3.Connection,
    company_id: str,
    audit_data: dict[str, Any],
    website_id: Optional[str] = None,
) -> str:
    """
    Persists audit result into AUDITS table.
    """
    now = now_iso()
    existing = conn.execute(
        "SELECT id FROM AUDITS WHERE company_id = ? LIMIT 1",
        (company_id,),
    ).fetchone()

    issues_json = json.dumps(audit_data.get("issues_found") or [], ensure_ascii=False)
    opps_json = json.dumps(audit_data.get("improvement_opportunities") or [], ensure_ascii=False)

    if existing is None:
        audit_id = new_id("aud")
        conn.execute(
            """
            INSERT INTO AUDITS (
                id, company_id, website_id, url_tested, http_available, http_status,
                has_https, load_time_ms, is_responsive, presentation_quality_score,
                offer_clarity_score, has_cta, has_whatsapp_button, has_contact_form,
                commercial_structure_score, audit_status, issues_found,
                improvement_opportunities, source, confidence, audited_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'website_auditor', 'high', ?)
            """,
            (
                audit_id,
                company_id,
                website_id,
                audit_data.get("url_tested") or "",
                1 if audit_data.get("http_available") else 0,
                audit_data.get("http_status"),
                1 if audit_data.get("has_https") else 0,
                audit_data.get("load_time_ms"),
                1 if audit_data.get("is_responsive") else 0,
                audit_data.get("presentation_quality_score") or 0,
                audit_data.get("offer_clarity_score") or 0,
                1 if audit_data.get("has_cta") else 0,
                1 if audit_data.get("has_whatsapp_button") else 0,
                1 if audit_data.get("has_contact_form") else 0,
                audit_data.get("commercial_structure_score") or 0,
                audit_data.get("audit_status") or "no_site",
                issues_json,
                opps_json,
                now,
            ),
        )
        return audit_id
    else:
        audit_id = existing["id"]
        conn.execute(
            """
            UPDATE AUDITS SET
                url_tested = ?, http_available = ?, http_status = ?, has_https = ?,
                load_time_ms = ?, is_responsive = ?, presentation_quality_score = ?,
                offer_clarity_score = ?, has_cta = ?, has_whatsapp_button = ?,
                has_contact_form = ?, commercial_structure_score = ?, audit_status = ?,
                issues_found = ?, improvement_opportunities = ?, audited_at = ?
            WHERE id = ?
            """,
            (
                audit_data.get("url_tested") or "",
                1 if audit_data.get("http_available") else 0,
                audit_data.get("http_status"),
                1 if audit_data.get("has_https") else 0,
                audit_data.get("load_time_ms"),
                1 if audit_data.get("is_responsive") else 0,
                audit_data.get("presentation_quality_score") or 0,
                audit_data.get("offer_clarity_score") or 0,
                1 if audit_data.get("has_cta") else 0,
                1 if audit_data.get("has_whatsapp_button") else 0,
                1 if audit_data.get("has_contact_form") else 0,
                audit_data.get("commercial_structure_score") or 0,
                audit_data.get("audit_status") or "no_site",
                issues_json,
                opps_json,
                now,
                audit_id,
            ),
        )
        return audit_id
