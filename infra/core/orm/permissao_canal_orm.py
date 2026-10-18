from typing import Optional
from sqlalchemy import CheckConstraint, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from infra.database import Base


class PermissaoCanalORM(Base):
    """Sobrescrita de permissões em um canal, para um cargo OU para um usuário."""

    __tablename__ = "permissoes_canal"
    __table_args__ = (
        UniqueConstraint("canal_id", "cargo_id", name="uq_permissao_canal_cargo"),
        UniqueConstraint("canal_id", "usuario_id", name="uq_permissao_canal_usuario"),
        CheckConstraint(
            "(cargo_id IS NULL) != (usuario_id IS NULL)",
            name="ck_permissao_canal_alvo",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    canal_id: Mapped[int] = mapped_column(ForeignKey("canais.id", ondelete="CASCADE"), index=True)
    cargo_id: Mapped[Optional[int]] = mapped_column(ForeignKey("cargos.id", ondelete="CASCADE"), nullable=True)
    usuario_id: Mapped[Optional[int]] = mapped_column(ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=True)
    permitir: Mapped[int] = mapped_column(Integer, default=0)
    negar: Mapped[int] = mapped_column(Integer, default=0)
