from domain.core import Cargo
from infra.core.orm import CargoORM


def cargo_to_domain(orm: CargoORM | None) -> Cargo | None:
    if not orm:
        return None
    return Cargo(
        id=orm.id,
        gremio_id=orm.gremio_id,
        nome=orm.nome,
        cor=orm.cor,
        prioridade=orm.prioridade,
        permissoes=orm.permissoes,
        padrao=orm.padrao,
    )


def cargo_to_orm(domain: Cargo) -> CargoORM:
    return CargoORM(
        id=domain.id,
        gremio_id=domain.gremio_id,
        nome=domain.nome,
        cor=domain.cor,
        prioridade=domain.prioridade,
        permissoes=domain.permissoes,
        padrao=domain.padrao,
    )
