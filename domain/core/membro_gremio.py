class MembroGremio:
    """Vínculo usuário-grêmio.

    permissoes_permitidas / permissoes_negadas são as sobrescritas
    individuais do usuário no grêmio (somam-se às dos cargos).
    """

    def __init__(
        self, id: int, usuario_id: int, gremio_id: int,
        permissoes_permitidas: int = 0,
        permissoes_negadas: int = 0,
    ):
        self.id = id
        self.usuario_id = usuario_id
        self.gremio_id = gremio_id
        self.permissoes_permitidas = permissoes_permitidas
        self.permissoes_negadas = permissoes_negadas
