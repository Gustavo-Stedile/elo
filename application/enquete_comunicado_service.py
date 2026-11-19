from datetime import datetime, timezone

from application.autorizacao_service import AutorizacaoService
from application.exceptions.autorizacao_exceptions import SemPermissaoErro
from application.excecoes_enquete_comunicado import (
    EnqueteNaoEncontradaErro,
    EnqueteOpcaoInvalidaErro,
    EnqueteVotoInvalidoErro,
)
from application.permissao_relacional_service import PermissaoRelacionalService
from application.exceptions.cargo_exceptions import CargoNaoExisteErro
from application.exceptions.canal_exceptions import CanalNaoExisteErro
from domain.core.permissoes import Permissao
from infra.core.repositories import (
    EnqueteRepository,
    ComunicadoRepository,
    CargoRepository,
    UsuarioRepository,
)
from infra.unit_of_work import UnitOfWork


class EnqueteService:
    def __init__(
        self,
        repositorio: EnqueteRepository,
        usuario_repository: UsuarioRepository,
        autorizacao: AutorizacaoService,
        uow: UnitOfWork,
        cargo_repository: CargoRepository | None = None,
        permissoes_relacionais: PermissaoRelacionalService | None = None,
    ):
        self.repositorio = repositorio
        self.usuario_repository = usuario_repository
        self.autorizacao = autorizacao
        self.uow = uow
        self.cargo_repository = cargo_repository
        self.permissoes_relacionais = permissoes_relacionais

    def criar(
        self, gremio_id, ator_id, pergunta, opcoes, tipo_votacao,
        votos_visiveis, canal_id=None,
    ):
        ctx = self.autorizacao.contexto(gremio_id, ator_id)
        if canal_id is None:
            self._exigir_gremio(ctx.membro.id, gremio_id, "GREMIO_CRIAR_ENQUETE")
        else:
            acesso = self.autorizacao.acessar_canal(
                canal_id, ator_id, Permissao.VER_CANAL
            )
            if acesso.canal.gremio_id != gremio_id:
                raise CanalNaoExisteErro()
            self._exigir_canal(
                ctx.membro.id, gremio_id, canal_id, "CANAL_CRIAR_ENQUETE"
            )
        if tipo_votacao not in ("UNICA", "MULTIPLA"):
            raise EnqueteVotoInvalidoErro("Tipo de votação inválido.")
        textos = [str(texto).strip() for texto in opcoes if str(texto).strip()]
        if len(textos) < 2 or len(set(textos)) != len(textos):
            raise EnqueteOpcaoInvalidaErro()

        enquete = self.repositorio.create(
            gremio_id, ator_id, pergunta, tipo_votacao,
            votos_visiveis, canal_id,
        )
        for texto in textos:
            self.repositorio.adicionar_opcao(enquete.id, texto)
        cargo_membro, cargo_administrador = self._cargos_basicos(gremio_id)
        self.permissoes_relacionais.criar_permissoes_enquete(
            gremio_id,
            enquete.id,
            ctx.membro.id,
            cargo_membro.id,
            cargo_administrador.id,
        )
        self.uow.commit()
        return self._filtrar_resultado(self.repositorio.get(enquete.id))

    def listar(self, gremio_id, usuario_id, canal_id=None):
        if canal_id is not None:
            self.autorizacao.acessar_canal(canal_id, usuario_id, Permissao.VER_CANAL)
        else:
            self.autorizacao.contexto(gremio_id, usuario_id)
        enquetes = self.repositorio.listar(gremio_id, canal_id)
        ctx = self.autorizacao.contexto(gremio_id, usuario_id)
        enquetes = [
            enquete
            for enquete in enquetes
            if self.permissoes_relacionais.membro_possui_codigo(
                ctx.membro.id,
                gremio_id,
                "ENQUETE",
                enquete.id,
                "ENQUETE_VOTAR",
            )
        ]
        usuarios = self.usuario_repository.get_many([e.criador_id for e in enquetes])
        for enquete in enquetes:
            autor = usuarios.get(enquete.criador_id)
            enquete.criador_nome = autor.nome if autor else None
        return [self._filtrar_resultado(enquete) for enquete in enquetes]

    def votar(self, gremio_id, enquete_id, usuario_id, opcao_ids):
        ctx = self.autorizacao.contexto(gremio_id, usuario_id)
        enquete = self.repositorio.get(enquete_id)
        if not enquete or enquete.gremio_id != gremio_id:
            raise EnqueteNaoEncontradaErro()
        if enquete.canal_id is not None:
            self.autorizacao.acessar_canal(
                enquete.canal_id, usuario_id, Permissao.VER_CANAL
            )
        if not self.permissoes_relacionais.membro_possui_codigo(
            ctx.membro.id,
            gremio_id,
            "ENQUETE",
            enquete.id,
            "ENQUETE_VOTAR",
        ):
            raise SemPermissaoErro(["ENQUETE_VOTAR"])
        ids = set(opcao_ids)
        validos = {opcao.id for opcao in enquete.opcoes}
        if not ids or not ids.issubset(validos):
            raise EnqueteOpcaoInvalidaErro()
        if enquete.tipo_votacao == "UNICA" and len(ids) != 1:
            raise EnqueteVotoInvalidoErro("Esta enquete aceita uma única opção.")
        self.repositorio.registrar_votos(enquete.id, usuario_id, ids)
        self.uow.commit()
        return self._filtrar_resultado(self.repositorio.get(enquete.id))

    def _exigir_gremio(self, membro_id: int, gremio_id: int, codigo: str):
        if not self.permissoes_relacionais:
            raise SemPermissaoErro([codigo])
        self.permissoes_relacionais.exigir_codigo_gremio(
            membro_id, gremio_id, codigo
        )

    def _exigir_canal(
        self, membro_id: int, gremio_id: int, canal_id: int, codigo: str
    ):
        if not self.permissoes_relacionais:
            raise SemPermissaoErro([codigo])
        self.permissoes_relacionais.exigir_codigo_canal(
            membro_id, gremio_id, canal_id, codigo
        )

    def _cargos_basicos(self, gremio_id: int):
        if not self.cargo_repository or not self.permissoes_relacionais:
            raise SemPermissaoErro(["Permissões relacionais do grêmio"])
        cargos = self.cargo_repository.listar_por_gremio(gremio_id)
        cargo_membro = next((cargo for cargo in cargos if cargo.padrao), None)
        cargo_administrador = next(
            (
                cargo for cargo in cargos
                if cargo.permissoes & int(Permissao.ADMINISTRADOR)
            ),
            None,
        )
        if not cargo_membro or not cargo_administrador:
            raise CargoNaoExisteErro()
        return cargo_membro, cargo_administrador

    def _filtrar_resultado(self, enquete):
        if enquete and not enquete.votos_visiveis:
            for opcao in enquete.opcoes:
                opcao.votos = None
                opcao.participantes = None
        return enquete


