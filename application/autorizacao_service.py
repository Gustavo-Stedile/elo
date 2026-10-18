from dataclasses import dataclass

from application.exceptions.autorizacao_exceptions import (
    HierarquiaInsuficienteErro,
    NaoEMembroErro,
    SemPermissaoErro,
)
from application.exceptions.canal_exceptions import CanalNaoExisteErro
from application.exceptions.gremio_exceptions import GremioNaoExisteErro
from domain.core import Canal, Cargo, Gremio, MembroGremio, PermissaoCanal
from domain.core.autorizacao import (
    calcular_permissoes_canal,
    calcular_permissoes_gremio,
)
from domain.core.permissoes import Permissao, para_nomes
from infra.core.repositories import (
    CanalRepository,
    CargoRepository,
    GremioRepository,
    MembroGremioRepository,
    PermissaoCanalRepository,
)

# Maior que qualquer prioridade de cargo: o fundador está acima de todos.
PRIORIDADE_FUNDADOR = 10**9


@dataclass
class ContextoMembro:
    """Quem é o usuário dentro de um grêmio e o que ele pode fazer nele."""
    gremio: Gremio
    membro: MembroGremio
    cargo_padrao: Cargo | None
    cargos: list[Cargo]          # cargos atribuídos (sem o padrão)
    fundador: bool
    permissoes: int              # permissões efetivas no grêmio (bitmask)
    prioridade: int              # maior prioridade entre seus cargos

    @property
    def usuario_id(self) -> int:
        return self.membro.usuario_id


@dataclass
class AcessoCanal:
    canal: Canal
    contexto: ContextoMembro
    permissoes: int              # permissões efetivas neste canal (bitmask)


class AutorizacaoService:
    """Único ponto onde permissões são calculadas e exigidas."""

    def __init__(
        self,
        gremio_repository: GremioRepository,
        membro_gremio_repository: MembroGremioRepository,
        cargo_repository: CargoRepository,
        canal_repository: CanalRepository,
        permissao_canal_repository: PermissaoCanalRepository,
    ):
        self.gremio_repository = gremio_repository
        self.membro_gremio_repository = membro_gremio_repository
        self.cargo_repository = cargo_repository
        self.canal_repository = canal_repository
        self.permissao_canal_repository = permissao_canal_repository

    # ------------------------------------------------------------------
    # Grêmio
    # ------------------------------------------------------------------
    def contexto(self, gremio_id: int, usuario_id: int) -> ContextoMembro:
        """Carrega o vínculo do usuário com o grêmio. Falha se não for membro."""
        gremio = self.gremio_repository.get_by_id(gremio_id)
        if not gremio:
            raise GremioNaoExisteErro()

        membro = self.membro_gremio_repository.get(gremio_id, usuario_id)
        if not membro:
            raise NaoEMembroErro()

        cargo_padrao = self.cargo_repository.get_padrao(gremio_id)
        cargos = self.cargo_repository.listar_do_membro(membro.id)
        fundador = gremio.fundador_id == usuario_id

        permissoes = calcular_permissoes_gremio(
            fundador=fundador,
            cargo_padrao=cargo_padrao,
            cargos=cargos,
            permitir_usuario=membro.permissoes_permitidas,
            negar_usuario=membro.permissoes_negadas,
        )
        prioridade = (
            PRIORIDADE_FUNDADOR
            if fundador
            else max((c.prioridade for c in cargos), default=0)
        )

        return ContextoMembro(
            gremio=gremio,
            membro=membro,
            cargo_padrao=cargo_padrao,
            cargos=cargos,
            fundador=fundador,
            permissoes=permissoes,
            prioridade=prioridade,
        )

    def exigir_gremio(
        self, gremio_id: int, usuario_id: int, permissao: Permissao
    ) -> ContextoMembro:
        ctx = self.contexto(gremio_id, usuario_id)
        self.exigir(ctx.permissoes, permissao)
        return ctx

    # ------------------------------------------------------------------
    # Canal
    # ------------------------------------------------------------------
    def permissoes_no_canal(
        self,
        ctx: ContextoMembro,
        canal_id: int,
        sobrescritas: list[PermissaoCanal] | None = None,
    ) -> int:
        if sobrescritas is None:
            sobrescritas = self.permissao_canal_repository.listar_por_canal(canal_id)

        ids_cargos = {c.id for c in ctx.cargos}
        id_padrao = ctx.cargo_padrao.id if ctx.cargo_padrao else None

        ow_padrao = next(
            (o for o in sobrescritas if id_padrao is not None and o.cargo_id == id_padrao),
            None,
        )
        ow_cargos = [o for o in sobrescritas if o.cargo_id in ids_cargos]
        ow_usuario = next(
            (o for o in sobrescritas if o.usuario_id == ctx.usuario_id), None
        )

        return calcular_permissoes_canal(
            ctx.permissoes,
            ow_padrao=ow_padrao,
            ow_cargos=ow_cargos,
            ow_usuario=ow_usuario,
        )

    def acessar_canal(
        self,
        canal_id: int,
        usuario_id: int,
        exigir: Permissao | int = Permissao.VER_CANAL,
    ) -> AcessoCanal:
        """Carrega o canal e confere as permissões do usuário nele.

        Quem não enxerga o canal recebe "não encontrado" (como se ele não
        existisse), para não vazar a existência de canais privados. Quem tem
        GERENCIAR_CANAIS sempre o encontra, para poder corrigir suas permissões;
        ler/enviar mensagens continua dependendo das permissões do canal.
        """
        canal = self.canal_repository.get_by_id(canal_id)
        if not canal:
            raise CanalNaoExisteErro()

        try:
            ctx = self.contexto(canal.gremio_id, usuario_id)
        except NaoEMembroErro:
            raise CanalNaoExisteErro()

        permissoes = self.permissoes_no_canal(ctx, canal.id)

        enxerga = permissoes & int(Permissao.VER_CANAL)
        gerencia = ctx.permissoes & int(Permissao.GERENCIAR_CANAIS)
        if not enxerga and not gerencia:
            raise CanalNaoExisteErro()

        self.exigir(permissoes, exigir)
        return AcessoCanal(canal=canal, contexto=ctx, permissoes=permissoes)

    # ------------------------------------------------------------------
    # Regras reutilizáveis
    # ------------------------------------------------------------------
    @staticmethod
    def exigir(permissoes: int, necessarias: Permissao | int) -> None:
        faltando = int(necessarias) & ~permissoes
        if faltando:
            raise SemPermissaoErro(para_nomes(faltando))

    @staticmethod
    def exigir_acima(ctx: ContextoMembro, prioridade_alvo: int) -> None:
        """O ator só age sobre cargos/membros de prioridade estritamente menor."""
        if ctx.prioridade <= prioridade_alvo:
            raise HierarquiaInsuficienteErro()

    @staticmethod
    def exigir_subconjunto(permissoes_do_ator: int, a_conceder: int) -> None:
        """Ninguém concede permissões que ele mesmo não possui."""
        indevidas = a_conceder & ~permissoes_do_ator
        if indevidas:
            raise SemPermissaoErro(
                mensagem=(
                    "Você não pode conceder permissões que não possui: "
                    + ", ".join(para_nomes(indevidas)) + "."
                )
            )
