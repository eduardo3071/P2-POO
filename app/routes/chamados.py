from fastapi import APIRouter, Response, status

from app.controllers.chamado_controller import ChamadoController
from app.controllers.pessoa_controller import PessoaController
from app.routes.schemas import (
    ChamadoAlterar,
    ChamadoCriar,
    ChamadoFechar,
    SolicitanteCriar,
    TecnicoCriar,
)

router = APIRouter()
chamados = ChamadoController()
pessoas = PessoaController()


@router.get("/chamados", tags=["Chamados"])
def listar_chamados(tipo: str | None = None):
    """Lista chamados; filtre com ?tipo=hardware|software|rede."""
    return [c.resumo() for c in chamados.listar(tipo)]


# Rota fixa antes de /chamados/{id} para não ser capturada como id.
@router.get("/chamados/fora-do-prazo", tags=["Chamados"])
def chamados_fora_do_prazo():
    """Cálculo do tema: chamados que estouraram o SLA."""
    lista = chamados.fora_do_prazo()
    return {"total": len(lista), "chamados": [c.resumo() for c in lista]}


@router.get("/chamados/{id}", tags=["Chamados"])
def buscar_chamado(id: int):
    return chamados.buscar(id).resumo()


@router.post("/chamados", status_code=status.HTTP_201_CREATED, tags=["Chamados"])
def criar_chamado(dados: ChamadoCriar):
    return chamados.criar(**dados.model_dump()).resumo()


@router.put("/chamados/{id}", tags=["Chamados"])
def alterar_chamado(id: int, dados: ChamadoAlterar):
    return chamados.alterar(id, **dados.model_dump()).resumo()


@router.post("/chamados/{id}/fechar", tags=["Chamados"])
def fechar_chamado(id: int, dados: ChamadoFechar):
    return chamados.fechar(id, dados.solucao).resumo()


@router.delete("/chamados/{id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Chamados"])
def remover_chamado(id: int):
    chamados.remover(id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/solicitantes", status_code=status.HTTP_201_CREATED, tags=["Pessoas"])
def criar_solicitante(dados: SolicitanteCriar):
    return pessoas.criar_solicitante(dados.nome, dados.email).to_dict()


@router.post("/tecnicos", status_code=status.HTTP_201_CREATED, tags=["Pessoas"])
def criar_tecnico(dados: TecnicoCriar):
    return pessoas.criar_tecnico(dados.nome).to_dict()
