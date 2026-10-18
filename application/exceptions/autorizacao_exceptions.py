from application.exceptions.base import AcessoNegadoErro, RegraDeNegocioErro


class NaoEMembroErro(AcessoNegadoErro):
    def __init__(self, mensagem="Você não é membro deste Grêmio."):
        super().__init__(mensagem)


class SemPermissaoErro(AcessoNegadoErro):
    def __init__(self, permissoes: list[str] | None = None, mensagem=None):
        if mensagem is None:
            mensagem = "Você não tem permissão para realizar esta ação."
            if permissoes:
                mensagem += f" Necessário: {', '.join(permissoes)}."
        super().__init__(mensagem)


class HierarquiaInsuficienteErro(AcessoNegadoErro):
    def __init__(self, mensagem="Seu cargo é inferior ou igual ao do alvo desta ação."):
        super().__init__(mensagem)


class PermissaoInvalidaErro(RegraDeNegocioErro):
    def __init__(self, mensagem="Conjunto de permissões inválido."):
        super().__init__(mensagem)
