# Central-De-Alertas-PGM

Sistema web de controle de prazos processuais desenvolvido para a Subprocuradoria Contenciosa da Procuradoria-Geral do Município de Porto Velho.

---

## Funcionalidades

- **Dashboard** com indicadores em tempo real: total de processos, vencidos, próximos 7 dias e cumpridos
- **Gráfico de performance** por responsável com taxa de cumprimento
- **Vence Hoje** — processos com prazo no dia atual
- **Próximos 7 Dias** — processos com prazo iminente, com filtros por responsável e data
- **Vencidos** — processos com prazo expirado não cumpridos
- **Importação de planilha** XLSX com comparativo da importação anterior
- **Alertas via WhatsApp** — mensagem pré-preenchida enviada ao responsável pelo processo
- **Relatórios em PDF** — semanal, mensal, individual e de críticos, com resumo por tipo de petição
- **Gestão de equipe** — cadastro de membros com nome, função, e-mail e WhatsApp
- **Marcar como cumprido** — remove o processo das listas de pendentes
- **Modo noturno** — tema claro e escuro

---

## Stack

| Camada | Tecnologia |
|--------|-----------|
| Backend | Python 3 + Flask |
| Banco de dados | Supabase (PostgreSQL) |
| Frontend | HTML + CSS + JavaScript puro |
| PDF | jsPDF + jsPDF-AutoTable |
| Gráficos | Chart.js |
| Excel | SheetJS |
| Deploy | Render |

---

## Estrutura do Projeto

```
├── app/
│   ├── __init__.py          # Factory do Flask
│   ├── routes.py            # Rotas e lógica de negócio
│   ├── static/              # Arquivos estáticos (logo, etc.)
│   └── templates/
│       └── dashboard.html   # Frontend completo (SPA)
├── run.py                   # Entrypoint da aplicação
├── requirements.txt         # Dependências Python
├── Procfile                 # Configuração do servidor
└── .gitignore
```

---

## Variáveis de Ambiente

Configure as variáveis de ambiente no painel do seu serviço de deploy. **Nunca as inclua no código ou no repositório.**

| Variável | Descrição |
|----------|-----------|
| `ACCESS_TOKEN` | Token de acesso ao painel |
| `SECRET_KEY` | Chave secreta do Flask |
| `SUPABASE_URL` | URL do projeto Supabase |
| `SUPABASE_KEY` | Service role key do Supabase |

---

## Banco de Dados

Execute os scripts SQL abaixo no editor do Supabase para criar as tabelas necessárias:

```sql
-- Tabela da equipe
CREATE TABLE IF NOT EXISTS equipe (
  id         BIGSERIAL PRIMARY KEY,
  nome       TEXT NOT NULL,
  funcao     TEXT,
  email      TEXT,
  whatsapp   TEXT,
  ativo      BOOLEAN DEFAULT TRUE,
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

---

## Rodando Localmente

```bash
# 1. Clonar o repositório
git clone <url-do-repositorio>
cd <nome-da-pasta>

# 2. Criar e ativar ambiente virtual
python -m venv venv
source venv/bin/activate       # Linux/Mac
venv\Scripts\activate          # Windows

# 3. Instalar dependências
pip install -r requirements.txt

# 4. Criar arquivo .env com as variáveis de ambiente
# (veja a seção acima)

# 5. Rodar
python run.py
```

---

## Deploy

1. Conecte o repositório ao serviço de deploy
2. Configure o build: `pip install -r requirements.txt`
3. Configure o start: `gunicorn run:app`
4. Adicione as variáveis de ambiente no painel
5. Após o deploy, acesse o painel e importe a planilha

---

## Como Usar

1. Acesse o painel com o token de acesso configurado
2. Vá em **Importar** e carregue o arquivo XLSX com os prazos
3. Cadastre os membros da equipe na aba **Equipe** com os números de WhatsApp
4. Acompanhe os prazos pelas abas **Vence Hoje**, **Próximos 7 Dias** e **Vencidos**
5. Use os filtros para buscar por responsável, data ou processo
6. Clique em 📱 para enviar alerta via WhatsApp ao responsável
7. Clique em ✓ para marcar um processo como cumprido
8. Gere relatórios PDF na aba **Relatórios**

---

## Formato da Planilha

A planilha XLSX deve conter as seguintes colunas:

| Coluna | Descrição |
|--------|-----------|
| PRAZO | Data do prazo (DD/MM/AAAA) |
| RESPONSÁVEL | Nome do procurador responsável |
| Nº DO PROCESSO | Número do processo |
| PARTE ATIVA | Nome da parte |
| VARA | Vara judicial |
| TIPO DE PETIÇÃO | Tipo da petição (opcional) |
| CUMPRIDO? | Status (SIM / PARCIAL / PREJUDICADO) |

---

Desenvolvido para a Procuradoria-Geral do Município de Porto Velho · 2026
