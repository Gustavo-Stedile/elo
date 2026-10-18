
class MembroJaExisteErro(Exception):
    def __init__(self, mensagem="Esse membro já foi adicionado a esse Grêmio."):
        super().__init__(mensagem)

class UsuarioOuGremioNaoEncontradoErro(Exception):
    def __init__(self, mensagem="Usuário ou Grêmios não foi encontrado para adicionar o novo membro."):
        super().__init__(mensagem)
