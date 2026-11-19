from application.exceptions.base import ConflitoErro, NaoEncontradoErro, RegraDeNegocioErro


class EnqueteNaoEncontradaErro(NaoEncontradoErro):
    def __init__(self): super().__init__("Enquete não encontrada.")


class EnqueteOpcaoInvalidaErro(RegraDeNegocioErro):
    def __init__(self): super().__init__("Opção de votação inválida.")


class EnqueteVotoInvalidoErro(RegraDeNegocioErro):
    def __init__(self, mensagem="Voto inválido para esta enquete."): super().__init__(mensagem)


class ComunicadoNaoEncontradoErro(NaoEncontradoErro):
    def __init__(self): super().__init__("Comunicado não encontrado.")
