from typing import Literal

from pydantic import BaseModel, Field

from domain.core.permissoes import nomes_validos

# Literal gerado a partir do enum, para o schema nunca sair de sincronia com
# o domínio. Valores desconhecidos viram 422 automaticamente.
PermissaoNome = Literal[tuple(nomes_validos())]


class PermissoesSchema(BaseModel):
    permitir: list[PermissaoNome] = Field(
        default_factory=list,
        description="Permissões concedidas",
        examples=[["ENVIAR_MENSAGENS"]],
    )
    negar: list[PermissaoNome] = Field(
        default_factory=list,
        description="Permissões negadas (vencem as concedidas por cargos)",
        examples=[["ENVIAR_MENSAGENS"]],
    )
