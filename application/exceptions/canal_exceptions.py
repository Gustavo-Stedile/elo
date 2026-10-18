from application.exceptions.base import ConflitoErro, NaoEncontradoErro


class CanalNaoExisteErro(NaoEncontradoErro):
    def __init__(self, mensagem="Canal não encontrado."):
        super().__init__(mensagem)


class CanalJaExisteErro(ConflitoErro):
    def __init__(self, mensagem="Já existe um canal com este nome neste Grêmio."):
        super().__init__(mensagem)
