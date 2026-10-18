from application.exceptions.base import ConflitoErro, NaoEncontradoErro


class CPFJaCadastradoErro(ConflitoErro):
    def __init__(self, mensagem="Já existe usuário com esse CPF."):
        super().__init__(mensagem)

class EmailJaCadastradoErro(ConflitoErro):
    def __init__(self, mensagem="Já existe usuário com esse Email."):
        super().__init__(mensagem)

class RAJaCadastradoErro(ConflitoErro):
    def __init__(self, mensagem="Já existe usuário com esse RA."):
        super().__init__(mensagem)

class UsuarioNaoExisteErro(NaoEncontradoErro):
    def __init__(self, mensagem="Usuário não existe."):
        super().__init__(mensagem)
