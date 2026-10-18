from fastapi import APIRouter, Depends, Response, status

from application import CargoService
from domain.core.permissoes import de_nomes
from presentation.deps.auth_deps import require_token
from presentation.deps.gremio_deps import get_cargo_service
from presentation.schemas.cargo_schemas import (
    CargoAtualizarSchema,
    CargoCriarSchema,
    CargoResposta,
)

router = APIRouter(prefix="/gremio/{gremio_id}/cargos", tags=["Cargos"])


@router.get("/", response_model=list[CargoResposta])
def listar_cargos(
    gremio_id: int,
    usuario_id: int = Depends(require_token),
    service: CargoService = Depends(get_cargo_service),
):
    cargos = service.listar_cargos(gremio_id, usuario_id)
    return [CargoResposta.de_dominio(c) for c in cargos]


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=CargoResposta)
def criar_cargo(
    gremio_id: int,
    payload: CargoCriarSchema,
    usuario_id: int = Depends(require_token),
    service: CargoService = Depends(get_cargo_service),
):
    cargo = service.criar_cargo(
        gremio_id,
        usuario_id,
        nome=payload.nome,
        cor=payload.cor,
        prioridade=payload.prioridade,
        permissoes=de_nomes(payload.permissoes),
    )
    return CargoResposta.de_dominio(cargo)


@router.patch("/{cargo_id}", response_model=CargoResposta)
def atualizar_cargo(
    gremio_id: int,
    cargo_id: int,
    payload: CargoAtualizarSchema,
    usuario_id: int = Depends(require_token),
    service: CargoService = Depends(get_cargo_service),
):
    cargo = service.atualizar_cargo(
        gremio_id,
        cargo_id,
        usuario_id,
        nome=payload.nome,
        cor=payload.cor,
        prioridade=payload.prioridade,
        permissoes=(
            None if payload.permissoes is None else de_nomes(payload.permissoes)
        ),
    )
    return CargoResposta.de_dominio(cargo)


@router.delete("/{cargo_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir_cargo(
    gremio_id: int,
    cargo_id: int,
    usuario_id: int = Depends(require_token),
    service: CargoService = Depends(get_cargo_service),
):
    service.excluir_cargo(gremio_id, cargo_id, usuario_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
