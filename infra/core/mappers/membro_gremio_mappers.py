from domain.core import MembroGremio
from infra.core.orm import MembroGremioORM


def membro_gremio_to_domain(orm: MembroGremioORM | None) -> MembroGremio | None:
    if not orm:
        return None

    return MembroGremio(
        id=orm.id,
        usuario_id=orm.usuario_id,
        gremio_id=orm.gremio_id,
        cargo=orm.cargo,
    )


def membro_gremio_to_orm(domain: MembroGremio) -> MembroGremioORM:
    return MembroGremioORM(
        id=domain.id,
        usuario_id=domain.usuario_id,
        gremio_id=domain.gremio_id,
        cargo=domain.cargo,
    )