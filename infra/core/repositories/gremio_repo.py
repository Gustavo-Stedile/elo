from sqlalchemy import select
from sqlalchemy.orm import Session
from application.exceptions.gremio_exceptions import GremioNaoExisteErro
from domain.core import Gremio
from infra.core.orm import GremioORM, MembroGremioORM
from infra.core.mappers.gremio_mappers import (
    gremio_to_domain,
    gremio_to_orm
)


class GremioRepository:
    """Os métodos de escrita apenas fazem flush; o commit é do UnitOfWork."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, id: int) -> Gremio | None:
        orm_gremio = self.db.get(GremioORM, id)
        return gremio_to_domain(orm_gremio)

    def get_all(self) -> list[Gremio]:
        orm_gremios = self.db.query(GremioORM).all()
        return [gremio_to_domain(g) for g in orm_gremios]

    def listar_por_usuario(self, usuario_id: int) -> list[Gremio]:
        """Grêmios dos quais o usuário é membro."""
        stmt = (
            select(GremioORM)
            .join(MembroGremioORM, MembroGremioORM.gremio_id == GremioORM.id)
            .where(MembroGremioORM.usuario_id == usuario_id)
            .order_by(GremioORM.id)
        )
        return [gremio_to_domain(g) for g in self.db.scalars(stmt).all()]

    def create(self, gremio: Gremio) -> Gremio:
        orm_gremio = gremio_to_orm(gremio)
        self.db.add(orm_gremio)
        self.db.flush()
        return gremio_to_domain(orm_gremio)

    def update(self, gremio: Gremio) -> Gremio:
        orm_gremio = self.db.get(GremioORM, gremio.id)

        if not orm_gremio:
            raise GremioNaoExisteErro()
        
        orm_gremio.nome = gremio.nome
        orm_gremio.instituicao = gremio.instituicao
        orm_gremio.etapa_ensino = gremio.etapa_ensino
        orm_gremio.legitimado = gremio.legitimado
        
        self.db.flush()
        return gremio_to_domain(orm_gremio)
