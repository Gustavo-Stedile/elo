from sqlalchemy import Boolean, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from infra.database import Base


class CargoORM(Base):
    __tablename__ = "cargos"
    __table_args__ = (
        UniqueConstraint("gremio_id", "nome", name="uq_cargo_gremio_nome"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    gremio_id: Mapped[int] = mapped_column(ForeignKey("gremios.id", ondelete="CASCADE"), index=True)
    nome: Mapped[str] = mapped_column(String(50))
    cor: Mapped[str] = mapped_column(String(7), default="#99AAB5")
    prioridade: Mapped[int] = mapped_column(Integer, default=0)
    permissoes: Mapped[int] = mapped_column(Integer, default=0)
    padrao: Mapped[bool] = mapped_column(Boolean, default=False)
