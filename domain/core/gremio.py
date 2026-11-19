class Gremio:
    def __init__(
        self, id: int, nome: str, 
        instituicao, etapa_ensino, 
        legitimado: bool = False, 
        fundador_id: int = None,
        descricao: str | None = None,
    ):
        self.id = id
        self.nome = nome
        self.descricao = descricao
        self.instituicao = instituicao
        self.etapa_ensino = etapa_ensino
        self.legitimado = legitimado
        self.fundador_id = fundador_id