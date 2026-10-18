from infra.core.repositories import (
    GremioRepository, MembroGremioRepository
)
from infra.database import SessionLocal

from application import GremioService


def get_gremio_service() -> GremioService:
    db = SessionLocal()

    gremio_repo = GremioRepository(db)
    usuario_repo = MembroGremioRepository(db)


    return GremioService(gremio_repo, usuario_repo)

