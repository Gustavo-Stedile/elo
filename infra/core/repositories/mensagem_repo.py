from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from domain.core import Mensagem
from infra.core.orm import MensagemORM
from infra.core.mappers.mensagem_mappers import (
    mensagem_to_domain,
    mensagem_to_orm,
)


class MensagemRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, mensagem: Mensagem) -> Mensagem:
        orm_obj = mensagem_to_orm(mensagem)
        self.db.add(orm_obj)
        self.db.flush()
        return mensagem_to_domain(orm_obj)

    def get_by_id(self, id: int) -> Mensagem | None:
        return mensagem_to_domain(self.db.get(MensagemORM, id))

    def listar(
        self,
        canal_id: int,
        limite: int,
        antes_de: int | None = None,
        depois_de: int | None = None,
    ) -> list[Mensagem]:
        """Mensagens do canal em ordem cronológica (mais antigas primeiro).

        * depois_de: mensagens mais novas que o id informado (para polling).
        * antes_de: página anterior, mais antigas que o id informado.
        * sem filtros: as `limite` mensagens mais recentes.
        """
        base = select(MensagemORM).where(MensagemORM.canal_id == canal_id)

        if depois_de is not None:
            stmt = (
                base.where(MensagemORM.id > depois_de)
                .order_by(MensagemORM.id.asc())
                .limit(limite)
            )
            return [mensagem_to_domain(m) for m in self.db.scalars(stmt).all()]

        if antes_de is not None:
            base = base.where(MensagemORM.id < antes_de)

        stmt = base.order_by(MensagemORM.id.desc()).limit(limite)
        mensagens = [mensagem_to_domain(m) for m in self.db.scalars(stmt).all()]
        mensagens.reverse()
        return mensagens

    def atualizar_conteudo(self, mensagem_id: int, conteudo: str, editada_em: datetime) -> Mensagem:
        orm_obj = self.db.get(MensagemORM, mensagem_id)
        orm_obj.conteudo = conteudo
        orm_obj.editada_em = editada_em
        self.db.flush()
        return mensagem_to_domain(orm_obj)

    def delete(self, mensagem_id: int) -> None:
        orm_obj = self.db.get(MensagemORM, mensagem_id)
        if orm_obj:
            self.db.delete(orm_obj)
            self.db.flush()
