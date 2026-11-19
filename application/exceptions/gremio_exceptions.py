from application.exceptions.base import ConflitoErro, NaoEncontradoErro, RegraDeNegocioErro


class GremioNaoExisteErro(NaoEncontradoErro):
    def __init__(self, mensagem="Não existe Grêmio com este ID."):
        super().__init__(mensagem)

class GremioJaExisteInstEtapaErro(ConflitoErro):
    def __init__(self, mensagem="Já existe um Grêmio com esta Instituicao e Etapa de Ensino."):
        super().__init__(mensagem)


class RAObrigatorioParaCriarGremioErro(RegraDeNegocioErro):
    def __init__(self, mensagem="Somente usuários com RA cadastrado podem criar grêmios."):
        super().__init__(mensagem)
