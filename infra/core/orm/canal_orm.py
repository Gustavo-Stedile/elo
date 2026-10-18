from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from infra.database import Base

class Canal(Base):
    __tablename__ = "canais"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    nome: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    gremio_id: Mapped[int] = mapped_column(ForeignKey("gremios.id"), nullable=False)

