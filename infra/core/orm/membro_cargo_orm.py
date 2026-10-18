from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from infra.database import Base


class MembroCargoORM(Base):
    __tablename__ = "membros_cargos"
    __table_args__ = (
        UniqueConstraint("membro_id", "cargo_id", name="uq_membro_cargo"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    membro_id: Mapped[int] = mapped_column(ForeignKey("membros_gremios.id", ondelete="CASCADE"), index=True)
    cargo_id: Mapped[int] = mapped_column(ForeignKey("cargos.id", ondelete="CASCADE"), index=True)
