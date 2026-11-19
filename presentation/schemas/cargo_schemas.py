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
    max_ocupantes: int = Field(default=0, ge=0, description="0 significa sem limite")
    permite_atribuicao: bool = Field(
        default=False,
        description="Permite que ocupantes deste cargo atribuam este cargo a membros",
    )
    permissao_administracao: PermissaoNome = Field(
        default="GERENCIAR_CARGOS",
        description="Permissão necessária para administrar e atribuir este cargo",
    )


class CargoAtualizarSchema(BaseModel):
    nome: Optional[str] = Field(default=None, min_length=2, max_length=50)
    cor: Optional[str] = Field(default=None, pattern=r"^#[0-9A-Fa-f]{6}$")
    prioridade: Optional[int] = Field(default=None, ge=1, le=1000)
    permissoes: Optional[list[PermissaoNome]] = None
    max_ocupantes: Optional[int] = Field(default=None, ge=0)
    permite_atribuicao: Optional[bool] = None
    permissao_administracao: Optional[PermissaoNome] = None


class CargoResposta(BaseModel):
    id: int
    gremio_id: int
    nome: str
    cor: str
    prioridade: int
    permissoes: list[str]
    padrao: bool
    max_ocupantes: int
    permite_atribuicao: bool
    permissao_administracao: str

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
            max_ocupantes=cargo.max_ocupantes,
            permite_atribuicao=cargo.permite_atribuicao,
            permissao_administracao=(
                para_nomes(cargo.permissao_administracao)[0]
                if para_nomes(cargo.permissao_administracao)
                else "GERENCIAR_CARGOS"
            ),
        )
