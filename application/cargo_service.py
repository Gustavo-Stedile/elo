from application.autorizacao_service import AutorizacaoService
from application.exceptions.autorizacao_exceptions import PermissaoInvalidaErro
from application.exceptions.cargo_exceptions import (
    CargoNaoExisteErro,
    CargoPadraoProtegidoErro,
)
from domain.core import Cargo
from domain.core.permissoes import TODAS, Permissao, e_valido
from infra.core.repositories import CargoRepository
from infra.unit_of_work import UnitOfWork


class CargoService:
    """Cargos do grêmio.

    Regras de segurança:
    * é preciso GERENCIAR_CARGOS;
    * só se mexe em cargos de prioridade menor que a sua (exceto o cargo
      padrão, que vale para todos);
    * ninguém concede permissões que não possui;
    * o cargo padrão não pode ser excluído, nem ter ADMINISTRADOR.
    """

    def __init__(
        self,
        cargo_repository: CargoRepository,
        autorizacao: AutorizacaoService,
        uow: UnitOfWork,
    ):
        self.cargo_repository = cargo_repository
        self.autorizacao = autorizacao
        self.uow = uow

    def listar_cargos(self, gremio_id: int, ator_id: int) -> list[Cargo]:
        self.autorizacao.contexto(gremio_id, ator_id)  # só membros
        return self.cargo_repository.listar_por_gremio(gremio_id)

    def criar_cargo(
        self,
        gremio_id: int,
        ator_id: int,
        nome: str,
        cor: str,
        prioridade: int,
        permissoes: int,
    ) -> Cargo:
        ctx = self.autorizacao.exigir_gremio(
            gremio_id, ator_id, Permissao.GERENCIAR_CARGOS
        )

        if not e_valido(permissoes, TODAS):
            raise PermissaoInvalidaErro()
        if prioridade < 1:
            raise PermissaoInvalidaErro("A prioridade de um cargo deve ser maior que zero.")

        self.autorizacao.exigir_acima(ctx, prioridade)
        self.autorizacao.exigir_subconjunto(ctx.permissoes, permissoes)

        cargo = self.cargo_repository.create(Cargo(
            id=None,
            gremio_id=gremio_id,
            nome=nome.strip(),
            cor=cor,
            prioridade=prioridade,
            permissoes=permissoes,
            padrao=False,
        ))
        self.uow.commit()
        return cargo

    def atualizar_cargo(
        self,
        gremio_id: int,
        cargo_id: int,
        ator_id: int,
        nome: str | None = None,
        cor: str | None = None,
        prioridade: int | None = None,
        permissoes: int | None = None,
    ) -> Cargo:
        ctx = self.autorizacao.exigir_gremio(
            gremio_id, ator_id, Permissao.GERENCIAR_CARGOS
        )
        cargo = self._obter(gremio_id, cargo_id)

        if cargo.padrao:
            if prioridade is not None:
                raise CargoPadraoProtegidoErro(
                    "A prioridade do cargo padrão não pode ser alterada."
                )
        else:
            self.autorizacao.exigir_acima(ctx, cargo.prioridade)

        if prioridade is not None:
            if prioridade < 1:
                raise PermissaoInvalidaErro("A prioridade de um cargo deve ser maior que zero.")
            self.autorizacao.exigir_acima(ctx, prioridade)
            cargo.prioridade = prioridade

        if permissoes is not None:
            if not e_valido(permissoes, TODAS):
                raise PermissaoInvalidaErro()
            if cargo.padrao and permissoes & int(Permissao.ADMINISTRADOR):
                raise CargoPadraoProtegidoErro(
                    "O cargo padrão não pode ter a permissão ADMINISTRADOR."
                )
            self.autorizacao.exigir_subconjunto(
                ctx.permissoes, permissoes & ~cargo.permissoes
            )
            cargo.permissoes = permissoes

        if nome is not None:
            cargo.nome = nome.strip()
        if cor is not None:
            cargo.cor = cor

        cargo = self.cargo_repository.update(cargo)
        self.uow.commit()
        return cargo

    def excluir_cargo(self, gremio_id: int, cargo_id: int, ator_id: int) -> None:
        ctx = self.autorizacao.exigir_gremio(
            gremio_id, ator_id, Permissao.GERENCIAR_CARGOS
        )
        cargo = self._obter(gremio_id, cargo_id)

        if cargo.padrao:
            raise CargoPadraoProtegidoErro("O cargo padrão não pode ser excluído.")
        self.autorizacao.exigir_acima(ctx, cargo.prioridade)

        # Atribuições e sobrescritas de canal do cargo caem em cascata (FK).
        self.cargo_repository.delete(cargo.id)
        self.uow.commit()

    def _obter(self, gremio_id: int, cargo_id: int) -> Cargo:
        cargo = self.cargo_repository.get_by_id(cargo_id)
        if not cargo or cargo.gremio_id != gremio_id:
            raise CargoNaoExisteErro()
        return cargo
