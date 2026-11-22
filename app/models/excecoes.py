"""Exceções de negócio do sistema de chamados de TI.

A camada de rotas traduz cada uma no código HTTP correspondente
(ver app/routes/erros.py). Nenhuma regra de negócio termina em 500.
"""


class ErroNegocio(Exception):
    """Classe base de todo erro de regra de negócio."""

    def __init__(self, mensagem: str):
        super().__init__(mensagem)
        self.mensagem = mensagem


class NaoEncontradoErro(ErroNegocio):
    """Registro inexistente (HTTP 404)."""


class ConflitoErro(ErroNegocio):
    """Operação em conflito com o estado atual (HTTP 409)."""


class DadoInvalidoErro(ErroNegocio):
    """Dado que viola uma regra do domínio (HTTP 422)."""
