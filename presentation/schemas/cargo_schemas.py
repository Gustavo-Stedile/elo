from typing import Optional

from pydantic import BaseModel, Field

from domain.core import Cargo
from domain.core.permissoes import para_nomes
from presentation.schemas.permissao_schemas import PermissaoNome


class CargoCriarSchema(BaseModel):
    nome: str = Field(..., min_length=2, max_length=50, examples=["Moderador"])
    cor: str = Field(default="#99AAB5", pattern=r"^#[0-9A-Fa-f]{6}$")
    prioridade: int = Field(
        ..., ge=1, le=1000,
        description="Hierarquia: só se gerencia cargos de prioridade menor que a sua",
    )
    permissoes: list[PermissaoNome] = Field(default_factory=list)


class CargoAtualizarSchema(BaseModel):
    nome: Optional[str] = Field(default=None, min_length=2, max_length=50)
    cor: Optional[str] = Field(default=None, pattern=r"^#[0-9A-Fa-f]{6}$")
    prioridade: Optional[int] = Field(default=None, ge=1, le=1000)
    permissoes: Optional[list[PermissaoNome]] = None


class CargoResposta(BaseModel):
    id: int
    gremio_id: int
    nome: str
    cor: str
    prioridade: int
    permissoes: list[str]
    padrao: bool

    @classmethod
    def de_dominio(cls, cargo: Cargo) -> "CargoResposta":
        return cls(
            id=cargo.id,
            gremio_id=cargo.gremio_id,
            nome=cargo.nome,
            cor=cargo.cor,
            prioridade=cargo.prioridade,
            permissoes=para_nomes(cargo.permissoes),
            padrao=cargo.padrao,
        )
