from fastapi import Depends
from sqlalchemy.orm import Session

from infra.core.repositories import UsuarioRepository
from presentation.deps.db_deps import get_db

from application import UsuarioService

def get_usuario_service(db: Session = Depends(get_db)) -> UsuarioService:
    usuario_repo = UsuarioRepository(db)

    return UsuarioService(usuario_repo)
