from datetime import datetime


class Comunicado:
    def __init__(
        self,
        id: int,
        gremio_id: int,
        autor_id: int,
        titulo: str,
        texto: str,
        valido_ate: datetime,
        criado_em: datetime,
        canal_id: int | None = None,
        autor_nome: str | None = None,
    ):
        self.id = id
        self.gremio_id = gremio_id
        self.canal_id = canal_id
        self.autor_id = autor_id
        self.autor_nome = autor_nome
        self.titulo = titulo
        self.texto = texto
        self.valido_ate = valido_ate
        self.criado_em = criado_em
