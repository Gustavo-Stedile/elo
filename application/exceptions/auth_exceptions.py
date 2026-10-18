class CredenciaisInvalidasErro(Exception):
    def __init__(self, mensagem="Credenciais para login de Usuário invalidas."):
        super().__init__(mensagem)
