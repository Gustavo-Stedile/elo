from fastapi import APIRouter, Depends, HTTPException, status

from application import GremioService
from presentation.deps.auth_deps import require_token
from presentation.deps.gremio_deps import get_gremio_service

from application.exceptions.usuario_exceptions import UsuarioNaoExisteErro

from presentation.schemas.gremio_schemas import (
    GremioCriarSchema,
)

router = APIRouter(prefix="/gremio", tags=["Grêmio"])


@router.post("/", status_code=status.HTTP_201_CREATED)
def criar_gremio(
    payload: GremioCriarSchema,
    usuario_id: dict = Depends(require_token),
    service: GremioService = Depends(get_gremio_service),
):
    try:
        gremio = service.criar_gremio(
            payload.nome_gremio,
            instituicao="eita",
            etapa_ensino="eita",
            fundador_id=usuario_id
        )

        return {
            "mensagem": "Grêmio criado com sucesso!",
            "gremio": gremio
        }
    
    except UsuarioNaoExisteErro as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.get("/")
def listar_meus_gremios(
    usuario_id: int = Depends(require_token),
    service: GremioService = Depends(get_gremio_service),
):
    """Grêmios dos quais o usuário logado é membro."""
    return {"gremios": service.listar_do_usuario(usuario_id)}


@router.get("/{gremio_id}")
def obter_gremio(
    gremio_id: int,
    usuario_id: int = Depends(require_token),
    service: GremioService = Depends(get_gremio_service),
):
    return {"gremio": service.obter_do_membro(gremio_id, usuario_id)}


@router.get("/{gremio_id}/permissoes/me")
def minhas_permissoes_no_gremio(
    gremio_id: int,
    usuario_id: int = Depends(require_token),
    service: GremioService = Depends(get_gremio_service),
):
    """Permissões efetivas do usuário logado no grêmio."""
    return service.minhas_permissoes(gremio_id, usuario_id)


# @router.patch("/{gremio_idelo}/legitimar")
# @router.put("/{gremio_idelo}/legitimar")
# def legitimar_gremio(
#     gremio_idelo: int,
#     usuario_atual: dict = Depends(obter_usuario_atual),
#     service: ServicoGremio = Depends(get_gremio_service),
# ):
#     try:
#         gremio = service.legitimar_gremio(gremio_idelo=gremio_idelo)
#         return {
#             "mensagem": "Grêmio legitimado com sucesso!",
#             "gremio": {
#                 "idelo": gremio.idelo,
#                 "nome": gremio.nome,
#                 "instituicao_idelo": gremio.instituicao_idelo,
#                 "etapa_ensino": gremio.etapa_ensino,
#                 "legitimado": gremio.legitimado,
#                 "fundador_idelo": gremio.fundador_idelo,
#                 "cargo_adm_idelo": gremio.cargo_adm_idelo,
#             },
#         }
#     except GremioNaoExisteErro:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Grêmio não encontrado.",
#         )


# @router.patch("/{gremio_idelo}")
# @router.put("/{gremio_idelo}")
# def atualizar_gremio(
#     gremio_idelo: int,
#     payload: GremioAtualizarSchema,
#     usuario_atual: dict = Depends(obter_usuario_atual),
#     service: ServicoGremio = Depends(get_gremio_service),
# ):
#     try:
#         gremio = service.atualizar_gremio(
#             gremio_idelo=gremio_idelo,
#             nome=payload.nome_gremio,
#         )
#         return {
#             "mensagem": "Grêmio atualizado com sucesso!",
#             "gremio": {
#                 "idelo": gremio.idelo,
#                 "nome": gremio.nome,
#                 "instituicao_idelo": gremio.instituicao_idelo,
#                 "etapa_ensino": gremio.etapa_ensino,
#                 "legitimado": gremio.legitimado,
#                 "fundador_idelo": gremio.fundador_idelo,
#                 "cargo_adm_idelo": gremio.cargo_adm_idelo,
#             },
#         }
#     except GremioNaoExisteErro:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Grêmio não encontrado.",
#         )


# @router.get("/{gremio_idelo}")
# def buscar_por_id(
#     gremio_idelo: int,
#     usuario_atual: dict = Depends(obter_usuario_atual),
#     service: ServicoGremio = Depends(get_gremio_service),
# ):
#     try:
#         gremio = service.obter_por_id(gremio_idelo=gremio_idelo)
#         return {
#             "idelo": gremio.idelo,
#             "nome": gremio.nome,
#             "instituicao_idelo": gremio.instituicao_idelo,
#             "etapa_ensino": gremio.etapa_ensino,
#             "legitimado": gremio.legitimado,
#             "fundador_idelo": gremio.fundador_idelo,
#             "cargo_adm_idelo": gremio.cargo_adm_idelo,
#         }
#     except GremioNaoExisteErro:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Grêmio não encontrado.",
#         )

# @router.patch("/{gremio_idelo}")
# @router.put("/{gremio_idelo}")
# def atualizar_gremio(
#     gremio_idelo: int,
#     payload: GremioAtualizarSchema,
#     usuario_atual: dict = Depends(obter_usuario_atual),
#     service: ServicoGremio = Depends(get_gremio_service),
# ):
#     try:
#         gremio = service.atualizar_gremio(
#             gremio_idelo=gremio_idelo,
#             nome=payload.nome_gremio,
#         )
#         return {
#             "mensagem": "Grêmio atualizado com sucesso!",
#             "gremio": {
#                 "idelo": gremio.idelo,
#                 "nome": gremio.nome,
#                 "instituicao_idelo": gremio.instituicao_idelo,
#                 "etapa_ensino": gremio.etapa_ensino,
#                 "legitimado": gremio.legitimado,
#                 "fundador_idelo": gremio.fundador_idelo,
#                 "cargo_adm_idelo": gremio.cargo_adm_idelo,
#             },
#         }
#     except GremioNaoExisteErro:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Grêmio não encontrado.",
#         )


# @router.get("/{gremio_idelo}")
# def buscar_por_id(
#     gremio_idelo: int,
#     usuario_atual: dict = Depends(obter_usuario_atual),
#     service: ServicoGremio = Depends(get_gremio_service),
# ):
#     try:
#         gremio = service.obter_por_id(gremio_idelo=gremio_idelo)
#         return {
#             "idelo": gremio.idelo,
#             "nome": gremio.nome,
#             "instituicao_idelo": gremio.instituicao_idelo,
#             "etapa_ensino": gremio.etapa_ensino,
#             "legitimado": gremio.legitimado,
#             "fundador_idelo": gremio.fundador_idelo,
#             "cargo_adm_idelo": gremio.cargo_adm_idelo,
#         }
#     except GremioNaoExisteErro:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Grêmio não encontrado.",
#         )

