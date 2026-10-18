from typing import Optional

from fastapi import APIRouter, Depends, Query, Response, status

from application import MensagemService
from presentation.deps.auth_deps import require_token
from presentation.deps.canal_deps import get_mensagem_service
from presentation.schemas.mensagem_schemas import (
    MensagemEnviarSchema,
    MensagemResposta,
)

router = APIRouter(prefix="/canal/{canal_id}/mensagens", tags=["Mensagens"])


@router.get("/", response_model=list[MensagemResposta])
def listar_mensagens(
    canal_id: int,
    limite: int = Query(50, ge=1, le=100),
    antes_de: Optional[int] = Query(None, description="Página anterior: mensagens com id menor que este"),
    depois_de: Optional[int] = Query(None, description="Novas mensagens: id maior que este (polling)"),
    usuario_id: int = Depends(require_token),
    service: MensagemService = Depends(get_mensagem_service),
):
    """Em ordem cronológica. Sem filtros, devolve as mais recentes."""
    mensagens = service.listar(
        canal_id, usuario_id,
        limite=limite, antes_de=antes_de, depois_de=depois_de,
    )
    return [MensagemResposta.de_dominio(m) for m in mensagens]


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=MensagemResposta)
def enviar_mensagem(
    canal_id: int,
    payload: MensagemEnviarSchema,
    usuario_id: int = Depends(require_token),
    service: MensagemService = Depends(get_mensagem_service),
):
    mensagem = service.enviar(canal_id, usuario_id, payload.conteudo)
    return MensagemResposta.de_dominio(mensagem)


@router.patch("/{mensagem_id}", response_model=MensagemResposta)
def editar_mensagem(
    canal_id: int,
    mensagem_id: int,
    payload: MensagemEnviarSchema,
    usuario_id: int = Depends(require_token),
    service: MensagemService = Depends(get_mensagem_service),
):
    mensagem = service.editar(canal_id, mensagem_id, usuario_id, payload.conteudo)
    return MensagemResposta.de_dominio(mensagem)


@router.delete("/{mensagem_id}", status_code=status.HTTP_204_NO_CONTENT)
def apagar_mensagem(
    canal_id: int,
    mensagem_id: int,
    usuario_id: int = Depends(require_token),
    service: MensagemService = Depends(get_mensagem_service),
):
    service.apagar(canal_id, mensagem_id, usuario_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
