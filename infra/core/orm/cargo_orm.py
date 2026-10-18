from sqlalchemy import ForeignKey, String

from infra.database import Base
from sqlalchemy.orm import Mapped, mapped_column


class Cargo(Base):
  __tablename__ = "cargo"

  id: Mapped[int] = mapped_column(primary_key=True)
  nome: Mapped[str] = mapped_column(String(50))
  gremio_id: Mapped[int] = mapped_column(ForeignKey("gremio.id"))