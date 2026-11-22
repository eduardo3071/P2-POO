from datetime import datetime

from app.data.repositorio import PASTA_DADOS, Repositorio, RepositorioJson
from app.models.chamado import Chamado, classe_do_tipo
from app.models.excecoes import NaoEncontradoErro
from app.models.pessoas import Solicitante, Tecnico


class ChamadoController:
    """Regras de aplicação: orquestra models e repositórios."""

    def __init__(
        self,
        repo_chamados: Repositorio | None = None,
        repo_solicitantes: Repositorio | None = None,
        repo_tecnicos: Repositorio | None = None,
    ):
        self.repo_chamados = repo_chamados or RepositorioJson(PASTA_DADOS / "chamados.json")
        self.repo_solicitantes = repo_solicitantes or RepositorioJson(PASTA_DADOS / "solicitantes.json")
        self.repo_tecnicos = repo_tecnicos or RepositorioJson(PASTA_DADOS / "tecnicos.json")

    # ---------- auxiliares ----------
    def _solicitante(self, id: int) -> Solicitante:
        dados = self.repo_solicitantes.buscar(id)
        if dados is None:
            raise NaoEncontradoErro(f"Solicitante {id} não encontrado.")
        return Solicitante.from_dict(dados)

    def _tecnico(self, id: int) -> Tecnico:
        dados = self.repo_tecnicos.buscar(id)
        if dados is None:
            raise NaoEncontradoErro(f"Técnico {id} não encontrado.")
        return Tecnico.from_dict(dados)

    def _reconstruir(self, dados: dict) -> Chamado:
        classe = classe_do_tipo(dados["tipo"])
        tecnico = self._tecnico(dados["tecnico_id"]) if dados.get("tecnico_id") else None
        return classe(
            titulo=dados["titulo"],
            descricao=dados["descricao"],
            solicitante=self._solicitante(dados["solicitante_id"]),
            tecnico=tecnico,
            id=dados["id"],
            status=dados["status"],
            solucao=dados.get("solucao"),
            aberto_em=datetime.fromisoformat(dados["aberto_em"]),
            fechado_em=datetime.fromisoformat(dados["fechado_em"]) if dados.get("fechado_em") else None,
        )

    def _abertos_do_tecnico(self, tecnico_id: int, ignorar_chamado_id: int | None = None) -> int:
        return sum(
            1
            for r in self.repo_chamados.listar()
            if r.get("tecnico_id") == tecnico_id
            and r["status"] != Chamado.FECHADO
            and r["id"] != ignorar_chamado_id
        )

    def _salvar(self, chamado: Chamado) -> Chamado:
        salvo = self.repo_chamados.salvar(chamado.to_dict())
        chamado.id = salvo["id"]
        return chamado

    # ---------- casos de uso ----------
    def listar(self, tipo: str | None = None) -> list[Chamado]:
        if tipo is not None:
            classe_do_tipo(tipo)  # valida o filtro (422 se inválido)
        registros = self.repo_chamados.listar()
        if tipo is not None:
            registros = [r for r in registros if r["tipo"] == tipo]
        return [self._reconstruir(r) for r in registros]

    def buscar(self, id: int) -> Chamado:
        dados = self.repo_chamados.buscar(id)
        if dados is None:
            raise NaoEncontradoErro(f"Chamado {id} não encontrado.")
        return self._reconstruir(dados)

    def criar(
        self,
        tipo: str,
        titulo: str,
        descricao: str,
        solicitante_id: int,
        tecnico_id: int | None = None,
    ) -> Chamado:
        classe = classe_do_tipo(tipo)
        chamado = classe(titulo, descricao, self._solicitante(solicitante_id))
        if tecnico_id is not None:
            chamado.atribuir(self._tecnico(tecnico_id), self._abertos_do_tecnico(tecnico_id))
        return self._salvar(chamado)

    def alterar(
        self,
        id: int,
        titulo: str | None = None,
        descricao: str | None = None,
        tecnico_id: int | None = None,
    ) -> Chamado:
        chamado = self.buscar(id)
        chamado.garantir_editavel()
        if titulo is not None:
            chamado.titulo = titulo
        if descricao is not None:
            chamado.descricao = descricao
        if tecnico_id is not None:
            chamado.atribuir(
                self._tecnico(tecnico_id),
                self._abertos_do_tecnico(tecnico_id, ignorar_chamado_id=id),
            )
        return self._salvar(chamado)

    def remover(self, id: int) -> None:
        if not self.repo_chamados.remover(id):
            raise NaoEncontradoErro(f"Chamado {id} não encontrado.")

    def fechar(self, id: int, solucao: str) -> Chamado:
        chamado = self.buscar(id)
        chamado.fechar(solucao)
        return self._salvar(chamado)

    def fora_do_prazo(self, agora: datetime | None = None) -> list[Chamado]:
        agora = agora or datetime.now()
        return [c for c in self.listar() if c.fora_do_prazo(agora)]
