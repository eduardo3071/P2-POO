from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.models.excecoes import (
    ConflitoErro,
    DadoInvalidoErro,
    ErroNegocio,
    NaoEncontradoErro,
)

# exceção -> código HTTP
CODIGOS = {
    NaoEncontradoErro: 404,
    ConflitoErro: 409,
    DadoInvalidoErro: 422,
}


def registrar_tratadores(app: FastAPI) -> None:
    @app.exception_handler(ErroNegocio)
    async def tratar_erro_negocio(request: Request, erro: ErroNegocio):
        codigo = next(
            (c for classe, c in CODIGOS.items() if isinstance(erro, classe)), 400
        )
        return JSONResponse(status_code=codigo, content={"detail": erro.mensagem})
