from typing import Optional

from pydantic import BaseModel, Field

from domain.core import Canal, PermissaoCanal
from domain.core.permissoes import para_nomes


class CanalCriarSchema(BaseModel):
    nome: str = Field(..., min_length=1, max_length=100, examples=["avisos"])
    descricao: Optional[str] = Field(default=None, max_length=255)


class CanalAtualizarSchema(BaseModel):
    nome: Optional[str] = Field(default=None, min_length=1, max_length=100)
    descricao: Optional[str] = Field(default=None, max_length=255)


class CanalResposta(BaseModel):
    id: int
    gremio_id: int
    nome: str
    descricao: Optional[str]
    # Permissões efetivas do usuário logado neste canal (útil para o front
    # esconder o que o usuário não pode fazer). Ausente nas listagens.
    minhas_permissoes: Optional[list[str]] = None

    @classmethod
    def de_dominio(cls, canal: Canal, permissoes: Optional[int] = None) -> "CanalResposta":
        return cls(
            id=canal.id,
            gremio_id=canal.gremio_id,
            nome=canal.nome,
            descricao=canal.descricao,
            minhas_permissoes=None if permissoes is None else para_nomes(permissoes),
        )


class PermissaoCanalResposta(BaseModel):
    canal_id: int
    cargo_id: Optional[int]
    usuario_id: Optional[int]
    permitir: list[str]
    negar: list[str]

    @classmethod
    def de_dominio(cls, p: PermissaoCanal) -> "PermissaoCanalResposta":
        return cls(
            canal_id=p.canal_id,
            cargo_id=p.cargo_id,
            usuario_id=p.usuario_id,
            permitir=para_nomes(p.permitir),
            negar=para_nomes(p.negar),
        )
