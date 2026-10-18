from datetime import datetime, timezone

from domain.core import Mensagem
from infra.core.orm import MensagemORM


def _utc(valor: datetime | None) -> datetime | None:
    # SQLite devolve datetimes sem fuso; tudo é gravado em UTC.
    if valor is not None and valor.tzinfo is None:
        return valor.replace(tzinfo=timezone.utc)
    return valor


def mensagem_to_domain(orm: MensagemORM | None) -> Mensagem | None:
    if not orm:
        return None
    return Mensagem(
        id=orm.id,
        canal_id=orm.canal_id,
        autor_id=orm.autor_id,
        conteudo=orm.conteudo,
        criada_em=_utc(orm.criada_em),
        editada_em=_utc(orm.editada_em),
    )


def mensagem_to_orm(domain: Mensagem) -> MensagemORM:
    return MensagemORM(
        id=domain.id,
        canal_id=domain.canal_id,
        autor_id=domain.autor_id,
        conteudo=domain.conteudo,
        criada_em=domain.criada_em,
        editada_em=domain.editada_em,
    )
