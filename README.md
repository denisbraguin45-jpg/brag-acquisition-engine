# BRAG INTERNATIONAL — MÁQUINA DE AQUISIÇÃO B2B & SALES OPERATION ENGINE

Sistema completo de prospecção ativa, qualificação de leads por ICP (Score 0-100), extração de contatos (e-mails, telefones e Instagram), geração automatizada de protótipos/showrooms no conceito *Avantgarde / Campello Racing* e CRM de abordagem com disparos diretos e controle de funil.

---

## 🎯 Objetivo da Ferramenta para os Sócios

Capacitar o time comercial a **prospectar diariamente dezenas ou centenas de negócios qualificados**, encontrar decisores (Instagram, WhatsApp e E-mail), consultar o perfil da loja antes da abordagem e enviar mensagens de alta conversão ancoradas em **demonstrações já publicadas no ar (*Build Before Pitch*)**.

---

## ⚡ Principais Funcionalidades

1. **Mecanismo de Aquisição & Enriquecimento (`backend/`):**
   - Extração e enriquecimento de leads via **Instagram**, **Google Maps** e **Websites**.
   - Identificação automática de e-mails, telefones e perfis de redes sociais.
   - Auditoria técnica em tempo real de websites (SEO, responsividade mobile, velocidade).
   - Cálculo automático do **Brag Lead Score (0 a 100)** e classificação em Prioridades A e B.

2. **Gerador Automático de Showrooms Digitais (`backend/demo_builder.py`):**
   - Criação de landing pages personalizadas de altíssimo luxo para cada empresa qualificada.
   - Padrão estético inspirado na *Avantgarde Concept Store* e *Campello Racing*.
   - Integração direta de botões de contato com WhatsApp do proprietário da loja.

3. **Módulo Comercial & Assistente de Vendas (`demos/sales.html`):**
   - **Divisão Equilibrada de Carteira:** Distribuição balanceada de leads entre vendedores (ex: Bruce e Gabriel).
   - **Briefing de Instagram Integrado:** Card dedicado ao lado de cada cliente com link direto para o Instagram para entender a loja, modelos e fotos antes de ligar.
   - **9 Scripts Comerciais Dinâmicos:** Adaptação instantânea do texto (inserindo nome da empresa, decisor e link da demonstração).
   - **Fila Inteligente de Retomada:** Filtros específicos para `⏳ Ainda Não Abordados`, `📞 Cliente Que Atendeu`, `🔥 Demonstrou Interesse` e `🔄 Não Atendeu (Recall)`.
   - **Regra de Anotação Obrigatória:** Campo obrigatório para registrar a resposta e feedback de cada ligação.
   - **Simulador de Faturamento:** Projeção dinâmica de receita baseada em ticket médio de R$ 1.500/cliente.

4. **Hub de Disparos WhatsApp & CRM (`demos/crm.html`):**
   - Interface rápida para envio de mensagens personalizadas no WhatsApp com 1 clique.
   - Roteiros de vídeo executivo de 60 segundos por empresa.

---

## 🚀 Como Iniciar e Usar a Ferramenta

### 1. Pré-requisitos
- Python 3.10 ou superior instalado.
- Conexão com a internet para requisições e APIs.

### 2. Instalação
Clone este repositório e instale as dependências:
```bash
git clone https://github.com/denisbraguin45-jpg/brag-acquisition-engine.git
cd brag-acquisition-engine
```

*(Opcional: configure variáveis de ambiente em um arquivo `.env` para Apify Token ou Google Places API se desejar executar campanhas automáticas de raspagem massiva).*

```env
PORT=8090
APIFY_TOKEN=seu_token_aqui
GOOGLE_PLACES_API_KEY=sua_chave_aqui
```

### 3. Rodando o Servidor Localmente
Para iniciar a central de aquisição e o CRM local:
```bash
python server.py --port 8090
```

Abra no navegador:
- **Painel de Prospecção & Campanhas:** `http://localhost:8090/`
- **Módulo Comercial (Bruce vs Gabriel):** `http://localhost:8090/demos/sales.html`
- **Central de Disparo WhatsApp & CRM:** `http://localhost:8090/demos/crm.html`
- **Hub Geral de Showrooms Publicados:** `http://localhost:8090/demos/`

---

## 📲 Passo a Passo de Abordagem para o Sócio / Vendedor

1. **Abrir a carteira no Módulo Comercial (`sales.html`).**
2. **Selecionar o Lead:**
   - O painel lateral **BRAG Sales Assistant** carregará os dados do cliente.
   - Clique em **"Abrir Perfil ↗"** no card do Instagram para ver os produtos, fotos e estilo da empresa.
3. **Executar a Ligação ou Mensagem:**
   - Use o botão **"📞 Iniciar Ligação"** ou **"💬 WhatsApp"**.
   - O script da lateral adapta automaticamente o nome da empresa e o link da demonstração navegável pronta.
4. **Registrar a Resposta (Regra Obrigatória):**
   - Clique em **"📝 Registrar Resposta da Ligação"**.
   - Selecione o desfecho (`Atendeu`, `Interessado`, `Não Atendeu`, etc.).
   - Escreva o que o cliente falou no campo de anotações.
   - Se ele não atendeu, programe o retorno para que o lead caia na fila de retomada.
5. **Acompanhar o Faturamento:**
   - Monitore o card de conversão e receita em tempo real.

---

## 📁 Estrutura de Pastas

```text
├── backend/
│   ├── agents/              # Inteligência de oferta, mercado e testes
│   ├── collectors/          # Extratores de Instagram, Google Maps e Web
│   ├── campaign_runner.py   # Execução de campanhas de prospecção
│   ├── deduplication.py     # Deduplicação estrita de contatos e telefones
│   ├── demo_builder.py      # Motor de geração de showrooms Avantgarde
│   ├── sales_service.py     # Lógica comercial e scripts de venda
│   └── sales_ui.py          # Interface do Módulo Comercial
├── data/                    # Banco SQLite local (brag_lead_hunter.db)
├── demos/                   # Páginas HTML dos showrooms gerados e CRM
├── frontend/                # Interface inicial do Lead Hunter
├── server.py                # Servidor HTTP nativo em Python
└── README.md
```

---

## 🔒 Licença & Confidencialidade
Desenvolvido exclusivamente para a operação comercial da **BRAG International**.
Proibida a reprodução ou redistribuição sem autorização prévia.
