"""Rotas da API para séries econômicas."""

import math
from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import logger
from app.db.models import Observacao, Serie
from app.db.session import get_db
from app.schemas.series import (
    CatalogoSerieOut,
    InsightsResponse,
    ObservacaoOut,
    SerieDetalhe,
    SerieResumo,
    SyncRequest,
    SyncResponse,
)
from app.services.bcb_client import buscar_serie, listar_catalogo_series, nome_serie
from app.services.insights import calcular_insights

router = APIRouter(prefix="/series", tags=["Séries"])


@router.get("/catalogo", response_model=list[CatalogoSerieOut])
def obter_catalogo_series():
    """Retorna catálogo inicial de 20 séries sugeridas."""
    return listar_catalogo_series()


# ── POST /series/{codigo}/sync ───────────────────────────────────────────────


@router.post("/{codigo}/sync", response_model=SyncResponse)
async def sincronizar_serie(
    codigo: int,
    body: SyncRequest | None = None,
    db: Session = Depends(get_db),
):
    """Baixa dados do BCB e salva/atualiza no banco local."""
    body = body or SyncRequest()

    # 1. Buscar dados do BCB
    try:
        dados = await buscar_serie(
            codigo=codigo,
            data_inicial=body.data_inicial,
            data_final=body.data_final,
        )
    except Exception as exc:
        logger.error("Erro ao buscar série %d do BCB: %s", codigo, exc)
        raise HTTPException(status_code=502, detail=f"Erro ao consultar BCB: {exc}")

    if not dados:
        raise HTTPException(status_code=404, detail="Nenhum dado retornado pelo BCB para essa série.")

    # 2. Garantir que a série existe no banco
    serie = db.query(Serie).filter(Serie.codigo == codigo).first()
    if not serie:
        serie = Serie(codigo=codigo, nome=nome_serie(codigo))
        db.add(serie)
        db.flush()

    # 3. Upsert das observações
    novos = 0
    atualizados = 0
    for item in dados:
        obs = (
            db.query(Observacao)
            .filter(Observacao.serie_id == serie.id, Observacao.data == item["data"])
            .first()
        )
        if obs:
            if obs.valor != item["valor"]:
                obs.valor = item["valor"]
                atualizados += 1
        else:
            db.add(Observacao(serie_id=serie.id, data=item["data"], valor=item["valor"]))
            novos += 1

    serie.ultima_sync = datetime.utcnow()
    db.commit()

    total = db.query(func.count(Observacao.id)).filter(Observacao.serie_id == serie.id).scalar()

    logger.info("Sync série %d: %d novos, %d atualizados, %d total", codigo, novos, atualizados, total)

    return SyncResponse(
        codigo=codigo,
        nome=serie.nome,
        registros_novos=novos,
        registros_atualizados=atualizados,
        total_registros=total,
        mensagem=f"Sincronização concluída: {novos} novos, {atualizados} atualizados.",
    )


# ── GET /series ──────────────────────────────────────────────────────────────


@router.get("", response_model=list[SerieResumo])
def listar_series(db: Session = Depends(get_db)):
    """Lista todas as séries já sincronizadas."""
    series = db.query(Serie).order_by(Serie.codigo).all()
    resultado = []
    for s in series:
        total = db.query(func.count(Observacao.id)).filter(Observacao.serie_id == s.id).scalar()
        resultado.append(
            SerieResumo(
                codigo=s.codigo,
                nome=s.nome,
                descricao=s.descricao,
                ultima_sync=s.ultima_sync,
                total_observacoes=total,
            )
        )
    return resultado


# ── GET /series/{codigo} ─────────────────────────────────────────────────────


@router.get("/{codigo}", response_model=SerieDetalhe)
def obter_serie(
    codigo: int,
    pagina: int = Query(1, ge=1, description="Página (começa em 1)"),
    tamanho: int = Query(None, ge=1, le=500, description="Itens por página"),
    data_inicial: date | None = Query(None, description="Filtro data inicial"),
    data_final: date | None = Query(None, description="Filtro data final"),
    db: Session = Depends(get_db),
):
    """Retorna dados paginados de uma série (com filtro opcional de datas)."""
    serie = db.query(Serie).filter(Serie.codigo == codigo).first()
    if not serie:
        raise HTTPException(status_code=404, detail="Série não encontrada. Faça o sync primeiro.")

    tam = tamanho or settings.PAGE_SIZE

    query = db.query(Observacao).filter(Observacao.serie_id == serie.id)
    if data_inicial:
        query = query.filter(Observacao.data >= data_inicial)
    if data_final:
        query = query.filter(Observacao.data <= data_final)
    query = query.order_by(Observacao.data)

    total = query.count()
    total_paginas = max(1, math.ceil(total / tam))
    offset = (pagina - 1) * tam

    obs = query.offset(offset).limit(tam).all()

    return SerieDetalhe(
        codigo=serie.codigo,
        nome=serie.nome,
        pagina=pagina,
        total_paginas=total_paginas,
        total_observacoes=total,
        observacoes=[ObservacaoOut.model_validate(o) for o in obs],
    )


# ── GET /series/{codigo}/insights ────────────────────────────────────────────


@router.get("/{codigo}/insights", response_model=InsightsResponse)
def obter_insights(
    codigo: int,
    data_inicial: date | None = Query(None, description="Filtro data inicial"),
    data_final: date | None = Query(None, description="Filtro data final"),
    ultimas_n: int = Query(10, ge=1, le=100, description="Qtd de últimas observações"),
    db: Session = Depends(get_db),
):
    """Retorna métricas e insights calculados sobre a série."""
    serie = db.query(Serie).filter(Serie.codigo == codigo).first()
    if not serie:
        raise HTTPException(status_code=404, detail="Série não encontrada. Faça o sync primeiro.")

    query = db.query(Observacao).filter(Observacao.serie_id == serie.id)
    if data_inicial:
        query = query.filter(Observacao.data >= data_inicial)
    if data_final:
        query = query.filter(Observacao.data <= data_final)
    obs = query.order_by(Observacao.data).all()

    if not obs:
        raise HTTPException(status_code=404, detail="Nenhuma observação encontrada para o período.")

    resultado = calcular_insights(obs, ultimas_n=ultimas_n)

    return InsightsResponse(
        codigo=serie.codigo,
        nome=serie.nome,
        total_observacoes=resultado.total_observacoes,
        data_inicio=resultado.data_inicio,
        data_fim=resultado.data_fim,
        valor_minimo=resultado.valor_minimo,
        valor_maximo=resultado.valor_maximo,
        data_minimo=resultado.data_minimo,
        data_maximo=resultado.data_maximo,
        variacao_absoluta=resultado.variacao_absoluta,
        variacao_percentual=resultado.variacao_percentual,
        media=resultado.media,
        media_movel_7=resultado.media_movel_7,
        media_movel_30=resultado.media_movel_30,
        ultimas_observacoes=resultado.ultimas_observacoes,
    )
