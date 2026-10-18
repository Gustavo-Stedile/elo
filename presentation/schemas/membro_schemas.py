from typing import Optional

from pydantic import BaseModel

from application.membro_service import MembroDetalhe
from domain.core.permissoes import para_nomes


class MembroAdicionarSchema(BaseModel):
    usuario_id: int


class MembroResposta(BaseModel):
    usuario_id: int
    nome: Optional[str]
    fundador: bool
    cargos_ids: list[int]
    permissoes_permitidas: list[str]
    permissoes_negadas: list[str]

    @classmethod
    def de_detalhe(cls, m: MembroDetalhe) -> "MembroResposta":
        return cls(
            usuario_id=m.usuario_id,
            nome=m.nome,
            fundador=m.fundador,
            cargos_ids=m.cargos_ids,
            permissoes_permitidas=para_nomes(m.permissoes_permitidas),
            permissoes_negadas=para_nomes(m.permissoes_negadas),
        )
