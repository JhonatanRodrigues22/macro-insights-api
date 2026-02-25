"""Macro Insights API – ponto de entrada da aplicação FastAPI."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes_series import router as series_router
from app.core.config import settings
from app.core.logging import logger
from app.db.session import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Inicializa recursos ao subir a aplicação."""
    logger.info("Inicializando banco de dados...")
    init_db()
    logger.info("Banco de dados pronto.")
    yield
    logger.info("Encerrando aplicação.")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "API que coleta séries econômicas do Banco Central do Brasil (SGS/BCData), "
        "armazena localmente e gera insights como variação, médias móveis e tendências."
    ),
    lifespan=lifespan,
)

# CORS – permite qualquer origem em dev; restringir em produção
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(series_router)


@app.get("/", tags=["Health"])
def root():
    """Health-check simples."""
    return {
        "app": settings.APP_NAME,
        "versao": settings.APP_VERSION,
        "status": "ok",
    }
