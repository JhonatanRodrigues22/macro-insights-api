"""Modelos SQLAlchemy para séries e observações do BCB."""

from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, Integer, String, Text, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Serie(Base):
    """Metadados de uma série econômica do BCB/SGS."""

    __tablename__ = "series"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    codigo: Mapped[int] = mapped_column(Integer, unique=True, nullable=False, index=True)
    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    descricao: Mapped[str | None] = mapped_column(Text, nullable=True)
    ultima_sync: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    observacoes: Mapped[list["Observacao"]] = relationship(
        back_populates="serie", cascade="all, delete-orphan", order_by="Observacao.data"
    )

    def __repr__(self) -> str:
        return f"<Serie codigo={self.codigo} nome={self.nome!r}>"


class Observacao(Base):
    """Um ponto de dado (data + valor) dentro de uma série."""

    __tablename__ = "observacoes"
    __table_args__ = (
        UniqueConstraint("serie_id", "data", name="uq_serie_data"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    serie_id: Mapped[int] = mapped_column(Integer, ForeignKey("series.id"), nullable=False, index=True)
    data: Mapped[date] = mapped_column(Date, nullable=False)
    valor: Mapped[float] = mapped_column(Float, nullable=False)

    serie: Mapped["Serie"] = relationship(back_populates="observacoes")

    def __repr__(self) -> str:
        return f"<Observacao data={self.data} valor={self.valor}>"
