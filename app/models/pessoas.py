from app.models.excecoes import ConflitoErro, DadoInvalidoErro


class Solicitante:
    """Quem abre o chamado (aluno, professor ou funcionário)."""

    def __init__(self, nome: str, email: str, id: int | None = None):
        self.id = id
        self.nome = nome
        self.email = email

    @property
    def nome(self) -> str:
        return self._nome

    @nome.setter
    def nome(self, valor: str) -> None:
        if not isinstance(valor, str) or len(valor.strip()) < 2:
            raise DadoInvalidoErro("O nome do solicitante deve ter ao menos 2 caracteres.")
        self._nome = valor.strip()

    @property
    def email(self) -> str:
        return self._email

    @email.setter
    def email(self, valor: str) -> None:
        if not isinstance(valor, str) or "@" not in valor or " " in valor.strip():
            raise DadoInvalidoErro("E-mail do solicitante inválido.")
        self._email = valor.strip().lower()

    def to_dict(self) -> dict:
        return {"id": self.id, "nome": self.nome, "email": self.email}

    @classmethod
    def from_dict(cls, dados: dict) -> "Solicitante":
        return cls(dados["nome"], dados["email"], dados.get("id"))


class Tecnico:
    """Quem atende os chamados."""

    MAX_ABERTOS = 5  # RN: técnico com no máximo 5 chamados abertos

    def __init__(self, nome: str, id: int | None = None):
        self.id = id
        self.nome = nome

    @property
    def nome(self) -> str:
        return self._nome

    @nome.setter
    def nome(self, valor: str) -> None:
        if not isinstance(valor, str) or len(valor.strip()) < 2:
            raise DadoInvalidoErro("O nome do técnico deve ter ao menos 2 caracteres.")
        self._nome = valor.strip()

    def validar_capacidade(self, abertos: int) -> None:
        """Garante que o técnico ainda pode receber mais um chamado."""
        if abertos >= self.MAX_ABERTOS:
            raise ConflitoErro(
                f"O técnico {self.nome} já tem {abertos} chamados abertos "
                f"(máximo {self.MAX_ABERTOS})."
            )

    def to_dict(self) -> dict:
        return {"id": self.id, "nome": self.nome}

    @classmethod
    def from_dict(cls, dados: dict) -> "Tecnico":
        return cls(dados["nome"], dados.get("id"))
