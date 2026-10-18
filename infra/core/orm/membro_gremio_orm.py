from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from infra.database import Base

class MembroGremioORM(Base):
    __tablename__ = "membros_gremios"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id", ondelete="CASCADE"))
    gremio_id: Mapped[int] = mapped_column(ForeignKey("gremios.id", ondelete="CASCADE"))
    cargo: Mapped[str] = mapped_column(String(50), default="membro")  # Ex: "fundador", "admin", "membro"

    # Ligações de volta para as entidades
    usuario: Mapped["UsuarioORM"] = relationship(back_populates="gremios_participantes")
    gremio: Mapped["GremioORM"] = relationship(back_populates="membros")