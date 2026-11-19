from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from infra.database import Base


class PermissaoObjetoORM(Base):
    __tablename__ = "permissoes_objeto"
    __table_args__ = (
        Index(
            "uq_permissao_gremio_recurso_codigo",
            "recurso_tipo",
            "recurso_id",
            "codigo",
            unique=True,
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    gremio_id: Mapped[int] = mapped_column(
        ForeignKey("gremios.id", ondelete="CASCADE"), index=True
    )
    recurso_tipo: Mapped[str] = mapped_column(String(20))
    recurso_id: Mapped[int] = mapped_column(index=True)
    codigo: Mapped[str] = mapped_column(String(80))
    nome: Mapped[str] = mapped_column(String(120))
    descricao: Mapped[str | None] = mapped_column(Text, nullable=True)
