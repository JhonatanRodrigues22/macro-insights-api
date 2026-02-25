"""Schemas Pydantic para request/response das séries."""

from datetime import date, datetime

from pydantic import BaseModel, Field


# ── Request ──────────────────────────────────────────────────────────────────

class SyncRequest(BaseModel):
    """Parâmetros opcionais para sincronização de série."""
    data_inicial: date | None = Field(None, description="Data inicial no formato YYYY-MM-DD")
    data_final: date | None = Field(None, description="Data final no formato YYYY-MM-DD")


# ── Response ─────────────────────────────────────────────────────────────────

class ObservacaoOut(BaseModel):
    """Uma observação (data + valor)."""
    data: date
    valor: float

    model_config = {"from_attributes": True}


class SerieResumo(BaseModel):
    """Resumo de uma série cadastrada."""
    codigo: int
    nome: str
    descricao: str | None = None
    ultima_sync: datetime | None = None
    total_observacoes: int = 0

    model_config = {"from_attributes": True}


class SerieDetalhe(BaseModel):
    """Série com suas observações (paginadas)."""
    codigo: int
    nome: str
    pagina: int
    total_paginas: int
    total_observacoes: int
    observacoes: list[ObservacaoOut]


class SyncResponse(BaseModel):
    """Resposta da sincronização."""
    codigo: int
    nome: str
    registros_novos: int
    registros_atualizados: int
    total_registros: int
    mensagem: str


class InsightsResponse(BaseModel):
    """Métricas calculadas sobre a série."""
    codigo: int
    nome: str
    total_observacoes: int
    data_inicio: date | None
    data_fim: date | None

    valor_minimo: float | None
    valor_maximo: float | None
    data_minimo: date | None
    data_maximo: date | None

    variacao_absoluta: float | None
    variacao_percentual: float | None

    media: float | None
    media_movel_7: list[dict] | None
    media_movel_30: list[dict] | None

    ultimas_observacoes: list[dict]
