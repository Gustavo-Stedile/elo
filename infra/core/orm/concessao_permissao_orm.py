from sqlalchemy import CheckConstraint, ForeignKey, Index, text
from sqlalchemy.orm import Mapped, mapped_column
from infra.database import Base


class ConcessaoPermissaoORM(Base):
    __tablename__ = "concessoes_permissoes"
    __table_args__ = (
        CheckConstraint(
            "(cargo_id IS NOT NULL AND membro_id IS NULL) OR "
            "(cargo_id IS NULL AND membro_id IS NOT NULL)",
            name="ck_concessao_permissao_alvo",
        ),
        Index(
            "uq_concessao_permissao_cargo",
            "permissao_id",
            "cargo_id",
            unique=True,
            sqlite_where=text("cargo_id IS NOT NULL"),
            postgresql_where=text("cargo_id IS NOT NULL"),
        ),
        Index(
            "uq_concessao_permissao_membro",
            "permissao_id",
            "membro_id",
            unique=True,
            sqlite_where=text("membro_id IS NOT NULL"),
            postgresql_where=text("membro_id IS NOT NULL"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    permissao_id: Mapped[int] = mapped_column(
        ForeignKey("permissoes_objeto.id", ondelete="CASCADE"), index=True
    )
    cargo_id: Mapped[int | None] = mapped_column(
        ForeignKey("cargos.id", ondelete="CASCADE"), nullable=True, index=True
    )
    membro_id: Mapped[int | None] = mapped_column(
        ForeignKey("membros_gremios.id", ondelete="CASCADE"), nullable=True, index=True
    )
