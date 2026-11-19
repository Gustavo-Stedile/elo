from fastapi import Depends
from sqlalchemy.orm import Session

from infra.core.repositories import (
    GremioRepository,
    MembroGremioRepository,
    UsuarioRepository,
)
from infra.unit_of_work import UnitOfWork
from presentation.deps.db_deps import get_db

from application import UsuarioService

def get_usuario_service(db: Session = Depends(get_db)) -> UsuarioService:
    return UsuarioService(
        UsuarioRepository(db),
        GremioRepository(db),
        MembroGremioRepository(db),
        UnitOfWork(db),
    )
