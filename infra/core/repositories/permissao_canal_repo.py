from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from domain.core import PermissaoCanal
from infra.core.orm import CanalORM, PermissaoCanalORM
from infra.core.mappers.permissao_canal_mappers import (
    permissao_canal_to_domain,
)


class PermissaoCanalRepository:
    """Sobrescritas de permissão por canal (para cargos e para usuários)."""

    def __init__(self, db: Session):
        self.db = db

    def listar_por_canal(self, canal_id: int) -> list[PermissaoCanal]:
        stmt = select(PermissaoCanalORM).where(PermissaoCanalORM.canal_id == canal_id)
        return [permissao_canal_to_domain(p) for p in self.db.scalars(stmt).all()]

    def listar_por_canais(self, canal_ids: list[int]) -> dict[int, list[PermissaoCanal]]:
        """Mapa canal_id -> sobrescritas, em uma única consulta."""
        resultado: dict[int, list[PermissaoCanal]] = {cid: [] for cid in canal_ids}
        if not canal_ids:
            return resultado
        stmt = select(PermissaoCanalORM).where(PermissaoCanalORM.canal_id.in_(canal_ids))
        for orm_obj in self.db.scalars(stmt).all():
            resultado[orm_obj.canal_id].append(permissao_canal_to_domain(orm_obj))
        return resultado

    def definir_cargo(self, canal_id: int, cargo_id: int, permitir: int, negar: int) -> PermissaoCanal:
        stmt = select(PermissaoCanalORM).where(
            PermissaoCanalORM.canal_id == canal_id,
            PermissaoCanalORM.cargo_id == cargo_id,
        )
        orm_obj = self.db.scalars(stmt).first()
        if orm_obj is None:
            orm_obj = PermissaoCanalORM(canal_id=canal_id, cargo_id=cargo_id)
            self.db.add(orm_obj)
        orm_obj.permitir = permitir
        orm_obj.negar = negar
        self.db.flush()
        return permissao_canal_to_domain(orm_obj)

    def definir_usuario(self, canal_id: int, usuario_id: int, permitir: int, negar: int) -> PermissaoCanal:
        stmt = select(PermissaoCanalORM).where(
            PermissaoCanalORM.canal_id == canal_id,
            PermissaoCanalORM.usuario_id == usuario_id,
        )
        orm_obj = self.db.scalars(stmt).first()
        if orm_obj is None:
            orm_obj = PermissaoCanalORM(canal_id=canal_id, usuario_id=usuario_id)
            self.db.add(orm_obj)
        orm_obj.permitir = permitir
        orm_obj.negar = negar
        self.db.flush()
        return permissao_canal_to_domain(orm_obj)

    def remover_cargo(self, canal_id: int, cargo_id: int) -> None:
        self.db.execute(
            delete(PermissaoCanalORM).where(
                PermissaoCanalORM.canal_id == canal_id,
                PermissaoCanalORM.cargo_id == cargo_id,
            )
        )
        self.db.flush()

    def remover_usuario(self, canal_id: int, usuario_id: int) -> None:
        self.db.execute(
            delete(PermissaoCanalORM).where(
                PermissaoCanalORM.canal_id == canal_id,
                PermissaoCanalORM.usuario_id == usuario_id,
            )
        )
        self.db.flush()

    def remover_do_usuario_no_gremio(self, gremio_id: int, usuario_id: int) -> None:
        """Apaga todas as sobrescritas do usuário nos canais do grêmio (ao sair/ser removido)."""
        canais_do_gremio = select(CanalORM.id).where(CanalORM.gremio_id == gremio_id)
        self.db.execute(
            delete(PermissaoCanalORM).where(
                PermissaoCanalORM.usuario_id == usuario_id,
                PermissaoCanalORM.canal_id.in_(canais_do_gremio),
            )
        )
        self.db.flush()
