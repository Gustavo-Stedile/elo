from fastapi import APIRouter, Depends, Response, status

from application import MembroService
from domain.core.permissoes import de_nomes
from presentation.deps.auth_deps import require_token
from presentation.deps.gremio_deps import get_membro_service
from presentation.schemas.membro_schemas import (
    MembroAdicionarSchema,
    MembroResposta,
)
from presentation.schemas.permissao_schemas import PermissoesSchema

router = APIRouter(prefix="/gremio/{gremio_id}/membros", tags=["Membros"])


@router.get("/", response_model=list[MembroResposta])
def listar_membros(
    gremio_id: int,
    usuario_id: int = Depends(require_token),
    service: MembroService = Depends(get_membro_service),
):
    membros = service.listar_membros(gremio_id, usuario_id)
    return [MembroResposta.de_detalhe(m) for m in membros]


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=MembroResposta)
def adicionar_membro(
    gremio_id: int,
    payload: MembroAdicionarSchema,
    usuario_id: int = Depends(require_token),
    service: MembroService = Depends(get_membro_service),
):
    membro = service.adicionar_membro(gremio_id, usuario_id, payload.usuario_id)
    return MembroResposta.de_detalhe(membro)


@router.delete("/{alvo_id}", status_code=status.HTTP_204_NO_CONTENT)
def remover_membro(
    gremio_id: int,
    alvo_id: int,
    usuario_id: int = Depends(require_token),
    service: MembroService = Depends(get_membro_service),
):
    """Remove um membro. Usar o próprio id equivale a sair do grêmio."""
    service.remover_membro(gremio_id, usuario_id, alvo_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put("/{alvo_id}/cargos/{cargo_id}", status_code=status.HTTP_204_NO_CONTENT)
def atribuir_cargo(
    gremio_id: int,
    alvo_id: int,
    cargo_id: int,
    usuario_id: int = Depends(require_token),
    service: MembroService = Depends(get_membro_service),
):
    service.atribuir_cargo(gremio_id, usuario_id, alvo_id, cargo_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/{alvo_id}/cargos/{cargo_id}", status_code=status.HTTP_204_NO_CONTENT)
def remover_cargo(
    gremio_id: int,
    alvo_id: int,
    cargo_id: int,
    usuario_id: int = Depends(require_token),
    service: MembroService = Depends(get_membro_service),
):
    service.remover_cargo(gremio_id, usuario_id, alvo_id, cargo_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put("/{alvo_id}/permissoes", response_model=MembroResposta)
def definir_permissoes_do_membro(
    gremio_id: int,
    alvo_id: int,
    payload: PermissoesSchema,
    usuario_id: int = Depends(require_token),
    service: MembroService = Depends(get_membro_service),
):
    """Permissões individuais do usuário no grêmio (substitui as atuais)."""
    membro = service.definir_permissoes_usuario(
        gremio_id,
        usuario_id,
        alvo_id,
        permitir=de_nomes(payload.permitir),
        negar=de_nomes(payload.negar),
    )
    return MembroResposta.de_detalhe(membro)
