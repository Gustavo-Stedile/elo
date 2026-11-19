from domain.core import Enquete, EnqueteOpcao, Comunicado
from infra.core.orm.enquete_orm import EnqueteORM, EnqueteOpcaoORM
from infra.core.orm.comunicado_orm import ComunicadoORM


def enquete_to_domain(orm: EnqueteORM) -> Enquete:
    return Enquete(
        id=orm.id,
        gremio_id=orm.gremio_id,
        canal_id=orm.canal_id,
        criador_id=orm.criador_id,
        pergunta=orm.pergunta,
        tipo_votacao=orm.tipo_votacao,
        votos_visiveis=orm.votos_visiveis,
        criada_em=orm.criada_em,
    )


def opcao_to_domain(orm: EnqueteOpcaoORM, votos: int = 0) -> EnqueteOpcao:
    opcao = EnqueteOpcao(id=orm.id, enquete_id=orm.enquete_id, texto=orm.texto)
    opcao.votos = votos
    return opcao


def comunicado_to_domain(orm: ComunicadoORM) -> Comunicado:
    return Comunicado(
        id=orm.id,
        gremio_id=orm.gremio_id,
        canal_id=orm.canal_id,
        autor_id=orm.autor_id,
        titulo=orm.titulo,
        texto=orm.texto,
        valido_ate=orm.valido_ate,
        criado_em=orm.criado_em,
    )
