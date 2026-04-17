# Subprocuradoria Contenciosa — Painel de Prazos

Sistema web de controle de prazos processuais da Subprocuradoria Contenciosa da PGM Porto Velho.

## Funcionalidades

- **Dashboard** com KPIs em tempo real: total de processos, vencidos, próximos 7 dias e cumpridos
- **Gráfico de performance** por responsável com taxa de cumprimento
- **Aba Críticos** — processos vencendo nos próximos 7 dias, com filtros por responsável e vara
- **Aba Vencidos** — processos com prazo expirado não cumpridos, com filtros
- **Importação de planilha** XLSX (Prazos_2026_Contencioso.xlsx) com diff da importação anterior
- **Alertas via WhatsApp** — abre conversa com mensagem pré-preenchida para o responsável
- **Relatórios em PDF** — semanal, mensal, individual (com indicadores de cumprimento) e de críticos
- **Gestão de equipe** — cadastro com nome, função, email e WhatsApp
- **Marcar como cumprido** — remove o processo das listas de pendentes
- **Modo noturno** — tema claro e escuro

## Stack

| Camada | Tecnologia |
|--------|-----------|
| Backend | Python 3 + Flask |
| Banco de dados | Supabase (PostgreSQL) |
| Frontend | HTML + CSS + JavaScript puro |
| PDF | jsPDF + jsPDF-AutoTable |
| Gráficos | Chart.js |
| Excel | SheetJS |
| Deploy | Render (Web Service) |

## Estrutura

```
├── app/
│   ├── __init__.py          # Factory do Flask
│   ├── routes.py            # Todas as rotas e lógica de negócio
│   └── templates/
│       └── dashboard.html   # Frontend completo (SPA)
├── run.py                   # Entrypoint
├── requirements.txt         # Dependências Python
├── Procfile                 # Configuração do Render/Gunicorn
└── .gitignore
```

## Variáveis de Ambiente

Configure no painel do Render em **Settings → Environment**:

| Variável | Descrição | Exemplo |
|----------|-----------|---------|
| `ACCESS_TOKEN` | Token de acesso ao painel | `pgm-contenciosa-2026` |
| `SECRET_KEY` | Chave secreta do Flask | qualquer string aleatória |
| `SUPABASE_URL` | URL do projeto Supabase | `https://xxx.supabase.co` |
| `SUPABASE_KEY` | Service role key do Supabase | `eyJ...` |

## Banco de Dados (Supabase)

Execute no SQL Editor do Supabase para criar as tabelas:

```sql
-- Tabela da equipe
CREATE TABLE IF NOT EXISTS equipe (
  id         BIGSERIAL PRIMARY KEY,
  nome       TEXT NOT NULL,
  funcao     TEXT,
  email      TEXT,
  whatsapp   TEXT,
  criado_em  TIMESTAMPTZ DEFAULT NOW()
);

-- Tabela de cache dos dados da planilha
CREATE TABLE IF NOT EXISTS dados_cache (
  id         BIGSERIAL PRIMARY KEY,
  chave      TEXT UNIQUE NOT NULL,
  valor      JSONB,
  atualizado TIMESTAMPTZ DEFAULT NOW()
);

-- Desabilitar RLS para acesso pelo servidor
ALTER TABLE equipe      DISABLE ROW LEVEL SECURITY;
ALTER TABLE dados_cache DISABLE ROW LEVEL SECURITY;
```

## Como Rodar Localmente

```bash
# Clonar o repositório
git clone https://github.com/giopsx/refeito-certo.git
cd refeito-certo

# Criar ambiente virtual
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Instalar dependências
pip install -r requirements.txt

# Criar arquivo .env
echo "ACCESS_TOKEN=pgm-contenciosa-2026" > .env
echo "SECRET_KEY=dev-secret-key" >> .env
echo "SUPABASE_URL=https://sua-url.supabase.co" >> .env
echo "SUPABASE_KEY=sua-service-role-key" >> .env

# Rodar
python run.py
```

Acesse: `http://localhost:5000/?token=pgm-contenciosa-2026`

## Deploy no Render

1. Conecte o repositório GitHub ao Render
2. Crie um **Web Service** com:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn run:app`
3. Configure as variáveis de ambiente
4. Após o deploy, acesse o painel e importe a planilha

## Uso

1. Acesse o painel via URL com o token de acesso
2. Vá em **Importar** e carregue o arquivo `Prazos_2026_Contencioso.xlsx`
3. Cadastre os membros da equipe na aba **Equipe** com os números de WhatsApp
4. Use os filtros nas abas **Críticos** e **Vencidos** para gerenciar os prazos
5. Clique em 📱 para enviar alerta via WhatsApp ao responsável
6. Clique em ✓ para marcar um processo como cumprido
7. Gere relatórios PDF na aba **Relatórios**

---

Desenvolvido para a Procuradoria-Geral do Município de Porto Velho · 2026
