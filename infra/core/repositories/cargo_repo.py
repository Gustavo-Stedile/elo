from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from application.exceptions.cargo_exceptions import CargoJaExisteErro
from domain.core import Cargo
from infra.core.orm import CargoORM, MembroCargoORM, MembroGremioORM
from infra.core.mappers.cargo_mappers import cargo_to_domain, cargo_to_orm


class CargoRepository:
    def __init__(self, db: Session):
        self.db = db

    # ---------- Cargos ----------
    def create(self, cargo: Cargo) -> Cargo:
        try:
            orm_obj = cargo_to_orm(cargo)
            self.db.add(orm_obj)
            self.db.flush()
            return cargo_to_domain(orm_obj)
        except IntegrityError as e:
            self.db.rollback()
            self._tratar_integridade(e)

    def get_by_id(self, id: int) -> Cargo | None:
        return cargo_to_domain(self.db.get(CargoORM, id))

    def get_padrao(self, gremio_id: int) -> Cargo | None:
        stmt = select(CargoORM).where(
            CargoORM.gremio_id == gremio_id, CargoORM.padrao.is_(True)
        )
        return cargo_to_domain(self.db.scalars(stmt).first())

    def listar_por_gremio(self, gremio_id: int) -> list[Cargo]:
        stmt = (
            select(CargoORM)
            .where(CargoORM.gremio_id == gremio_id)
            .order_by(CargoORM.prioridade.desc(), CargoORM.id)
        )
        return [cargo_to_domain(c) for c in self.db.scalars(stmt).all()]

    def update(self, cargo: Cargo) -> Cargo:
        try:
            orm_obj = self.db.get(CargoORM, cargo.id)
            orm_obj.nome = cargo.nome
            orm_obj.cor = cargo.cor
            orm_obj.prioridade = cargo.prioridade
            orm_obj.permissoes = cargo.permissoes
            self.db.flush()
            return cargo_to_domain(orm_obj)
        except IntegrityError as e:
            self.db.rollback()
            self._tratar_integridade(e)

    def delete(self, cargo_id: int) -> None:
        orm_obj = self.db.get(CargoORM, cargo_id)
        if orm_obj:
            self.db.delete(orm_obj)
            self.db.flush()

    # ---------- Atribuição de cargos a membros ----------
    def listar_do_membro(self, membro_id: int) -> list[Cargo]:
        """Cargos atribuídos explicitamente ao membro (não inclui o padrão)."""
        stmt = (
            select(CargoORM)
            .join(MembroCargoORM, MembroCargoORM.cargo_id == CargoORM.id)
            .where(MembroCargoORM.membro_id == membro_id)
        )
        return [cargo_to_domain(c) for c in self.db.scalars(stmt).all()]

    def listar_atribuicoes_do_gremio(self, gremio_id: int) -> dict[int, list[int]]:
        """Mapa membro_id -> ids dos cargos atribuídos, para todo o grêmio."""
        stmt = (
            select(MembroCargoORM.membro_id, MembroCargoORM.cargo_id)
            .join(MembroGremioORM, MembroGremioORM.id == MembroCargoORM.membro_id)
            .where(MembroGremioORM.gremio_id == gremio_id)
        )
        resultado: dict[int, list[int]] = {}
        for membro_id, cargo_id in self.db.execute(stmt).all():
            resultado.setdefault(membro_id, []).append(cargo_id)
        return resultado

    def atribuir(self, membro_id: int, cargo_id: int) -> None:
        """Idempotente: atribuir um cargo que o membro já tem não faz nada."""
        stmt = select(MembroCargoORM).where(
            MembroCargoORM.membro_id == membro_id,
            MembroCargoORM.cargo_id == cargo_id,
        )
        if self.db.scalars(stmt).first():
            return
        self.db.add(MembroCargoORM(membro_id=membro_id, cargo_id=cargo_id))
        self.db.flush()

    def desatribuir(self, membro_id: int, cargo_id: int) -> None:
        self.db.execute(
            delete(MembroCargoORM).where(
                MembroCargoORM.membro_id == membro_id,
                MembroCargoORM.cargo_id == cargo_id,
            )
        )
        self.db.flush()

    @staticmethod
    def _tratar_integridade(e: IntegrityError):
        if "unique" in str(e.orig).lower():
            raise CargoJaExisteErro()
        raise e
