from typing import Optional


class Canal:
    def __init__(
        self, id: int, gremio_id: int, nome: str,
        descricao: Optional[str] = None,
        permissao_ver: int = 0,
        permissao_ler: int = 0,
        permissao_escrever: int = 0,
        permissao_gerenciar_mensagens: int = 0,
    ):
        self.id = id
        self.gremio_id = gremio_id
        self.nome = nome
        self.descricao = descricao
        self.permissao_ver = permissao_ver
        self.permissao_ler = permissao_ler
        self.permissao_escrever = permissao_escrever
        self.permissao_gerenciar_mensagens = permissao_gerenciar_mensagens
