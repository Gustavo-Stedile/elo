from typing import List, Optional
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
        """Salva ou atualiza um vínculo de membro/cargo no grêmio com tratamento de integridade."""
        try:
            orm_obj = membro_gremio_to_orm(membro)
            
            self.db.add(orm_obj)
            self.db.commit()
            self.db.refresh(orm_obj)
            
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

    def listar_por_gremio(self, gremio_id: int) -> List[MembroGremio]:
        """Retorna todos os membros associados a um determinado grêmio."""
        orm_objs = self.db.query(MembroGremioORM).filter(MembroGremioORM.gremio_id == gremio_id).all()
        return [membro_gremio_to_domain(obj) for obj in orm_objs]