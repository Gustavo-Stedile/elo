from application.exceptions.autorizacao_exceptions import SemPermissaoErro
from domain.core import PermissaoObjeto
from infra.core.repositories import PermissaoObjetoRepository


PERMISSOES_GREMIO = (
    ("GREMIO_EDITAR_NOME", "Editar nome do grêmio"),
    ("GREMIO_EDITAR_DESCRICAO", "Editar descrição do grêmio"),
    ("GREMIO_CRIAR_CARGO", "Criar cargos"),
    ("GREMIO_CRIAR_CANAL", "Criar canais"),
    ("GREMIO_CRIAR_ENQUETE", "Criar enquetes do grêmio"),
    ("GREMIO_CRIAR_COMUNICADO", "Criar comunicados do grêmio"),
    ("GREMIO_GERENCIAR_PERMISSOES", "Gerenciar permissões do grêmio"),
)
PERMISSOES_CARGO = (
    ("CARGO_EDITAR", "Editar cargo"),
    ("CARGO_ATRIBUIR", "Atribuir ou remover cargo"),
)
PERMISSOES_CANAL = (
    ("CANAL_VER", "Ver canal"),
    ("CANAL_LER_HISTORICO", "Ler histórico do canal"),
    ("CANAL_ENVIAR_MENSAGENS", "Enviar mensagens no canal"),
    ("CANAL_GERENCIAR_MENSAGENS", "Gerenciar mensagens do canal"),
    ("CANAL_EDITAR", "Editar canal"),
    ("CANAL_EXCLUIR", "Excluir canal"),
    ("CANAL_GERENCIAR_PERMISSOES", "Gerenciar permissões do canal"),
    ("CANAL_CRIAR_ENQUETE", "Criar enquetes no canal"),
    ("CANAL_CRIAR_COMUNICADO", "Criar comunicados no canal"),
)
PERMISSOES_ENQUETE = (
    ("ENQUETE_VOTAR", "Votar nesta enquete"),
)
PERMISSOES_COMUNICADO = (
    ("COMUNICADO_VISUALIZAR", "Visualizar este comunicado"),
)


