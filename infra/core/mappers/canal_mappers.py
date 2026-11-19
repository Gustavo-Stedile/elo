from domain.core import Canal
from infra.core.orm import CanalORM


def canal_to_domain(orm: CanalORM | None) -> Canal | None:
    if not orm:
        return None
    return Canal(
        id=orm.id,
        gremio_id=orm.gremio_id,
        nome=orm.nome,
        descricao=orm.descricao,
        permissao_ver=orm.permissao_ver,
        permissao_ler=orm.permissao_ler,
        permissao_escrever=orm.permissao_escrever,
        permissao_gerenciar_mensagens=orm.permissao_gerenciar_mensagens,
    )


def canal_to_orm(domain: Canal) -> CanalORM:
    return CanalORM(
        id=domain.id,
        gremio_id=domain.gremio_id,
        nome=domain.nome,
        descricao=domain.descricao,
        permissao_ver=domain.permissao_ver,
        permissao_ler=domain.permissao_ler,
        permissao_escrever=domain.permissao_escrever,
        permissao_gerenciar_mensagens=domain.permissao_gerenciar_mensagens,
    )
