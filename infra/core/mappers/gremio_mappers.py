from domain.core import Gremio
from infra.core.orm import GremioORM

def gremio_to_domain(orm: GremioORM | None) -> Gremio | None:
    if not orm:
        return None
    return Gremio(
        id=orm.id,
        nome=orm.nome,
        instituicao=orm.instituicao,
        etapa_ensino=orm.etapa_ensino,
        legitimado=orm.legitimado,
        fundador_id=orm.fundador_id,
    )

def gremio_to_orm(domain: Gremio) -> GremioORM:
    return GremioORM(
        id=domain.id,
        nome=domain.nome,
        instituicao=domain.instituicao,
        etapa_ensino=domain.etapa_ensino,
        legitimado=domain.legitimado,
        fundador_id=domain.fundador_id,
    )
