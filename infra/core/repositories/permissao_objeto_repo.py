from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from domain.core import ConcessaoPermissao, PermissaoObjeto
from infra.core.orm import (
    CargoORM,
    ConcessaoPermissaoORM,
    MembroCargoORM,
    MembroGremioORM,
    PermissaoObjetoORM,
)


def _permissao_to_domain(orm: PermissaoObjetoORM) -> PermissaoObjeto:
    return PermissaoObjeto(
        id=orm.id,
        gremio_id=orm.gremio_id,
        recurso_tipo=orm.recurso_tipo,
        recurso_id=orm.recurso_id,
        codigo=orm.codigo,
        nome=orm.nome,
        descricao=orm.descricao,
    )


class PermissaoObjetoRepository:
    """Persiste permissões contextuais e suas concessões."""

    def __init__(self, db: Session):
        self.db = db

    def obter_ou_criar(
        self,
        gremio_id: int,
        recurso_tipo: str,
        recurso_id: int,
        codigo: str,
        nome: str,
        descricao: str | None = None,
    ) -> PermissaoObjeto:
        stmt = select(PermissaoObjetoORM).where(
            PermissaoObjetoORM.recurso_tipo == recurso_tipo,
            PermissaoObjetoORM.recurso_id == recurso_id,
            PermissaoObjetoORM.codigo == codigo,
        )
        orm = self.db.scalars(stmt).first()
        if orm:
            return _permissao_to_domain(orm)
        orm = PermissaoObjetoORM(
            gremio_id=gremio_id,
            recurso_tipo=recurso_tipo,
            recurso_id=recurso_id,
            codigo=codigo,
            nome=nome,
            descricao=descricao,
        )
        self.db.add(orm)
        self.db.flush()
        return _permissao_to_domain(orm)

    def obter(self, permissao_id: int) -> PermissaoObjeto | None:
        orm = self.db.get(PermissaoObjetoORM, permissao_id)
        return _permissao_to_domain(orm) if orm else None

    def obter_por_recurso(
        self, gremio_id: int, recurso_tipo: str, recurso_id: int, codigo: str
    ) -> PermissaoObjeto | None:
        stmt = select(PermissaoObjetoORM).where(
            PermissaoObjetoORM.gremio_id == gremio_id,
            PermissaoObjetoORM.recurso_tipo == recurso_tipo,
            PermissaoObjetoORM.recurso_id == recurso_id,
            PermissaoObjetoORM.codigo == codigo,
        )
        orm = self.db.scalars(stmt).first()
        return _permissao_to_domain(orm) if orm else None

    def listar_do_gremio(self, gremio_id: int) -> list[PermissaoObjeto]:
        stmt = (
            select(PermissaoObjetoORM)
            .where(PermissaoObjetoORM.gremio_id == gremio_id)
            .order_by(PermissaoObjetoORM.recurso_tipo, PermissaoObjetoORM.recurso_id,
                      PermissaoObjetoORM.id)
        )
        return [_permissao_to_domain(p) for p in self.db.scalars(stmt).all()]

    def listar_do_recurso(
        self, gremio_id: int, recurso_tipo: str, recurso_id: int
    ) -> list[PermissaoObjeto]:
        stmt = (
            select(PermissaoObjetoORM)
            .where(
                PermissaoObjetoORM.gremio_id == gremio_id,
                PermissaoObjetoORM.recurso_tipo == recurso_tipo,
                PermissaoObjetoORM.recurso_id == recurso_id,
            )
            .order_by(PermissaoObjetoORM.id)
        )
        return [_permissao_to_domain(p) for p in self.db.scalars(stmt).all()]

    def listar_do_gremio_por_ids(self, ids: set[int]) -> list[PermissaoObjeto]:
        if not ids:
            return []
        stmt = (
            select(PermissaoObjetoORM)
            .where(PermissaoObjetoORM.id.in_(ids))
            .order_by(PermissaoObjetoORM.id)
        )
        return [_permissao_to_domain(p) for p in self.db.scalars(stmt).all()]

    def listar_do_cargo(self, cargo_id: int) -> list[PermissaoObjeto]:
        stmt = (
            select(PermissaoObjetoORM)
            .join(
                ConcessaoPermissaoORM,
                ConcessaoPermissaoORM.permissao_id == PermissaoObjetoORM.id,
            )
            .where(ConcessaoPermissaoORM.cargo_id == cargo_id)
        )
        return [_permissao_to_domain(p) for p in self.db.scalars(stmt).all()]

    def listar_ids_concedidos_ao_membro(self, membro_id: int) -> set[int]:
        membro = self.db.get(MembroGremioORM, membro_id)
        if not membro:
            return set()
        stmt = (
            select(ConcessaoPermissaoORM.permissao_id)
            .join(
                PermissaoObjetoORM,
                PermissaoObjetoORM.id == ConcessaoPermissaoORM.permissao_id,
            )
            .join(
                MembroGremioORM,
                MembroGremioORM.id == ConcessaoPermissaoORM.membro_id,
            )
            .where(
                ConcessaoPermissaoORM.membro_id == membro_id,
                MembroGremioORM.gremio_id == PermissaoObjetoORM.gremio_id,
            )
        )
        ids = set(self.db.scalars(stmt).all())
        stmt_cargos = (
            select(ConcessaoPermissaoORM.permissao_id)
            .join(CargoORM, CargoORM.id == ConcessaoPermissaoORM.cargo_id)
            .join(MembroCargoORM, MembroCargoORM.cargo_id == CargoORM.id)
            .join(
                MembroGremioORM,
                MembroGremioORM.id == MembroCargoORM.membro_id,
            )
            .join(
                PermissaoObjetoORM,
                PermissaoObjetoORM.id == ConcessaoPermissaoORM.permissao_id,
            )
            .where(
                MembroCargoORM.membro_id == membro_id,
                CargoORM.gremio_id == MembroGremioORM.gremio_id,
                PermissaoObjetoORM.gremio_id == MembroGremioORM.gremio_id,
            )
        )
        ids.update(self.db.scalars(stmt_cargos).all())
        stmt_padrao = (
            select(ConcessaoPermissaoORM.permissao_id)
            .join(CargoORM, CargoORM.id == ConcessaoPermissaoORM.cargo_id)
            .join(
                PermissaoObjetoORM,
                PermissaoObjetoORM.id == ConcessaoPermissaoORM.permissao_id,
            )
            .where(
                CargoORM.gremio_id == membro.gremio_id,
                CargoORM.padrao.is_(True),
                PermissaoObjetoORM.gremio_id == membro.gremio_id,
            )
        )
        ids.update(self.db.scalars(stmt_padrao).all())
        return ids

    def membro_possui(self, membro_id: int, permissao_id: int) -> bool:
        ids = self.listar_ids_concedidos_ao_membro(membro_id)
        if permissao_id in ids:
            return True

        # ADMINISTRADOR recebe toda permissão contextual do grêmio.
        stmt = (
            select(MembroGremioORM.id)
            .join(MembroCargoORM, MembroCargoORM.membro_id == MembroGremioORM.id)
            .join(CargoORM, CargoORM.id == MembroCargoORM.cargo_id)
            .join(
                PermissaoObjetoORM,
                PermissaoObjetoORM.gremio_id == CargoORM.gremio_id,
            )
            .where(
                MembroGremioORM.id == membro_id,
                PermissaoObjetoORM.id == permissao_id,
                MembroGremioORM.gremio_id == CargoORM.gremio_id,
                CargoORM.permissoes.bitwise_and(1 << 15) != 0,
            )
        )
        return self.db.scalars(stmt).first() is not None

    def conceder_a_cargo(self, permissao_id: int, cargo_id: int) -> ConcessaoPermissao:
        stmt = select(ConcessaoPermissaoORM).where(
            ConcessaoPermissaoORM.permissao_id == permissao_id,
            ConcessaoPermissaoORM.cargo_id == cargo_id,
        )
        orm = self.db.scalars(stmt).first()
        if not orm:
            orm = ConcessaoPermissaoORM(
                permissao_id=permissao_id,
                cargo_id=cargo_id,
            )
            self.db.add(orm)
            self.db.flush()
        return ConcessaoPermissao(
            orm.id, orm.permissao_id, cargo_id=orm.cargo_id
        )

    def conceder_a_membro(self, permissao_id: int, membro_id: int) -> ConcessaoPermissao:
        stmt = select(ConcessaoPermissaoORM).where(
            ConcessaoPermissaoORM.permissao_id == permissao_id,
            ConcessaoPermissaoORM.membro_id == membro_id,
        )
        orm = self.db.scalars(stmt).first()
        if not orm:
            orm = ConcessaoPermissaoORM(
                permissao_id=permissao_id,
                membro_id=membro_id,
            )
            self.db.add(orm)
            self.db.flush()
        return ConcessaoPermissao(
            orm.id, orm.permissao_id, membro_id=orm.membro_id
        )

    def revogar_de_cargo(self, permissao_id: int, cargo_id: int) -> None:
        self.db.execute(delete(ConcessaoPermissaoORM).where(
            ConcessaoPermissaoORM.permissao_id == permissao_id,
            ConcessaoPermissaoORM.cargo_id == cargo_id,
        ))
        self.db.flush()

    def revogar_de_membro(self, permissao_id: int, membro_id: int) -> None:
        self.db.execute(delete(ConcessaoPermissaoORM).where(
            ConcessaoPermissaoORM.permissao_id == permissao_id,
            ConcessaoPermissaoORM.membro_id == membro_id,
        ))
        self.db.flush()

    def excluir_do_recurso(
        self, gremio_id: int, recurso_tipo: str, recurso_id: int
    ) -> None:
        self.db.execute(
            delete(PermissaoObjetoORM).where(
                PermissaoObjetoORM.gremio_id == gremio_id,
                PermissaoObjetoORM.recurso_tipo == recurso_tipo,
                PermissaoObjetoORM.recurso_id == recurso_id,
            )
        )
        self.db.flush()
