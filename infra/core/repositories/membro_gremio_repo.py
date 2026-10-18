from typing import List
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from domain.core import MembroGremio
from infra.core.orm.membro_gremio_orm import MembroGremioORM
from infra.core.mappers.membro_gremio_mappers import (
    membro_gremio_to_domain,
    membro_gremio_to_orm,
)

from application.exceptions.membro_gremio_exceptions import (
    MembroJaExisteErro,
    UsuarioOuGremioNaoEncontradoErro
)


class MembroGremioRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, membro: MembroGremio) -> MembroGremio:
        """Cria o vínculo usuário-grêmio com tratamento de integridade."""
        try:
            orm_obj = membro_gremio_to_orm(membro)

            self.db.add(orm_obj)
            self.db.flush()

            return membro_gremio_to_domain(orm_obj)

        except IntegrityError as e:
            self.db.rollback()
            erro_msg = str(e.orig).lower()

            # Se violar a UniqueConstraint (usuário já está no grêmio)
            if "unique" in erro_msg or "uq_usuario_gremio" in erro_msg:
                raise MembroJaExisteErro()

            # Se violar a ForeignKey (ID de usuário ou grêmio inválido)
            if "foreign key" in erro_msg or "fk_" in erro_msg:
                raise UsuarioOuGremioNaoEncontradoErro()

            # Se for outro erro de integridade desconhecido, propaga a exceção original
            raise e

    def get(self, gremio_id: int, usuario_id: int) -> MembroGremio | None:
        stmt = select(MembroGremioORM).where(
            MembroGremioORM.gremio_id == gremio_id,
            MembroGremioORM.usuario_id == usuario_id,
        )
        return membro_gremio_to_domain(self.db.scalars(stmt).first())

    def listar_por_gremio(self, gremio_id: int) -> List[MembroGremio]:
        """Retorna todos os membros associados a um determinado grêmio."""
        stmt = (
            select(MembroGremioORM)
            .where(MembroGremioORM.gremio_id == gremio_id)
            .order_by(MembroGremioORM.id)
        )
        return [membro_gremio_to_domain(obj) for obj in self.db.scalars(stmt).all()]

    def atualizar_permissoes(self, membro: MembroGremio) -> MembroGremio:
        orm_obj = self.db.get(MembroGremioORM, membro.id)
        orm_obj.permissoes_permitidas = membro.permissoes_permitidas
        orm_obj.permissoes_negadas = membro.permissoes_negadas
        self.db.flush()
        return membro_gremio_to_domain(orm_obj)

    def remover(self, membro_id: int) -> None:
        orm_obj = self.db.get(MembroGremioORM, membro_id)
        if orm_obj:
            self.db.delete(orm_obj)
            self.db.flush()
