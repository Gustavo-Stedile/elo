from typing import TYPE_CHECKING

from application.exceptions.autorizacao_exceptions import SemPermissaoErro
from domain.core import PermissaoGlobal

if TYPE_CHECKING:
    from infra.core.repositories.permissao_global_repo import (
        PermissaoGlobalRepository,
    )


PERMISSOES_GLOBAIS = (
    (
        "LEGITIMAR_GREMIO",
        "Legitimar grêmios",
        "Autoriza legitimar um grêmio no sistema.",
    ),
)


class PermissaoGlobalService:
    """Verifica permissões atribuídas diretamente a usuários do sistema."""

    def __init__(self, repositorio: "PermissaoGlobalRepository"):
        self.repositorio = repositorio

    def criar_catalogo(self) -> list[PermissaoGlobal]:
        return [
            self.repositorio.obter_ou_criar(codigo, nome, descricao)
            for codigo, nome, descricao in PERMISSOES_GLOBAIS
        ]

    def exigir(self, usuario_id: int, codigo: str) -> None:
        permissao = self.repositorio.obter_por_codigo(codigo)
        if not permissao or not self.repositorio.usuario_possui(
            usuario_id, permissao.id
        ):
            raise SemPermissaoErro([codigo])
