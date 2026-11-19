from application.autorizacao_service import AutorizacaoService
from application.exceptions.autorizacao_exceptions import PermissaoInvalidaErro
from application.exceptions.cargo_exceptions import (
    CargoNaoExisteErro,
    CargoPadraoProtegidoErro,
)
from application.exceptions.autorizacao_exceptions import SemPermissaoErro
from application.permissao_relacional_service import PermissaoRelacionalService
from domain.core import Cargo
from domain.core.permissoes import TODAS, Permissao, e_valido
from infra.core.repositories import CargoRepository
from infra.unit_of_work import UnitOfWork


class CargoService:
    """Cargos do grêmio.

    Regras de segurança:
    * criar cargo exige GREMIO_CRIAR_CARGO;
    * editar e atribuir cargos exigem permissões relacionais do próprio cargo;
    * delegar permissões relacionais exige GREMIO_GERENCIAR_PERMISSOES e posse
      da permissão;
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
        permissoes_relacionais: PermissaoRelacionalService | None = None,
    ):
        self.cargo_repository = cargo_repository
        self.autorizacao = autorizacao
        self.uow = uow
        self.permissoes_relacionais = permissoes_relacionais

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
        max_ocupantes: int = 0,
        permite_atribuicao: bool = False,
        permissao_administracao: int = int(Permissao.GERENCIAR_CARGOS),
    ) -> Cargo:
        ctx = self.autorizacao.contexto(gremio_id, ator_id)
        if not self.permissoes_relacionais:
            raise SemPermissaoErro(["GREMIO_CRIAR_CARGO"])
        self.permissoes_relacionais.exigir_codigo_gremio(
            ctx.membro.id, gremio_id, "GREMIO_CRIAR_CARGO"
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
            max_ocupantes=max_ocupantes,
            permite_atribuicao=permite_atribuicao,
            permissao_administracao=permissao_administracao,
        ))
        cargo_administrador = next(
            (
                existente
                for existente in self.cargo_repository.listar_por_gremio(gremio_id)
                if existente.permissoes & int(Permissao.ADMINISTRADOR)
            ),
            None,
        )
        if not cargo_administrador:
            raise SemPermissaoErro(["cargo Administrador"])
        self.permissoes_relacionais.criar_permissoes_cargo(
            gremio_id,
            cargo.id,
            ctx.membro.id,
            cargo_administrador.id,
        )
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
        max_ocupantes: int | None = None,
        permite_atribuicao: bool | None = None,
        permissao_administracao: int | None = None,
    ) -> Cargo:
        ctx = self.autorizacao.contexto(gremio_id, ator_id)
        cargo = self._obter(gremio_id, cargo_id)

        if cargo.padrao:
            if prioridade is not None:
                raise CargoPadraoProtegidoErro(
                    "A prioridade do cargo padrão não pode ser alterada."
                )
        else:
            self.autorizacao.exigir_acima(ctx, cargo.prioridade)
        self._exigir_edicao(ctx.membro.id, gremio_id, cargo_id)

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
        if max_ocupantes is not None:
            if max_ocupantes < 0:
                raise PermissaoInvalidaErro("O número máximo de ocupantes não pode ser negativo.")
            if (
                max_ocupantes > 0
                and max_ocupantes < self.cargo_repository.contar_ocupantes(cargo.id)
            ):
                raise PermissaoInvalidaErro(
                    "O limite não pode ser menor que a quantidade atual de ocupantes."
                )
            cargo.max_ocupantes = max_ocupantes
        if permite_atribuicao is not None:
            cargo.permite_atribuicao = permite_atribuicao
        if permissao_administracao is not None:
            if not e_valido(permissao_administracao, TODAS):
                raise PermissaoInvalidaErro()
            cargo.permissao_administracao = permissao_administracao

        cargo = self.cargo_repository.update(cargo)
        self.uow.commit()
        return cargo

    def excluir_cargo(self, gremio_id: int, cargo_id: int, ator_id: int) -> None:
        ctx = self.autorizacao.contexto(gremio_id, ator_id)
        cargo = self._obter(gremio_id, cargo_id)

        if cargo.padrao:
            raise CargoPadraoProtegidoErro("O cargo padrão não pode ser excluído.")
        self.autorizacao.exigir_acima(ctx, cargo.prioridade)
        self._exigir_edicao(ctx.membro.id, gremio_id, cargo_id)

        # Atribuições e sobrescritas de canal do cargo caem em cascata (FK).
        if self.permissoes_relacionais:
            self.permissoes_relacionais.excluir_recurso(
                gremio_id, "CARGO", cargo.id
            )
        self.cargo_repository.delete(cargo.id)
        self.uow.commit()

    def listar_permissoes_relacionais(
        self, gremio_id: int, cargo_id: int, ator_id: int
    ) -> list[dict]:
        ctx = self.autorizacao.contexto(gremio_id, ator_id)
        self._exigir_gerenciar_permissoes(ctx.membro.id, gremio_id)
        cargo = self._obter(gremio_id, cargo_id)
        if not cargo.padrao:
            self.autorizacao.exigir_acima(ctx, cargo.prioridade)
        concedidas = self.permissoes_relacionais.listar_concedidas_ao_cargo(cargo_id)
        return [
            {
                "id": permissao.id,
                "codigo": permissao.codigo,
                "nome": permissao.nome,
                "descricao": permissao.descricao,
                "recurso_tipo": permissao.recurso_tipo,
                "recurso_id": permissao.recurso_id,
                "concedida": permissao.id in concedidas,
            }
            for permissao in self.permissoes_relacionais.listar_do_gremio(gremio_id)
        ]

    def definir_permissao_relacional(
        self,
        gremio_id: int,
        cargo_id: int,
        permissao_id: int,
        ator_id: int,
        conceder: bool,
    ) -> None:
        ctx = self.autorizacao.contexto(gremio_id, ator_id)
        cargo = self._obter(gremio_id, cargo_id)
        self.autorizacao.exigir_acima(ctx, cargo.prioridade)
        self._exigir_gerenciar_permissoes(ctx.membro.id, gremio_id)
        permissao = next(
            (
                p for p in self.permissoes_relacionais.listar_do_gremio(gremio_id)
                if p.id == permissao_id
            ),
            None,
        )
        self.permissoes_relacionais.exigir_membro(
            ctx.membro.id, permissao, "Conceder esta permissão"
        )
        self.permissoes_relacionais.definir_concessao_a_cargo(
            gremio_id, cargo_id, permissao_id, conceder
        )
        self.uow.commit()

    def _exigir_edicao(self, membro_id: int, gremio_id: int, cargo_id: int) -> None:
        if not self.permissoes_relacionais:
            raise SemPermissaoErro(["CARGO_EDITAR"])
        self.permissoes_relacionais.exigir_codigo_cargo(
            membro_id, gremio_id, cargo_id, "CARGO_EDITAR"
        )

    def _exigir_gerenciar_permissoes(
        self, membro_id: int, gremio_id: int
    ) -> None:
        if not self.permissoes_relacionais:
            raise SemPermissaoErro(["GREMIO_GERENCIAR_PERMISSOES"])
        self.permissoes_relacionais.exigir_codigo_gremio(
            membro_id, gremio_id, "GREMIO_GERENCIAR_PERMISSOES"
        )

    def _obter(self, gremio_id: int, cargo_id: int) -> Cargo:
        cargo = self.cargo_repository.get_by_id(cargo_id)
        if not cargo or cargo.gremio_id != gremio_id:
            raise CargoNaoExisteErro()
        return cargo
