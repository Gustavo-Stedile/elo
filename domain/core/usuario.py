class Usuario:
    def __init__(
        self, id: int, nome: str, 
        cpf: str, email: str, ra: str, 
        senha: str, gremio_id: int = None
    ):
        self.id = id
        self.nome = nome
        self.cpf = cpf
        self.email = email
        self.ra = ra
        self.senha = senha