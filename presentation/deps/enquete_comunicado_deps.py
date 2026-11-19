from fastapi import Depends
from sqlalchemy.orm import Session

from application import EnqueteService, ComunicadoService
from infra.core.repositories import (
    EnqueteRepository,
    ComunicadoRepository,
    CargoRepository,
    PermissaoObjetoRepository,
    UsuarioRepository,
)
from application import PermissaoRelacionalService
from infra.unit_of_work import UnitOfWork
from presentation.deps.db_deps import get_db
from presentation.deps.gremio_deps import get_autorizacao_service
from application.autorizacao_service import AutorizacaoService


def get_enquete_service(
    db: Session = Depends(get_db),
    autorizacao: AutorizacaoService = Depends(get_autorizacao_service),
) -> EnqueteService:
    return EnqueteService(
        EnqueteRepository(db),
        UsuarioRepository(db),
        autorizacao,
        UnitOfWork(db),
        CargoRepository(db),
        PermissaoRelacionalService(PermissaoObjetoRepository(db)),
    )


def get_comunicado_service(
    db: Session = Depends(get_db),
    autorizacao: AutorizacaoService = Depends(get_autorizacao_service),
) -> ComunicadoService:
    return ComunicadoService(
        ComunicadoRepository(db),
        UsuarioRepository(db),
        autorizacao,
        UnitOfWork(db),
        CargoRepository(db),
        PermissaoRelacionalService(PermissaoObjetoRepository(db)),
    )
