from domain.core import PermissaoCanal
from infra.core.orm import PermissaoCanalORM


def permissao_canal_to_domain(orm: PermissaoCanalORM | None) -> PermissaoCanal | None:
    if not orm:
        return None
    return PermissaoCanal(
        id=orm.id,
        canal_id=orm.canal_id,
        permitir=orm.permitir,
        negar=orm.negar,
        cargo_id=orm.cargo_id,
        usuario_id=orm.usuario_id,
    )


def permissao_canal_to_orm(domain: PermissaoCanal) -> PermissaoCanalORM:
    return PermissaoCanalORM(
        id=domain.id,
        canal_id=domain.canal_id,
        permitir=domain.permitir,
        negar=domain.negar,
        cargo_id=domain.cargo_id,
        usuario_id=domain.usuario_id,
    )
