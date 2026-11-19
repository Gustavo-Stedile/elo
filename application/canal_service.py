from application.autorizacao_service import AcessoCanal, AutorizacaoService
from application.exceptions.autorizacao_exceptions import (
    PermissaoInvalidaErro,
    SemPermissaoErro,
)
from application.exceptions.cargo_exceptions import CargoNaoExisteErro
from application.exceptions.membro_gremio_exceptions import (
    FundadorProtegidoErro,
    MembroNaoExisteErro,
)
from application.permissao_relacional_service import PermissaoRelacionalService
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
        permissoes_relacionais: PermissaoRelacionalService | None = None,
    ):
        self.canal_repository = canal_repository
        self.permissao_canal_repository = permissao_canal_repository
        self.cargo_repository = cargo_repository
        self.membro_gremio_repository = membro_gremio_repository
        self.autorizacao = autorizacao
        self.uow = uow
        self.permissoes_relacionais = permissoes_relacionais

    # ------------------------------------------------------------------
    # Canais
    # ------------------------------------------------------------------
    def criar_canal(
        self, gremio_id: int, ator_id: int, nome: str, descricao: str | None = None,
        permissao_ver: int = 0,
        permissao_ler: int = 0,
        permissao_escrever: int = 0,
        permissao_gerenciar_mensagens: int = 0,
    ) -> Canal:
        contexto = self.autorizacao.contexto(gremio_id, ator_id)
        if not self.permissoes_relacionais:
            raise SemPermissaoErro(["GREMIO_CRIAR_CANAL"])
        self.permissoes_relacionais.exigir_codigo_gremio(
            contexto.membro.id, gremio_id, "GREMIO_CRIAR_CANAL"
        )
        canal = self.canal_repository.create(Canal(
            id=None, gremio_id=gremio_id, nome=nome.strip(), descricao=descricao,
        ))
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
            raise SemPermissaoErro(["cargos Membro e Administrador"])
        self.permissoes_relacionais.criar_permissoes_canal(
            gremio_id,
            canal.id,
            contexto.membro.id,
            cargo_membro.id,
            cargo_administrador.id,
        )
        self.uow.commit()
        return canal

    def listar_canais(self, gremio_id: int, usuario_id: int) -> list[Canal]:
        """Apenas os canais que o usuário pode ver."""
        ctx = self.autorizacao.contexto(gremio_id, usuario_id)
        canais = self.canal_repository.listar_por_gremio(gremio_id)
        return [
            c for c in canais
            if self.autorizacao.permissoes_no_canal(ctx, c.id) & _VER
        ]

    def obter_canal(self, canal_id: int, usuario_id: int) -> AcessoCanal:
        return self.autorizacao.acessar_canal(canal_id, usuario_id, Permissao.VER_CANAL)

    def atualizar_canal(
        self,
        canal_id: int,
        ator_id: int,
        nome: str | None = None,
        descricao: str | None = None,
        permissao_ver: int | None = None,
        permissao_ler: int | None = None,
        permissao_escrever: int | None = None,
        permissao_gerenciar_mensagens: int | None = None,
    ) -> Canal:
        canal, contexto = self._obter_canal_para_gerenciar(
            canal_id, ator_id, "CANAL_EDITAR"
        )
        if nome is not None:
            canal.nome = nome.strip()
        if descricao is not None:
            canal.descricao = descricao
        canal = self.canal_repository.update(canal)
        self.uow.commit()
        return canal

    def excluir_canal(self, canal_id: int, ator_id: int) -> None:
        canal, contexto = self._obter_canal_para_gerenciar(
            canal_id, ator_id, "CANAL_EXCLUIR"
        )
        if self.permissoes_relacionais:
            self.permissoes_relacionais.excluir_recurso(
                canal.gremio_id, "CANAL", canal.id
            )
        self.canal_repository.delete(canal.id)
        self.uow.commit()

    # ------------------------------------------------------------------
    # Permissões do canal
    # ------------------------------------------------------------------
    def listar_permissoes(self, canal_id: int, ator_id: int) -> list[PermissaoCanal]:
        canal, _ = self._obter_canal_para_gerenciar(
            canal_id, ator_id, "CANAL_GERENCIAR_PERMISSOES"
        )
        return self.permissao_canal_repository.listar_por_canal(canal.id)

    def listar_permissoes_relacionais(
        self, canal_id: int, ator_id: int, cargo_id: int
    ) -> list[dict]:
        canal, contexto = self._obter_canal_para_gerenciar(
            canal_id, ator_id, "CANAL_GERENCIAR_PERMISSOES"
        )
        cargo = self.cargo_repository.get_by_id(cargo_id)
        if not cargo or cargo.gremio_id != canal.gremio_id:
            raise CargoNaoExisteErro()
        if not cargo.padrao:
            self.autorizacao.exigir_acima(contexto, cargo.prioridade)
        concedidas = self.permissoes_relacionais.listar_concedidas_ao_cargo(
            cargo_id
        )
        return [
            {
                "id": permissao.id,
                "codigo": permissao.codigo,
                "nome": permissao.nome,
                "concedida": permissao.id in concedidas,
            }
            for permissao in self.permissoes_relacionais.listar_do_recurso(
                canal.gremio_id, "CANAL", canal.id
            )
        ]

    def definir_permissao_relacional_cargo(
        self,
        canal_id: int,
        ator_id: int,
        cargo_id: int,
        permissao_id: int,
        conceder: bool,
    ) -> None:
        canal, contexto = self._obter_canal_para_gerenciar(
            canal_id, ator_id, "CANAL_GERENCIAR_PERMISSOES"
        )
        cargo = self.cargo_repository.get_by_id(cargo_id)
        if not cargo or cargo.gremio_id != canal.gremio_id:
            raise CargoNaoExisteErro()
        self.autorizacao.exigir_acima(contexto, cargo.prioridade)
        permissao = next(
            (
                item for item in self.permissoes_relacionais.listar_do_recurso(
                    canal.gremio_id, "CANAL", canal.id
                )
                if item.id == permissao_id
            ),
            None,
        )
        self.permissoes_relacionais.exigir_membro(
            contexto.membro.id, permissao, "Conceder esta permissão"
        )
        self.permissoes_relacionais.definir_concessao_a_cargo(
            canal.gremio_id, cargo_id, permissao_id, conceder
        )
        self.uow.commit()

    def definir_permissao_cargo(
        self, canal_id: int, ator_id: int, cargo_id: int,
        permitir: int, negar: int,
    ) -> None:
        """Define a sobrescrita de um cargo no canal (substitui a anterior).

        Retorna None quando permitir e negar são 0 (a sobrescrita é removida).
        """
        acesso = self.autorizacao.acessar_canal(canal_id, ator_id, _VER)
        self._validar_mascaras(permitir, negar)

        cargo = self.cargo_repository.get_by_id(cargo_id)
        if not cargo or cargo.gremio_id != acesso.canal.gremio_id:
            raise CargoNaoExisteErro()

        self._exigir_gerenciar_permissoes(
            acesso.contexto.membro.id, acesso.canal
        )
        # O cargo padrão vale para todos e é exceção à hierarquia.
        if not cargo.padrao:
            self.autorizacao.exigir_acima(acesso.contexto, cargo.prioridade)
        resultado = self._substituir_concessoes_canal(
            acesso.canal,
            acesso.contexto.membro.id,
            cargo.id,
            None,
            permitir,
            negar,
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
        acesso = self.autorizacao.acessar_canal(canal_id, ator_id, _VER)
        self._validar_mascaras(permitir, negar)

        gremio_id = acesso.canal.gremio_id
        if not self.membro_gremio_repository.get(gremio_id, usuario_id):
            raise MembroNaoExisteErro()
        if usuario_id == acesso.contexto.gremio.fundador_id:
            raise FundadorProtegidoErro()

        alvo_ctx = self.autorizacao.contexto(gremio_id, usuario_id)
        if alvo_ctx.prioridade > acesso.contexto.prioridade:
            self.autorizacao.exigir_acima(acesso.contexto, alvo_ctx.prioridade)
        self._exigir_gerenciar_permissoes(
            acesso.contexto.membro.id, acesso.canal
        )
        self.autorizacao.exigir_acima(acesso.contexto, alvo_ctx.prioridade)
        self.autorizacao.exigir_subconjunto(acesso.permissoes, permitir)

        membro = self.membro_gremio_repository.get(gremio_id, usuario_id)
        resultado = self._substituir_concessoes_canal(
            acesso.canal,
            acesso.contexto.membro.id,
            None,
            membro.id,
            permitir,
            negar,
        )
        self.uow.commit()
        return resultado

    def remover_permissao_cargo(self, canal_id: int, ator_id: int, cargo_id: int) -> None:
        self.definir_permissao_cargo(canal_id, ator_id, cargo_id, 0, 0)

    def remover_permissao_usuario(self, canal_id: int, ator_id: int, usuario_id: int) -> None:
        self.definir_permissao_usuario(canal_id, ator_id, usuario_id, 0, 0)

    def _substituir_concessoes_canal(
        self,
        canal: Canal,
        ator_membro_id: int,
        cargo_id: int | None,
        membro_id: int | None,
        permitir: int,
        negar: int,
    ) -> None:
        if not self.permissoes_relacionais:
            raise SemPermissaoErro(["Permissões relacionais do canal"])
        codigos = (
            (int(Permissao.VER_CANAL), "CANAL_VER"),
            (int(Permissao.LER_HISTORICO), "CANAL_LER_HISTORICO"),
            (int(Permissao.ENVIAR_MENSAGENS), "CANAL_ENVIAR_MENSAGENS"),
            (int(Permissao.GERENCIAR_MENSAGENS), "CANAL_GERENCIAR_MENSAGENS"),
        )
        alvo = cargo_id if cargo_id is not None else membro_id
        for bit, codigo in codigos:
            if not ((permitir | negar) & bit):
                continue
            permissao = next(
                (
                    item
                    for item in self.permissoes_relacionais.listar_do_recurso(
                        canal.gremio_id, "CANAL", canal.id
                    )
                    if item.codigo == codigo
                ),
                None,
            )
            if not permissao:
                continue
            conceder = bool(permitir & bit) and not bool(negar & bit)
            if conceder:
                self.permissoes_relacionais.exigir_membro(
                    ator_membro_id,
                    permissao,
                    "Conceder esta permissão",
                )
            if cargo_id is not None:
                self.permissoes_relacionais.definir_concessao_a_cargo(
                    canal.gremio_id, cargo_id, permissao.id, conceder
                )
            else:
                self.permissoes_relacionais.definir_concessao_a_membro(
                    canal.gremio_id, membro_id, permissao.id, conceder
                )
        return None

    def _obter_canal_para_gerenciar(
        self, canal_id: int, ator_id: int, codigo: str
    ) -> tuple[Canal, object]:
        canal = self.canal_repository.get_by_id(canal_id)
        if not canal:
            from application.exceptions.canal_exceptions import CanalNaoExisteErro
            raise CanalNaoExisteErro()
        contexto = self.autorizacao.contexto(canal.gremio_id, ator_id)
        if not self.permissoes_relacionais:
            raise SemPermissaoErro([codigo])
        self.permissoes_relacionais.exigir_codigo_canal(
            contexto.membro.id, canal.gremio_id, canal.id, codigo
        )
        return canal, contexto

    def _exigir_gerenciar_permissoes(self, membro_id: int, canal: Canal) -> None:
        if not self.permissoes_relacionais:
            raise SemPermissaoErro(["CANAL_GERENCIAR_PERMISSOES"])
        self.permissoes_relacionais.exigir_codigo_canal(
            membro_id, canal.gremio_id, canal.id,
            "CANAL_GERENCIAR_PERMISSOES",
        )

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
