from typing import Optional
from pydantic import AliasChoices, BaseModel, Field


class GremioCriarSchema(BaseModel):
    nome_gremio: str = Field(
        ...,
        min_length=2,
        max_length=255,
        description="Nome do grêmio estudantil",
        examples=["Grêmio Estudantil Elo"]
    )


class GremioAtualizarSchema(BaseModel):
    nome: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=100,
        description="Novo nome do grêmio",
        validation_alias=AliasChoices("nome", "nome_gremio"),
    )
    descricao: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Descrição do grêmio",
    )
