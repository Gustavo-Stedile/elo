from application.exceptions.base import ConflitoErro, NaoEncontradoErro


class GremioNaoExisteErro(NaoEncontradoErro):
    def __init__(self, mensagem="Não existe Grêmio com este ID."):
        super().__init__(mensagem)

class GremioJaExisteInstEtapaErro(ConflitoErro):
    def __init__(self, mensagem="Já existe um Grêmio com esta Instituicao e Etapa de Ensino."):
        super().__init__(mensagem)
