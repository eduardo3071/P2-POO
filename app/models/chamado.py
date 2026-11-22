from abc import ABC, abstractmethod
from datetime import datetime, timedelta

from app.models.excecoes import ConflitoErro, DadoInvalidoErro
from app.models.pessoas import Solicitante, Tecnico


class Chamado(ABC):
    """Topo da hierarquia. Cada filha define o próprio prazo de SLA."""

    ABERTO = "aberto"
    EM_ANDAMENTO = "em_andamento"
    FECHADO = "fechado"

    TIPO = ""  # identificador do tipo, definido em cada filha

    def __init__(
        self,
        titulo: str,
        descricao: str,
        solicitante: Solicitante,
        tecnico: Tecnico | None = None,
        id: int | None = None,
        status: str = ABERTO,
        solucao: str | None = None,
        aberto_em: datetime | None = None,
        fechado_em: datetime | None = None,
    ):
        self.id = id
        self.titulo = titulo
        self.descricao = descricao
        self.solicitante = solicitante  # composição
        self.tecnico = tecnico  # composição (opcional até ser atribuído)
        self._status = status
        self._solucao = solucao
        self._aberto_em = aberto_em or datetime.now()
        self._fechado_em = fechado_em

    # ---------- encapsulamento ----------
    @property
    def titulo(self) -> str:
        return self._titulo

    @titulo.setter
    def titulo(self, valor: str) -> None:
        if not isinstance(valor, str) or len(valor.strip()) < 3:
            raise DadoInvalidoErro("O título deve ter ao menos 3 caracteres.")
        self._titulo = valor.strip()

    @property
    def descricao(self) -> str:
        return self._descricao

    @descricao.setter
    def descricao(self, valor: str) -> None:
        if not isinstance(valor, str) or not valor.strip():
            raise DadoInvalidoErro("A descrição não pode ser vazia.")
        self._descricao = valor.strip()

    @property
    def status(self) -> str:
        return self._status

    @property
    def solucao(self) -> str | None:
        return self._solucao

    @solucao.setter
    def solucao(self, valor: str | None) -> None:
        if not isinstance(valor, str) or not valor.strip():
            raise DadoInvalidoErro("Não é possível fechar o chamado sem uma solução escrita.")
        self._solucao = valor.strip()

    @property
    def aberto_em(self) -> datetime:
        return self._aberto_em

    @property
    def fechado_em(self) -> datetime | None:
        return self._fechado_em

    @property
    def esta_aberto(self) -> bool:
        return self._status != self.FECHADO

    # ---------- polimorfismo ----------
    @abstractmethod
    def prazo_sla(self) -> int:
        """Prazo de atendimento em horas."""

    def prazo_limite(self) -> datetime:
        return self._aberto_em + timedelta(hours=self.prazo_sla())

    def fora_do_prazo(self, agora: datetime | None = None) -> bool:
        """Fechado: compara a data de fechamento. Aberto: compara com agora."""
        referencia = self._fechado_em or agora or datetime.now()
        return referencia > self.prazo_limite()

    # ---------- regras de negócio ----------
    def atribuir(self, tecnico: Tecnico, abertos_do_tecnico: int) -> None:
        """Atribui um técnico. `abertos_do_tecnico` não conta este chamado."""
        if not self.esta_aberto:
            raise ConflitoErro("Chamado fechado não pode ser reatribuído.")
        tecnico.validar_capacidade(abertos_do_tecnico)
        self.tecnico = tecnico
        self._status = self.EM_ANDAMENTO

    def fechar(self, solucao: str, agora: datetime | None = None) -> None:
        if not self.esta_aberto:
            raise ConflitoErro("O chamado já está fechado.")
        self.solucao = solucao  # valida: sem solução escrita não fecha
        self._status = self.FECHADO
        self._fechado_em = agora or datetime.now()

    def garantir_editavel(self) -> None:
        if not self.esta_aberto:
            raise ConflitoErro("Chamado fechado não pode ser alterado.")

    # ---------- serialização ----------
    def to_dict(self) -> dict:
        """Formato salvo no JSON (composição guardada por id)."""
        return {
            "id": self.id,
            "tipo": self.TIPO,
            "titulo": self.titulo,
            "descricao": self.descricao,
            "solicitante_id": self.solicitante.id,
            "tecnico_id": self.tecnico.id if self.tecnico else None,
            "status": self._status,
            "solucao": self._solucao,
            "aberto_em": self._aberto_em.isoformat(),
            "fechado_em": self._fechado_em.isoformat() if self._fechado_em else None,
        }

    def resumo(self, agora: datetime | None = None) -> dict:
        """Formato devolvido pela API (objetos compostos expandidos)."""
        return {
            "id": self.id,
            "tipo": self.TIPO,
            "titulo": self.titulo,
            "descricao": self.descricao,
            "status": self._status,
            "solicitante": self.solicitante.to_dict(),
            "tecnico": self.tecnico.to_dict() if self.tecnico else None,
            "solucao": self._solucao,
            "aberto_em": self._aberto_em.isoformat(),
            "fechado_em": self._fechado_em.isoformat() if self._fechado_em else None,
            "prazo_sla_horas": self.prazo_sla(),
            "prazo_limite": self.prazo_limite().isoformat(),
            "fora_do_prazo": self.fora_do_prazo(agora),
        }


class Hardware(Chamado):
    TIPO = "hardware"
    SLA_HORAS = 48  # exige peça ou visita presencial

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def prazo_sla(self) -> int:
        return self.SLA_HORAS


class Software(Chamado):
    TIPO = "software"
    SLA_HORAS = 24  # instalação/configuração costuma ser remota

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def prazo_sla(self) -> int:
        return self.SLA_HORAS


class Rede(Chamado):
    TIPO = "rede"
    SLA_HORAS = 8  # afeta muitos usuários, prioridade alta

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def prazo_sla(self) -> int:
        return self.SLA_HORAS


# Registro de tipos: evita if/isinstance para escolher a classe.
TIPOS: dict[str, type[Chamado]] = {c.TIPO: c for c in (Hardware, Software, Rede)}


def classe_do_tipo(tipo: str) -> type[Chamado]:
    try:
        return TIPOS[tipo]
    except (KeyError, TypeError):
        raise DadoInvalidoErro(
            f"Tipo de chamado inválido: {tipo!r}. Use: {', '.join(TIPOS)}."
        )
