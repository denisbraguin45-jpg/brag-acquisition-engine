import json
from pathlib import Path

demos_dir = Path("D:/app/brag-lead-hunter/demos")
with open(demos_dir / "database_all_demos.json", "r", encoding="utf-8") as f:
    database = json.load(f)

manifest_json = json.dumps(database, ensure_ascii=False)

html_content = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>BRAG International — Dashboard Executivo &amp; Banco de Dados de Demos</title>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@400;600;700;800&family=Plus+Jakarta+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@500;700&display=swap" rel="stylesheet" />
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
        <div class="eyebrow">AVANTGARDE CONCEPT STORE · BANCO DE DADOS UNIFICADO (428 DEMOS)</div>
        <h1>Dashboard Executivo &amp; Central de Demos</h1>
        <p class="sub">Visão completa de todos os <strong>428 showrooms digitais publicados</strong> na Vercel. Acompanhe a operação entre os sócios, filtre por responsável (Denis ou Gabriel), realize disparos de 1 clique no WhatsApp e monitore o funil de abordagem.</p>
      </div>
      <div class="actions-top">
        <a href="/demos/crm_all_leads.csv" download class="btn-top btn-top-gold">
          📥 Baixar Planilha CSV Completa
        </a>
        <a href="/demos/database_all_demos.json" download class="btn-top">
          📄 Baixar Banco JSON (428)
        </a>
        <button type="button" class="btn-top" onclick="copyPartnerShareLink()">
          🔗 Copiar Link da Fila
        </button>
      </div>
    </header>

    <!-- 3 WORKSPACE TABS -->
    <div class="partner-switcher" role="tablist" aria-label="Seleção de Fila por Sócio">
      <button type="button" id="tabBtnDenis" class="partner-tab active-denis" onclick="setPartnerQueue('denis')">
        <span class="partner-tab-kicker">CARTEIRA DENIS (398 DEMOS)</span>
        <span class="partner-tab-title">Fila Denis</span>
        <div class="partner-tab-meta">
          <span id="metaDenisCount">Carregando...</span>
          <span style="color:#ff9d72;">?fila=denis</span>
        </div>
      </button>

      <button type="button" id="tabBtnGabriel" class="partner-tab" onclick="setPartnerQueue('gabriel')">
        <span class="partner-tab-kicker">CARTEIRA GABRIEL (30 DEMOS)</span>
        <span class="partner-tab-title">Fila Gabriel</span>
        <div class="partner-tab-meta">
          <span id="metaGabrielCount">Carregando...</span>
          <span style="color:#93c5fd;">?fila=gabriel</span>
        </div>
      </button>

      <button type="button" id="tabBtnAll" class="partner-tab" onclick="setPartnerQueue('all')">
        <span class="partner-tab-kicker">BANCO DE DADOS CONSOLIDADO</span>
        <span class="partner-tab-title">Todas as 428 Demos</span>
        <div class="partner-tab-meta">
          <span id="metaAllCount">428 Showrooms Online</span>
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
        <div class="kpi-pill">Total Online na Vercel: <strong style="color:#34d399;">428/428</strong></div>
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

# Write to demos/index.html
index_file = demos_dir / "index.html"
index_file.write_text(html_content, encoding="utf-8")
print(f"Generated complete dashboard at {index_file} ({len(html_content)} bytes)!")

# Update manifest.json to include all 428 leads so any API/tool reads the whole database
manifest_file = demos_dir / "manifest.json"
manifest_file.write_text(json.dumps(database, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"Updated {manifest_file} with all {len(database)} records!")
