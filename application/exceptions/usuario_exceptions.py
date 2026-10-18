
class CPFJaCadastradoErro(Exception):
    def __init__(self, mensagem="Já existe usuário com esse CPF."):
        super().__init__(mensagem)

class EmailJaCadastradoErro(Exception):
    def __init__(self, mensagem="Já existe usuário com esse Email."):
        super().__init__(mensagem)

class RAJaCadastradoErro(Exception):
    def __init__(self, mensagem="Já existe usuário com esse RA."):
        super().__init__(mensagem)

class UsuarioNaoExisteErro(Exception):
    def __init__(self, mensagem="Usuário não existe."):
        super().__init__(mensagem)