class ComunicadoService:
    def __init__(
        self,
        repositorio: ComunicadoRepository,
        usuario_repository: UsuarioRepository,
        autorizacao: AutorizacaoService,
        uow: UnitOfWork,
        cargo_repository: CargoRepository | None = None,
        permissoes_relacionais: PermissaoRelacionalService | None = None,
    ):
        self.repositorio = repositorio
        self.usuario_repository = usuario_repository
        self.autorizacao = autorizacao
        self.uow = uow
        self.cargo_repository = cargo_repository
        self.permissoes_relacionais = permissoes_relacionais

    def criar(self, gremio_id, autor_id, titulo, texto, valido_ate, canal_id=None):
        ctx = self.autorizacao.contexto(gremio_id, autor_id)
        if canal_id is None:
            if not self.permissoes_relacionais:
                raise SemPermissaoErro(["GREMIO_CRIAR_COMUNICADO"])
            self.permissoes_relacionais.exigir_codigo_gremio(
                ctx.membro.id, gremio_id, "GREMIO_CRIAR_COMUNICADO"
            )
        else:
            acesso = self.autorizacao.acessar_canal(
                canal_id, autor_id, Permissao.VER_CANAL
            )
            if acesso.canal.gremio_id != gremio_id:
                raise CanalNaoExisteErro()
            if not self.permissoes_relacionais:
                raise SemPermissaoErro(["CANAL_CRIAR_COMUNICADO"])
            self.permissoes_relacionais.exigir_codigo_canal(
                ctx.membro.id, gremio_id, canal_id, "CANAL_CRIAR_COMUNICADO"
            )

        validade = valido_ate
        if validade.tzinfo is None:
            validade = validade.replace(tzinfo=timezone.utc)
        if validade <= datetime.now(timezone.utc):
            raise EnqueteVotoInvalidoErro("A data de validade deve ser futura.")

        comunicado = self.repositorio.create(
            gremio_id, autor_id, titulo, texto, validade, canal_id
        )
        if not self.permissoes_relacionais or not self.cargo_repository:
            raise SemPermissaoErro(["Permissões relacionais do comunicado"])
        cargos = self.cargo_repository.listar_por_gremio(gremio_id)
        cargo_membro = next((cargo for cargo in cargos if cargo.padrao), None)
        cargo_administrador = next(
            (
                cargo for cargo in cargos
                if cargo.permissoes & int(Permissao.ADMINISTRADOR)
            ),
            None,
        )
        if not cargo_membro or not cargo_administrador:
            raise CargoNaoExisteErro()
        self.permissoes_relacionais.criar_permissoes_comunicado(
            gremio_id,
            comunicado.id,
            ctx.membro.id,
            cargo_membro.id,
            cargo_administrador.id,
        )
        self.uow.commit()
        autor = self.usuario_repository.get_by_id(autor_id)
        comunicado.autor_nome = autor.nome if autor else None
        return comunicado

    def listar(self, gremio_id, usuario_id, canal_id=None):
        if canal_id is not None:
            acesso = self.autorizacao.acessar_canal(
                canal_id, usuario_id, Permissao.VER_CANAL
            )
            if acesso.canal.gremio_id != gremio_id:
                raise CanalNaoExisteErro()
        ctx = self.autorizacao.contexto(gremio_id, usuario_id)
        comunicados = self.repositorio.listar_validos(gremio_id, canal_id)
        comunicados = [
            comunicado
            for comunicado in comunicados
            if self.permissoes_relacionais.membro_possui_codigo(
                ctx.membro.id,
                gremio_id,
                "COMUNICADO",
                comunicado.id,
                "COMUNICADO_VISUALIZAR",
            )
        ]
        autores = self.usuario_repository.get_many([c.autor_id for c in comunicados])
        for comunicado in comunicados:
            autor = autores.get(comunicado.autor_id)
            comunicado.autor_nome = autor.nome if autor else None
        return comunicados
