from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from domain.core import Mensagem


class MensagemEnviarSchema(BaseModel):
    conteudo: str = Field(..., min_length=1, max_length=4000, examples=["Olá, pessoal!"])


class MensagemResposta(BaseModel):
    id: int
    canal_id: int
    autor_id: int
    autor_nome: Optional[str]
    conteudo: str
    criada_em: datetime
    editada_em: Optional[datetime]

    @classmethod
    def de_dominio(cls, m: Mensagem) -> "MensagemResposta":
        return cls(
            id=m.id,
            canal_id=m.canal_id,
            autor_id=m.autor_id,
            autor_nome=m.autor_nome,
            conteudo=m.conteudo,
            criada_em=m.criada_em,
            editada_em=m.editada_em,
        )
