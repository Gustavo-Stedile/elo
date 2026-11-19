from sqlalchemy import String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from infra.database import Base


class PermissaoGlobalORM(Base):
    __tablename__ = "permissoes_globais"
    __table_args__ = (
        UniqueConstraint("codigo", name="uq_permissao_global_codigo"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    codigo: Mapped[str] = mapped_column(String(80))
    nome: Mapped[str] = mapped_column(String(120))
    descricao: Mapped[str | None] = mapped_column(Text, nullable=True)
