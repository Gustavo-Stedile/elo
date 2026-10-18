from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
import jwt

from infra.core.repositories import (
    UsuarioRepository
)
from presentation.deps.db_deps import get_db

from application import AuthService
from presentation.security import SECRET_KEY, ALGORITHM


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    usuario_repo = UsuarioRepository(db)

    return AuthService(usuario_repo)


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth")

def require_token(
    token: str = Depends(oauth2_scheme),
) -> dict:
    credential_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Usuário não autenticado",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise credential_exception

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        usuario_id = payload.get("sub")

        if usuario_id is None:
            raise credential_exception

    except jwt.PyJWTError:
        raise credential_exception

    return int(usuario_id)