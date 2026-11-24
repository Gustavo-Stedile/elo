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
        orm_obj.marcada_inapropriada_ia = mensagem.marcada_inapropriada_ia
        orm_obj.avaliacao_admin = mensagem.avaliacao_admin
        self.db.add(orm_obj)
        self.db.flush()
        return self._para_dominio(orm_obj)

    def get_by_id(self, id: int) -> Mensagem | None:
        return self._para_dominio(self.db.get(MensagemORM, id))

    @staticmethod
    def _para_dominio(orm_obj: MensagemORM | None) -> Mensagem | None:
        mensagem = mensagem_to_domain(orm_obj)
        if mensagem is not None and orm_obj is not None:
            mensagem.marcada_inapropriada_ia = orm_obj.marcada_inapropriada_ia
            mensagem.avaliacao_admin = orm_obj.avaliacao_admin
        return mensagem

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
            return [self._para_dominio(m) for m in self.db.scalars(stmt).all()]

        if antes_de is not None:
            base = base.where(MensagemORM.id < antes_de)

        stmt = base.order_by(MensagemORM.id.desc()).limit(limite)
        mensagens = [self._para_dominio(m) for m in self.db.scalars(stmt).all()]
        mensagens.reverse()
        return mensagens

    def atualizar_conteudo(
        self,
        mensagem_id: int,
        conteudo: str,
        editada_em: datetime,
        marcada_inapropriada_ia: bool,
        avaliacao_admin: bool | None,
    ) -> Mensagem:
        orm_obj = self.db.get(MensagemORM, mensagem_id)
        orm_obj.conteudo = conteudo
        orm_obj.editada_em = editada_em
        orm_obj.marcada_inapropriada_ia = marcada_inapropriada_ia
        orm_obj.avaliacao_admin = avaliacao_admin
        self.db.flush()
        return self._para_dominio(orm_obj)

    def avaliar(
        self, mensagem_id: int, apropriada: bool
    ) -> Mensagem | None:
        orm_obj = self.db.get(MensagemORM, mensagem_id)
        if not orm_obj:
            return None
        orm_obj.avaliacao_admin = apropriada
        self.db.flush()
        return self._para_dominio(orm_obj)

    def delete(self, mensagem_id: int) -> None:
        orm_obj = self.db.get(MensagemORM, mensagem_id)
        if orm_obj:
            self.db.delete(orm_obj)
            self.db.flush()
