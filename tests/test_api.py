"""Testes de integração para os endpoints da API."""

from unittest.mock import AsyncMock, patch


class TestHealthCheck:
    """Testa o endpoint root."""

    def test_root(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert "versao" in data


class TestListarSeries:
    """Testa GET /series."""

    def test_lista_vazia(self, client):
        resp = client.get("/series")
        assert resp.status_code == 200
        assert resp.json() == []


class TestCatalogoSeries:
    """Testa GET /series/catalogo."""

    def test_catalogo_retorna_20_series(self, client):
        resp = client.get("/series/catalogo")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 20
        assert data[0]["codigo"] == 432


class TestObterSerie:
    """Testa GET /series/{codigo}."""

    def test_serie_inexistente(self, client):
        resp = client.get("/series/9999")
        assert resp.status_code == 404


class TestObterInsights:
    """Testa GET /series/{codigo}/insights."""

    def test_insights_serie_inexistente(self, client):
        resp = client.get("/series/9999/insights")
        assert resp.status_code == 404


class TestSyncSerie:
    """Testa POST /series/{codigo}/sync."""

    @patch("app.api.routes_series.buscar_serie", new_callable=AsyncMock)
    def test_sync_com_dados(self, mock_buscar, client):
        """Testa sync com dados mockados (sem chamar o BCB real)."""
        from datetime import date

        mock_buscar.return_value = [
            {"data": date(2024, 1, 2), "valor": 11.75},
            {"data": date(2024, 1, 3), "valor": 11.75},
            {"data": date(2024, 1, 4), "valor": 11.65},
        ]

        resp = client.post("/series/432/sync", json={})
        assert resp.status_code == 200
        data = resp.json()
        assert data["codigo"] == 432
        assert data["registros_novos"] == 3
        assert data["total_registros"] == 3

    @patch("app.api.routes_series.buscar_serie", new_callable=AsyncMock)
    def test_sync_sem_dados(self, mock_buscar, client):
        """Testa sync quando BCB retorna lista vazia."""
        mock_buscar.return_value = []

        resp = client.post("/series/9999/sync", json={})
        assert resp.status_code == 404

    @patch("app.api.routes_series.buscar_serie", new_callable=AsyncMock)
    def test_sync_depois_lista(self, mock_buscar, client):
        """Após sync, a série aparece em GET /series."""
        from datetime import date

        mock_buscar.return_value = [
            {"data": date(2024, 1, 2), "valor": 5.10},
        ]

        client.post("/series/1/sync", json={})

        resp = client.get("/series")
        assert resp.status_code == 200
        series = resp.json()
        assert len(series) == 1
        assert series[0]["codigo"] == 1

    @patch("app.api.routes_series.buscar_serie", new_callable=AsyncMock)
    def test_sync_depois_insights(self, mock_buscar, client):
        """Após sync, insights devem retornar métricas."""
        from datetime import date

        mock_buscar.return_value = [
            {"data": date(2024, 1, 2), "valor": 100.0},
            {"data": date(2024, 1, 3), "valor": 110.0},
            {"data": date(2024, 1, 4), "valor": 105.0},
        ]

        client.post("/series/432/sync", json={})

        resp = client.get("/series/432/insights")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_observacoes"] == 3
        assert data["valor_minimo"] == 100.0
        assert data["valor_maximo"] == 110.0
        assert data["variacao_absoluta"] == 5.0

    @patch("app.api.routes_series.buscar_serie", new_callable=AsyncMock)
    def test_paginacao(self, mock_buscar, client):
        """Testa paginação de GET /series/{codigo}."""
        from datetime import date, timedelta

        base = date(2024, 1, 1)
        mock_buscar.return_value = [
            {"data": base + timedelta(days=i), "valor": float(i)}
            for i in range(10)
        ]

        client.post("/series/432/sync", json={})

        resp = client.get("/series/432?tamanho=3&pagina=1")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["observacoes"]) == 3
        assert data["total_paginas"] == 4
        assert data["total_observacoes"] == 10
