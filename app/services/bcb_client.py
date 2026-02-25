"""Cliente HTTP para a API do Banco Central do Brasil (SGS/BCData)."""

from datetime import date, datetime

import httpx

from app.core.config import settings
from app.core.logging import logger

# Catálogo inicial com 20 séries para uso rápido na API/UI.
# Observação: alguns rótulos são genéricos para facilitar expansão do catálogo.
CATALOGO_SERIES: list[dict[str, int | str]] = [
    {"codigo": 432, "nome": "SELIC (meta) – % a.a."},
    {"codigo": 1, "nome": "Dólar comercial (venda)"},
    {"codigo": 10813, "nome": "Dólar comercial (compra)"},
    {"codigo": 433, "nome": "IPCA – variação mensal"},
    {"codigo": 4389, "nome": "CDI – % a.d."},
    {"codigo": 11, "nome": "SELIC diária"},
    {"codigo": 4380, "nome": "PIB mensal – valores correntes"},
    {"codigo": 25433, "nome": "IPCA-15 – variação mensal"},
    {"codigo": 1178, "nome": "Série SGS #1178"},
    {"codigo": 226, "nome": "Série SGS #226"},
    {"codigo": 188, "nome": "Série SGS #188"},
    {"codigo": 189, "nome": "Série SGS #189"},
    {"codigo": 190, "nome": "Série SGS #190"},
    {"codigo": 4390, "nome": "Série SGS #4390"},
    {"codigo": 21619, "nome": "Série SGS #21619"},
    {"codigo": 21620, "nome": "Série SGS #21620"},
    {"codigo": 24363, "nome": "Série SGS #24363"},
    {"codigo": 24364, "nome": "Série SGS #24364"},
    {"codigo": 22707, "nome": "Série SGS #22707"},
    {"codigo": 22708, "nome": "Série SGS #22708"},
]

SERIES_CONHECIDAS: dict[int, str] = {
    int(item["codigo"]): str(item["nome"]) for item in CATALOGO_SERIES
}


def _parse_data(raw: str) -> date:
    """Converte data no formato dd/mm/yyyy retornado pelo BCB."""
    return datetime.strptime(raw, "%d/%m/%Y").date()


async def buscar_serie(
    codigo: int,
    data_inicial: date | None = None,
    data_final: date | None = None,
) -> list[dict]:
    """Busca dados de uma série do BCB/SGS.

    Retorna lista de dicts com chaves ``data`` (date) e ``valor`` (float).
    Registros sem valor numérico são descartados silenciosamente.
    """
    url = f"{settings.BCB_BASE_URL}.{codigo}/dados"
    params: dict[str, str] = {"formato": "json"}
    if data_inicial:
        params["dataInicial"] = data_inicial.strftime("%d/%m/%Y")
    if data_final:
        params["dataFinal"] = data_final.strftime("%d/%m/%Y")

    logger.info("BCB request: GET %s params=%s", url, params)

    async with httpx.AsyncClient(timeout=settings.BCB_TIMEOUT) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()

    dados_brutos: list[dict] = resp.json()
    logger.info("BCB retornou %d registros para série %d", len(dados_brutos), codigo)

    resultado: list[dict] = []
    for item in dados_brutos:
        try:
            valor = float(item["valor"])
        except (ValueError, TypeError):
            continue  # pula registros sem valor numérico
        resultado.append({"data": _parse_data(item["data"]), "valor": valor})

    return resultado


def nome_serie(codigo: int) -> str:
    """Retorna nome amigável da série ou um nome genérico."""
    return SERIES_CONHECIDAS.get(codigo, f"Série BCB #{codigo}")


def listar_catalogo_series() -> list[dict[str, int | str]]:
    """Retorna catálogo inicial de séries sugeridas."""
    return CATALOGO_SERIES
