class Cargo:
    """Papel dentro de um grêmio, agrupando permissões.

    * prioridade: define a hierarquia. Um membro só gerencia cargos com
      prioridade menor que a sua maior prioridade.
    * padrao: cargo implícito de todos os membros (equivalente ao @everyone).
    """

    def __init__(
        self,
        id: int,
        gremio_id: int,
        nome: str,
        cor: str = "#99AAB5",
        prioridade: int = 0,
        permissoes: int = 0,
        padrao: bool = False,
    ):
        self.id = id
        self.gremio_id = gremio_id
        self.nome = nome
        self.cor = cor
        self.prioridade = prioridade
        self.permissoes = permissoes
        self.padrao = padrao
