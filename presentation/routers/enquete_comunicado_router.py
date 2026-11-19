from fastapi import APIRouter, Depends

from application import EnqueteService, ComunicadoService
from presentation.deps.auth_deps import require_token
from presentation.deps.enquete_comunicado_deps import (
    get_enquete_service,
    get_comunicado_service,
)
from presentation.schemas.enquete_comunicado_schemas import (
    EnqueteCriarSchema,
    EnqueteVotarSchema,
    EnqueteResposta,
    ComunicadoCriarSchema,
    ComunicadoResposta,
)

enquete_gremio_router = APIRouter(prefix="/gremio/{gremio_id}")
enquete_canal_router = APIRouter(prefix="/canal/{canal_id}")
comunicado_router = APIRouter(prefix="/gremio/{gremio_id}/comunicados", tags=["Comunicados"])


@enquete_gremio_router.post("/enquetes", response_model=EnqueteResposta)
def criar_enquete_gremio(
    gremio_id: int,
    payload: EnqueteCriarSchema,
    usuario_id: int = Depends(require_token),
    service: EnqueteService = Depends(get_enquete_service),
):
    return EnqueteResposta.de_dominio(service.criar(
        gremio_id, usuario_id, payload.pergunta, payload.opcoes,
        payload.tipo_votacao, payload.votos_visiveis,
    ))


@enquete_gremio_router.get("/enquetes", response_model=list[EnqueteResposta])
def listar_enquetes_gremio(
    gremio_id: int,
    usuario_id: int = Depends(require_token),
    service: EnqueteService = Depends(get_enquete_service),
):
    return [EnqueteResposta.de_dominio(e) for e in service.listar(gremio_id, usuario_id)]


@enquete_canal_router.post("/enquetes", response_model=EnqueteResposta)
def criar_enquete_canal(
    canal_id: int,
    payload: EnqueteCriarSchema,
    usuario_id: int = Depends(require_token),
    service: EnqueteService = Depends(get_enquete_service),
):
    # O grêmio é identificado por meio da autorização no CanalService.
    acesso = service.autorizacao.acessar_canal(canal_id, usuario_id)
    e = service.criar(
        acesso.canal.gremio_id, usuario_id, payload.pergunta,
        payload.opcoes, payload.tipo_votacao, payload.votos_visiveis,
        canal_id=canal_id,
    )
    return EnqueteResposta.de_dominio(e)


@enquete_canal_router.get("/enquetes", response_model=list[EnqueteResposta])
def listar_enquetes_canal(
    canal_id: int,
    usuario_id: int = Depends(require_token),
    service: EnqueteService = Depends(get_enquete_service),
):
    acesso = service.autorizacao.acessar_canal(canal_id, usuario_id)
    return [
        EnqueteResposta.de_dominio(e)
        for e in service.listar(acesso.canal.gremio_id, usuario_id, canal_id)
    ]


@enquete_gremio_router.post("/enquetes/{enquete_id}/votos", response_model=EnqueteResposta)
def votar_enquete(
    gremio_id: int,
    enquete_id: int,
    payload: EnqueteVotarSchema,
    usuario_id: int = Depends(require_token),
    service: EnqueteService = Depends(get_enquete_service),
):
    return EnqueteResposta.de_dominio(
        service.votar(gremio_id, enquete_id, usuario_id, payload.opcao_ids)
    )


@enquete_canal_router.post("/comunicados", response_model=ComunicadoResposta)
def criar_comunicado_canal(
    canal_id: int,
    payload: ComunicadoCriarSchema,
    usuario_id: int = Depends(require_token),
    service: ComunicadoService = Depends(get_comunicado_service),
):
    acesso = service.autorizacao.acessar_canal(
        canal_id, usuario_id
    )
    return ComunicadoResposta.de_dominio(
        service.criar(
            acesso.canal.gremio_id,
            usuario_id,
            payload.titulo,
            payload.texto,
            payload.valido_ate,
            canal_id=canal_id,
        )
    )


@enquete_canal_router.get("/comunicados", response_model=list[ComunicadoResposta])
def listar_comunicados_canal(
    canal_id: int,
    usuario_id: int = Depends(require_token),
    service: ComunicadoService = Depends(get_comunicado_service),
):
    acesso = service.autorizacao.acessar_canal(canal_id, usuario_id)
    return [
        ComunicadoResposta.de_dominio(comunicado)
        for comunicado in service.listar(
            acesso.canal.gremio_id, usuario_id, canal_id=canal_id
        )
    ]


@comunicado_router.post("", response_model=ComunicadoResposta)
def criar_comunicado(
    gremio_id: int,
    payload: ComunicadoCriarSchema,
    usuario_id: int = Depends(require_token),
    service: ComunicadoService = Depends(get_comunicado_service),
):
    return ComunicadoResposta.de_dominio(service.criar(
        gremio_id, usuario_id, payload.titulo, payload.texto, payload.valido_ate
    ))


@comunicado_router.get("", response_model=list[ComunicadoResposta])
def listar_comunicados(
    gremio_id: int,
    usuario_id: int = Depends(require_token),
    service: ComunicadoService = Depends(get_comunicado_service),
):
    return [
        ComunicadoResposta.de_dominio(c)
        for c in service.listar(gremio_id, usuario_id)
    ]
