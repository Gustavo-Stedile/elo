from typing import Optional
from sqlalchemy import String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from infra.database import Base


class CanalORM(Base):
    __tablename__ = "canais"
    __table_args__ = (
        UniqueConstraint("gremio_id", "nome", name="uq_canal_gremio_nome"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    gremio_id: Mapped[int] = mapped_column(ForeignKey("gremios.id", ondelete="CASCADE"), index=True)
    nome: Mapped[str] = mapped_column(String(100), nullable=False)
    descricao: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
