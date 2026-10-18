from infra.database import SessionLocal
from infra.core.repositories import UsuarioRepository

from application import UsuarioService

def get_usuario_service() -> UsuarioService:
    db = SessionLocal()
    usuario_repo = UsuarioRepository(db)

    return UsuarioService(usuario_repo)
