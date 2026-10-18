from application.exceptions.base import (
    AcessoNegadoErro, NaoEncontradoErro, RegraDeNegocioErro
)


class MensagemNaoExisteErro(NaoEncontradoErro):
    def __init__(self, mensagem="Mensagem não encontrada."):
        super().__init__(mensagem)


class MensagemInvalidaErro(RegraDeNegocioErro):
    def __init__(self, mensagem="A mensagem não pode ser vazia."):
        super().__init__(mensagem)


class NaoEAutorErro(AcessoNegadoErro):
    def __init__(self, mensagem="Apenas o autor pode editar esta mensagem."):
        super().__init__(mensagem)
