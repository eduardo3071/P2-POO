from app.data.repositorio import PASTA_DADOS, Repositorio, RepositorioJson
from app.models.excecoes import ConflitoErro
from app.models.pessoas import Solicitante, Tecnico


class PessoaController:
    def __init__(
        self,
        repo_solicitantes: Repositorio | None = None,
        repo_tecnicos: Repositorio | None = None,
    ):
        self.repo_solicitantes = repo_solicitantes or RepositorioJson(PASTA_DADOS / "solicitantes.json")
        self.repo_tecnicos = repo_tecnicos or RepositorioJson(PASTA_DADOS / "tecnicos.json")

    def criar_solicitante(self, nome: str, email: str) -> Solicitante:
        solicitante = Solicitante(nome, email)  # o model valida
        if any(r["email"] == solicitante.email for r in self.repo_solicitantes.listar()):
            raise ConflitoErro(f"Já existe um solicitante com o e-mail {solicitante.email}.")
        salvo = self.repo_solicitantes.salvar(solicitante.to_dict())
        return Solicitante.from_dict(salvo)

    def criar_tecnico(self, nome: str) -> Tecnico:
        tecnico = Tecnico(nome)
        salvo = self.repo_tecnicos.salvar(tecnico.to_dict())
        return Tecnico.from_dict(salvo)

    def listar_tecnicos(self) -> list[Tecnico]:
        return [Tecnico.from_dict(r) for r in self.repo_tecnicos.listar()]
