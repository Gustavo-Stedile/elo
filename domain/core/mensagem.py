from datetime import datetime
from typing import Optional


class Mensagem:
    def __init__(
        self, id: int, canal_id: int, autor_id: int, conteudo: str,
        criada_em: datetime,
        editada_em: Optional[datetime] = None,
        autor_nome: Optional[str] = None,
    ):
        self.id = id
        self.canal_id = canal_id
        self.autor_id = autor_id
        self.conteudo = conteudo
        self.criada_em = criada_em
        self.editada_em = editada_em
        self.autor_nome = autor_nome  # preenchido pela camada de aplicação
