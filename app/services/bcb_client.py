"""Cliente HTTP para a API do Banco Central do Brasil (SGS/BCData)."""

from datetime import date, datetime

import httpx

from app.core.config import settings
from app.core.logging import logger

# Mapeamento de códigos conhecidos para nomes amigáveis
SERIES_CONHECIDAS: dict[int, str] = {
    11:   "SELIC (meta)",
    432:  "SELIC (meta) – % a.a.",
    4389: "CDI – % a.d.",
    1:    "Dólar comercial (venda)",
    10813: "Dólar comercial (compra)",
    433:  "IPCA – variação mensal",
    4380: "PIB mensal – valores correntes",
    25433: "IPCA-15 – variação mensal",
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
