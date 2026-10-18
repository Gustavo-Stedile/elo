from application.exceptions.base import (
    ConflitoErro, NaoEncontradoErro, RegraDeNegocioErro
)


class CargoNaoExisteErro(NaoEncontradoErro):
    def __init__(self, mensagem="Cargo não encontrado neste Grêmio."):
        super().__init__(mensagem)


class CargoJaExisteErro(ConflitoErro):
    def __init__(self, mensagem="Já existe um cargo com este nome neste Grêmio."):
        super().__init__(mensagem)


class CargoPadraoProtegidoErro(RegraDeNegocioErro):
    def __init__(self, mensagem="Operação não permitida no cargo padrão do Grêmio."):
        super().__init__(mensagem)
