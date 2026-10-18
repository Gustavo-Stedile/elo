from datetime import datetime
from typing import Optional
from sqlalchemy import DateTime, ForeignKey, Index, Text
from sqlalchemy.orm import Mapped, mapped_column
from infra.database import Base


class MensagemORM(Base):
    __tablename__ = "mensagens"
    __table_args__ = (
        Index("ix_mensagens_canal_id_id", "canal_id", "id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    canal_id: Mapped[int] = mapped_column(ForeignKey("canais.id", ondelete="CASCADE"))
    autor_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id", ondelete="CASCADE"), index=True)
    conteudo: Mapped[str] = mapped_column(Text)
    criada_em: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    editada_em: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
