from typing import Optional


class PermissaoCanal:
    """Sobrescrita de permissões em um canal.

    Aplica-se a um cargo (cargo_id) OU a um usuário (usuario_id), nunca aos dois.
    """

    def __init__(
        self, id: int, canal_id: int,
        permitir: int = 0, negar: int = 0,
        cargo_id: Optional[int] = None,
        usuario_id: Optional[int] = None,
    ):
        self.id = id
        self.canal_id = canal_id
        self.permitir = permitir
        self.negar = negar
        self.cargo_id = cargo_id
        self.usuario_id = usuario_id
