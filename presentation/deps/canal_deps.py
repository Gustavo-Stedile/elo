from fastapi import Depends
from sqlalchemy.orm import Session

from infra.core.repositories import (
    CanalRepository,
    CargoRepository,
    MembroGremioRepository,
    MensagemRepository,
    PermissaoCanalRepository,
    UsuarioRepository,
)
from infra.unit_of_work import UnitOfWork
from presentation.deps.db_deps import get_db
from presentation.deps.gremio_deps import get_autorizacao_service

from application import AutorizacaoService, CanalService, MensagemService


def get_canal_service(
    db: Session = Depends(get_db),
    autorizacao: AutorizacaoService = Depends(get_autorizacao_service),
) -> CanalService:
    return CanalService(
        canal_repository=CanalRepository(db),
        permissao_canal_repository=PermissaoCanalRepository(db),
        cargo_repository=CargoRepository(db),
        membro_gremio_repository=MembroGremioRepository(db),
        autorizacao=autorizacao,
        uow=UnitOfWork(db),
    )


def get_mensagem_service(
    db: Session = Depends(get_db),
    autorizacao: AutorizacaoService = Depends(get_autorizacao_service),
) -> MensagemService:
    return MensagemService(
        mensagem_repository=MensagemRepository(db),
        usuario_repository=UsuarioRepository(db),
        autorizacao=autorizacao,
        uow=UnitOfWork(db),
    )
