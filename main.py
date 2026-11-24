import os

from infra.database import engine, Base, SessionLocal
from infra.database_migrations import garantir_unicidade_gremio_instituicao_etapa
from application.permissao_relacional_service import (
    PERMISSOES_CANAL,
    PermissaoRelacionalService,
)
from application.permissao_global_service import PermissaoGlobalService
from domain.core.permissoes import PERMISSOES_DE_CANAL, Permissao
from infra.core.repositories import (
    CargoRepository,
    CanalRepository,
    GremioRepository,
    MembroGremioRepository,
    PermissaoCanalRepository,
    PermissaoObjetoRepository,
    PermissaoGlobalRepository,
)

from application.usuario_service import UsuarioService
from infra.core.repositories import UsuarioRepository
from domain.core import Usuario
import infra.core.orm  # noqa: F401  (registra todos os modelos no metadata)
from infra.core.orm import ComunicadoORM, EnqueteORM
from sqlalchemy import select

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from presentation.error_handlers import registrar_error_handlers
from presentation.routers import api_router

def init_db():
    # Apagar o banco a cada inicialização destruiria as mensagens do chat.
    # Para recriar do zero em desenvolvimento: ELO_RESET_DB=1
    if os.getenv("ELO_RESET_DB") == "1":
        Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    # SQLite.create_all não altera tabelas existentes. Mantém app.db
    # compatível com os novos campos de cargos sem apagar dados.
    if engine.url.get_backend_name() == "sqlite":
        with engine.begin() as connection:
            from sqlalchemy import inspect, text
            columns = {c["name"] for c in inspect(connection).get_columns("cargos")}
            if "max_ocupantes" not in columns:
                connection.execute(text(
                    "ALTER TABLE cargos ADD COLUMN max_ocupantes INTEGER NOT NULL DEFAULT 0"
                ))
            if "permite_atribuicao" not in columns:
                connection.execute(text(
                    "ALTER TABLE cargos ADD COLUMN permite_atribuicao BOOLEAN NOT NULL DEFAULT 0"
                ))
            if "permissao_administracao" not in columns:
                connection.execute(text(
                    "ALTER TABLE cargos ADD COLUMN permissao_administracao INTEGER NOT NULL DEFAULT 512"
                ))
            canal_columns = {c["name"] for c in inspect(connection).get_columns("canais")}
            canal_fields = (
                ("permissao_ver", "INTEGER", "1"),
                ("permissao_ler", "INTEGER", "2"),
                ("permissao_escrever", "INTEGER", "4"),
                ("permissao_gerenciar_mensagens", "INTEGER", "8"),
            )
            for name, sql_type, default in canal_fields:
                if name not in canal_columns:
                    connection.execute(text(
                        f"ALTER TABLE canais ADD COLUMN {name} {sql_type} NOT NULL DEFAULT {default}"
                    ))
            gremio_columns = {
                c["name"] for c in inspect(connection).get_columns("gremios")
            }
            if "descricao" not in gremio_columns:
                connection.execute(text(
                    "ALTER TABLE gremios ADD COLUMN descricao VARCHAR(1000)"
                ))
            mensagem_columns = {
                c["name"] for c in inspect(connection).get_columns("mensagens")
            }
            if "marcada_inapropriada_ia" not in mensagem_columns:
                connection.execute(text(
                    "ALTER TABLE mensagens ADD COLUMN "
                    "marcada_inapropriada_ia BOOLEAN NOT NULL DEFAULT 0"
                ))
            if "avaliacao_admin" not in mensagem_columns:
                connection.execute(text(
                    "ALTER TABLE mensagens ADD COLUMN avaliacao_admin BOOLEAN"
                ))
            garantir_unicidade_gremio_instituicao_etapa(connection)

init_db()


def init_permissoes_globais():
    with SessionLocal() as db:
        PermissaoGlobalService(PermissaoGlobalRepository(db)).criar_catalogo()
        db.commit()


init_permissoes_globais()


