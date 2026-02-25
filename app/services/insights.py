"""Cálculos de insights sobre séries temporais."""

from dataclasses import dataclass
from datetime import date

from app.db.models import Observacao


@dataclass
class InsightsResult:
    """Resultado dos cálculos de insight para uma série."""

    total_observacoes: int
    data_inicio: date | None
    data_fim: date | None

    # Valores extremos
    valor_minimo: float | None
    valor_maximo: float | None
    data_minimo: date | None
    data_maximo: date | None

    # Variação no período
    variacao_absoluta: float | None
    variacao_percentual: float | None

    # Médias
    media: float | None
    media_movel_7: list[dict] | None
    media_movel_30: list[dict] | None

    # Últimas observações
    ultimas_observacoes: list[dict]


def calcular_insights(
    observacoes: list[Observacao],
    ultimas_n: int = 10,
) -> InsightsResult:
    """Calcula métricas sobre uma lista de observações ordenadas por data."""

    if not observacoes:
        return InsightsResult(
            total_observacoes=0,
            data_inicio=None,
            data_fim=None,
            valor_minimo=None,
            valor_maximo=None,
            data_minimo=None,
            data_maximo=None,
            variacao_absoluta=None,
            variacao_percentual=None,
            media=None,
            media_movel_7=None,
            media_movel_30=None,
            ultimas_observacoes=[],
        )

    valores = [o.valor for o in observacoes]
    datas = [o.data for o in observacoes]

    # Extremos
    idx_min = valores.index(min(valores))
    idx_max = valores.index(max(valores))

    # Variação
    primeiro = valores[0]
    ultimo = valores[-1]
    variacao_abs = ultimo - primeiro
    variacao_pct = (variacao_abs / primeiro * 100) if primeiro != 0 else None

    # Média
    media = sum(valores) / len(valores)

    # Médias móveis
    mm7 = _media_movel(observacoes, janela=7)
    mm30 = _media_movel(observacoes, janela=30)

    # Últimas N
    ultimas = [
        {"data": o.data.isoformat(), "valor": o.valor}
        for o in observacoes[-ultimas_n:]
    ]

    return InsightsResult(
        total_observacoes=len(observacoes),
        data_inicio=datas[0],
        data_fim=datas[-1],
        valor_minimo=valores[idx_min],
        valor_maximo=valores[idx_max],
        data_minimo=datas[idx_min],
        data_maximo=datas[idx_max],
        variacao_absoluta=round(variacao_abs, 6),
        variacao_percentual=round(variacao_pct, 4) if variacao_pct is not None else None,
        media=round(media, 6),
        media_movel_7=mm7,
        media_movel_30=mm30,
        ultimas_observacoes=ultimas,
    )


def _media_movel(
    observacoes: list[Observacao],
    janela: int,
) -> list[dict]:
    """Calcula média móvel simples com a janela especificada.

    Retorna apenas os últimos 30 pontos para manter a resposta leve.
    """
    if len(observacoes) < janela:
        return []

    resultado: list[dict] = []
    valores = [o.valor for o in observacoes]
    datas = [o.data for o in observacoes]

    for i in range(janela - 1, len(valores)):
        janela_valores = valores[i - janela + 1 : i + 1]
        media = sum(janela_valores) / janela
        resultado.append({
            "data": datas[i].isoformat(),
            "valor": round(media, 6),
        })

    # Retorna apenas os últimos 30 pontos
    return resultado[-30:]
