from fastapi import APIRouter, Depends, HTTPException, status

from application.exceptions.usuario_exceptions import (
    CPFJaCadastradoErro,
    EmailJaCadastradoErro,
    RAJaCadastradoErro,
    UsuarioNaoExisteErro,
)
from application.usuario_service import UsuarioService

from presentation.deps.auth_deps import require_token
from presentation.deps.usuario_deps import (
    get_usuario_service,
)

from presentation.schemas.usuario_schemas import UsuarioCadastroSchema

router = APIRouter(prefix="/usuario")

@router.post("/", status_code=status.HTTP_201_CREATED)
def cadastrar(
    payload: UsuarioCadastroSchema,
    service: UsuarioService = Depends(get_usuario_service),
):
    try:
        dados_cadastro = payload.model_dump()
        novo_usuario = service.criar_usuario(**dados_cadastro)

        return {
            "mensagem": "Usuário cadastrado com sucesso!",
            "usuario": novo_usuario
        }

    except CPFJaCadastradoErro as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )
    except EmailJaCadastradoErro as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )
    except RAJaCadastradoErro as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )

@router.get("/me")
def obter_usuario_logado(
    usuario_id: int = Depends(require_token),
    usuario_service: UsuarioService = Depends(get_usuario_service)
):
    try:
        usuario = usuario_service.buscar_por_id(usuario_id)
        return {
            "usuario": usuario
        }
    
    except UsuarioNaoExisteErro as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

@router.get("/{id}")
def obter_usuario(
    usuario_id: int = Depends(require_token),
    usuario_service: UsuarioService = Depends(get_usuario_service)
):
    try:
        usuario = usuario_service.buscar_por_id(usuario_id)
        return {
            "usuario": {
                "nome": usuario["nome"],
                "ra": usuario["ra"],
                "email": usuario["email"]
            }
        }
    
    except UsuarioNaoExisteErro as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )