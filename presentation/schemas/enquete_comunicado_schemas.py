from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field

from domain.core import Enquete, Comunicado


class EnqueteCriarSchema(BaseModel):
    pergunta: str = Field(..., min_length=3, max_length=255)
    opcoes: list[str] = Field(..., min_length=2, max_length=20)
    tipo_votacao: Literal["UNICA", "MULTIPLA"] = "UNICA"
    votos_visiveis: bool = True


class EnqueteVotarSchema(BaseModel):
    opcao_ids: list[int] = Field(..., min_length=1)


class EnqueteOpcaoResposta(BaseModel):
    id: int
    texto: str
    votos: int | None
    participantes: list[str] | None = None


class EnqueteResposta(BaseModel):
    id: int
    gremio_id: int
    canal_id: int | None
    criador_id: int
    criador_nome: str | None
    pergunta: str
    tipo_votacao: str
    votos_visiveis: bool
    criada_em: datetime
    opcoes: list[EnqueteOpcaoResposta]

    @classmethod
    def de_dominio(cls, e: Enquete):
        return cls(
            id=e.id,
            gremio_id=e.gremio_id,
            canal_id=e.canal_id,
            criador_id=e.criador_id,
            criador_nome=e.criador_nome,
            pergunta=e.pergunta,
            tipo_votacao=e.tipo_votacao,
            votos_visiveis=e.votos_visiveis,
            criada_em=e.criada_em,
            opcoes=[
                EnqueteOpcaoResposta(
                    id=o.id,
                    texto=o.texto,
                    votos=o.votos,
                    participantes=o.participantes,
                )
                for o in e.opcoes
            ],
        )


class ComunicadoCriarSchema(BaseModel):
    titulo: str = Field(..., min_length=2, max_length=255)
    texto: str = Field(..., min_length=1, max_length=4000)
    valido_ate: datetime


class ComunicadoResposta(BaseModel):
    id: int
    gremio_id: int
    canal_id: int | None
    autor_id: int
    autor_nome: str | None
    titulo: str
    texto: str
    valido_ate: datetime
    criado_em: datetime

    @classmethod
    def de_dominio(cls, c: Comunicado):
        return cls(
            id=c.id,
            gremio_id=c.gremio_id,
            canal_id=c.canal_id,
            autor_id=c.autor_id,
            autor_nome=c.autor_nome,
            titulo=c.titulo,
            texto=c.texto,
            valido_ate=c.valido_ate,
            criado_em=c.criado_em,
        )
