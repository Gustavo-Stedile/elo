from application.exceptions.base import (
    AcessoNegadoErro, ConflitoErro, NaoEncontradoErro
)


class MembroJaExisteErro(ConflitoErro):
    def __init__(self, mensagem="Esse membro já foi adicionado a esse Grêmio."):
        super().__init__(mensagem)

class UsuarioOuGremioNaoEncontradoErro(NaoEncontradoErro):
    def __init__(self, mensagem="Usuário ou Grêmios não foi encontrado para adicionar o novo membro."):
        super().__init__(mensagem)

class MembroNaoExisteErro(NaoEncontradoErro):
    def __init__(self, mensagem="Este usuário não é membro do Grêmio."):
        super().__init__(mensagem)

class FundadorProtegidoErro(AcessoNegadoErro):
    def __init__(self, mensagem="O fundador do Grêmio não pode ser removido nem ter suas permissões alteradas."):
        super().__init__(mensagem)


class MembroNaoPodeSairErro(AcessoNegadoErro):
    def __init__(self, mensagem="Um membro não pode deixar o Grêmio."):
        super().__init__(mensagem)


from application.exceptions.base import RegraDeNegocioErro


class UsuarioForaDaInstituicaoEtapaErro(RegraDeNegocioErro):
    def __init__(self, mensagem="O RA do usuário não corresponde à Instituição e à Etapa deste Grêmio."):
        super().__init__(mensagem)
