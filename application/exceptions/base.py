"""Categorias de erro da aplicação.

A camada de apresentação traduz cada categoria para um status HTTP em um
único lugar (presentation/error_handlers.py), então as rotas não precisam de
try/except para cada exceção.
"""


class ErroDeAplicacao(Exception):
    pass


class NaoEncontradoErro(ErroDeAplicacao):
    """404"""


class ConflitoErro(ErroDeAplicacao):
    """409"""


class AcessoNegadoErro(ErroDeAplicacao):
    """403"""


class RegraDeNegocioErro(ErroDeAplicacao):
    """400"""