class PermissaoRelacionalService:
    """Cria permissões contextuais e mantém suas concessões a membros e cargos."""

    def __init__(self, repositorio: PermissaoObjetoRepository):
        self.repositorio = repositorio

    def criar_permissoes_gremio(self, gremio_id: int) -> list[PermissaoObjeto]:
        return [
            self.repositorio.obter_ou_criar(
                gremio_id, "GREMIO", gremio_id, codigo, nome
            )
            for codigo, nome in PERMISSOES_GREMIO
        ]

    def criar_permissoes_cargo(
        self,
        gremio_id: int,
        cargo_id: int,
        membro_criador_id: int | None,
        cargo_administrador_id: int | None,
    ) -> list[PermissaoObjeto]:
        permissoes = [
            self.repositorio.obter_ou_criar(
                gremio_id, "CARGO", cargo_id, codigo, nome
            )
            for codigo, nome in PERMISSOES_CARGO
        ]
        for permissao in permissoes:
            if membro_criador_id is not None:
                self.repositorio.conceder_a_membro(
                    permissao.id, membro_criador_id
                )
            if cargo_administrador_id is not None:
                self.repositorio.conceder_a_cargo(
                    permissao.id, cargo_administrador_id
                )
        return permissoes

    def criar_permissoes_canal(
        self,
        gremio_id: int,
        canal_id: int,
        membro_criador_id: int,
        cargo_membro_id: int,
        cargo_administrador_id: int,
    ) -> list[PermissaoObjeto]:
        permissoes = self.criar_permissoes_recurso(
            gremio_id, "CANAL", canal_id, PERMISSOES_CANAL
        )
        por_codigo = {p.codigo: p for p in permissoes}
        codigos_membro = (
            "CANAL_VER",
            "CANAL_LER_HISTORICO",
            "CANAL_ENVIAR_MENSAGENS",
        )
        codigos_criador = (
            "CANAL_EDITAR",
            "CANAL_EXCLUIR",
            "CANAL_GERENCIAR_PERMISSOES",
        )
        for codigo in codigos_membro:
            self.repositorio.conceder_a_cargo(
                por_codigo[codigo].id, cargo_membro_id
            )
        for permissao in permissoes:
            self.repositorio.conceder_a_cargo(
                permissao.id, cargo_administrador_id
            )
        for codigo in codigos_criador:
            self.repositorio.conceder_a_membro(
                por_codigo[codigo].id, membro_criador_id
            )
        return permissoes

    def criar_permissoes_enquete(
        self,
        gremio_id: int,
        enquete_id: int,
        criador_membro_id: int,
        cargo_membro_id: int,
        cargo_administrador_id: int,
    ) -> list[PermissaoObjeto]:
        permissoes = self.criar_permissoes_recurso(
            gremio_id, "ENQUETE", enquete_id, PERMISSOES_ENQUETE
        )
        for permissao in permissoes:
            self.repositorio.conceder_a_cargo(
                permissao.id, cargo_membro_id
            )
            self.repositorio.conceder_a_cargo(
                permissao.id, cargo_administrador_id
            )
            self.repositorio.conceder_a_membro(
                permissao.id, criador_membro_id
            )
        return permissoes

    def criar_permissoes_comunicado(
        self,
        gremio_id: int,
        comunicado_id: int,
        autor_membro_id: int,
        cargo_membro_id: int,
        cargo_administrador_id: int,
    ) -> list[PermissaoObjeto]:
        permissoes = self.criar_permissoes_recurso(
            gremio_id, "COMUNICADO", comunicado_id, PERMISSOES_COMUNICADO
        )
        for permissao in permissoes:
            self.repositorio.conceder_a_cargo(
                permissao.id, cargo_membro_id
            )
            self.repositorio.conceder_a_cargo(
                permissao.id, cargo_administrador_id
            )
            self.repositorio.conceder_a_membro(
                permissao.id, autor_membro_id
            )
        return permissoes

    def criar_permissoes_recurso(
        self,
        gremio_id: int,
        recurso_tipo: str,
        recurso_id: int,
        definicoes: tuple[tuple[str, str], ...],
    ) -> list[PermissaoObjeto]:
        return [
            self.repositorio.obter_ou_criar(
                gremio_id, recurso_tipo, recurso_id, codigo, nome
            )
            for codigo, nome in definicoes
        ]

    def conceder_permissoes_gremio_ao_cargo(
        self, gremio_id: int, cargo_id: int
    ) -> None:
        for permissao in self.criar_permissoes_gremio(gremio_id):
            self.repositorio.conceder_a_cargo(permissao.id, cargo_id)

    def conceder_a_cargo(self, permissao_id: int, cargo_id: int) -> None:
        self.repositorio.conceder_a_cargo(permissao_id, cargo_id)

    def revogar_de_cargo(self, permissao_id: int, cargo_id: int) -> None:
        self.repositorio.revogar_de_cargo(permissao_id, cargo_id)

    def listar_do_gremio(self, gremio_id: int) -> list[PermissaoObjeto]:
        return self.repositorio.listar_do_gremio(gremio_id)

    def listar_do_gremio_por_ids(self, ids: set[int]) -> list[PermissaoObjeto]:
        return self.repositorio.listar_do_gremio_por_ids(ids)

    def listar_do_recurso(
        self, gremio_id: int, recurso_tipo: str, recurso_id: int
    ) -> list[PermissaoObjeto]:
        return self.repositorio.listar_do_recurso(
            gremio_id, recurso_tipo, recurso_id
        )

    def listar_concedidas_ao_cargo(self, cargo_id: int) -> set[int]:
        return {
            permissao.id
            for permissao in self.repositorio.listar_do_cargo(cargo_id)
        }

    def listar_concedidas_ao_membro(self, membro_id: int) -> list[PermissaoObjeto]:
        ids = self.repositorio.listar_ids_concedidos_ao_membro(membro_id)
        return [
            permissao
            for permissao in self.repositorio.listar_do_gremio_por_ids(ids)
        ]

    def exigir_membro(
        self,
        membro_id: int,
        permissao: PermissaoObjeto | None,
        nome: str | None = None,
    ) -> None:
        if not permissao or not self.repositorio.membro_possui(
            membro_id, permissao.id
        ):
            raise SemPermissaoErro([nome or (permissao.nome if permissao else "permissão")])

    def membro_possui_codigo(
        self,
        membro_id: int,
        gremio_id: int,
        recurso_tipo: str,
        recurso_id: int,
        codigo: str,
    ) -> bool:
        permissao = self.repositorio.obter_por_recurso(
            gremio_id, recurso_tipo, recurso_id, codigo
        )
        return bool(
            permissao
            and self.repositorio.membro_possui(membro_id, permissao.id)
        )

    def exigir_codigo_gremio(self, membro_id: int, gremio_id: int, codigo: str) -> None:
        permissao = self.repositorio.obter_por_recurso(
            gremio_id, "GREMIO", gremio_id, codigo
        )
        self.exigir_membro(membro_id, permissao, codigo)

    def exigir_codigo_cargo(
        self, membro_id: int, gremio_id: int, cargo_id: int, codigo: str
    ) -> None:
        permissao = self.repositorio.obter_por_recurso(
            gremio_id, "CARGO", cargo_id, codigo
        )
        self.exigir_membro(membro_id, permissao, codigo)

    def definir_concessao_a_cargo(
        self, gremio_id: int, cargo_id: int, permissao_id: int, conceder: bool
    ) -> None:
        permissao = self.repositorio.obter(permissao_id)
        if not permissao or permissao.gremio_id != gremio_id:
            raise SemPermissaoErro(["Permissão do grêmio"])
        if conceder:
            self.conceder_a_cargo(permissao_id, cargo_id)
        else:
            self.revogar_de_cargo(permissao_id, cargo_id)

    def definir_concessao_a_membro(
        self, gremio_id: int, membro_id: int, permissao_id: int, conceder: bool
    ) -> None:
        permissao = self.repositorio.obter(permissao_id)
        if not permissao or permissao.gremio_id != gremio_id:
            raise SemPermissaoErro(["Permissão do grêmio"])
        if conceder:
            self.repositorio.conceder_a_membro(permissao_id, membro_id)
        else:
            self.repositorio.revogar_de_membro(permissao_id, membro_id)

    def exigir_codigo_recurso(
        self,
        membro_id: int,
        gremio_id: int,
        recurso_tipo: str,
        recurso_id: int,
        codigo: str,
    ) -> None:
        permissao = self.repositorio.obter_por_recurso(
            gremio_id, recurso_tipo, recurso_id, codigo
        )
        self.exigir_membro(membro_id, permissao, codigo)

    def exigir_codigo_canal(
        self, membro_id: int, gremio_id: int, canal_id: int, codigo: str
    ) -> None:
        self.exigir_codigo_recurso(
            membro_id, gremio_id, "CANAL", canal_id, codigo
        )

    def excluir_recurso(
        self, gremio_id: int, recurso_tipo: str, recurso_id: int
    ) -> None:
        self.repositorio.excluir_do_recurso(
            gremio_id, recurso_tipo, recurso_id
        )
