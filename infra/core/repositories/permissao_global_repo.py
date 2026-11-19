from sqlalchemy import select
from sqlalchemy.orm import Session

from domain.core import PermissaoGlobal
from infra.core.orm import ConcessaoPermissaoGlobalORM, PermissaoGlobalORM


def _para_dominio(orm: PermissaoGlobalORM) -> PermissaoGlobal:
    return PermissaoGlobal(
        id=orm.id,
        codigo=orm.codigo,
        nome=orm.nome,
        descricao=orm.descricao,
    )


class PermissaoGlobalRepository:
    """Persiste o catálogo e as concessões de permissões de sistema."""

    def __init__(self, db: Session):
        self.db = db

    def obter_ou_criar(
        self, codigo: str, nome: str, descricao: str | None = None
    ) -> PermissaoGlobal:
        orm = self.db.scalars(
            select(PermissaoGlobalORM).where(
                PermissaoGlobalORM.codigo == codigo
            )
        ).first()
        if orm is None:
            orm = PermissaoGlobalORM(
                codigo=codigo,
                nome=nome,
                descricao=descricao,
            )
            self.db.add(orm)
            self.db.flush()
        return _para_dominio(orm)

    def obter_por_codigo(self, codigo: str) -> PermissaoGlobal | None:
        orm = self.db.scalars(
            select(PermissaoGlobalORM).where(
                PermissaoGlobalORM.codigo == codigo
            )
        ).first()
        return _para_dominio(orm) if orm else None

    def usuario_possui(self, usuario_id: int, permissao_id: int) -> bool:
        stmt = (
            select(ConcessaoPermissaoGlobalORM.id)
            .where(
                ConcessaoPermissaoGlobalORM.usuario_id == usuario_id,
                ConcessaoPermissaoGlobalORM.permissao_id == permissao_id,
            )
        )
        return self.db.scalars(stmt).first() is not None

    def conceder_a_usuario(self, permissao_id: int, usuario_id: int) -> None:
        existente = self.db.scalars(
            select(ConcessaoPermissaoGlobalORM).where(
                ConcessaoPermissaoGlobalORM.permissao_id == permissao_id,
                ConcessaoPermissaoGlobalORM.usuario_id == usuario_id,
            )
        ).first()
        if existente is None:
            self.db.add(
                ConcessaoPermissaoGlobalORM(
                    permissao_id=permissao_id,
                    usuario_id=usuario_id,
                )
            )
            self.db.flush()
