class Cargo:
  def __init__(
      self, id: int, gremio_id: int, nome: str, cor: str, prioridade: int = 0
  ):
    self.id = id
    self.gremio_id = gremio_id
    self.nome = nome
    self.cor = cor