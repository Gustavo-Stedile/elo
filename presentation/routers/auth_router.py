from fastapi import APIRouter, Depends, status, HTTPException

from application import AuthService

from application.exceptions.auth_exceptions import CredenciaisInvalidasErro
from presentation.schemas.auth_schemas import AuthSchema
from presentation.deps.auth_deps import get_auth_service
from presentation.security import create_access_token

router = APIRouter(prefix="/auth", tags=["Usuário"])

@router.post("/")
def login(
    payload: AuthSchema,
    service: AuthService = Depends(get_auth_service)
):
    try:
        usuario_id = service.autenticar(payload.email, payload.senha)

        token_payload = {
            "sub": str(usuario_id),
        }

        token = create_access_token(token_payload)

        return {"access_token": token, "token_type": "bearer"}

    except CredenciaisInvalidasErro as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )