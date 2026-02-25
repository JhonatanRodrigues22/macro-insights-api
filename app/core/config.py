"""Configurações centrais da aplicação (via variáveis de ambiente)."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Carrega configurações do arquivo .env ou variáveis de ambiente."""

    APP_NAME: str = "Macro Insights API"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True

    # Banco de dados
    DATABASE_URL: str = "sqlite:///./macro_insights.db"

    # BCB
    BCB_BASE_URL: str = "https://api.bcb.gov.br/dados/serie/bcdata.sgs"
    BCB_TIMEOUT: int = 30

    # Paginação padrão
    PAGE_SIZE: int = 50

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
