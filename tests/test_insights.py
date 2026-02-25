"""Testes unitários para o serviço de insights."""

from dataclasses import dataclass
from datetime import date

from app.services.insights import calcular_insights


@dataclass
class FakeObs:
    """Substituto leve de Observacao para testes sem banco."""
    data: date
    valor: float


def _criar_observacoes(dados: list[tuple[str, float]]) -> list[FakeObs]:
    """Helper: cria lista de FakeObs a partir de (data_str, valor)."""
    return [FakeObs(data=date.fromisoformat(d), valor=v) for d, v in dados]


class TestCalcularInsights:
    """Testa cálculos de métricas do serviço de insights."""

    def test_lista_vazia(self):
        resultado = calcular_insights([])
        assert resultado.total_observacoes == 0
        assert resultado.media is None
        assert resultado.variacao_absoluta is None

    def test_metricas_basicas(self):
        obs = _criar_observacoes([
            ("2024-01-01", 10.0),
            ("2024-01-02", 12.0),
            ("2024-01-03", 11.0),
            ("2024-01-04", 15.0),
            ("2024-01-05", 13.0),
        ])
        resultado = calcular_insights(obs)

        assert resultado.total_observacoes == 5
        assert resultado.valor_minimo == 10.0
        assert resultado.valor_maximo == 15.0
        assert resultado.data_inicio == date(2024, 1, 1)
        assert resultado.data_fim == date(2024, 1, 5)

    def test_variacao(self):
        obs = _criar_observacoes([
            ("2024-01-01", 100.0),
            ("2024-01-02", 130.0),
        ])
        resultado = calcular_insights(obs)

        assert resultado.variacao_absoluta == 30.0
        assert resultado.variacao_percentual == 30.0

    def test_media(self):
        obs = _criar_observacoes([
            ("2024-01-01", 10.0),
            ("2024-01-02", 20.0),
            ("2024-01-03", 30.0),
        ])
        resultado = calcular_insights(obs)
        assert resultado.media == 20.0

    def test_media_movel_insuficiente(self):
        obs = _criar_observacoes([
            ("2024-01-01", 10.0),
            ("2024-01-02", 20.0),
        ])
        resultado = calcular_insights(obs)
        # Com 2 pontos não dá pra calcular MM7
        assert resultado.media_movel_7 == []

    def test_media_movel_7(self):
        dados = [(f"2024-01-{i+1:02d}", float(i + 1)) for i in range(10)]
        obs = _criar_observacoes(dados)
        resultado = calcular_insights(obs)

        assert len(resultado.media_movel_7) > 0
        # Primeiro ponto da MM7 é a média dos 7 primeiros valores
        primeiro = resultado.media_movel_7[0]
        assert primeiro["valor"] == round(sum(range(1, 8)) / 7, 6)

    def test_ultimas_observacoes(self):
        dados = [(f"2024-01-{i+1:02d}", float(i)) for i in range(20)]
        obs = _criar_observacoes(dados)
        resultado = calcular_insights(obs, ultimas_n=5)

        assert len(resultado.ultimas_observacoes) == 5
        assert resultado.ultimas_observacoes[-1]["valor"] == 19.0

    def test_extremos_com_datas(self):
        obs = _criar_observacoes([
            ("2024-01-01", 5.0),
            ("2024-01-02", 1.0),   # min
            ("2024-01-03", 10.0),  # max
            ("2024-01-04", 7.0),
        ])
        resultado = calcular_insights(obs)

        assert resultado.valor_minimo == 1.0
        assert resultado.data_minimo == date(2024, 1, 2)
        assert resultado.valor_maximo == 10.0
        assert resultado.data_maximo == date(2024, 1, 3)
