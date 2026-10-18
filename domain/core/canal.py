from typing import Optional


class Canal:
    def __init__(
        self, id: int, gremio_id: int, nome: str,
        descricao: Optional[str] = None
    ):
        self.id = id
        self.gremio_id = gremio_id
        self.nome = nome
        self.descricao = descricao
