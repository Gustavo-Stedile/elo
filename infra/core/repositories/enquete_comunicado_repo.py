from datetime import datetime, timezone
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from infra.core.orm.enquete_orm import EnqueteORM, EnqueteOpcaoORM, EnqueteVotoORM
from infra.core.orm.comunicado_orm import ComunicadoORM
from infra.core.orm.usuario_orm import UsuarioORM
from infra.core.mappers.enquete_comunicado_mappers import (
    enquete_to_domain,
    opcao_to_domain,
    comunicado_to_domain,
)


class EnqueteRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, gremio_id, criador_id, pergunta, tipo, visivel, canal_id=None):
        orm = EnqueteORM(
            gremio_id=gremio_id,
            canal_id=canal_id,
            criador_id=criador_id,
            pergunta=pergunta.strip(),
            tipo_votacao=tipo,
            votos_visiveis=visivel,
            criada_em=datetime.now(timezone.utc),
        )
        self.db.add(orm)
        self.db.flush()
        return enquete_to_domain(orm)

    def adicionar_opcao(self, enquete_id, texto):
        orm = EnqueteOpcaoORM(enquete_id=enquete_id, texto=texto.strip())
        self.db.add(orm)
        self.db.flush()
        return opcao_to_domain(orm)

    def get(self, enquete_id):
        orm = self.db.get(EnqueteORM, enquete_id)
        if not orm:
            return None
        enquete = enquete_to_domain(orm)
        for opcao in self.db.scalars(
            select(EnqueteOpcaoORM).where(EnqueteOpcaoORM.enquete_id == enquete_id)
        ).all():
            votos = self.db.scalar(
                select(func.count()).select_from(EnqueteVotoORM)
                .where(EnqueteVotoORM.opcao_id == opcao.id)
            ) or 0
            dominio = opcao_to_domain(opcao, votos)
            dominio.participantes = list(
                self.db.scalars(
                    select(UsuarioORM.nome)
                    .join(
                        EnqueteVotoORM,
                        EnqueteVotoORM.usuario_id == UsuarioORM.id,
                    )
                    .where(EnqueteVotoORM.opcao_id == opcao.id)
                    .order_by(UsuarioORM.nome, UsuarioORM.id)
                ).all()
            )
            enquete.opcoes.append(dominio)
        return enquete

    def listar(self, gremio_id, canal_id=None):
        stmt = select(EnqueteORM).where(EnqueteORM.gremio_id == gremio_id)
        stmt = stmt.where(EnqueteORM.canal_id == canal_id)
        return [self.get(e.id) for e in self.db.scalars(stmt.order_by(EnqueteORM.id.desc())).all()]

    def registrar_votos(self, enquete_id, usuario_id, opcao_ids):
        atuais = self.db.scalars(
            select(EnqueteVotoORM).where(
                EnqueteVotoORM.enquete_id == enquete_id,
                EnqueteVotoORM.usuario_id == usuario_id,
            )
        ).all()
        for voto in atuais:
            self.db.delete(voto)
        self.db.flush()
        self.db.add_all(
            EnqueteVotoORM(
                enquete_id=enquete_id,
                opcao_id=opcao_id,
                usuario_id=usuario_id,
            )
            for opcao_id in opcao_ids
        )
        self.db.flush()


class ComunicadoRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, gremio_id, autor_id, titulo, texto, valido_ate, canal_id=None):
        orm = ComunicadoORM(
            gremio_id=gremio_id,
            canal_id=canal_id,
            autor_id=autor_id,
            titulo=titulo.strip(),
            texto=texto.strip(),
            valido_ate=valido_ate,
            criado_em=datetime.now(timezone.utc),
        )
        self.db.add(orm)
        self.db.flush()
        return comunicado_to_domain(orm)

    def listar_validos(self, gremio_id, canal_id=None, agora=None):
        agora = agora or datetime.now(timezone.utc)
        stmt = (
            select(ComunicadoORM)
            .where(ComunicadoORM.gremio_id == gremio_id)
            .where(ComunicadoORM.canal_id == canal_id)
            .where(ComunicadoORM.valido_ate >= agora)
            .order_by(ComunicadoORM.valido_ate.desc())
        )
        return [comunicado_to_domain(c) for c in self.db.scalars(stmt).all()]
