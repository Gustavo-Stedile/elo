from application.autorizacao_service import AutorizacaoService
from application.exceptions.gremio_exceptions import (
    GremioJaExisteInstEtapaErro,
    GremioNaoExisteErro,
    RAObrigatorioParaCriarGremioErro,
)
from application.exceptions.autorizacao_exceptions import SemPermissaoErro
from application.ra_resolver import resolvedor_ra
from application.permissao_relacional_service import PermissaoRelacionalService
from application.permissao_global_service import PermissaoGlobalService
from application.exceptions.usuario_exceptions import UsuarioNaoExisteErro
from domain.core import Cargo, Canal, Gremio, MembroGremio
from domain.core.permissoes import (
    PERMISSOES_PADRAO_MEMBRO,
    Permissao,
    para_nomes,
)
from infra.core.repositories import (
    CanalRepository,
    CargoRepository,
    GremioRepository,
    MembroGremioRepository,
    UsuarioRepository,
)
from infra.unit_of_work import UnitOfWork


class GremioService:
    def __init__(
        self,
        gremio_repository: GremioRepository,
        membro_gremio_repository: MembroGremioRepository,
        cargo_repository: CargoRepository,
        canal_repository: CanalRepository,
        usuario_repository: UsuarioRepository,
        autorizacao: AutorizacaoService,
        uow: UnitOfWork,
        permissoes_relacionais: PermissaoRelacionalService | None = None,
        permissoes_globais: PermissaoGlobalService | None = None,
    ):
        self.gremio_repository = gremio_repository
        self.membro_gremio_repository = membro_gremio_repository
        self.cargo_repository = cargo_repository
        self.canal_repository = canal_repository
        self.usuario_repository = usuario_repository
        self.autorizacao = autorizacao
        self.uow = uow
        self.permissoes_relacionais = permissoes_relacionais
        self.permissoes_globais = permissoes_globais

    @staticmethod
    def _para_dict(gremio: Gremio) -> dict:
        return {
            "id": gremio.id,
            "nome": gremio.nome,
            "descricao": gremio.descricao,
            "instituicao": gremio.instituicao,
            "etapa_ensino": gremio.etapa_ensino,
            "legitimado": gremio.legitimado,
            "fundador_id": gremio.fundador_id,
        }

    def criar_gremio(
        self, 
        nome: str, 
        instituicao: str | None = None,
        etapa_ensino: int | None = None,
        fundador_id: int | None = None,
    ) -> dict:
        """Cria um grêmio com a estrutura inicial de comunicação.

        Em uma única transação cria: o grêmio, o cargo padrão "Membro" (todos
        os membros), o cargo "Administrador", o vínculo do fundador e o canal
        "geral".
        """
        fundador = self.usuario_repository.get_by_id(fundador_id)
        if not fundador:
            raise UsuarioNaoExisteErro()
        if not fundador.ra:
            raise RAObrigatorioParaCriarGremioErro()

        dados_ra = resolvedor_ra.resolve(fundador.ra)
        if not dados_ra:
            raise RAObrigatorioParaCriarGremioErro()

        instituicao = dados_ra.instituicao
        etapa_ensino = dados_ra.etapa_ensino

        if self.gremio_repository.get_by_instituicao_etapa(
            instituicao, etapa_ensino
        ):
            raise GremioJaExisteInstEtapaErro()

        gremio_salvo = self.gremio_repository.create(Gremio(
            id=None,
            nome=nome,
            instituicao=instituicao,
            etapa_ensino=etapa_ensino,
            legitimado=False,
            fundador_id=fundador_id,
        ))

        cargo_membro = self.cargo_repository.create(Cargo(
            id=None,
            gremio_id=gremio_salvo.id,
            nome="Membro",
            cor="#99AAB5",
            prioridade=0,
            permissoes=PERMISSOES_PADRAO_MEMBRO,
            padrao=True,
        ))
        cargo_administrador = self.cargo_repository.create(Cargo(
            id=None,
            gremio_id=gremio_salvo.id,
            nome="Administrador",
            cor="#E67E22",
            prioridade=100,
            permissoes=int(Permissao.ADMINISTRADOR),
        ))

        membro = self.membro_gremio_repository.create(MembroGremio(
            id=None,
            usuario_id=fundador_id,
            gremio_id=gremio_salvo.id,
        ))
        self.cargo_repository.atribuir(membro.id, cargo_administrador.id)

        if self.permissoes_relacionais:
            permissoes_gremio = self.permissoes_relacionais.criar_permissoes_gremio(
                gremio_salvo.id
            )
            self.permissoes_relacionais.conceder_permissoes_gremio_ao_cargo(
                gremio_salvo.id, cargo_administrador.id
            )
            for permissao in permissoes_gremio:
                self.permissoes_relacionais.definir_concessao_a_membro(
                    gremio_salvo.id, membro.id, permissao.id, True
                )
            for cargo in (cargo_membro, cargo_administrador):
                self.permissoes_relacionais.criar_permissoes_cargo(
                    gremio_salvo.id,
                    cargo.id,
                    membro.id,
                    cargo_administrador.id,
                )

        for usuario in self.usuario_repository.listar_com_ra():
            if usuario.id == fundador_id:
                continue
            dados_ra_usuario = resolvedor_ra.resolve(usuario.ra)
            if (
                dados_ra_usuario
                and dados_ra_usuario.instituicao == instituicao
                and dados_ra_usuario.etapa_ensino == etapa_ensino
            ):
                self.membro_gremio_repository.create(MembroGremio(
                    id=None,
                    usuario_id=usuario.id,
                    gremio_id=gremio_salvo.id,
                ))

        canal = self.canal_repository.create(Canal(
            id=None,
            gremio_id=gremio_salvo.id,
            nome="geral",
            descricao="Canal geral do grêmio",
        ))
        if self.permissoes_relacionais:
            self.permissoes_relacionais.criar_permissoes_canal(
                gremio_salvo.id,
                canal.id,
                membro.id,
                cargo_membro.id,
                cargo_administrador.id,
            )

        self.uow.commit()
        return self._para_dict(gremio_salvo)

    def legitimar_gremio(self, gremio_id: int, ator_id: int) -> dict:
        gremio = self.gremio_repository.get_by_id(gremio_id)
        if not gremio:
            raise GremioNaoExisteErro()
        if not self.permissoes_globais:
            raise SemPermissaoErro(["LEGITIMAR_GREMIO"])
        self.permissoes_globais.exigir(ator_id, "LEGITIMAR_GREMIO")
        gremio.legitimado = True
        gremio = self.gremio_repository.update(gremio)
        self.uow.commit()
        return self._para_dict(gremio)

    def buscar_por_id(self, id: int) -> dict:
        """Busca um grêmio pelo ID. Lança exceção se não encontrar."""
        gremio = self.gremio_repository.get_by_id(id)

        if not gremio:
            raise GremioNaoExisteErro()
        
        return self._para_dict(gremio)

    def obter_do_membro(self, gremio_id: int, usuario_id: int) -> dict:
        """Dados do grêmio, visíveis apenas para seus membros."""
        ctx = self.autorizacao.contexto(gremio_id, usuario_id)
        return self._para_dict(ctx.gremio)

    def atualizar(
        self,
        gremio_id: int,
        usuario_id: int,
        nome: str | None = None,
        descricao: str | None = None,
    ) -> dict:
        ctx = self.autorizacao.contexto(gremio_id, usuario_id)
        if nome is not None:
            if not self.permissoes_relacionais:
                raise SemPermissaoErro(["GREMIO_EDITAR_NOME"])
            self.permissoes_relacionais.exigir_codigo_gremio(
                ctx.membro.id, gremio_id, "GREMIO_EDITAR_NOME"
            )
            ctx.gremio.nome = nome.strip()
        if descricao is not None:
            if not self.permissoes_relacionais:
                raise SemPermissaoErro(["GREMIO_EDITAR_DESCRICAO"])
            self.permissoes_relacionais.exigir_codigo_gremio(
                ctx.membro.id, gremio_id, "GREMIO_EDITAR_DESCRICAO"
            )
            ctx.gremio.descricao = descricao.strip() or None
        gremio = self.gremio_repository.update(ctx.gremio)
        self.uow.commit()
        return self._para_dict(gremio)

    def listar_do_usuario(self, usuario_id: int) -> list[dict]:
        return [
            self._para_dict(g)
            for g in self.gremio_repository.listar_por_usuario(usuario_id)
        ]

    def minhas_permissoes(self, gremio_id: int, usuario_id: int) -> dict:
        ctx = self.autorizacao.contexto(gremio_id, usuario_id)
        return {
            "fundador": ctx.fundador,
            "cargos": [c.id for c in ctx.cargos],
            "permissoes": para_nomes(ctx.permissoes),
            "permissoes_objeto": (
                [
                    {
                        "id": permissao.id,
                        "codigo": permissao.codigo,
                        "nome": permissao.nome,
                        "recurso_tipo": permissao.recurso_tipo,
                        "recurso_id": permissao.recurso_id,
                    }
                    for permissao in self.permissoes_relacionais.listar_do_gremio_por_ids(
                        {
                            permissao.id
                            for permissao in self.permissoes_relacionais.listar_concedidas_ao_membro(
                                ctx.membro.id
                            )
                        }
                        | {
                            permissao_id
                            for cargo in ([ctx.cargo_padrao] if ctx.cargo_padrao else [])
                            + ctx.cargos
                            for permissao_id in self.permissoes_relacionais.listar_concedidas_ao_cargo(
                                cargo.id
                            )
                        }
                    )
                ]
                if self.permissoes_relacionais else []
            ),
        }

    def verificar_disponibilidade_criacao(self, usuario_id: int) -> dict:
        usuario = self.usuario_repository.get_by_id(usuario_id)
        if not usuario or not usuario.ra:
            return {
                "pode_criar": False,
                "motivo": "Usuário sem RA",
                "instituicao": None,
                "etapa_ensino": None,
            }

        dados_ra = resolvedor_ra.resolve(usuario.ra)
        if not dados_ra:
            return {
                "pode_criar": False,
                "motivo": "RA não identificado",
                "instituicao": None,
                "etapa_ensino": None,
            }

        existente = self.gremio_repository.get_by_instituicao_etapa(
            dados_ra.instituicao,
            dados_ra.etapa_ensino,
        )
        return {
            "pode_criar": existente is None,
            "motivo": None if existente is None else "Já existe um grêmio para esta instituição e etapa",
            "instituicao": dados_ra.instituicao,
            "etapa_ensino": dados_ra.etapa_ensino,
        }
