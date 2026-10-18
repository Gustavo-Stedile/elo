from typing import Optional
from pydantic import BaseModel, Field


class GremioCriarSchema(BaseModel):
    nome_gremio: str = Field(
        ...,
        min_length=2,
        max_length=255,
        description="Nome do grêmio estudantil",
        examples=["Grêmio Estudantil Elo"]
    )


class GremioAtualizarSchema(BaseModel):
    nome_gremio: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=255,
        description="Novo nome do grêmio estudantil",
        examples=["Novo Nome do Grêmio"]
    )

