class PermissaoGlobal:
    """Permissão aplicável ao sistema, sem vínculo com um grêmio."""

    def __init__(
        self,
        id: int | None,
        codigo: str,
        nome: str,
        descricao: str | None = None,
    ):
        self.id = id
        self.codigo = codigo
        self.nome = nome
        self.descricao = descricao
