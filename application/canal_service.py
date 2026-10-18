from application.autorizacao_service import AcessoCanal, AutorizacaoService
from application.exceptions.autorizacao_exceptions import PermissaoInvalidaErro
from application.exceptions.cargo_exceptions import CargoNaoExisteErro
from application.exceptions.membro_gremio_exceptions import (
    FundadorProtegidoErro,
    MembroNaoExisteErro,
)
from domain.core import Canal, PermissaoCanal
from domain.core.permissoes import PERMISSOES_DE_CANAL, Permissao, e_valido
from infra.core.repositories import (
    CanalRepository,
    CargoRepository,
    MembroGremioRepository,
    PermissaoCanalRepository,
)
from infra.unit_of_work import UnitOfWork

_VER = int(Permissao.VER_CANAL)
_GERENCIAR_CANAIS = Permissao.GERENCIAR_CANAIS


class CanalService:
    """Canais do grêmio e suas permissões por cargo e por usuário."""

    def __init__(
        self,
        canal_repository: CanalRepository,
        permissao_canal_repository: PermissaoCanalRepository,
        cargo_repository: CargoRepository,
        membro_gremio_repository: MembroGremioRepository,
        autorizacao: AutorizacaoService,
        uow: UnitOfWork,
    ):
        self.canal_repository = canal_repository
        self.permissao_canal_repository = permissao_canal_repository
        self.cargo_repository = cargo_repository
        self.membro_gremio_repository = membro_gremio_repository
        self.autorizacao = autorizacao
        self.uow = uow

    # ------------------------------------------------------------------
    # Canais
    # ------------------------------------------------------------------
    def criar_canal(
        self, gremio_id: int, ator_id: int, nome: str, descricao: str | None = None
    ) -> Canal:
        self.autorizacao.exigir_gremio(gremio_id, ator_id, _GERENCIAR_CANAIS)
        canal = self.canal_repository.create(Canal(
            id=None, gremio_id=gremio_id, nome=nome.strip(), descricao=descricao
        ))
        self.uow.commit()
        return canal

    def listar_canais(self, gremio_id: int, usuario_id: int) -> list[Canal]:
        """Apenas os canais que o usuário pode ver."""
        ctx = self.autorizacao.contexto(gremio_id, usuario_id)
        canais = self.canal_repository.listar_por_gremio(gremio_id)
        sobrescritas = self.permissao_canal_repository.listar_por_canais(
            [c.id for c in canais]
        )
        return [
            c for c in canais
            if self.autorizacao.permissoes_no_canal(ctx, c.id, sobrescritas[c.id]) & _VER
        ]

    def obter_canal(self, canal_id: int, usuario_id: int) -> AcessoCanal:
        return self.autorizacao.acessar_canal(canal_id, usuario_id, Permissao.VER_CANAL)

    def atualizar_canal(
        self,
        canal_id: int,
        ator_id: int,
        nome: str | None = None,
        descricao: str | None = None,
    ) -> Canal:
        acesso = self.autorizacao.acessar_canal(canal_id, ator_id, _GERENCIAR_CANAIS)
        canal = acesso.canal
        if nome is not None:
            canal.nome = nome.strip()
        if descricao is not None:
            canal.descricao = descricao
        canal = self.canal_repository.update(canal)
        self.uow.commit()
        return canal

    def excluir_canal(self, canal_id: int, ator_id: int) -> None:
        acesso = self.autorizacao.acessar_canal(canal_id, ator_id, _GERENCIAR_CANAIS)
        # Mensagens e sobrescritas do canal caem em cascata (FK).
        self.canal_repository.delete(acesso.canal.id)
        self.uow.commit()

    # ------------------------------------------------------------------
    # Permissões do canal
    # ------------------------------------------------------------------
    def listar_permissoes(self, canal_id: int, ator_id: int) -> list[PermissaoCanal]:
        acesso = self.autorizacao.acessar_canal(canal_id, ator_id, _GERENCIAR_CANAIS)
        return self.permissao_canal_repository.listar_por_canal(acesso.canal.id)

    def definir_permissao_cargo(
        self, canal_id: int, ator_id: int, cargo_id: int,
        permitir: int, negar: int,
    ) -> PermissaoCanal | None:
        """Define a sobrescrita de um cargo no canal (substitui a anterior).

        Retorna None quando permitir e negar são 0 (a sobrescrita é removida).
        """
        acesso = self.autorizacao.acessar_canal(canal_id, ator_id, _GERENCIAR_CANAIS)
        self._validar_mascaras(permitir, negar)

        cargo = self.cargo_repository.get_by_id(cargo_id)
        if not cargo or cargo.gremio_id != acesso.canal.gremio_id:
            raise CargoNaoExisteErro()

        # O cargo padrão vale para todos e é exceção à hierarquia.
        if not cargo.padrao:
            self.autorizacao.exigir_acima(acesso.contexto, cargo.prioridade)
        self.autorizacao.exigir_subconjunto(acesso.permissoes, permitir)

        if permitir == 0 and negar == 0:
            self.permissao_canal_repository.remover_cargo(acesso.canal.id, cargo.id)
            self.uow.commit()
            return None

        resultado = self.permissao_canal_repository.definir_cargo(
            acesso.canal.id, cargo.id, permitir, negar
        )
        self.uow.commit()
        return resultado

    def definir_permissao_usuario(
        self, canal_id: int, ator_id: int, usuario_id: int,
        permitir: int, negar: int,
    ) -> PermissaoCanal | None:
        """Define a sobrescrita de um usuário no canal (substitui a anterior).

        É a camada mais específica: vence cargos e sobrescritas de cargo.
        Retorna None quando permitir e negar são 0 (a sobrescrita é removida).
        """
        acesso = self.autorizacao.acessar_canal(canal_id, ator_id, _GERENCIAR_CANAIS)
        self._validar_mascaras(permitir, negar)

        gremio_id = acesso.canal.gremio_id
        if not self.membro_gremio_repository.get(gremio_id, usuario_id):
            raise MembroNaoExisteErro()
        if usuario_id == acesso.contexto.gremio.fundador_id:
            raise FundadorProtegidoErro()

        alvo_ctx = self.autorizacao.contexto(gremio_id, usuario_id)
        self.autorizacao.exigir_acima(acesso.contexto, alvo_ctx.prioridade)
        self.autorizacao.exigir_subconjunto(acesso.permissoes, permitir)

        if permitir == 0 and negar == 0:
            self.permissao_canal_repository.remover_usuario(acesso.canal.id, usuario_id)
            self.uow.commit()
            return None

        resultado = self.permissao_canal_repository.definir_usuario(
            acesso.canal.id, usuario_id, permitir, negar
        )
        self.uow.commit()
        return resultado

    def remover_permissao_cargo(self, canal_id: int, ator_id: int, cargo_id: int) -> None:
        self.definir_permissao_cargo(canal_id, ator_id, cargo_id, 0, 0)

    def remover_permissao_usuario(self, canal_id: int, ator_id: int, usuario_id: int) -> None:
        self.definir_permissao_usuario(canal_id, ator_id, usuario_id, 0, 0)

    # ------------------------------------------------------------------
    @staticmethod
    def _validar_mascaras(permitir: int, negar: int) -> None:
        if not e_valido(permitir, PERMISSOES_DE_CANAL) or not e_valido(negar, PERMISSOES_DE_CANAL):
            raise PermissaoInvalidaErro(
                "Canais só aceitam permissões de canal: VER_CANAL, LER_HISTORICO, "
                "ENVIAR_MENSAGENS e GERENCIAR_MENSAGENS."
            )
        if permitir & negar:
            raise PermissaoInvalidaErro(
                "Uma permissão não pode ser permitida e negada ao mesmo tempo."
            )
