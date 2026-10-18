from sqlalchemy import Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from infra.database import Base

class MembroGremioORM(Base):
    __tablename__ = "membros_gremios"
    __table_args__ = (
        UniqueConstraint("usuario_id", "gremio_id", name="uq_usuario_gremio"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id", ondelete="CASCADE"), index=True)
    gremio_id: Mapped[int] = mapped_column(ForeignKey("gremios.id", ondelete="CASCADE"), index=True)

    # Sobrescritas individuais de permissão no grêmio (bitmask)
    permissoes_permitidas: Mapped[int] = mapped_column(Integer, default=0)
    permissoes_negadas: Mapped[int] = mapped_column(Integer, default=0)

    # Ligações de volta para as entidades
    usuario: Mapped["UsuarioORM"] = relationship(back_populates="gremios_participantes")
    gremio: Mapped["GremioORM"] = relationship(back_populates="membros")
