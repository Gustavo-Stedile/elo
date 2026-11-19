class ConcessaoPermissao:
    """Relação que concede uma permissão a um cargo ou membro."""

    def __init__(
        self,
        id: int | None,
        permissao_id: int,
        cargo_id: int | None = None,
        membro_id: int | None = None,
    ):
        if (cargo_id is None) == (membro_id is None):
            raise ValueError("A concessão deve apontar para um cargo ou membro.")
        self.id = id
        self.permissao_id = permissao_id
        self.cargo_id = cargo_id
        self.membro_id = membro_id
