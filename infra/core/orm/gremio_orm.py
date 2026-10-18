from typing import List
from sqlalchemy import String, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from infra.database import Base

class GremioORM(Base):
    __tablename__ = "gremios"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    nome: Mapped[str] = mapped_column(String(100))
    instituicao: Mapped[str] = mapped_column(String(150))
    etapa_ensino: Mapped[str] = mapped_column(String(50))
    legitimado: Mapped[bool] = mapped_column(Boolean, default=False)
    fundador_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), index=True)

    # Relação com a tabela associativa de membros
    membros: Mapped[List["MembroGremioORM"]] = relationship(back_populates="gremio", cascade="all, delete-orphan")
