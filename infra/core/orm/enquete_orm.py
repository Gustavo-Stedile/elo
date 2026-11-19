from datetime import datetime
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from infra.database import Base


class EnqueteORM(Base):
    __tablename__ = "enquetes"
    id: Mapped[int] = mapped_column(primary_key=True)
    gremio_id: Mapped[int] = mapped_column(ForeignKey("gremios.id", ondelete="CASCADE"), index=True)
    canal_id: Mapped[int | None] = mapped_column(ForeignKey("canais.id", ondelete="CASCADE"), nullable=True)
    criador_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id", ondelete="CASCADE"), index=True)
    pergunta: Mapped[str] = mapped_column(String(255))
    tipo_votacao: Mapped[str] = mapped_column(String(20))
    votos_visiveis: Mapped[bool] = mapped_column(Boolean, default=False)
    criada_em: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class EnqueteOpcaoORM(Base):
    __tablename__ = "enquete_opcoes"
    id: Mapped[int] = mapped_column(primary_key=True)
    enquete_id: Mapped[int] = mapped_column(ForeignKey("enquetes.id", ondelete="CASCADE"), index=True)
    texto: Mapped[str] = mapped_column(String(255))


class EnqueteVotoORM(Base):
    __tablename__ = "enquete_votos"
    __table_args__ = (
        UniqueConstraint("enquete_id", "usuario_id", "opcao_id", name="uq_enquete_voto"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    enquete_id: Mapped[int] = mapped_column(ForeignKey("enquetes.id", ondelete="CASCADE"), index=True)
    opcao_id: Mapped[int] = mapped_column(ForeignKey("enquete_opcoes.id", ondelete="CASCADE"), index=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id", ondelete="CASCADE"), index=True)
