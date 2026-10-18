from typing import List, Optional
from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from infra.database import Base

class UsuarioORM(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    nome: Mapped[str] = mapped_column(String(100))
    cpf: Mapped[str] = mapped_column(String(14), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    ra: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=True)
    senha: Mapped[str] = mapped_column(String(255))

    # Relação com a tabela associativa de membros
    gremios_participantes: Mapped[List["MembroGremioORM"]] = relationship(back_populates="usuario", cascade="all, delete-orphan")