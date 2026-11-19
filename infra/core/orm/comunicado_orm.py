from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from infra.database import Base


class ComunicadoORM(Base):
    __tablename__ = "comunicados"
    id: Mapped[int] = mapped_column(primary_key=True)
    gremio_id: Mapped[int] = mapped_column(ForeignKey("gremios.id", ondelete="CASCADE"), index=True)
    canal_id: Mapped[int | None] = mapped_column(ForeignKey("canais.id", ondelete="CASCADE"), nullable=True)
    autor_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id", ondelete="CASCADE"), index=True)
    titulo: Mapped[str] = mapped_column(String(255))
    texto: Mapped[str] = mapped_column(Text)
    valido_ate: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True))
