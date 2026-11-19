from typing import List
from sqlalchemy import String, Boolean, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from infra.database import Base

class GremioORM(Base):
    __tablename__ = "gremios"
    __table_args__ = (
        UniqueConstraint(
            "instituicao",
            "etapa_ensino",
            name="uq_gremio_instituicao_etapa",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    nome: Mapped[str] = mapped_column(String(100))
    descricao: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    instituicao: Mapped[str] = mapped_column(String(150))
    etapa_ensino: Mapped[int] = mapped_column(Integer)
    legitimado: Mapped[bool] = mapped_column(Boolean, default=False)
    fundador_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), index=True)

    # Relação com a tabela associativa de membros
    membros: Mapped[List["MembroGremioORM"]] = relationship(back_populates="gremio", cascade="all, delete-orphan")
