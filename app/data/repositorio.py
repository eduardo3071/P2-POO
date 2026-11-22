import json
import os
import threading
from abc import ABC, abstractmethod
from pathlib import Path

PASTA_DADOS = Path(__file__).parent


class Repositorio(ABC):
    """Contrato de persistência. Trabalha com dicionários simples."""

    @abstractmethod
    def listar(self) -> list[dict]:
        ...

    @abstractmethod
    def buscar(self, id: int) -> dict | None:
        ...

    @abstractmethod
    def salvar(self, registro: dict) -> dict:
        """Cria (sem id) ou atualiza (com id) e devolve o registro salvo."""

    @abstractmethod
    def remover(self, id: int) -> bool:
        ...


class RepositorioJson(Repositorio):
    """Guarda uma lista de registros em um arquivo .json."""

    def __init__(self, caminho: str | Path):
        self._caminho = Path(caminho)
        self._lock = threading.Lock()
        self._caminho.parent.mkdir(parents=True, exist_ok=True)
        if not self._caminho.exists():
            self._gravar([])

    def _ler(self) -> list[dict]:
        with open(self._caminho, "r", encoding="utf-8") as f:
            conteudo = f.read().strip()
        return json.loads(conteudo) if conteudo else []

    def _gravar(self, registros: list[dict]) -> None:
        temporario = self._caminho.with_suffix(".tmp")
        with open(temporario, "w", encoding="utf-8") as f:
            json.dump(registros, f, ensure_ascii=False, indent=2)
        os.replace(temporario, self._caminho)

    def listar(self) -> list[dict]:
        with self._lock:
            return self._ler()

    def buscar(self, id: int) -> dict | None:
        with self._lock:
            for registro in self._ler():
                if registro["id"] == id:
                    return registro
        return None

    def salvar(self, registro: dict) -> dict:
        with self._lock:
            registros = self._ler()
            if registro.get("id") is None:
                registro = {**registro, "id": max((r["id"] for r in registros), default=0) + 1}
                registros.append(registro)
            else:
                for i, existente in enumerate(registros):
                    if existente["id"] == registro["id"]:
                        registros[i] = registro
                        break
                else:
                    registros.append(registro)
            self._gravar(registros)
            return registro

    def remover(self, id: int) -> bool:
        with self._lock:
            registros = self._ler()
            restantes = [r for r in registros if r["id"] != id]
            if len(restantes) == len(registros):
                return False
            self._gravar(restantes)
            return True
