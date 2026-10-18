from fastapi import Depends
from sqlalchemy.orm import Session

from infra.core.repositories import (
    CanalRepository,
    CargoRepository,
    GremioRepository,
    MembroGremioRepository,
    PermissaoCanalRepository,
    UsuarioRepository,
)
from infra.unit_of_work import UnitOfWork
from presentation.deps.db_deps import get_db

from application import (
    AutorizacaoService,
    CargoService,
    GremioService,
    MembroService,
)


def get_autorizacao_service(db: Session = Depends(get_db)) -> AutorizacaoService:
    return AutorizacaoService(
        gremio_repository=GremioRepository(db),
        membro_gremio_repository=MembroGremioRepository(db),
        cargo_repository=CargoRepository(db),
        canal_repository=CanalRepository(db),
        permissao_canal_repository=PermissaoCanalRepository(db),
    )


def get_gremio_service(
    db: Session = Depends(get_db),
    autorizacao: AutorizacaoService = Depends(get_autorizacao_service),
) -> GremioService:
    return GremioService(
        gremio_repository=GremioRepository(db),
        membro_gremio_repository=MembroGremioRepository(db),
        cargo_repository=CargoRepository(db),
        canal_repository=CanalRepository(db),
        usuario_repository=UsuarioRepository(db),
        autorizacao=autorizacao,
        uow=UnitOfWork(db),
    )


def get_membro_service(
    db: Session = Depends(get_db),
    autorizacao: AutorizacaoService = Depends(get_autorizacao_service),
) -> MembroService:
    return MembroService(
        gremio_repository=GremioRepository(db),
        membro_gremio_repository=MembroGremioRepository(db),
        cargo_repository=CargoRepository(db),
        permissao_canal_repository=PermissaoCanalRepository(db),
        usuario_repository=UsuarioRepository(db),
        autorizacao=autorizacao,
        uow=UnitOfWork(db),
    )


def get_cargo_service(
    db: Session = Depends(get_db),
    autorizacao: AutorizacaoService = Depends(get_autorizacao_service),
) -> CargoService:
    return CargoService(
        cargo_repository=CargoRepository(db),
        autorizacao=autorizacao,
        uow=UnitOfWork(db),
    )
