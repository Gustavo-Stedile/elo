from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from infra.database import Base


class ConcessaoPermissaoGlobalORM(Base):
    __tablename__ = "concessoes_permissoes_globais"
    __table_args__ = (
        UniqueConstraint(
            "permissao_id",
            "usuario_id",
            name="uq_concessao_permissao_global_usuario",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    permissao_id: Mapped[int] = mapped_column(
        ForeignKey("permissoes_globais.id", ondelete="CASCADE"), index=True
    )
    usuario_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id", ondelete="CASCADE"), index=True
    )
