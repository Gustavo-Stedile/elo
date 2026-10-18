from dataclasses import dataclass

from application.autorizacao_service import AutorizacaoService
from application.exceptions.cargo_exceptions import (
    CargoNaoExisteErro,
    CargoPadraoProtegidoErro,
)
from application.exceptions.autorizacao_exceptions import PermissaoInvalidaErro
from application.exceptions.membro_gremio_exceptions import (
    FundadorProtegidoErro,
    MembroNaoExisteErro,
)
from application.exceptions.usuario_exceptions import UsuarioNaoExisteErro
from domain.core import MembroGremio
from domain.core.permissoes import TODAS, Permissao, e_valido
from infra.core.repositories import (
    CargoRepository,
    GremioRepository,
    MembroGremioRepository,
    PermissaoCanalRepository,
    UsuarioRepository,
)
from infra.unit_of_work import UnitOfWork


@dataclass
class MembroDetalhe:
    usuario_id: int
    nome: str | None
    fundador: bool
    cargos_ids: list[int]
    permissoes_permitidas: int
    permissoes_negadas: int


class MembroService:
    def __init__(
        self,
        gremio_repository: GremioRepository,
        membro_gremio_repository: MembroGremioRepository,
        cargo_repository: CargoRepository,
        permissao_canal_repository: PermissaoCanalRepository,
        usuario_repository: UsuarioRepository,
        autorizacao: AutorizacaoService,
        uow: UnitOfWork,
    ):
        self.gremio_repository = gremio_repository
        self.membro_gremio_repository = membro_gremio_repository
        self.cargo_repository = cargo_repository
        self.permissao_canal_repository = permissao_canal_repository
        self.usuario_repository = usuario_repository
        self.autorizacao = autorizacao
        self.uow = uow

    # ------------------------------------------------------------------
    def listar_membros(self, gremio_id: int, ator_id: int) -> list[MembroDetalhe]:
        ctx = self.autorizacao.contexto(gremio_id, ator_id)  # só membros listam

        membros = self.membro_gremio_repository.listar_por_gremio(gremio_id)
        usuarios = self.usuario_repository.get_many([m.usuario_id for m in membros])
        atribuicoes = self.cargo_repository.listar_atribuicoes_do_gremio(gremio_id)

        return [
            MembroDetalhe(
                usuario_id=m.usuario_id,
                nome=usuarios[m.usuario_id].nome if m.usuario_id in usuarios else None,
                fundador=m.usuario_id == ctx.gremio.fundador_id,
                cargos_ids=atribuicoes.get(m.id, []),
                permissoes_permitidas=m.permissoes_permitidas,
                permissoes_negadas=m.permissoes_negadas,
            )
            for m in membros
        ]

    def adicionar_membro(
        self, gremio_id: int, ator_id: int, usuario_id: int
    ) -> MembroDetalhe:
        ctx = self.autorizacao.exigir_gremio(
            gremio_id, ator_id, Permissao.GERENCIAR_MEMBROS
        )

        usuario = self.usuario_repository.get_by_id(usuario_id)
        if not usuario:
            raise UsuarioNaoExisteErro()

        membro = self.membro_gremio_repository.create(
            MembroGremio(id=None, usuario_id=usuario_id, gremio_id=gremio_id)
        )
        self.uow.commit()

        return MembroDetalhe(
            usuario_id=membro.usuario_id,
            nome=usuario.nome,
            fundador=membro.usuario_id == ctx.gremio.fundador_id,
            cargos_ids=[],
            permissoes_permitidas=0,
            permissoes_negadas=0,
        )

    def remover_membro(self, gremio_id: int, ator_id: int, usuario_id: int) -> None:
        """Remove um membro, ou permite que o próprio usuário saia do grêmio."""
        ctx = self.autorizacao.contexto(gremio_id, ator_id)

        if usuario_id == ctx.gremio.fundador_id:
            raise FundadorProtegidoErro()

        if usuario_id == ator_id:
            alvo = ctx.membro  # saindo por conta própria: não exige permissão
        else:
            self.autorizacao.exigir(ctx.permissoes, Permissao.GERENCIAR_MEMBROS)
            alvo_ctx = self._contexto_alvo(gremio_id, usuario_id)
            self.autorizacao.exigir_acima(ctx, alvo_ctx.prioridade)
            alvo = alvo_ctx.membro

        # Sobrescritas por canal apontam para o usuário (não para o vínculo),
        # então são limpas explicitamente. Cargos atribuídos caem em cascata.
        self.permissao_canal_repository.remover_do_usuario_no_gremio(
            gremio_id, usuario_id
        )
        self.membro_gremio_repository.remover(alvo.id)
        self.uow.commit()

    # ------------------------------------------------------------------
    def atribuir_cargo(
        self, gremio_id: int, ator_id: int, usuario_id: int, cargo_id: int
    ) -> None:
        ctx = self.autorizacao.exigir_gremio(
            gremio_id, ator_id, Permissao.GERENCIAR_CARGOS
        )
        cargo = self._cargo_atribuivel(ctx, gremio_id, cargo_id)
        membro = self._membro(gremio_id, usuario_id)

        self.cargo_repository.atribuir(membro.id, cargo.id)
        self.uow.commit()

    def remover_cargo(
        self, gremio_id: int, ator_id: int, usuario_id: int, cargo_id: int
    ) -> None:
        ctx = self.autorizacao.exigir_gremio(
            gremio_id, ator_id, Permissao.GERENCIAR_CARGOS
        )
        cargo = self._cargo_atribuivel(ctx, gremio_id, cargo_id)
        membro = self._membro(gremio_id, usuario_id)

        self.cargo_repository.desatribuir(membro.id, cargo.id)
        self.uow.commit()

    # ------------------------------------------------------------------
    def definir_permissoes_usuario(
        self,
        gremio_id: int,
        ator_id: int,
        usuario_id: int,
        permitir: int,
        negar: int,
    ) -> MembroDetalhe:
        """Define as permissões individuais do usuário no grêmio.

        Substitui as sobrescritas atuais. Enviar permitir=0 e negar=0 limpa.
        """
        ctx = self.autorizacao.exigir_gremio(
            gremio_id, ator_id, Permissao.GERENCIAR_CARGOS
        )

        if not e_valido(permitir, TODAS) or not e_valido(negar, TODAS):
            raise PermissaoInvalidaErro()
        if permitir & negar:
            raise PermissaoInvalidaErro(
                "Uma permissão não pode ser permitida e negada ao mesmo tempo."
            )

        if usuario_id == ctx.gremio.fundador_id:
            raise FundadorProtegidoErro()

        alvo_ctx = self._contexto_alvo(gremio_id, usuario_id)
        self.autorizacao.exigir_acima(ctx, alvo_ctx.prioridade)
        self.autorizacao.exigir_subconjunto(ctx.permissoes, permitir)

        alvo = alvo_ctx.membro
        alvo.permissoes_permitidas = permitir
        alvo.permissoes_negadas = negar
        alvo = self.membro_gremio_repository.atualizar_permissoes(alvo)
        self.uow.commit()

        usuario = self.usuario_repository.get_by_id(usuario_id)
        return MembroDetalhe(
            usuario_id=usuario_id,
            nome=usuario.nome if usuario else None,
            fundador=False,
            cargos_ids=[c.id for c in alvo_ctx.cargos],
            permissoes_permitidas=alvo.permissoes_permitidas,
            permissoes_negadas=alvo.permissoes_negadas,
        )

    # ------------------------------------------------------------------
    def _membro(self, gremio_id: int, usuario_id: int) -> MembroGremio:
        membro = self.membro_gremio_repository.get(gremio_id, usuario_id)
        if not membro:
            raise MembroNaoExisteErro()
        return membro

    def _contexto_alvo(self, gremio_id: int, usuario_id: int):
        self._membro(gremio_id, usuario_id)  # 404 amigável se não for membro
        return self.autorizacao.contexto(gremio_id, usuario_id)

    def _cargo_atribuivel(self, ctx, gremio_id: int, cargo_id: int):
        cargo = self.cargo_repository.get_by_id(cargo_id)
        if not cargo or cargo.gremio_id != gremio_id:
            raise CargoNaoExisteErro()
        if cargo.padrao:
            raise CargoPadraoProtegidoErro(
                "O cargo padrão já pertence a todos os membros."
            )
        self.autorizacao.exigir_acima(ctx, cargo.prioridade)
        return cargo
