from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from application.exceptions.base import (
    AcessoNegadoErro,
    ConflitoErro,
    NaoEncontradoErro,
    RegraDeNegocioErro,
)

_STATUS_POR_CATEGORIA = [
    (NaoEncontradoErro, 404),
    (ConflitoErro, 409),
    (AcessoNegadoErro, 403),
    (RegraDeNegocioErro, 400),
]


def _criar_handler(status_code: int):
    async def handler(request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(status_code=status_code, content={"detail": str(exc)})
    return handler


def registrar_error_handlers(app: FastAPI) -> None:
    """Traduz as categorias de erro da aplicação para respostas HTTP."""
    for categoria, status_code in _STATUS_POR_CATEGORIA:
        app.add_exception_handler(categoria, _criar_handler(status_code))
