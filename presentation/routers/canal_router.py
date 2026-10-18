from fastapi import APIRouter, Depends, Response, status

from application import CanalService
from domain.core.permissoes import de_nomes
from presentation.deps.auth_deps import require_token
from presentation.deps.canal_deps import get_canal_service
from presentation.schemas.canal_schemas import (
    CanalAtualizarSchema,
    CanalCriarSchema,
    CanalResposta,
    PermissaoCanalResposta,
)
from presentation.schemas.permissao_schemas import PermissoesSchema

# Canais dentro de um grêmio (listar / criar)
gremio_canais_router = APIRouter(prefix="/gremio/{gremio_id}/canais", tags=["Canais"])

# Operações sobre um canal específico
router = APIRouter(prefix="/canal", tags=["Canais"])


@gremio_canais_router.get("/", response_model=list[CanalResposta])
def listar_canais(
    gremio_id: int,
    usuario_id: int = Depends(require_token),
    service: CanalService = Depends(get_canal_service),
):
    """Lista apenas os canais que o usuário tem permissão de ver."""
    canais = service.listar_canais(gremio_id, usuario_id)
    return [CanalResposta.de_dominio(c) for c in canais]


@gremio_canais_router.post("/", status_code=status.HTTP_201_CREATED, response_model=CanalResposta)
def criar_canal(
    gremio_id: int,
    payload: CanalCriarSchema,
    usuario_id: int = Depends(require_token),
    service: CanalService = Depends(get_canal_service),
):
    canal = service.criar_canal(gremio_id, usuario_id, payload.nome, payload.descricao)
    return CanalResposta.de_dominio(canal)


@router.get("/{canal_id}", response_model=CanalResposta)
def obter_canal(
    canal_id: int,
    usuario_id: int = Depends(require_token),
    service: CanalService = Depends(get_canal_service),
):
    acesso = service.obter_canal(canal_id, usuario_id)
    return CanalResposta.de_dominio(acesso.canal, acesso.permissoes)


@router.patch("/{canal_id}", response_model=CanalResposta)
def atualizar_canal(
    canal_id: int,
    payload: CanalAtualizarSchema,
    usuario_id: int = Depends(require_token),
    service: CanalService = Depends(get_canal_service),
):
    canal = service.atualizar_canal(
        canal_id, usuario_id, nome=payload.nome, descricao=payload.descricao
    )
    return CanalResposta.de_dominio(canal)


@router.delete("/{canal_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir_canal(
    canal_id: int,
    usuario_id: int = Depends(require_token),
    service: CanalService = Depends(get_canal_service),
):
    service.excluir_canal(canal_id, usuario_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------
# Permissões do canal (sobrescritas por cargo e por usuário)
# ---------------------------------------------------------------------
@router.get("/{canal_id}/permissoes", response_model=list[PermissaoCanalResposta])
def listar_permissoes_do_canal(
    canal_id: int,
    usuario_id: int = Depends(require_token),
    service: CanalService = Depends(get_canal_service),
):
    permissoes = service.listar_permissoes(canal_id, usuario_id)
    return [PermissaoCanalResposta.de_dominio(p) for p in permissoes]


@router.put("/{canal_id}/permissoes/cargos/{cargo_id}")
def definir_permissao_do_cargo(
    canal_id: int,
    cargo_id: int,
    payload: PermissoesSchema,
    usuario_id: int = Depends(require_token),
    service: CanalService = Depends(get_canal_service),
):
    """Substitui a sobrescrita do cargo no canal. Listas vazias a removem."""
    resultado = service.definir_permissao_cargo(
        canal_id, usuario_id, cargo_id,
        permitir=de_nomes(payload.permitir),
        negar=de_nomes(payload.negar),
    )
    if resultado is None:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    return PermissaoCanalResposta.de_dominio(resultado)


@router.delete("/{canal_id}/permissoes/cargos/{cargo_id}", status_code=status.HTTP_204_NO_CONTENT)
def remover_permissao_do_cargo(
    canal_id: int,
    cargo_id: int,
    usuario_id: int = Depends(require_token),
    service: CanalService = Depends(get_canal_service),
):
    service.remover_permissao_cargo(canal_id, usuario_id, cargo_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put("/{canal_id}/permissoes/usuarios/{alvo_id}")
def definir_permissao_do_usuario(
    canal_id: int,
    alvo_id: int,
    payload: PermissoesSchema,
    usuario_id: int = Depends(require_token),
    service: CanalService = Depends(get_canal_service),
):
    """Substitui a sobrescrita do usuário no canal. Listas vazias a removem."""
    resultado = service.definir_permissao_usuario(
        canal_id, usuario_id, alvo_id,
        permitir=de_nomes(payload.permitir),
        negar=de_nomes(payload.negar),
    )
    if resultado is None:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    return PermissaoCanalResposta.de_dominio(resultado)


@router.delete("/{canal_id}/permissoes/usuarios/{alvo_id}", status_code=status.HTTP_204_NO_CONTENT)
def remover_permissao_do_usuario(
    canal_id: int,
    alvo_id: int,
    usuario_id: int = Depends(require_token),
    service: CanalService = Depends(get_canal_service),
):
    service.remover_permissao_usuario(canal_id, usuario_id, alvo_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
