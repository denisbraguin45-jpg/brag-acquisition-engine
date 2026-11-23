import json
from pathlib import Path

crm_json_path = Path("D:/app/brag-lead-hunter/demos/crm_all_leads.json")
with open(crm_json_path, "r", encoding="utf-8") as f:
    crm_leads = json.load(f)

crm_leads_json = json.dumps(crm_leads, ensure_ascii=False)

html_content = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>BRAG CRM — Base Completa de Contatos com Demos (Recuperação WhatsApp)</title>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@600;700;800&family=DM+Sans:ital,opsz,wght@0,9..40,100..1000;1,9..40,100..1000&family=JetBrains+Mono:wght@400;500;600;700&display=swap" rel="stylesheet" />
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
      --font-sans: 'DM Sans', sans-serif;
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
      color: var(--color-gold);
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
      grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
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
    .badge-online {{
      display: inline-block;
      padding: 0.15rem 0.55rem;
      background: rgba(16, 185, 129, 0.16);
      border: 1px solid rgba(16, 185, 129, 0.4);
      color: #34d399;
      font-size: 0.7rem;
      font-family: var(--font-mono);
      font-weight: 600;
    }}
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
        <div class="eyebrow">BRAG INTERNATIONAL · CRM UNIFICADO DE RECUPERAÇÃO</div>
        <h1>Todos os Leads com Demos Criadas</h1>
        <p class="sub">Central consolidada com <strong>todos os 328 leads</strong> que possuem showroom e demonstração funcional ativa na Vercel. Ideal para recuperação imediata de contatos após perda de acesso ao WhatsApp.</p>
      </div>
      <div class="actions-top">
        <a href="crm_all_leads.csv" download class="btn-top btn-top-gold">
          📥 Baixar Planilha CSV Completa
        </a>
        <a href="crm_all_leads.json" download class="btn-top">
          📄 Baixar JSON
        </a>
        <a href="index.html" class="btn-top">
          ⚡ Ir para Fila Ativa (60 Demos)
        </a>
      </div>
    </header>

    <!-- WORKSPACE TABS -->
    <div class="partner-switcher" role="tablist" aria-label="Seleção de Filtro por Responsável">
      <button type="button" id="tabBtnDenis" class="partner-tab active-denis" onclick="setFilter('denis')">
        <span class="partner-tab-kicker">CARTEIRA DENIS (TODOS OS LOTES)</span>
        <span class="partner-tab-title">Leads Denis (298)</span>
        <div class="partner-tab-meta">
          <span>298 Demos &amp; Telefones</span>
          <span style="color:#ff9d72;">Filtro: Denis</span>
        </div>
      </button>

      <button type="button" id="tabBtnGabriel" class="partner-tab" onclick="setFilter('gabriel')">
        <span class="partner-tab-kicker">CARTEIRA GABRIEL (SÓCIO)</span>
        <span class="partner-tab-title">Leads Gabriel (30)</span>
        <div class="partner-tab-meta">
          <span>30 Demos &amp; Telefones</span>
          <span style="color:#93c5fd;">Filtro: Gabriel</span>
        </div>
      </button>

      <button type="button" id="tabBtnAll" class="partner-tab" onclick="setFilter('all')">
        <span class="partner-tab-kicker">BASE GLOBAL CONSOLIDADA</span>
        <span class="partner-tab-title">Todos os 328 Leads</span>
        <div class="partner-tab-meta">
          <span>328 Demos Online na Vercel</span>
          <span style="color:#10b981;">Total Geral</span>
        </div>
      </button>
    </div>

    <div class="toolbar">
      <div style="display:flex;align-items:center;gap:0.75rem;flex-wrap:wrap;">
        <input type="search" id="crmSearch" class="search-input" placeholder="Buscar por loja, telefone, cidade, UF ou @instagram..." oninput="renderTable()" />
      </div>
      <div class="kpi-pills">
        <div class="kpi-pill">Mostrando: <strong id="kpiCount">0</strong> leads</div>
        <div class="kpi-pill">Total com WhatsApp: <strong style="color:#10b981;">328/328 (100%)</strong></div>
        <div class="kpi-pill">Status Vercel: <strong style="color:#34d399;">328/328 Online</strong></div>
      </div>
    </div>

    <main>
      <table>
        <thead>
          <tr>
            <th>#</th>
            <th>Responsável</th>
            <th>Loja / Concessionária</th>
            <th>Cidade &amp; Estado</th>
            <th>Instagram</th>
            <th>WhatsApp &amp; Telefone</th>
            <th>Status Demo Vercel</th>
            <th>Ações de Contato Rápido</th>
          </tr>
        </thead>
        <tbody id="crmTableBody"></tbody>
      </table>
      <div id="emptyNotice" class="empty-state" style="display:none;">
        Nenhum lead encontrado para os critérios de busca digitados.
      </div>
    </main>
  </div>

  <!-- Modal Roteiro & Mensagem -->
  <div id="scriptModal" class="modal-backdrop" onclick="if(event.target===this) closeScriptModal()">
    <div class="modal-box">
      <div style="display:flex;justify-content:space-between;align-items:center;gap:1rem;border-bottom:1px solid var(--border-subtle);padding-bottom:0.75rem;">
        <h2 id="modalTitle" style="font-family:var(--font-display);font-size:1.4rem;text-transform:uppercase;letter-spacing:0.08em;">Recuperação de Contato WhatsApp</h2>
        <button type="button" class="btn-ghost" onclick="closeScriptModal()">Fechar</button>
      </div>
      <div style="margin-top:1rem;">
        <div style="display:flex;justify-content:space-between;align-items:center;">
          <strong style="font-size:0.8rem;text-transform:uppercase;letter-spacing:0.12em;color:var(--color-gold);">Mensagem Pronta para Envio</strong>
          <button type="button" class="btn-ghost" id="modalCopyMsgBtn">Copiar Mensagem</button>
        </div>
        <pre id="modalMsgPre" class="modal-pre"></pre>
      </div>
      <div style="margin-top:1.25rem;display:flex;justify-content:flex-end;gap:0.75rem;">
        <a id="modalWaBtn" href="#" target="_blank" rel="noopener" class="btn-wa">Abrir Conversa no WhatsApp Web</a>
        <button type="button" class="btn-ghost" onclick="closeScriptModal()">Concluído</button>
      </div>
    </div>
  </div>

  <script>
    const CRM_LEADS = {crm_leads_json};
    let currentFilter = "denis";

    function setFilter(filt) {{
      currentFilter = filt;
      document.getElementById("tabBtnDenis").className = "partner-tab" + (filt === "denis" ? " active-denis" : "");
      document.getElementById("tabBtnGabriel").className = "partner-tab" + (filt === "gabriel" ? " active-gabriel" : "");
      document.getElementById("tabBtnAll").className = "partner-tab" + (filt === "all" ? " active-all" : "");
      renderTable();
    }}

    function copyMsg(slug) {{
      const item = CRM_LEADS.find(x => x.slug === slug);
      if (!item) return;
      navigator.clipboard.writeText(item.whatsapp_message);
      alert("Mensagem copiada para " + item.name + "!");
    }}

    function openModal(slug) {{
      const item = CRM_LEADS.find(x => x.slug === slug);
      if (!item) return;
      document.getElementById("modalTitle").textContent = `${{item.name}} — ${{item.phone_display}}`;
      document.getElementById("modalMsgPre").textContent = item.whatsapp_message;
      document.getElementById("modalCopyMsgBtn").onclick = () => copyMsg(slug);
      document.getElementById("modalWaBtn").href = item.whatsapp_send_url || `https://wa.me/${{item.whatsapp_e164}}`;
      document.getElementById("scriptModal").classList.add("open");
    }}

    function closeScriptModal() {{
      document.getElementById("scriptModal").classList.remove("open");
    }}

    function escapeHtml(str) {{
      return String(str || "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;");
    }}

    function renderTable() {{
      const q = (document.getElementById("crmSearch").value || "").toLowerCase().trim();
      const filtered = CRM_LEADS.filter(d => {{
        if (currentFilter !== "all" && d.owner !== currentFilter) return false;
        if (!q) return true;
        const hay = `${{d.name}} ${{d.city}} ${{d.state}} ${{d.instagram_username}} ${{d.phone_display}} ${{d.whatsapp_e164}} ${{d.slug}}`.toLowerCase();
        return hay.includes(q);
      }});

      document.getElementById("kpiCount").textContent = String(filtered.length);
      const tbody = document.getElementById("crmTableBody");
      const emptyNotice = document.getElementById("emptyNotice");

      if (filtered.length === 0) {{
        tbody.innerHTML = "";
        emptyNotice.style.display = "block";
        return;
      }}
      emptyNotice.style.display = "none";

      tbody.innerHTML = filtered.map((d, idx) => {{
        const ownerBadge = d.owner === "denis"
          ? `<span class="badge-owner-denis">Denis</span>`
          : `<span class="badge-owner-gabriel">Gabriel</span>`;
        
        const igHtml = d.instagram_username
          ? `<a href="${{escapeHtml(d.instagram_url)}}" target="_blank" rel="noopener" style="color:var(--color-accent);text-decoration:none;">@${{escapeHtml(d.instagram_username)}}</a>`
          : `<span style="color:var(--color-text-secondary);">-</span>`;

        return `
          <tr>
            <td class="tabular" style="color:var(--color-text-secondary);font-size:0.8rem;">#${{String(idx + 1).padStart(3, '0')}}</td>
            <td>${{ownerBadge}}</td>
            <td>
              <strong style="font-size:1.02rem;font-family:var(--font-display);letter-spacing:0.06em;text-transform:uppercase;">${{escapeHtml(d.name)}}</strong>
              <div style="font-size:0.74rem;color:var(--color-text-secondary);font-family:var(--font-mono);">${{escapeHtml(d.slug)}}</div>
            </td>
            <td>
              <div><strong>${{escapeHtml(d.city || "Brasil")}}</strong> · ${{escapeHtml(d.state || "BR")}}</div>
            </td>
            <td>${{igHtml}}</td>
            <td class="tabular">
              <div style="color:#10b981;font-weight:700;font-size:0.88rem;">${{escapeHtml(d.phone_display)}}</div>
              <div style="font-size:0.72rem;color:var(--color-text-secondary);font-family:var(--font-mono);">+${{escapeHtml(d.whatsapp_e164)}}</div>
            </td>
            <td>
              <span class="badge-online">● Online na Vercel</span>
            </td>
            <td>
              <div style="display:flex;gap:0.4rem;flex-wrap:wrap;">
                <a href="${{escapeHtml(d.demo_url)}}" target="_blank" rel="noopener" class="btn-ag">Abrir Demo</a>
                <a href="${{escapeHtml(d.whatsapp_send_url || ('https://wa.me/' + d.whatsapp_e164))}}" target="_blank" rel="noopener" class="btn-wa">Chamar no WhatsApp</a>
                <button type="button" class="btn-ghost" onclick="copyMsg('${{escapeHtml(d.slug)}}')">Copiar Msg</button>
                <button type="button" class="btn-ghost" onclick="openModal('${{escapeHtml(d.slug)}}')">Ver Mensagem</button>
              </div>
            </td>
          </tr>
        `;
      }}).join("");
    }}

    // Check query params
    const params = new URLSearchParams(window.location.search);
    const initialFila = (params.get("fila") || "denis").toLowerCase();
    if (["denis", "gabriel", "all"].includes(initialFila)) {{
      setFilter(initialFila);
    }} else {{
      setFilter("denis");
    }}
  </script>
</body>
</html>
"""

crm_html_path = Path("D:/app/brag-lead-hunter/demos/crm.html")
crm_html_path.write_text(html_content, encoding="utf-8")
print(f"Generated CRM UI at {crm_html_path} ({len(html_content)} bytes)!")
