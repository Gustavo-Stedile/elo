class PermissaoObjeto:
    """Permissão contextual vinculada a um grêmio ou cargo."""

    def __init__(
        self,
        id: int | None,
        gremio_id: int,
        recurso_tipo: str,
        recurso_id: int,
        codigo: str,
        nome: str,
        descricao: str | None = None,
    ):
        self.id = id
        self.gremio_id = gremio_id
        self.recurso_tipo = recurso_tipo
        self.recurso_id = recurso_id
        self.codigo = codigo
        self.nome = nome
        self.descricao = descricao