def init_permissoes_objeto_existentes():
    with SessionLocal() as db:
        gremios = GremioRepository(db)
        cargos = CargoRepository(db)
        canais = CanalRepository(db)
        permissoes_canais = PermissaoCanalRepository(db)
        membros = MembroGremioRepository(db)
        permissoes = PermissaoRelacionalService(PermissaoObjetoRepository(db))

        for gremio in gremios.get_all():
            cargos_gremio = cargos.listar_por_gremio(gremio.id)
            administradores = [
                cargo for cargo in cargos_gremio
                if cargo.permissoes & int(Permissao.ADMINISTRADOR)
            ]
            cargo_administrador = administradores[0] if administradores else None
            cargo_membro = next(
                (cargo for cargo in cargos_gremio if cargo.padrao), None
            )
            permissoes_gremio = permissoes.criar_permissoes_gremio(gremio.id)
            membro_fundador = membros.get(gremio.id, gremio.fundador_id)
            mapa_legado_gremio = {
                int(Permissao.GERENCIAR_CARGOS): {
                    "GREMIO_CRIAR_CARGO",
                    "GREMIO_GERENCIAR_PERMISSOES",
                },
                int(Permissao.GERENCIAR_CANAIS): {"GREMIO_CRIAR_CANAL"},
                int(Permissao.CRIAR_ENQUETE): {"GREMIO_CRIAR_ENQUETE"},
                int(Permissao.CRIAR_COMUNICADO): {"GREMIO_CRIAR_COMUNICADO"},
                int(Permissao.GERENCIAR_GREMIO): {
                    "GREMIO_EDITAR_NOME",
                    "GREMIO_EDITAR_DESCRICAO",
                },
            }
            for cargo in cargos_gremio:
                codigos = {
                    codigo
                    for bit, codigos_bit in mapa_legado_gremio.items()
                    if cargo.permissoes & bit
                    for codigo in codigos_bit
                }
                if cargo.permissoes & int(Permissao.ADMINISTRADOR):
                    codigos.update(p.codigo for p in permissoes_gremio)
                for permissao in permissoes_gremio:
                    if permissao.codigo in codigos:
                        permissoes.conceder_a_cargo(
                            permissao.id, cargo.id
                        )

            if membro_fundador:
                for permissao in permissoes_gremio:
                    permissoes.definir_concessao_a_membro(
                        gremio.id,
                        membro_fundador.id,
                        permissao.id,
                        True,
                    )

            for membro in membros.listar_por_gremio(gremio.id):
                for bit, codigos_bit in mapa_legado_gremio.items():
                    if (
                        membro.permissoes_permitidas & bit
                        and not membro.permissoes_negadas & bit
                    ):
                        for codigo in codigos_bit:
                            permissao = next(
                                p for p in permissoes_gremio
                                if p.codigo == codigo
                            )
                            permissoes.definir_concessao_a_membro(
                                gremio.id, membro.id, permissao.id, True
                            )

            for cargo in cargos_gremio:
                permissoes_cargo = permissoes.criar_permissoes_cargo(
                    gremio.id,
                    cargo.id,
                    membro_fundador.id if membro_fundador else None,
                    cargo_administrador.id if cargo_administrador else None,
                )
                if cargo.permissoes & int(Permissao.GERENCIAR_CARGOS):
                    for permissao in permissoes_cargo:
                        permissoes.conceder_a_cargo(
                            permissao.id, cargo.id
                        )

            bit_para_codigo = {
                int(Permissao.VER_CANAL): "CANAL_VER",
                int(Permissao.LER_HISTORICO): "CANAL_LER_HISTORICO",
                int(Permissao.ENVIAR_MENSAGENS): "CANAL_ENVIAR_MENSAGENS",
                int(Permissao.GERENCIAR_MENSAGENS): "CANAL_GERENCIAR_MENSAGENS",
            }
            for canal in canais.listar_por_gremio(gremio.id):
                permissoes_canal = permissoes.criar_permissoes_recurso(
                    gremio.id, "CANAL", canal.id, PERMISSOES_CANAL
                )
                permissoes_por_codigo = {
                    item.codigo: item for item in permissoes_canal
                }
                overrides = permissoes_canais.listar_por_canal(canal.id)
                overrides_cargo = {
                    item.cargo_id: item
                    for item in overrides
                    if item.cargo_id is not None
                }
                overrides_membro = [
                    item for item in overrides if item.usuario_id is not None
                ]
                for cargo in cargos_gremio:
                    administrador = bool(
                        cargo.permissoes & int(Permissao.ADMINISTRADOR)
                    )
                    base = (
                        int(PERMISSOES_DE_CANAL)
                        if administrador
                        else cargo.permissoes & int(PERMISSOES_DE_CANAL)
                    )
                    override = overrides_cargo.get(cargo.id)
                    if override:
                        base = (base & ~override.negar) | override.permitir
                    for bit, codigo in bit_para_codigo.items():
                        if base & bit:
                            permissoes.conceder_a_cargo(
                                permissoes_por_codigo[codigo].id, cargo.id
                            )
                    if cargo.permissoes & int(Permissao.GERENCIAR_CANAIS):
                        for codigo in (
                            "CANAL_EDITAR",
                            "CANAL_EXCLUIR",
                            "CANAL_GERENCIAR_PERMISSOES",
                        ):
                            permissoes.conceder_a_cargo(
                                permissoes_por_codigo[codigo].id, cargo.id
                            )
                    if administrador:
                        for permissao in permissoes_canal:
                            permissoes.conceder_a_cargo(
                                permissao.id, cargo.id
                            )
                    for bit, codigo in (
                        (int(Permissao.CRIAR_ENQUETE), "CANAL_CRIAR_ENQUETE"),
                        (int(Permissao.CRIAR_COMUNICADO), "CANAL_CRIAR_COMUNICADO"),
                    ):
                        if cargo.permissoes & bit:
                            permissoes.conceder_a_cargo(
                                permissoes_por_codigo[codigo].id, cargo.id
                            )
                for override in overrides_membro:
                    membro = membros.get(gremio.id, override.usuario_id)
                    if not membro:
                        continue
                    for bit, codigo in bit_para_codigo.items():
                        if override.permitir & bit and not override.negar & bit:
                            permissoes.definir_concessao_a_membro(
                                gremio.id,
                                membro.id,
                                permissoes_por_codigo[codigo].id,
                                True,
                            )
                if membro_fundador:
                    for codigo in (
                        "CANAL_EDITAR",
                        "CANAL_EXCLUIR",
                        "CANAL_GERENCIAR_PERMISSOES",
                    ):
                        permissoes.definir_concessao_a_membro(
                            gremio.id,
                            membro_fundador.id,
                            permissoes_por_codigo[codigo].id,
                            True,
                        )

            if cargo_membro:
                for enquete in db.scalars(
                    select(EnqueteORM).where(
                        EnqueteORM.gremio_id == gremio.id
                    )
                ).all():
                    permissao = permissoes.criar_permissoes_recurso(
                        gremio.id,
                        "ENQUETE",
                        enquete.id,
                        (("ENQUETE_VOTAR", "Votar nesta enquete"),),
                    )[0]
                    permissoes.conceder_a_cargo(
                        permissao.id, cargo_membro.id
                    )
                    if cargo_administrador:
                        permissoes.conceder_a_cargo(
                            permissao.id, cargo_administrador.id
                        )

                for comunicado in db.scalars(
                    select(ComunicadoORM).where(
                        ComunicadoORM.gremio_id == gremio.id
                    )
                ).all():
                    permissao = permissoes.criar_permissoes_recurso(
                        gremio.id,
                        "COMUNICADO",
                        comunicado.id,
                        (("COMUNICADO_VISUALIZAR", "Visualizar este comunicado"),),
                    )[0]
                    permissoes.conceder_a_cargo(
                        permissao.id, cargo_membro.id
                    )
                    if cargo_administrador:
                        permissoes.conceder_a_cargo(
                            permissao.id, cargo_administrador.id
                        )
        db.commit()


init_permissoes_objeto_existentes()

app = FastAPI(
    title="ELO API",
    description="Backend do sistema ELO integrado com React",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

registrar_error_handlers(app)

app.include_router(api_router)

@app.get("/", tags=["Health Check"])
def health_check():
    return {"status": "ok", "mensagem": "API ELO rodando com sucesso!"}
