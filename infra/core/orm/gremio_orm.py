from typing import List
from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from infra.database import Base

class GremioORM(Base):
    __tablename__ = "gremios"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    nome: Mapped[str] = mapped_column(String(100))
    instituicao: Mapped[str] = mapped_column(String(150))
    etapa_ensino: Mapped[str] = mapped_column(String(50))
    legitimado: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relação com a tabela associativa de membros
    membros: Mapped[List["MembroGremioORM"]] = relationship(back_populates="gremio", cascade="all, delete-orphan")