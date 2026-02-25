"""Testes para o cliente BCB."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.bcb_client import nome_serie, _parse_data, SERIES_CONHECIDAS


class TestNomeSerie:
    """Testa o mapeamento de códigos para nomes."""

    def test_serie_conhecida(self):
        assert nome_serie(432) == "SELIC (meta) – % a.a."
        assert nome_serie(1) == "Dólar comercial (venda)"

    def test_serie_desconhecida(self):
        assert nome_serie(99999) == "Série BCB #99999"


class TestParseData:
    """Testa o parser de datas do formato BCB."""

    def test_formato_valido(self):
        from datetime import date
        assert _parse_data("01/01/2024") == date(2024, 1, 1)
        assert _parse_data("31/12/2023") == date(2023, 12, 31)

    def test_formato_invalido(self):
        with pytest.raises(ValueError):
            _parse_data("2024-01-01")
