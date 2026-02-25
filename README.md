# Macro Insights API

API que coleta séries econômicas do Banco Central do Brasil (SGS/BCData), armazena localmente e gera insights como variação, médias móveis e tendências.

## O que faz

- **Coleta** séries temporais do BCB via endpoint público `api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo}`
- **Armazena** em SQLite (pronto pra migrar pra Postgres)
- **Calcula** métricas: variação (absoluta e %), média, média móvel (7/30 dias), max/min
- **Expõe** endpoints REST prontos pra virar dashboard

## Fonte dos dados

[Banco Central do Brasil – Dados Abertos (SGS/BCData)](https://dadosabertos.bcb.gov.br/)

Séries disponíveis no catálogo inicial (20):

| Código | Série |
|--------|-------|
| 432 | SELIC (meta) – % a.a. |
| 1 | Dólar comercial (venda) |
| 10813 | Dólar comercial (compra) |
| 433 | IPCA – variação mensal |
| 4389 | CDI – % a.d. |
| 11 | SELIC diária |
| 4380 | PIB mensal – valores correntes |
| 25433 | IPCA-15 – variação mensal |
| 1178 | Série SGS #1178 |
| 226 | Série SGS #226 |
| 188 | Série SGS #188 |
| 189 | Série SGS #189 |
| 190 | Série SGS #190 |
| 4390 | Série SGS #4390 |
| 21619 | Série SGS #21619 |
| 21620 | Série SGS #21620 |
| 24363 | Série SGS #24363 |
| 24364 | Série SGS #24364 |
| 22707 | Série SGS #22707 |
| 22708 | Série SGS #22708 |

## Endpoints

| Método | Rota | Descrição |
|--------|------|-----------|
| `GET` | `/` | Health-check |
| `GET` | `/series/catalogo` | Retorna catálogo inicial com 20 séries sugeridas |
| `POST` | `/series/{codigo}/sync` | Baixa dados do BCB e salva no banco |
| `GET` | `/series` | Lista séries já sincronizadas |
| `GET` | `/series/{codigo}` | Dados paginados (com filtro de datas) |
| `GET` | `/series/{codigo}/insights` | Métricas: variação, média, max/min, média móvel |

## Como rodar

```bash
# 1. Clonar o repositório
git clone https://github.com/JhonatanRodrigues22/macro-insights-api.git
cd macro-insights-api

# 2. Criar e ativar ambiente virtual
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate

# 3. Instalar dependências
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 4. Rodar a API
uvicorn app.main:app --reload
```

A documentação interativa estará em **http://127.0.0.1:8000/docs**

Mini interface web disponível em **http://127.0.0.1:8000/app**

Fluxo sugerido na interface:

1. Sincronizar série (ex.: 432 ou 1)
2. Listar séries salvas
3. Consultar insights da série

## Rodar testes

```bash
pytest -v
```

## Rodar com Docker

```bash
# build
docker build -t macro-insights-api .

# run
docker run --rm -p 8000:8000 macro-insights-api
```

## Publicar no GitHub

```bash
git remote add origin https://github.com/seu-usuario/macro-insights-api.git
git branch -M main
git push -u origin main
```

## CI (GitHub Actions)

Ao fazer push ou abrir Pull Request nas branches `main`/`master`, o workflow de CI roda automaticamente:

- instalação de dependências
- execução da suíte de testes com `pytest -v`

## Exemplo de uso

### Sincronizar SELIC (código 432)

```bash
curl -X POST "http://127.0.0.1:8000/series/432/sync" \
  -H "Content-Type: application/json" \
  -d '{"data_inicial": "2024-01-01"}'
```

### Consultar insights

```bash
curl "http://127.0.0.1:8000/series/432/insights"
```

### Sincronizar Dólar (código 1)

```bash
curl -X POST "http://127.0.0.1:8000/series/1/sync" \
  -H "Content-Type: application/json" \
  -d '{"data_inicial": "2024-01-01"}'
```

## Estrutura do projeto

```
app/
  main.py              # FastAPI app + lifespan
  core/
    config.py          # Settings via .env
    logging.py         # Logger centralizado
  db/
    base.py            # Declarative base
    models.py          # Serie, Observacao
    session.py         # Engine, SessionLocal, get_db
  services/
    bcb_client.py      # Cliente HTTP para API do BCB
    insights.py        # Cálculos de métricas
  api/
    routes_series.py   # Endpoints REST
  schemas/
    series.py          # Pydantic models (request/response)
```

## Tech stack

- **Python 3.12+**
- **FastAPI** – framework web async
- **SQLAlchemy 2.0** – ORM
- **SQLite** – banco local (fácil migração pra Postgres)
- **Pydantic v2** – validação de dados
- **httpx** – cliente HTTP async
- **Uvicorn** – ASGI server

## Roadmap

- [ ] Autenticação (API key)
- [ ] Cache de respostas (Redis)
- [ ] Background job para sync automático (cron/APScheduler)
- [ ] Mais séries (IPCA, CDI, PIB)
- [ ] Deploy (Render / Fly.io)
- [ ] Dashboard frontend (React / Next.js)

## Licença

MIT
