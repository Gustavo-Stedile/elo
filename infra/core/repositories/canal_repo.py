from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from application.exceptions.canal_exceptions import CanalJaExisteErro
from domain.core import Canal
from infra.core.orm import CanalORM
from infra.core.mappers.canal_mappers import canal_to_domain, canal_to_orm


class CanalRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, canal: Canal) -> Canal:
        try:
            orm_obj = canal_to_orm(canal)
            self.db.add(orm_obj)
            self.db.flush()
            return canal_to_domain(orm_obj)
        except IntegrityError as e:
            self.db.rollback()
            self._tratar_integridade(e)

    def get_by_id(self, id: int) -> Canal | None:
        return canal_to_domain(self.db.get(CanalORM, id))

    def listar_por_gremio(self, gremio_id: int) -> list[Canal]:
        stmt = (
            select(CanalORM)
            .where(CanalORM.gremio_id == gremio_id)
            .order_by(CanalORM.id)
        )
        return [canal_to_domain(c) for c in self.db.scalars(stmt).all()]

    def update(self, canal: Canal) -> Canal:
        try:
            orm_obj = self.db.get(CanalORM, canal.id)
            orm_obj.nome = canal.nome
            orm_obj.descricao = canal.descricao
            self.db.flush()
            return canal_to_domain(orm_obj)
        except IntegrityError as e:
            self.db.rollback()
            self._tratar_integridade(e)

    def delete(self, canal_id: int) -> None:
        orm_obj = self.db.get(CanalORM, canal_id)
        if orm_obj:
            self.db.delete(orm_obj)
            self.db.flush()

    @staticmethod
    def _tratar_integridade(e: IntegrityError):
        if "unique" in str(e.orig).lower():
            raise CanalJaExisteErro()
        raise e
