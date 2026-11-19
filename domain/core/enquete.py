from datetime import datetime
from typing import Optional


class EnqueteOpcao:
    def __init__(self, id: int, enquete_id: int, texto: str):
        self.id = id
        self.enquete_id = enquete_id
        self.texto = texto
        self.votos: int | None = 0
        self.participantes: list[str] | None = None


class Enquete:
    def __init__(
        self,
        id: int,
        gremio_id: int,
        criador_id: int,
        pergunta: str,
        tipo_votacao: str,
        votos_visiveis: bool,
        criada_em: datetime,
        canal_id: Optional[int] = None,
        criador_nome: Optional[str] = None,
        opcoes: list[EnqueteOpcao] | None = None,
    ):
        self.id = id
        self.gremio_id = gremio_id
        self.canal_id = canal_id
        self.criador_id = criador_id
        self.criador_nome = criador_nome
        self.pergunta = pergunta
        self.tipo_votacao = tipo_votacao
        self.votos_visiveis = votos_visiveis
        self.criada_em = criada_em
        self.opcoes = opcoes or []
